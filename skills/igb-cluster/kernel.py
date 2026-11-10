"""Helpers for running jobs on IGB Biocluster 4.

Auto-loaded into the kernel whenever the `igb-cluster` skill is loaded from a LOCAL
install. The GitHub skill importer excludes sidecar files, so anyone importing this
repository from GitHub will not have these functions - every rule encoded here is also
written out in prose in SKILL.md. Do not call these unless you have confirmed they
exist in your kernel.

Standard library only, so it loads in every environment. Every number here is a
measured property of the cluster, not a default to taste - see references/partitions.md.

MEASURED ON BIOCLUSTER 4 (biologin-0), 2026-10-31 / 2026-11-01. Biocluster 3 numbers
are not carried forward; several of them are now actively wrong.
"""

import os

# Measured 2026-10-31 by `sinfo -a` and `scontrol show partition <p>`.
# mem_ceiling_mb is RealMemory per node - the hard limit a job can be scheduled
# against; exceeding it pends forever with no error.
# `normal` and `gpu` are the two partitions an ordinary biocluster_queue account can
# submit to, and the only two represented here. `sinfo -a` reports sixteen; the other
# fourteen belong to specific labs, projects, teaching allocations or IGB staff, and
# several sit idle advertising GPUs and large-memory nodes that look better than
# anything here - which makes them the most likely thing to recommend by mistake.
# An idle node you cannot submit to is not capacity.
# The access test is that `scontrol show partition <name>` returns EMPTY for a
# partition the account cannot use, while `sinfo -a` still lists it.
IGB_PARTITIONS = {
    "gpu": {
        "nodes": ["compute-0-0", "compute-0-1", "compute-0-2"],
        "cpus_per_node": 32,
        "gpu_type": "A40",
        "gpus_per_node": 2,
        "gpu_mem_gb": 47.7,              # measured via torch on compute-0-0
        "compute_capability": "8.6",     # sm_86 - NO FP8 on this card
        "mem_ceiling_mb": 250000,
        "total_cpus": 96,
        "total_nodes": 3,
        "nodes_up_last_seen": 1,         # 2026-10-31: only compute-0-0
        "opened_by": "biocluster_queue",
        "max_time": "infinite (no wall-time limit)",
    },
    "normal": {
        "nodes": ["compute-1-%d" % i for i in range(7)],
        "cpus_per_node": 128,            # AMD EPYC 7543
        "gpu_type": None,
        "gpus_per_node": 0,
        "gpu_mem_gb": None,
        "compute_capability": None,
        "mem_ceiling_mb": 2000000,       # ~2 TB per node
        "total_cpus": 896,
        "total_nodes": 7,
        "nodes_up_last_seen": 2,         # 2026-10-31: compute-1-0, compute-1-2
        "opened_by": "biocluster_queue",
        "max_time": "infinite (no wall-time limit)",
    },
}

IGB_SITE_POLICY = [
    ("Never run compute on a login node",
     "IGB policy; accounts can be locked. Login nodes are for submitting, staging "
     "and building environments only. All real work goes through sbatch. The one "
     "exception is the Nextflow driver process, which is a scheduler, not compute."),
    ("Compute nodes have NO internet",
     "pip install, conda install and any download FAIL on a compute node - this is "
     "why a job must load a pre-built environment rather than create one. The login "
     "node does have egress; stage data there first."),
    ("Never request a whole GPU node",
     "Use --gres=gpu:1. Three GPU nodes serve the whole institute."),
    ("No HIPAA or PHI data on this cluster",
     "IGB policy."),
    ("Nothing here is backed up",
     "Storage is billed. Clean up intermediates."),
    ("Always request resources explicitly",
     "Nodes are large (128 cores on `normal`) but a job that does not ask gets a "
     "minimal default slice of 2 CPUs regardless of what the node has."),
]

