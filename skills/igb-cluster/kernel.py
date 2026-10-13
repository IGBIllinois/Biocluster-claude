"""Helpers for running jobs on the IGB biocluster.

Auto-loaded into the kernel whenever the `igb-cluster` skill is loaded. Standard
library only, so it loads in every environment. Every number here is a measured
property of the cluster, not a default to taste - see references/partitions.md.
"""

import os
import shlex

# Measured 2026-10-04 by `sinfo -o "%P %D %c %m %G %l %t"` and
# `scontrol show partition <p>`. mem_ceiling_mb is RealMemory per node, the hard limit
# a job can be scheduled against; exceeding it pends forever with no error.
# All three partitions have MaxTime=UNLIMITED, DefaultTime=NONE, MaxMemPerNode=UNLIMITED
# (the real limit is the node's RealMemory, not a partition cap).
IGB_PARTITIONS = {
    "admin": {
        "nodes": ["compute-5-8"],
        "cpus_per_node": 32,
        "gpu_type": "A6000",
        "gpus_per_node": 1,
        "gpu_mem_mib": 49140,
        "mem_ceiling_mb": 60000,         # verified 2026-10-04
        "total_cpus": 32,
        "total_nodes": 1,
        "opened_by": "admin_queue",
        "max_time": "UNLIMITED",
        "typical_wait": "under a minute, normally idle",
        "cpus_honoured_exactly": True,
    },
    "gpu": {
        "nodes": ["compute-0-0", "compute-0-1", "compute-0-2"],
        "cpus_per_node": 32,
        "gpu_type": "A40",
        "gpus_per_node": 2,
        "gpu_mem_mib": 46068,
        "mem_ceiling_mb": 250000,        # verified 2026-10-04
        "total_cpus": 96,
        "total_nodes": 3,
        "opened_by": "biocluster_queue",
        "max_time": "infinite (no wall-time limit)",
        "typical_wait": "22-32 h; chronically backlogged by multi-day array jobs",
        "cpus_honoured_exactly": True,
    },
    "normal": {
        # 7 nodes, each 128 cores (AMD EPYC 7543) and 2 TB RAM - uniform per sinfo.
        "nodes": ["compute-1-%d" % i for i in range(7)],
        "cpus_per_node": 128,
        "gpu_type": None,
        "gpus_per_node": 0,
        "gpu_mem_mib": None,
        "mem_ceiling_mb": 2000000,       # verified 2026-10-04 - 2 TB per node
        "total_cpus": 896,
        "total_nodes": 7,
        "opened_by": "biocluster_queue",
        "max_time": "infinite (no wall-time limit)",
        "typical_wait": "short",
        "cpus_honoured_exactly": False,
    },
}

IGB_SITE_POLICY = [
    ("Never run compute on a login node",
     "IGB policy; accounts can be locked. Login nodes are for submitting, staging "
     "and building environments only. All real work goes through sbatch."),
    ("Compute nodes have NO internet",
     "pip install, conda install and any download FAIL on a compute node - this is "
     "why a job must load a pre-built environment rather than create one. The login "
     "node does have egress; stage data there first."),
    ("Never request a whole GPU node",
     "Use --gres=gpu:1. Three GPU nodes serve the whole institute."),
    ("No HIPAA or PHI data on this cluster",
     "IGB policy."),
    ("Nothing here is backed up",
     "Storage costs $8.78/TB/month. Clean up intermediates; do not leave large "
     "scratch files sitting around."),
    ("Always request resources explicitly",
     "Nodes are large (128 cores on `normal`) but a job that does not ask gets a "
     "minimal default slice of 2 CPUs regardless of what the node has."),
]

# Verified 2026-10-04 on the login node.
IGB_FACTS = {
    "no_shared_conda_env": (
        "There is NO pre-built shared conda environment on this cluster. `conda` is "
        "not on the default PATH, and it is still not on PATH after "
        "`module load Miniconda3/24.7.1-0` in a non-interactive shell (conda needs its "
        "profile.d/conda.sh sourced). Eight Anaconda3 and four Miniconda3 modules exist "
        "to build on top of. The house pattern is a venv layered on an IGB module "
        "(`python -m venv --system-site-packages`), which is what cs/scanpy-leiden is."
    ),
    "no_slurm_account": (
        "`sacctmgr show assoc user=$USER` returns no rows: no account string is "
        "required on submission. Do not add --account."
    ),
    "quota_unavailable": (
        "`quota -s` fails on this cluster - the quota servers refuse the connection "
        "(data-robinson, data-hudson, mirror-priv). Do not rely on it; /home is a "
        "2.4 PB shared filesystem reported at 88% used, 310 TB available."
    ),
    "group_dirs_not_writable": (
        "No directory under /home/groups is writable by this account. 16 of the 18 are "
        "drwxrws--- owned by a lab-specific group this account is not in (groups: "
        "sagarj2, biocluster_queue, admin_queue, igb_users); the other two "
        "(example_layouts, hpcbio_shared) are drwxr-xr-x root:root - world-readable "
        "but root-owned, so not writable either. A lab shared root under "
        "/home/groups requires IGB to create a group. User home "
        "(/home/n-z/<user>, drwxr-sr-x) is world-readable, so it can host a read-only "
        "shared root in the interim."
    ),
    "module_count": "1784 lines of `module avail` output - always check before installing.",
}

