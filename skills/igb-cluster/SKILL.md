---
name: igb-cluster
description: "Run jobs on the IGB biocluster (University of Illinois Urbana-Champaign) through a Claude Science SSH compute target. Carries the partition map with its group ACLs, the shared-environment names, the AlphaFold/BioDB paths and snapshot dates, the node resource ceilings, the known failure modes with their diagnostics, and the house rules for what may and may not be run there. Load before submitting any job to the igb target, before estimating a cluster runtime, or when a cluster job has failed and you need the diagnostic."
---

# IGB biocluster

The compute target is **`igb`** (login node `biologin-3`). An older `biocluster`
target pointed at `biologin-2`, which no longer resolves — if you see it, do not use it.

## Confidence tiers

Every capability claim in the `igb-*` skills is tagged:

- **A — verified**: run on this cluster; the recipe is the one that worked, with timings.
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
4. Build the job script from `recipes/` or from `igb_sbatch_preamble()` in `kernel.py`.
5. Submit, end the cell, park on `wait_for_notification`.

**Do not go exploring.** Everything in this document was paid for by an earlier
session. If a fact you need is genuinely absent, run `cs-doctor` (one call, prints the
lot) rather than a handful of `module avail` probes — then append what it told you to
`compute_details`.

## Site policy — IGB's rules, not ours

Two of these are enforcement, not etiquette. Programmatic: `igb_site_policy()`.

1. **Never run compute on a login node.** IGB policy; accounts can be locked. Login
   nodes are for submitting, staging data and building environments only.
2. **Compute nodes have no internet.** `pip install`, `conda install` and any download
   *fail* there — this is the mechanical reason a job must load a pre-built environment
   instead of creating one. The login node does have egress: stage data there first.
3. **Never request a whole GPU node.** `--gres=gpu:1`. Three GPU nodes serve the whole
   institute.
4. **No HIPAA or PHI data on this cluster.**
5. **Nothing here is backed up**, and storage costs $8.78/TB/month. Clean up
   intermediates.
6. **Always request resources explicitly.** Nodes are large — 128 cores on `normal` —
   but a job that does not ask gets a minimal default slice of **2 CPUs** regardless.

## Hard rules

These are not preferences. Each one is a failure already paid for, or a boundary the
user set.

1. **Never create an environment.** No `pip install`, no `conda create`, no
   `python -m venv`, no `apptainer build` inside a job. Load a shared one:
   `module use "$CS_SHARED_ROOT/modulefiles" && module load cs/<name>`. If the name you
   need is not in `cs-env list`, **stop and report the missing name** — do not improvise
   one into existence.
2. **Never touch another user's work.** No `scancel`, `renice`, or preemption of a job
   you did not submit. No Slurm priority manipulation. If the partition you want is
   busy, use an idle partition the account is entitled to, or wait.
3. **Cap memory at the node's ceiling, not the job's ambition.** See the partition
   table. An over-ceiling request does not error — it pends forever. This is the only
   silent failure mode on this cluster.
4. **The user acts on the cluster too.** They cancel jobs under their own uid without
   telling you. Re-check `squeue`/`sacct` before reasoning about a job you submitted.
5. **Never resubmit after a transport-level submit failure** until you have checked
   `sacct` for an `operon-*` row. A dead connection can follow a successful `sbatch`;
   resubmitting forfeits a multi-day queue position and double-books the GPU.
6. **Write outputs into the job workdir** (`./` or `./out`), never to an absolute path
   under home or scratch — only workdir files are harvested back.
7. **`tee` console output to a named `run.log`.** `slurm-<jobid>.out` is never harvested.
8. **Tell the user where work runs** and give them the cluster-side command to check it
   themselves (`squeue`, `sacct`, `seff`, `tail -f run.log`). They audit independently;
   they should not have to take your report on trust.

## Partitions

Full table with group ACLs and hardware: `references/partitions.md`.
Resolve programmatically with `igb_partitions()` / `igb_sbatch_preamble()` from `kernel.py`.

| Partition | Hardware | Node mem ceiling | Wait | Use it for |
|---|---|---|---|---|
| `admin` | 1 node, 32 CPU, 1x RTX A6000 (48 GB) | **60 GB** | <1 min, normally idle | GPU work under 60 GB |
| `gpu` | 3 nodes, 32 CPU, 2x A40 (46 GB) each | **250 GB** | **22-32 h observed** | GPU work over 60 GB |
| `normal` | 7 nodes, 128 CPU (EPYC 7543), 2 TB each | **2 TB** | short | everything CPU |

All three verified 2026-10-04 (`sinfo`, `scontrol show partition`). Totals: `normal`
896 CPUs / 7 nodes, `gpu` 96 / 3, `admin` 32 / 1. Every partition has
`MaxTime=UNLIMITED`, `DefaultTime=NONE`, `MaxMemPerNode=UNLIMITED` — the binding limit
is always the node's RealMemory, never a partition cap. No wall-time limit anywhere,
so long jobs are allowed.

