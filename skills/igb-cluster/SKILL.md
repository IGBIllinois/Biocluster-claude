---
name: igb-cluster
description: "Run jobs on the IGB Biocluster 4 (University of Illinois Urbana-Champaign) through a Claude Science SSH compute target. Carries the partition map with its group ACLs and node hardware, the module-stack conventions, the reference-database paths, the measured runtimes, the known failure modes with their diagnostics, and the house rules for what may and may not be run there. Load before submitting any job to the igb target, before estimating a cluster runtime, or when a cluster job has failed and you need the diagnostic."
---

# IGB Biocluster 4

The compute target is **`igb`**, login node **`biologin-0.igb.illinois.edu`**
(`ClusterName=biocluster`, controller `biocluster4-headnode`, **Slurm 25.05.1**).

**This is Biocluster 4, which replaced Biocluster 3 in October 2026.** Everything below
was re-measured on the new hardware on **2026-10-31**. If you find a claim anywhere that
mentions `biologin-3`, the `IGB-gcc-8.2.0` toolchain, `/scratch`, or a 927-module stack,
it is Biocluster 3 material and is **wrong here** — report it rather than acting on it.

## About the optional sidecar

The repository also carries `kernel.py`, which turns the rules below into callable
helpers (`igb_sbatch_preamble`, `igb_choose_partition`, `igb_job_script`, ...). **It is
NOT installed when this skill is imported from GitHub — imported skills are
documentation-only and sidecar files are excluded.** Everything it encodes is stated in
full in this document, so nothing is lost; the file is there for anyone who wants to
install it by hand into a local copy of the skill. Do not call those functions unless
you have confirmed they exist in your kernel.

## Confidence tiers

Every capability claim in the `igb-*` skills is tagged:

- **A — verified**: run on Biocluster 4; the recipe is the one that worked, with timings.
- **B — documented**: the module exists and the invocation comes from `module show` or
  IGB's docs, but nobody has run it here.
- **C — listed**: the module is present. Nothing further is claimed.

Treat B as a starting point and C as "it exists, go and find out". If you run something
at tier C and it works, say so in your reply so the skill can be promoted.

## Order of operations

1. `compute_details({provider: 'ssh:igb', mode: 'read'})` — the local, per-install copy
   of these facts, plus anything later sessions appended.
2. `c = host.compute.create('igb')` in a **`repl`** cell.
3. Pick the partition from the table below against the user's groups. Do not probe.
4. Build the job script from the skeleton below, or adapt one in `recipes/`.
5. Submit, end the cell, park on `wait_for_notification`.

**Do not go exploring.** Everything in this document was paid for by an earlier
session. If a fact you need is genuinely absent, get it in **one** call rather than a
handful of probes — then append what it told you to `compute_details` so the next
session does not pay again:

    id; sinfo -a -o "%.14P %.6D %.20G %.10m %.12l %.20A"; module avail 2>&1 | grep -i <name>

Keep probes to `ls` and `module avail`. **Never** `find` or `du` over
`/private_stores/mirror` or `/home` — those are multi-petabyte networked filesystems and
the call will be killed before it returns.

## Site policy — IGB's rules, not ours

Two of these are enforcement, not etiquette.

1. **Never run compute on a login node.** IGB policy; accounts can be locked. Login
   nodes are for submitting, staging data and building environments only.
2. **Compute nodes have no internet.** `pip install`, `conda install` and any download
   *fail* there — this is the mechanical reason a job must load a pre-built environment
   instead of creating one. The login node does have egress: stage data there first.
   (Measured: a `pooch` dataset fetch inside a compute job failed with a connection
   error while the identical call on `biologin-0` succeeded.)
3. **Never request a whole GPU node.** `--gres=gpu:1`. Three GPU nodes serve the whole
   institute.
4. **No HIPAA or PHI data on this cluster.**
5. **Nothing here is backed up**, and storage is charged. Clean up intermediates.
6. **Always request resources explicitly.** Nodes are large — 128 cores on `normal` —
   but a job that does not ask gets a minimal default slice of **2 CPUs** regardless.

## Hard rules

These are not preferences. Each one is a failure already paid for, or a boundary the
user set.

1. **Never build an environment inside a job.** No `pip install`, no `conda create`, no
   `python -m venv`, no `apptainer build` in a batch script — compute nodes have no
   egress, so it cannot work. Build on the login node, then load it in the job. See
   *Building an environment* below.