IGB_GPU_DRIVER = {"driver": "570.86.15", "cuda": "12.8", "compute_capability": "8.6"}

IGB_PATHS = {
    "af3_container": "$EBROOTALPHAFOLD/alphafold.sif",
    "af3_root": "/home/apps/software/alphafold/3.0.2",
    "af3_db": "/private_stores/mirror/alphafold3-db/20250520",
    "af3_weights": "$BIODB/parameters/af3.bin",
    "pdb_seqres": "$BIODB/pdb_seqres_2022_09_28.fasta",
    "template_cutoff": "2022-09-28",
}


def igb_partitions(group_names=None):
    """The partition table, optionally filtered to partitions a group list opens.

    group_names: iterable of Unix group names (from `id`). None returns everything.
    """
    if group_names is None:
        return dict(IGB_PARTITIONS)
    groups = set(group_names)
    return {k: v for k, v in IGB_PARTITIONS.items() if v["opened_by"] in groups}


def igb_shared_root(default=None):
    """Where the shared envs and modulefiles live, per install."""
    return os.environ.get("CS_SHARED_ROOT") or default or "$CS_SHARED_ROOT"


def igb_sbatch_preamble(partition="admin", cpus=8, mem_gb=16, gpus=0,
                        time_min=None, nodes=1):
    """Emit #SBATCH directives with --mem clamped to the node ceiling.

    Raises ValueError on an unknown partition or a GPU request a partition cannot
    satisfy. A clamped memory request is noted in a comment line so the clamp is
    visible in the job script and in the approval card rather than silent.
    """
    if partition not in IGB_PARTITIONS:
        raise ValueError(
            "unknown partition %r; known: %s (others on this cluster are "
            "group-restricted - check `id` against `scontrol show partition`)"
            % (partition, ", ".join(sorted(IGB_PARTITIONS)))
        )
    p = IGB_PARTITIONS[partition]
    if gpus > p["gpus_per_node"]:
        raise ValueError(
            "partition %r has %d GPU(s) per node (%s), cannot satisfy gpus=%d"
            % (partition, p["gpus_per_node"], p["gpu_type"], gpus)
        )
    if cpus > p["cpus_per_node"]:
        raise ValueError(
            "partition %r has %d CPUs per node, cannot satisfy cpus=%d"
            % (partition, p["cpus_per_node"], cpus)
        )

    if p["mem_ceiling_mb"] is None:
        # No measured RealMemory for this partition: do not clamp, and say so.
        ceiling_gb = None
    else:
        ceiling_gb = p["mem_ceiling_mb"] // 1000
    asked_gb, note = mem_gb, None
    if ceiling_gb is None:
        note = ("# NOTE: node memory ceiling for partition %r has never been read off "
                "scontrol - request explicitly and verify with `scontrol show partition "
                "%s | grep -i mem`" % (partition, partition))
    elif mem_gb > ceiling_gb:
        mem_gb = ceiling_gb
        note = ("# NOTE: --mem clamped from %dg to %dg - RealMemory on %s is %d MB, "
                "and an over-ceiling request pends forever with Reason=Resources"
                % (asked_gb, mem_gb, ", ".join(p["nodes"]) or partition,
                   p["mem_ceiling_mb"]))

    lines = []
    if note:
        lines.append(note)
    lines += ["#SBATCH -p %s" % partition,
              "#SBATCH -N %d" % nodes,
              "#SBATCH -n %d" % cpus,
              "#SBATCH --mem=%dg" % mem_gb]
    if gpus:
        lines.append("#SBATCH --gres=gpu:%d" % gpus)
    if time_min:
        lines.append("#SBATCH --time=%d" % time_min)
    return "\n".join(lines)


def igb_choose_partition(needs_gpu=False, mem_gb=16):
    """Pick a partition from the two constraints that actually bind here.

    The tradeoff is specific to this cluster: the idle GPU partition has the SMALLEST
    memory (60 GB), and the huge-memory partition has no GPU at all.
    """
    if not needs_gpu:
        return ("normal", "7 nodes x 128 cores x 2 TB, short wait, no GPU")
    if mem_gb <= IGB_PARTITIONS["admin"]["mem_ceiling_mb"] // 1000:
        return ("admin", "idle A6000, starts in under a minute, but only 60 GB RAM")
    return ("gpu", "250 GB per node and 2x A40, but 22-32 h observed queue - "
                   "say so before submitting, and size run_timeout_s in tens of hours")