# Verified 2026-10-31 on biologin-0. Several of these REVERSE a Biocluster 3 fact.
IGB_FACTS = {
    "conda_works": (
        "REVERSAL vs Biocluster 3: conda IS usable. `module load Miniconda3/26.9.4` "
        "puts conda on PATH. Create environments on the LOGIN NODE only. The pattern "
        "with measured results behind it here is still a venv layered on an IGB "
        "module: `python -m venv --system-site-packages`."
    ),
    "nvidia_smi_on_path": (
        "REVERSAL vs Biocluster 3: nvidia-smi IS on PATH at /usr/bin/nvidia-smi on GPU "
        "compute nodes. Do not add an `nvidia-smi || exit 1` preflight; the old guard "
        "would have aborted every GPU job."
    ),
    "tensorflow_no_gpu": (
        "TensorFlow/2.21.0 reports `GPUs visible: 0` on the A40 - measured alone AND "
        "with CUDA/13.1.0 + cuDNN/9.17.1.4-CUDA-13.1.0 loaded. Biocluster 4 ships only "
        "CUDA 13.x and TF 2.21 is built against CUDA 12, so no module pairing fixes it. "
        "Use PyTorch for GPU work. A TF job runs on CPU with no error - a silent "
        "performance failure."
    ),
    "scratch_is_job_local": (
        "Inside a job Slurm provides a node-local /scratch/$SLURM_JOB_ID and sets TMPDIR "
        "to it (measured on compute-0-0, job 17991). On the LOGIN node there is no "
        "/scratch and TMPDIR is unset - which is why an earlier version of these notes "
        "wrongly claimed /scratch does not exist at all. Use the guarded form from "
        "igb_tmpdir_guard(). Node-local scratch is not shared between nodes and is "
        "cleaned at job end, so copy results into the workdir before exiting."
    ),
    "single_toolchain": (
        "One toolchain generation, 15.2.0. Over the live inventory of 212 "
        "name/version pairs: 108 carry -IGB-gcc-15.2.0, 6 carry -GCCcore-15.2.0, 3 "
        "carry it in another form (GCC/15.2.0, IGB-gcc/15.2.0, "
        "OpenMPI/5.0.9-GCC-15.2.0) and 95 carry no toolchain tag (108+6+3+95=212; the "
        "three added since 2026-10-31 are cellranger 10.1.0, cellranger-arc 2.2.0 and "
        "cellranger-atac 2.2.0). "
        "Biocluster 3's IGB-gcc-4.9.4 / IGB-gcc-8.2.0 split is gone, and with it the "
        "mixing hazard. Python-linked modules carry -Python-3.14.0."
    ),
    "stack_shrank": (
        "173 module names / 209 versions, down from 927 / 1795 on Biocluster 3. "
        "Gone: SPAdes, Trinity, salmon, scanpy, snakemake, rosetta, PyRosetta, pymol, "
        "rdkit, ViennaRNA, RNAstructure, RepeatMasker, hhsuite, cromwell, toil, "
        "standalone foldseek, transformers, jax, Anaconda3. Always `module avail` "
        "before promising a tool."
    ),
    "no_slurm_account": (
        "`sacctmgr show assoc user=$USER` returns no rows: no account string is "
        "required on submission. Do not add --account."
    ),
    "quota_unavailable": (
        "`quota -s` returns nothing at all. Size against `df -h $HOME` and sacct "
        "MaxRSS instead. Home is a 2.8 PB CephFS with ~1.3 PB available."
    ),
    "group_dirs_not_writable": (
        "/home/groups exists (drwxrwxr-x root:root) but nothing in it is writable by "
        "an ordinary account. A lab shared root there requires IGB to create a group."
    ),
}

IGB_GPU = {
    "name": "NVIDIA A40",
    "compute_capability": "8.6",
    "vram_gb": 47.7,
    "torch": "2.14.1+cu130",
    "cudnn": "92400",
    "fp8": False,   # sm_86 has no FP8 - Evo 2 40B/20B/1B cannot run here at all
    "matmul_4000x4000_s": 0.255,
}

IGB_PATHS = {
    "af3_container": "$EBROOTALPHAFOLD/alphafold.sif",
    "af3_root": "/home/apps/software/alphafold/3.0.4",
    "af3_db": "/private_stores/mirror/alphafold3-db/20250520",
    "af3_weights_dir": "$BIODB/parameters",
    "pdb_seqres": "$BIODB/pdb_seqres_2022_09_28.fasta",
    "template_cutoff": "2022-09-28",
    "mirror_root": "/private_stores/mirror",
}

