---
name: igb-workflows
description: "Running workflow managers on the IGB biocluster - Nextflow (16 versions) and nf-core pipelines, Snakemake, Cromwell, Toil, and Singularity/Apptainer containers. Load this when launching or configuring a pipeline that submits its own Slurm jobs, when a Nextflow or Snakemake profile needs cluster settings, or when a job needs to run inside a container image on IGB."
---

# Workflow managers on the IGB biocluster

**Tier C throughout** — these modules are present; nothing here has been run on this
cluster. The configuration below follows from site facts established elsewhere in these
skills, not from a successful run. Verify before trusting, and report back so this can
be promoted.

| Module | Versions | Newest |
|---|---|---|
| `nextflow` | 16 | `25.10.2-Java-25.0.1` |
| `snakemake` | 2 | `7.32.4-IGB-gcc-8.2.0-Python-3.10.1` |
| `singularity` | 1 | `3.8.1` |
| `cromwell`, `toil`, `nf-core`, `clusterflow`, `Mamba`, `EasyBuild` | — | present |

## The one thing that makes or breaks this

A workflow manager **submits its own Slurm jobs**. That means it bypasses every
resource decision made for you, and the site constraints have to go into its config
instead:

- **Partition and memory ceiling.** A profile that requests 128 GB will pend forever on
  `admin` (60 GB ceiling) with `Reason=Resources` and no error. Set the executor to
  `normal` for CPU work (2 TB/node) and only route GPU tasks to `admin`.
- **No internet on compute nodes.** Nextflow pulling a container or a plugin at task
  start fails. Pre-pull images on the **login node** into a shared cache and point
  `NXF_SINGULARITY_CACHEDIR` at it; same for `singularity pull`.
- **Never let it run on the login node.** `nextflow run` itself is a lightweight
  orchestrator and is usually acceptable there, but any task that does real work must go
  through the executor. IGB policy forbids login-node compute and can lock accounts.
- **Set `APPTAINER_CACHEDIR` / `APPTAINER_TMPDIR`** to a path under scratch before
  pulling, or the layer cache fills your home quota.
- **Unprivileged `singularity build` is usually unavailable** on a shared cluster — pull
  a prebuilt image instead of building on-cluster.

## Nextflow sketch (unverified)

    module load nextflow/25.10.2-Java-25.0.1
    module load singularity/3.8.1
    export NXF_SINGULARITY_CACHEDIR="$HOME/.nxf_singularity"   # pre-populated
    nextflow run nf-core/<pipeline> -profile singularity -c igb.config

with `igb.config` setting `process.executor = 'slurm'`, `process.queue = 'normal'`,
explicit `cpus`/`memory` per label, and no label exceeding its partition's ceiling.

**Before running a real pipeline**, confirm with one trivial workflow that the executor
submits correctly and that `squeue -u $USER` shows the child jobs — a misconfigured
executor silently runs everything locally on the login node, which is the one outcome
that gets an account locked.