def igb_tmpdir_guard():
    """Guarded TMPDIR. Nodes report TmpDisk=0 yet mkdir has been seen to succeed."""
    return (
        'if mkdir -p "/scratch/$SLURM_JOB_ID" 2>/dev/null '
        '&& [ -w "/scratch/$SLURM_JOB_ID" ]; then\n'
        '  export TMPDIR="/scratch/$SLURM_JOB_ID"\n'
        "  trap 'rm -rf \"/scratch/$SLURM_JOB_ID\"' EXIT\n"
        "else\n"
        '  export TMPDIR="$PWD/tmp"; mkdir -p "$TMPDIR"\n'
        "fi"
    )


def igb_env_preamble(env_name, shared_root=None):
    """Load a shared environment by name. Never build one in a job."""
    root = igb_shared_root(shared_root)
    return ('module use %s/modulefiles\nmodule load cs/%s\n'
            'export MPLCONFIGDIR="$PWD/.mplcache"'
            % (shlex.quote(root).replace("'$CS_SHARED_ROOT'", "$CS_SHARED_ROOT"),
               env_name))


def igb_job_script(body, env_name=None, log="run.log", **preamble_kwargs):
    """Assemble a complete, policy-conforming job script."""
    parts = [igb_sbatch_preamble(**preamble_kwargs), "", igb_tmpdir_guard(), ""]
    if env_name:
        parts += [igb_env_preamble(env_name), ""]
    parts += ["%s 2>&1 | tee -a ./%s" % (body.strip(), log),
              "ls -lh ./ ./out 2>/dev/null || true"]
    return "\n".join(parts)


def igb_audit_commands(since="2026-01-01", jobid="<jobid>", workdir="<workdir>"):
    """Cluster-side commands the user can run to check the work themselves.

    Agent-submitted jobs appear in Slurm as operon-<first 8 chars of the job uuid>.
    """
    return {
        "history": ("sacct -u $USER -S %s -X --format=JobID,JobName,Partition,"
                    "AllocCPUS,ReqTRES%%38,Elapsed,State,Submit,End" % since),
        "queue": "squeue -u $USER",
        "gpu_backlog": 'squeue -p gpu -t PENDING -o "%.12i %.10u %.20S %R"',
        "why_pending": "scontrol show job %s | grep -E 'Reason|TRES'" % jobid,
        "efficiency": "seff %s" % jobid,
        "live_log": "tail -f %s/run.log" % workdir,
    }


def igb_site_policy():
    """(rule, why) for the IGB site rules. Two are enforcement, not etiquette:
    login-node compute can lock the account, and compute nodes have no egress."""
    return list(IGB_SITE_POLICY)


def igb_known_failures():
    """(symptom, diagnostic, fix) for the failure modes already paid for."""
    return [
        ("PENDING forever, Reason=Resources, no error",
         "scontrol show job <id> | grep -E 'Reason|TRES'",
         "--mem exceeds the node ceiling (60 GB on admin). The only silent failure."),
        ("PENDING for a day on gpu",
         'squeue -p gpu -t PENDING -o "%.12i %.10u %.20S %R"',
         "gpu is backlogged 22-32 h; use admin unless the A6000 is unsuitable."),
        ("submit_job raised but a job may be queued",
         "sacct -u $USER -S <today> | grep operon-",
         "Never resubmit before checking; harvest from "
         "<scratch>/.claude-science/jobs/<uuid>/ with c.download."),
        ("Job dies in a temp-file step",
         "grep -i tmp run.log",
         "Unguarded /scratch mkdir; use igb_tmpdir_guard()."),
        ("Command after `module load` hits the system python, or "
         "libpython3.10.so.1.0: cannot open shared object file",
         "module list   # says 'No modules loaded'",
         "`module load` was piped or command-substituted, so it ran in a subshell and "
         "the load was discarded. Run it bare on its own line, never `| head`/`| tee`."),
        ("sc.tl.leiden raises on the scanpy module",
         "python -c 'import leidenalg'",
         "Module ships no leidenalg/igraph; module load cs/scanpy-leiden."),
        ("Job COMPLETED but no log came back",
         "ls <workdir>",
         "slurm-<jobid>.out is never harvested; tee to run.log and name it in outputs."),
        ("PermissionError reading hpc/<job_id>/ locally",
         "python: open('hpc/<id>/f')",
         "Outside the sandbox: save_artifacts first, then host.artifact_path(vid)."),
        ("Workdir holds only cmd.sh, job.sh, _staged",
         "ls <workdir>",
         "Normal - ssh:// inputs symlink at job start. Not a staging failure."),
    ]
