---
name: igb-workflows
description: "Workflow managers and containers on IGB Biocluster 4 — Nextflow (the only workflow manager left after the migration), Apptainer/Singularity, conda, and the site rules that govern them. Records that Nextflow already submits to Slurm site-wide, the mandatory NXF_HOME setting, IGB's concurrency limit, and that snakemake, cromwell and toil are gone. Load before running any multi-step pipeline or container here."
---

# Workflows and containers on Biocluster 4

Load `igb-cluster` first for partitions, ceilings and submission rules.

## What survived the migration

| Tool | Status |
|---|---|
| `nextflow` | **present** — 22.09.7-edge, 24.04.6, 25.10.2 |
| Apptainer / Singularity | **present**, no module needed |
| `Miniconda3` | **present** — 26.7.1, 26.9.4 |
| `snakemake` | **gone** |
| `cromwell` | **gone** |
| `toil` | **gone** |
| `clusterflow` | **gone** |

**Nextflow is the only workflow manager on Biocluster 4.** If a user arrives with a
Snakemake workflow, do not improvise a module for it — the honest options are to install
snakemake into a personal venv on the login node, or to run the steps as plain Slurm
jobs. Say which you are doing and why.

## Nextflow

Pick the version deliberately — each is pinned to a different Java:

| Module | Java |
|---|---|
| `nextflow/25.10.2-Java-25.0.1` | 25.0.1 |
| `nextflow/24.04.6-Java-21.0.8` | 21.0.8 |
| `nextflow/22.09.7-edge-Java-17.0.6` | 17.0.6 |

The module loads its Java for you. Do not load a second `Java` module alongside it.

### Two things that are not optional

**1. `NXF_HOME` must be set.** The module says so itself on load. Without it Nextflow
writes into a default location that may not be writable, and the failure is obscure.

    export NXF_HOME="$PWD/.nextflow"

**2. Nextflow already submits to Slurm.** This is configured site-wide at IGB — a
pipeline launched from the login node dispatches its tasks as Slurm jobs
(`executor > SLURM (n)`). **Do not wrap a Nextflow run in `sbatch` and do not set
`executor = 'local'`.** Wrapping it means your allocation sits idle while Nextflow
submits more jobs from inside it, double-booking the cluster.

Launch it from the login node. This is the one documented exception to "never run
anything on a login node" — the Nextflow process itself is a lightweight scheduler, not
compute. Keep it in a `tmux`/`screen` session so it survives a disconnect.

**IGB asks for at most 3 concurrent Nextflow pipelines per user.** Respect it, and tell
the user if their plan would exceed it.

### No internet on compute nodes

`nextflow run nextflow-io/hello` fails on a compute node with
`curl: (7) Failed to connect to www.nextflow.io port 443`. Anything that pulls a
pipeline, a container or a reference at runtime must be fetched **on the login node
first**:

    nextflow pull <pipeline>          # login node
    export NXF_SINGULARITY_CACHEDIR="$HOME/.nxf_singularity"

Pre-pulling container images into `NXF_SINGULARITY_CACHEDIR` is the usual fix for an
nf-core pipeline that dies partway through on a compute node.

    module purge
    module load nextflow/25.10.2-Java-25.0.1
    export NXF_HOME="$PWD/.nextflow"
    export NXF_SINGULARITY_CACHEDIR="$HOME/.nxf_singularity"
    nextflow run <pipeline> -profile singularity --outdir ./out 2>&1 | tee -a run.log

Tier B: the module, the Slurm executor and the `NXF_HOME` requirement are verified; no
full nf-core pipeline has been run end to end on Biocluster 4 through these skills.

## Apptainer / Singularity

**No module needed.** `/usr/bin/apptainer` is **1.5.3** on every node, with a
`singularity` alias. Any skill that tells you to `module load singularity` is carrying
Biocluster 3 material.

    apptainer exec --nv image.sif <command>     # --nv for GPU

Pull images **on the login node**:

    apptainer pull docker://<registry>/<image>:<tag>

Building a container inside a job cannot work — no internet, and `--fakeroot` is not
something to assume. Pull once, reuse.

Two measured gotchas, both in `igb-gpu-ml` in full:

- Triton inside a container cannot find `libcuda.so` — pass
  `--env TRITON_LIBCUDA_PATH=/.singularity.d/libs`.
- An NGC PyTorch image is a practical way to get a Python that is **not** 3.14 when a
  package has no 3.14 wheel; you can build a host-side venv with the container's
  interpreter.

## conda

**conda works on Biocluster 4.** This reverses the Biocluster 3 finding that it was
unusable:

    module load Miniconda3/26.9.4        # puts conda 26.9.4 on PATH

Create environments **on the login node only** — `conda create` and `conda install` need
internet. Then activate in the job.

That said, the pattern with measured results behind it here is a **venv layered on an
IGB module** (`python -m venv --system-site-packages`), which inherits the module's
CUDA-matched builds instead of resolving a parallel stack. Prefer it for anything
GPU-adjacent; reach for conda when a package only exists on conda-forge/bioconda.

## The rule that underlies all of this

Build environments and fetch artefacts on the **login node**. Run them on **compute
nodes**. Never create an environment inside a batch script — compute nodes have no
egress, so it cannot work, and the error you get will not say that.
