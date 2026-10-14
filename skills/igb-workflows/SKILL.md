---
name: igb-workflows
description: "Running workflow managers on the IGB biocluster - Nextflow (16 versions) and nf-core pipelines, Snakemake, Cromwell, Toil, and Singularity/Apptainer containers. Load this when launching or configuring a pipeline that submits its own Slurm jobs, when a Nextflow or Snakemake profile needs cluster settings, or when a job needs to run inside a container image on IGB."
---

# Workflow managers on the IGB biocluster

| Module | Versions | Newest | Status |
|---|---|---|---|
| `nextflow` | 16 | `25.10.2-Java-25.0.1` | **tier A** — ran a pipeline on compute-1-1 |
| `snakemake` | 2 | `7.32.4-IGB-gcc-8.2.0-Python-3.10.1` | **tier A** — ran a workflow, 2/2 steps |
| `singularity` | — | **`/usr/bin/singularity` 3.8.7** | **tier A** — ran the AlphaFold container |
| `cromwell`, `toil`, `nf-core`, `clusterflow`, `Mamba`, `EasyBuild` | — | present | tier C |

## Four things measured on the cluster 2026-10-13

**1. Nextflow already submits to Slurm — you do not configure the executor.** A bare
`nextflow run hello.nf` inside a job printed `executor > SLURM (1)` and dispatched the
process as its own Slurm job. There is a site-wide config doing this. Do not assume the
default local executor, and do not copy a generic `process.executor = 'slurm'` block
from a tutorial without checking what the site config already sets.

**2. `NXF_HOME` is mandatory here.** The module's own load message says so:
*"Please set the environmental variable NXF_HOME to a directory in your home directory.
Without this parameter, nextflow will not work."* Set it before the run:

    export NXF_HOME="$HOME/nextflow"

**3. IGB limits you to 3 concurrent nextflow jobs.** Also from the module's load
message: *"Please limit the number of nextflow jobs to 3 at a time. Using more creates a
lot of stress on the shared filesystem."* This is a site request, not a scheduler limit
— nothing will stop you exceeding it, which is exactly why it belongs here.

**4. Singularity needs no module.** It is `/usr/bin/singularity`, version **3.8.7**, on
the compute nodes — a *newer* build than the `singularity/3.8.1` module advertises.
`singularity exec` on the 4.9 GB AlphaFold image worked with nothing loaded but
`alphafold/3.0.2`, and reported Python 3.11.10 inside the container.

**Confirmed no-internet, concretely:** `nextflow run nextflow-io/hello` — the quickstart
in every tutorial — fails on a compute node with
`curl: (7) Failed to connect to www.nextflow.io port 443: Connection timed out`.
Nextflow also phones home for version checks at startup; `export NXF_OFFLINE=true`
suppresses that. Any pipeline that resolves itself from GitHub must be fetched on the
**login node** first.

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

## Nextflow starter — the module-load part is verified

    module purge
    module load nextflow/25.10.2-Java-25.0.1
    export NXF_HOME="$HOME/nextflow"                           # required, see above
    export NXF_OFFLINE=true                                    # skip the version phone-home
    export NXF_SINGULARITY_CACHEDIR="$HOME/.nxf_singularity"   # pre-populated on the login node
    nextflow run <local-pipeline-dir> -c igb.config

No `singularity` module is needed — `/usr/bin/singularity` 3.8.7 is already on `PATH`.
Replace `<local-pipeline-dir>` with a pipeline you fetched on the login node; a
`nf-core/<name>` reference resolves over the network and **will fail inside a job**.

with `igb.config` setting `process.executor = 'slurm'`, `process.queue = 'normal'`,
explicit `cpus`/`memory` per label, and no label exceeding its partition's ceiling.

**Before running a real pipeline**, confirm with one trivial workflow that the executor
submits correctly and that `squeue -u $USER` shows the child jobs — a misconfigured
executor silently runs everything locally on the login node, which is the one outcome
that gets an account locked.

## What is still unverified here

**Tier A:** everything in the four measured points above — nextflow 25.10.2 running a
pipeline, its Slurm executor, `NXF_HOME`, snakemake 7.32.4, and `singularity exec` on a
real image.

**Tier C — not run here:** any **real** nf-core pipeline (the test was a hello-world, not
a pipeline with containers, profiles and staged references), `NXF_SINGULARITY_CACHEDIR`
actually serving a pre-pulled image, `cromwell`, `toil`, `clusterflow`, and whether a
nextflow driver process is better placed on the login node or inside a job on this
cluster — the site's "limit to 3 nextflow jobs" notice implies the latter, but that is an
inference.

**Running one real pipeline would settle most of this at once.** If you do, **send back
the pipeline and revision, your config, whether containers resolved, and the wall time** —
in your reply to the agent, or as a PR on `IGBIllinois/Biocluster-claude`.