**The tradeoff that decides the partition** — and it is counter-intuitive: the *idle*
GPU partition has the **smallest** memory on the cluster, and the 2 TB partition has no
GPU at all. `igb_choose_partition(needs_gpu=, mem_gb=)` encodes it:

| Need | Partition | Why |
|---|---|---|
| GPU, ≤60 GB | `admin` | idle, starts in under a minute |
| GPU, >60 GB | `gpu` | 250 GB/node — but say the 22-32 h queue out loud first |
| no GPU, any memory | `normal` | 2 TB and 128 cores, short wait |

Membership comes from Unix groups, not from Slurm admin rights: `biocluster_queue`
opens `normal` and `gpu`; `admin_queue` opens `admin`. About fourteen further
partitions exist (`mmli` 4x A100, `cabbi` 8x RTX6000, `sonngpu`, `hpcbio`), all
group-restricted — check `id` against `scontrol show partition` before assuming `gpu`
is the only GPU route. The account has no Slurm `AdminLevel` and only Priority=0 QOS,
so there is no priority-bump route and none is needed.

`gpu` honours `--cpus-per-task` exactly; `normal` does not.

## Module conventions — three rules that prevent most failures

**1. Two toolchain generations exist and must not be mixed.** Of 1795 module versions,
680 carry `-IGB-gcc-4.9.4`, 608 carry `-IGB-gcc-8.2.0`, 507 carry no IGB tag. The two
are separate stacks with separate Python builds; loading one module from each in a job
produces linker and `libpython` errors that point nowhere near the cause. **Prefer
`-IGB-gcc-8.2.0`.** Never mix.

**2. Pin the version explicitly.** Version spread is wide and newest is not always
wanted: `cellranger` has 18 versions (2.1.0 to 10.0.0), `R` 14, `PyTorch` 15, `CUDA`
13, `nextflow` 16. `module load R` takes whatever the default happens to be and that
changes under you.

**3. Never pipe `module load`.** `module load X | head`, `| tee`, or `$(module load X)`
all run in a subshell and silently discard the load — `module list` then says "No
modules loaded" and you fall back to the system python 3.6.8. Run it bare, on its own
line.

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
`ncbi-blastdb` sets `$EBROOTNCBIMINBLASTDB`. Load the module and `echo` the variable;
do not hardcode a path. Detail and versions: the **`igb-reference-data`** skill.

**None of these 29 appear on the IGB Applications wiki page.** A newcomer who trusts
that page will spend days downloading a database the cluster already mirrors, pay for
the storage at $8.78/TB/month, and still fail on the compute node.

## What else is installed, and which skill covers it

927 modules / 1795 versions. Full searchable table:
`igb-ngs-pipelines/references/module-index.csv`.

| Area | Modules | Load this skill |
|---|---|---|
| assembly, alignment/QC, variant calling, RNA-seq, metagenomics, annotation | 466 | `igb-ngs-pipelines` |
| reference databases | 29 | `igb-reference-data` |
| structure prediction, docking, RNA folding | 26 | `igb-structure-prediction` |
| GPU / deep learning frameworks | 46 | `igb-gpu-ml` |
| single-cell and spatial | 17 | `igb-single-cell` |
| workflow managers and containers | 12 | `igb-workflows` |
| phylogenetics and comparative genomics | 57 | `igb-ngs-pipelines` (shares the conventions) |
| languages and stats (R, Python, Julia, MATLAB) | 28 | this skill — just `module load R/4.5.1` |
| imaging, proteomics, molecular dynamics | 27 | module-index.csv; thin coverage, verify before relying |
| compilers, libraries, utilities | 219 | dependencies, not capabilities — ignore |

For the science itself, load the tool's own skill (`alphafold2`, `boltz`, `scvi-tools`,
`proteinmpnn`, ...). The `igb-*` skills carry only what is specific to **this cluster**:
which module, which database, which partition, measured wall-clock, known failures.

## Shared environments

**There is no pre-built shared conda environment on this cluster** (verified
2026-10-04). `conda` is not on the default PATH, and it is still absent after
`module load Miniconda3/24.7.1-0` in a non-interactive shell — conda needs its
`profile.d/conda.sh` sourced. Eight `Anaconda3` and four `Miniconda3` modules exist to
build on. The house pattern is therefore a **venv layered on an IGB module**
(`python -m venv --system-site-packages`), which is exactly what `cs/scanpy-leiden` is.
Do not reach for conda here.

Two further facts worth not rediscovering: **no Slurm account string is required**
(`sacctmgr show assoc` returns no rows — do not add `--account`), and **`quota -s` does
not work** (the quota servers refuse the connection), so size against
`df -h $HOME` and `sacct` `MaxRSS` instead.

    module use "$CS_SHARED_ROOT/modulefiles"
    module load cs/<name>

`CS_SHARED_ROOT` is set per install by `bootstrap.sh`; `cs-env list` enumerates what
exists. Manifests live in `cluster/manifests/`. One owner builds; everyone else loads.