# The four database modules whose modulefile points at /home/mirrors (which does not
# exist). The real mount is /home/mirror, a symlink into /private_stores/mirror.
IGB_BROKEN_DB_MODULES = {
    "chocophlan": "/private_stores/mirror/chocophlan/0.1.1",
    "clusterblast": "/private_stores/mirror/clusterblast/20170105",
    "gatkbundle": "/private_stores/mirror/gatkbundle/20191118",
    "silva": "/private_stores/mirror/silva/138.1",
}


def igb_db_var(module_name):
    """The environment variable a reference-database module sets.

    EBROOT + the module name uppercased with every '-' replaced by 'MIN'.
    Verified against all 29 database modules with zero exceptions, 2026-10-31.

    >>> igb_db_var("ncbi-blastdb")
    'EBROOTNCBIMINBLASTDB'
    """
    return "EBROOT" + module_name.upper().replace("-", "MIN")


def igb_partitions(group_names=None):
    """The partition table, optionally filtered to partitions a group list opens.

    group_names: iterable of Unix group names (from `id`). None returns everything.
    """
    if group_names is None:
        return dict(IGB_PARTITIONS)
    groups = set(group_names)
    return {k: v for k, v in IGB_PARTITIONS.items() if v["opened_by"] in groups}


def igb_sbatch_preamble(partition="normal", cpus=8, mem_gb=16, gpus=0,
                        time_min=None, nodes=1):
    """Emit #SBATCH directives with --mem clamped to the node ceiling.

    Raises ValueError on an unknown partition or a GPU request a partition cannot
    satisfy. A clamped memory request is noted in a comment line so the clamp is
    visible in the job script rather than silent.
    """
    if partition not in IGB_PARTITIONS:
        raise ValueError(
            "partition %r is not one an ordinary account can submit to; use %s. "
            "The other partitions in `sinfo -a` belong to specific labs, projects or "
            "IGB staff - confirm with `scontrol show partition %s`, which returns "
            "empty when there is no access."
            % (partition, " or ".join(sorted(IGB_PARTITIONS)), partition)
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

    ceiling_gb = p["mem_ceiling_mb"] // 1000
    asked_gb, note = mem_gb, None
    if mem_gb > ceiling_gb:
        mem_gb = ceiling_gb
        note = ("# NOTE: --mem clamped from %dg to %dg - RealMemory on %s is %d MB, "
                "and an over-ceiling request pends forever with Reason=Resources"
                % (asked_gb, mem_gb, partition, p["mem_ceiling_mb"]))

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

    Only two partitions are open to general users, so the choice is just GPU or not.
    Queue depth is deliberately not asserted: Biocluster 3 showed 22-32 h GPU waits,
    while Biocluster 4 has started GPU jobs in under 20 s. Measure it with
    `squeue -p gpu -t PENDING` rather than quoting a number.
    """
    if not needs_gpu:
        return ("normal", "7 nodes x 128 cores x ~2 TB, no GPU")
    return ("gpu", "2x A40 (47.7 GB, sm_86) per node, 250 GB node ceiling; "
                   "check `squeue -p gpu -t PENDING` before promising a turnaround")


def igb_tmpdir_guard():
    """Writable TMPDIR, preferring the one Slurm already set.

    Inside a job Slurm provides /scratch/$SLURM_JOB_ID and sets TMPDIR to it; on the
    login node TMPDIR is unset. This form uses Slurm's when present and falls back to
    the workdir when not, so it is correct in both places.
    """
    return ': "${TMPDIR:=$PWD/tmp}"; mkdir -p "$TMPDIR"; export TMPDIR'


def igb_venv_preamble(venv_path, module=None):
    """Activate a venv built on the login node, optionally on top of an IGB module.

    Never build an environment inside a job - compute nodes have no egress.
    """
    lines = ["module purge"]
    if module:
        lines.append("module load %s" % module)
    # NB: a tilde inside double quotes is NOT expanded by bash, so normalise it.
    venv_path = venv_path.replace("~", "$HOME", 1) if venv_path.startswith("~") else venv_path
    lines += ['source "%s/bin/activate"' % venv_path,
              'export MPLCONFIGDIR="$PWD/.mplcache"']
    return "\n".join(lines)


def igb_job_script(body, venv_path=None, module=None, log="run.log",
                   **preamble_kwargs):
    """Assemble a complete, policy-conforming job script.

    Returns LF-terminated text. Write it with newline="\\n" - CRLF endings silently
    break job scripts on this cluster ('2>&1' becomes an ambiguous redirect).
    """
    parts = ["#!/bin/bash", igb_sbatch_preamble(**preamble_kwargs), "",
             'cd "$SLURM_SUBMIT_DIR"', igb_tmpdir_guard(), ""]
    if venv_path or module:
        parts += [igb_venv_preamble(venv_path or "$HOME/models/venv", module), ""]
    parts += ["%s 2>&1 | tee -a ./%s" % (body.strip(), log),
              "ls -lh ./ ./out 2>/dev/null || true"]
    return "\n".join(parts)


def igb_audit_commands(since="2026-01-01", jobid="<jobid>", workdir="<workdir>"):
    """Cluster-side commands the user can run to check the work themselves."""
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
    """(symptom, diagnostic, fix) for the failure modes already paid for.

    Full table, including transport-level modes: references/failures.md.
    """
    return [
        ("PENDING forever, Reason=Resources, no error",
         "scontrol show job <id> | grep -E 'Reason|TRES'",
         "--mem exceeds the node RealMemory (2,000,000 MB on normal, 250,000 MB on "
         "gpu). The only silent failure mode on this cluster."),
        ("TensorFlow trains slowly; 'GPUs visible: 0'",
         "python -c 'import tensorflow as tf; print(tf.config.list_physical_devices(\"GPU\"))'",
         "TF 2.21.0 cannot see the A40 and no CUDA/cuDNN module pairing fixes it. "
         "Use PyTorch, or raise it with IGB."),
        ("Job dies in a temp-file step, or a tool writes into $HOME",
         "grep -i tmp run.log",
         'No /scratch on Biocluster 4. export TMPDIR="$PWD/tmp".'),
        ("module load of a Biocluster 3 tool fails",
         "module avail <name>",
         "The stack shrank from 927 names to 173. Check before promising; do not "
         "invent a module name."),
        ("Command after `module load` hits the system python",
         "module list   # says 'No modules loaded'",
         "`module load` was piped or command-substituted, so it ran in a subshell and "
         "the load was discarded. Run it bare on its own line, never `| head`/`| tee`."),
        ("A database module loads but the path does not exist",
         'ls "$(eval echo \\$$(igb_db_var(name)))"',
         "Four modulefiles point at /home/mirrors. See IGB_BROKEN_DB_MODULES."),
        ("torch.load raises 'Weights only load failed'",
         "-",
         "PyTorch >= 2.6 defaults weights_only=True. For ESM-2: "
         "torch.serialization.add_safe_globals([argparse.Namespace])."),
        ("'Device compute capability 8.9 or higher required for FP8'",
         "-",
         "The A40 is sm_86 and has no FP8. Disable FP8 in the model config; the Evo 2 "
         "40B/20B/1B models cannot run here at all."),
        ("submit_job raised but a job may be queued",
         "sacct -u $USER -S <today> -X | grep operon-",
         "Never resubmit before checking - the sbatch usually dispatched anyway."),
        ("Job script fails with 'ambiguous redirect'",
         "ls -b <workdir>   # look for \\r in filenames",
         "CRLF line endings. Write job scripts with newline='\\n'."),
        ("Job COMPLETED but no log came back",
         "ls <workdir>",
         "slurm-<jobid>.out is never harvested; tee to run.log and name it in outputs."),
        ("PermissionError reading hpc/<job_id>/ locally",
         "python: open('hpc/<id>/f')",
         "Outside the sandbox: save_artifacts first, then host.artifact_path(vid)."),
    ]