2. **Never touch another user's work.** No `scancel`, `renice`, or preemption of a job
   you did not submit. No Slurm priority manipulation. If the partition you want is
   busy, use an idle partition the account is entitled to, or wait.
3. **Cap memory at the node's ceiling, not the job's ambition.** See the partition
   table. An over-ceiling request does not error — it pends forever. This is the only
   silent failure mode on this cluster.
4. **The user acts on the cluster too.** They cancel jobs under their own uid without
   telling you. Re-check `squeue`/`sacct` before reasoning about a job you submitted.
5. **Never resubmit after a transport-level submit failure** until you have checked
   `sacct` for the job. A dead connection can follow a successful `sbatch`;
   resubmitting forfeits a queue position and double-books the GPU.
6. **Write outputs into the job workdir** (`./` or `./out`), never to an absolute path
   under home — only workdir files are harvested back.
7. **`tee` console output to a named `run.log`.** `slurm-<jobid>.out` is never harvested.
8. **Tell the user where work runs** and give them the cluster-side command to check it
   themselves (`squeue`, `sacct`, `seff`, `tail -f run.log`). They audit independently;
   they should not have to take your report on trust.

## Partitions

Full table with group ACLs, live node states and the partitions to avoid:
`references/partitions.md`. Check access with `id` against
`scontrol show partition | grep AllowGroups`.

| Partition | Hardware | Node mem ceiling | Use it for |
|---|---|---|---|
| `normal` | 7 nodes, 128 CPU (EPYC 7543), ~2 TB each | **2,000,000 MB** | everything CPU-only |
| `gpu` | 3 nodes, 32 CPU, 2x **A40 (47.7 GB, sm_86)** each | **250,000 MB** | anything needing a GPU |

**These two are the only general-access partitions** — both gated on the
`biocluster_queue` Unix group. Verified 2026-10-31 (`sinfo`, `scontrol show partition`).
Configured totals: `normal` 896 CPUs / 7 nodes, `gpu` 96 CPUs / 3 nodes — but **check
what is actually up**, which on 2026-10-31 was **2 of 7** and **1 of 3** respectively.
Both carry `MaxTime=UNLIMITED`, `DefaultTime=NONE`, `MaxMemPerNode=UNLIMITED`, so the
binding limit is always the node's RealMemory, never a partition cap, and long jobs are
allowed.

| Need | Partition | Why |
|---|---|---|
| a GPU | `gpu` | `--gres=gpu:1` |
| no GPU | `normal` | 2 TB and 128 cores |

**Queue depth varies enormously — measure it, do not quote a number.** On Biocluster 3
GPU waits of 22-32 h were recorded; across a full day of Biocluster 4 testing the GPU
queue was empty and jobs started in under 20 s. Run
`squeue -p gpu -t PENDING` before promising the user a turnaround.

**Fifteen partitions appear in `sinfo -a`; an ordinary account can submit to these
two.** The other thirteen belong to specific labs, projects, teaching allocations or
IGB staff. Several of them sit idle advertising GPUs and large-memory nodes that look
better than anything in `normal` or `gpu` — which makes them the most likely thing to
recommend by mistake. **An idle node you cannot submit to is not capacity.**

The test is that `scontrol show partition <name>` returns **empty** for a partition the
account cannot use, while `sinfo -a` still lists it: **listing is not access.** Only
ever put `-p normal` or `-p gpu` in a job script. Full detail in
`references/partitions.md`.

Membership is by Unix group: `biocluster_queue` opens `normal` and `gpu`. There is no
Slurm `AdminLevel` and only Priority=0 QOS, so no priority-bump route exists and none is
needed.

## Module conventions — three rules that prevent most failures

**1. One toolchain generation, unlike Biocluster 3.** The stack is **212 name/version
pairs across 173 module names**, and every toolchain tag present is `15.2.0`: 108 carry
`-IGB-gcc-15.2.0`, 6 carry `-GCCcore-15.2.0`, 3 carry it in another form
(`GCC/15.2.0`, `IGB-gcc/15.2.0`, `OpenMPI/5.0.9-GCC-15.2.0`), and 95 carry no toolchain
tag at all — 108 + 6 + 3 + 95 = 212, counted over the live inventory on 2026-11-09. Biocluster 3's
`IGB-gcc-4.9.4` / `IGB-gcc-8.2.0` split is **gone**, and with it the mixing hazard that
caused most `libpython` link failures. If you are porting a
Biocluster 3 script, delete the toolchain suffix and re-resolve the version.