Known shared env: **`cs/scanpy-leiden`** — the IGB `scanpy/1.10.1-IGB-gcc-8.2.0-Python-3.10.1`
module supplies scanpy 1.10.1 / anndata 0.10.7 / umap 0.5.6 / sklearn but ships **no
leidenalg and no igraph**, so `sc.tl.leiden` fails on the bare module. The shared env is
a `venv --system-site-packages` layered on it plus leidenalg 0.12.0 and igraph 1.0.0.
Also set `MPLCONFIGDIR="$PWD/.mplcache"` in the job script or matplotlib warns on a
read-only home.

## Databases and application paths

Full detail: `references/databases.md`.

- AlphaFold modules: `alphafold/{2.1.2,2.3.1,2.3.2,3.0.1,3.0.2}`;
  databases `alphafold-db/{20210917,20220118,20230405,20240213}` (AF2) and
  `alphafold3-db/20250520` (AF3).
- AF3 container: `$EBROOTALPHAFOLD/alphafold.sif` (5.22 GB, `$EBROOTALPHAFOLD` =
  `/home/apps/software/alphafold/3.0.2`).
- AF3 databases + weights: `$BIODB` = `/private_stores/mirror/alphafold3-db/20250520`;
  weights at `$BIODB/parameters/af3.bin` (1.15 GB), world-readable here.
- **Template cutoff is 2022-09-28** (`pdb_2022_09_28`; sequence DBs `uniref90_2022_05`,
  `mgy_clusters_2022_05`, `uniprot_all_2021_04`). Any PDB entry deposited before that
  date is template-informed, not a blind fold — say so when reporting a result.
- `$BIODB/pdb_seqres_2022_09_28.fasta` is a reliable **offline** SEQRES source
  (headers `>2pv7_A mol:protein length:298`). Prefer resolving a sequence on the cluster
  to transcribing residues into the transcript, and never type a sequence from memory.

## Job script skeleton

`igb_sbatch_preamble()` in `kernel.py` emits the directives with the memory clamp
applied. Worked templates: `recipes/af3_monomer.sh`, `recipes/scanpy.sh`.

    #SBATCH -p admin
    #SBATCH -N 1
    #SBATCH -n 8
    #SBATCH --mem=16g
    #SBATCH --gres=gpu:1

    # /scratch guard: nodes report TmpDisk=0, but mkdir has been observed to succeed
    if mkdir -p "/scratch/$SLURM_JOB_ID" 2>/dev/null && [ -w "/scratch/$SLURM_JOB_ID" ]; then
      export TMPDIR="/scratch/$SLURM_JOB_ID"; trap 'rm -rf "/scratch/$SLURM_JOB_ID"' EXIT
    else
      export TMPDIR="$PWD/tmp"; mkdir -p "$TMPDIR"
    fi

    module use "$CS_SHARED_ROOT/modulefiles"
    module load cs/<name>

    <work> 2>&1 | tee -a ./run.log
    ls -lh ./out 2>/dev/null || true

## Observed runtimes

Do not extrapolate from problem size alone — on this cluster AF3 wall-clock is
dominated by the **template stage**, not the MSA.

| Job | Shape | Wall clock | Breakdown |
|---|---|---|---|
| AF3 ubiquitin (1UBQ chain A) | 76 aa monomer, 1 seed / 5 samples | 33 min 37 s | jackhmmer MSA 539 s; **templates ~23.5 min**; inference 42.8 s |
| AF3 2PV7 homodimer | 596 tokens, 4778 atoms | ~40 min | MSA ~590 s (hit the 5000-sequence cap); hmmsearch 7 s |

Both were `-n 8 --mem=16g` on `admin`. `seff` on the dimer: CPU efficiency 9.73%,
6.42 GB of 56 GB reserved — the IGB doc's `--mem=128g -n 4` is a ~20x memory
over-reservation. The honest ask for this size is `-n 8 --mem=16g`.

The PBMC-3k scanpy pipeline is likewise over-served by 8 CPU / 32 GB: 12.96% CPU
efficiency, 1.31 GB used. Roughly 2 cores and 8 GB suffices and queues sooner.

## When it breaks

Symptom-to-diagnosis table: `references/failures.md`. Programmatic:
`igb_known_failures()`.

The one to internalise: a job PENDING with `Reason=Resources` that never starts is
usually an **unschedulable memory request**, not a queue wait. Diagnostic:

    scontrol show job <jobid> | grep -E 'Reason|TRES'

## Auditing — hand these to the user

Agent-submitted jobs appear in Slurm as `operon-<first 8 chars of the job uuid>`.

    sacct -u $USER -S <YYYY-MM-DD> -X --format=JobID,JobName,Partition,AllocCPUS,ReqTRES%38,Elapsed,State,Submit,End
    squeue -u $USER
    squeue -p gpu -t PENDING -o "%.12i %.10u %.20S %R"     # before planning GPU work
    seff <jobid>                                            # after it finishes
    scontrol show job <jobid> | grep -E 'Reason|TRES'       # why is it still pending
    tail -f <workdir>/run.log

`igb_audit_commands()` returns these as a dict for pasting into a reply.