**2. Pin the version explicitly.** 22 modules carry more than one version — `interpro`
has 6, `kraken2-db` 5, `alphafold-db` 4, `ncbi-blastdb` 4, `pfam` 4, `gtdb` 3,
`uniprot` 3, `nextflow` 3, `Java` 3. `module load interpro` takes whatever the default
happens to be and that changes under you.

**3. Never pipe `module load`.** `module load X | head`, `| tee`, or `$(module load X)`
all run in a subshell and silently discard the load — `module list` then says "No
modules loaded" and you fall back to the system python. Run it bare, on its own line.

The stack is much smaller than Biocluster 3's (173 names vs 927) and **many tools did
not survive the migration**. Confirmed absent: `snakemake`, `scanpy`, `rosetta` /
`PyRosetta`, `hhsuite`, `pymol`, `rdkit`, `ViennaRNA`, `RNAstructure`, `SPAdes`,
`Trinity`, `salmon`, `RepeatMasker`, `cromwell`, `toil`, standalone `foldseek`,
`transformers`, `jax`, `Anaconda3`. **Check `module avail` before promising a tool.**

## Reference data is already here — never download it

IGB mirrors the major reference databases **as loadable modules**. Compute nodes have
no internet, so this is not a convenience, it is the only way to get a reference onto a
compute node without staging it by hand.

    module load gtdb/226            # then use $EBROOTGTDB

29 of them exist: alphafold-db, alphafold3-db, ncbi-blastdb, genbank, refseq-db,
uniprot, pfam, interpro, gtdb, silva, kraken2-db, checkm-db, checkm2-db, checkv-db,
BUSCO-db, humann-db, chocophlan, metaphlan4-db, megares-db, card-prevalence,
gatkbundle, funannotate-db, foldseek-db, dorado-db, pgap-db, KneadData-db, bart2-db,
clusterblast, tailseeker-db.

**The variable name is not guessable**: `EBROOT` + the module name uppercased with
every `-` replaced by `MIN`. So `alphafold3-db` sets `$EBROOTALPHAFOLD3MINDB`,
`ncbi-blastdb` sets `$EBROOTNCBIMINBLASTDB`. The rule held for all 29 with zero
exceptions when re-checked on 2026-10-31. Load the module and `echo` the variable; do
not hardcode a path.

**Four of the 29 point at a directory that does not exist** (`chocophlan`,
`clusterblast`, `gatkbundle`, `silva` — the modulefiles say `/home/mirrors`, the real
mount is `/home/mirror`), and **11 need a subdirectory rather than the module root**.
Both lists, with the working paths, are in the **`igb-reference-data`** skill. Always
`ls` the variable before passing it to a tool.

## What else is installed, and which skill covers it

173 modules / 212 versions. Full searchable table:
`igb-ngs-pipelines/references/module-index.csv`.

| Area | Load this skill |
|---|---|
| assembly, alignment/QC, variant calling, RNA-seq, metagenomics, annotation | `igb-ngs-pipelines` |
| reference databases | `igb-reference-data` |
| structure prediction and docking | `igb-structure-prediction` |
| GPU / deep learning frameworks | `igb-gpu-ml` |
| single-cell, spatial and long-read | `igb-single-cell` |
| workflow managers and containers | `igb-workflows` |
| languages and stats (R, Python, Julia, MATLAB) | this skill — just `module load R/<ver>` |

For the science itself, load the tool's own skill (`alphafold2`, `boltz`, `scvi-tools`,
`proteinmpnn`, ...). The `igb-*` skills carry only what is specific to **this cluster**:
which module, which database, which partition, measured wall-clock, known failures.

## Building an environment

**conda now works on Biocluster 4.** This reverses the Biocluster 3 finding:

    module load Miniconda3/26.9.4        # puts conda 26.9.4 on PATH

The pattern that has actually been exercised here, though, is a **venv layered on an IGB
module**, which keeps the module's CUDA-matched PyTorch and adds only what is missing:

    module load PyTorch/2.14.1-IGB-gcc-15.2.0-Python-3.14.0
    python -m venv --system-site-packages ~/envs/<name>
    source ~/envs/<name>/bin/activate
    pip install <packages>               # login node only

Four foundation models (ESM-2, SAM, DINOv2, Evo 2) were installed this way and run; the
traps that cost time are written up in **`igb-gpu-ml`**. Build on the login node, load
in the job, and **never** let a batch script create an environment.

Two further facts worth not rediscovering: **no Slurm account string is required**
(`sacctmgr show assoc` returns no rows — do not add `--account`), and **`quota -s`
returns nothing at all**, so size against `df -h $HOME` and `sacct` `MaxRSS` instead.
Home is a 2.8 PB CephFS with ~1.3 PB free; `/home/groups` exists but nothing in it is
writable by an ordinary account.

## Job script skeleton

Worked templates in `recipes/`. **Check `--mem` against the partition's ceiling in the
table above before submitting** — over it, the job pends forever with
`Reason=Resources` and no error. Jobs are **billed**, so request what you measured you
need rather than padding.

    #!/bin/bash
    #SBATCH -p gpu            # or -p normal for CPU-only work
    #SBATCH -N 1
    #SBATCH -n 8
    #SBATCH --mem=16g
    #SBATCH --gres=gpu:1
    #SBATCH -t 04:00:00

    # Slurm gives each job a node-local /scratch/$SLURM_JOB_ID and sets TMPDIR to it
    # (measured on compute-0-0, job 17991). Use it, but do not assume it: TMPDIR is
    # NOT set on the login node, and a job that falls through to an unset TMPDIR will
    # scribble into $HOME. Guard it.
    : "${TMPDIR:=$PWD/tmp}"; mkdir -p "$TMPDIR"; export TMPDIR
    export MPLCONFIGDIR="$PWD/.mplcache"

    module purge
    module load <module>/<version>

    <work> 2>&1 | tee -a ./run.log
    ls -lh ./out 2>/dev/null || true

Write job scripts with **LF line endings**. A CRLF script fails in ways that do not name
the cause: `2>&1` becomes an "ambiguous redirect" and `> out.log` creates a file called
`out.log\r`. The repository ships a `.gitattributes` that enforces this.

## Observed runtimes

Measured on Biocluster 4 unless noted. GPU timings are on an **A40**.

| Job | Shape | Wall clock | Notes |
|---|---|---|---|
| ESM-2 650M, deep mutational scan | 1,444 variants of a 76 aa protein | 23 s | 1.6 s of it on the GPU |
| SAM ViT-H, automatic masks | one 512x512 microscopy image | 10.7 s | 391 raw masks |
| DINOv2-large, tile embedding | 300 tiles of 64 px | 1 m 31 s | 3.5 s of it on the GPU |
| Evo 2 7B, variant scoring | 25 sequences of 219 bp | 54 s | 7.4 s of it on the GPU |
| PyTorch 4000x4000 matmul | single op | 0.255 s | A40, torch 2.14.1+cu130 |

The pattern across all four model runs: **GPU time was under 25 s in total; everything
else was staging.** Size the job for the data movement, not the arithmetic, and do not
reserve a GPU for hours because the model name sounds expensive.

AlphaFold 3 timings measured on Biocluster 3 (`alphafold/3.0.2`, different GPU) are
**not carried forward** — Biocluster 4 ships `alphafold/3.0.4` on A40s. See
`igb-structure-prediction` for the current status of that recipe.

## When it breaks

Symptom-to-diagnosis table: `references/failures.md`.

The one to internalise: a job PENDING with `Reason=Resources` that never starts is
usually an **unschedulable memory request**, not a queue wait. Diagnostic:

    scontrol show job <jobid> | grep -E 'Reason|TRES'

## Auditing — hand these to the user

    sacct -u $USER -S <YYYY-MM-DD> -X --format=JobID,JobName,Partition,AllocCPUS,ReqTRES%38,Elapsed,State,Submit,End
    squeue -u $USER
    squeue -p gpu -t PENDING -o "%.12i %.10u %.20S %R"     # before planning GPU work
    seff <jobid>                                            # after it finishes
    scontrol show job <jobid> | grep -E 'Reason|TRES'       # why is it still pending
    tail -f <workdir>/run.log

Hand these to the user rather than only reporting your own account of the run.
