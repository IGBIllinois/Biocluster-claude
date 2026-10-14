---
name: igb-single-cell
description: "Single-cell and spatial analysis on the IGB biocluster - Cell Ranger (18 versions, plus cellranger-arc and cellranger-atac), Space Ranger for Visium, the scanpy module and its missing leidenalg, alevin-fry, velocyto, CITE-seq-Count, MAESTRO, scenicplus and popscle. Load this when running 10x pipelines, counting or demultiplexing single-cell libraries, or doing scanpy/Seurat clustering on IGB, and before assuming a package is available in the scanpy module."
---

# Single-cell on the IGB biocluster

## The scanpy module is missing leidenalg — tier A, verified

`scanpy/1.10.1-IGB-gcc-8.2.0-Python-3.10.1` is the **only** scanpy module. It gives
Python 3.10.1, scanpy 1.10.1, anndata 0.10.7, umap 0.5.6 and scikit-learn — and **no
`leidenalg`, no `igraph`**, so `sc.tl.leiden` raises `ModuleNotFoundError`.

The working pattern is a venv layered on the module (verified 2026-10-06: imports scanpy
1.10.1 / leidenalg 0.12.0 / igraph 1.0.0):

    python -m venv --system-site-packages <path>/scanpy-leiden   # login node only
    <path>/scanpy-leiden/bin/pip install leidenalg igraph

In a job: load the module **first**, then use the venv's interpreter. The venv's
`bin/python` needs the module's `libpython3.10.so.1.0` on `LD_LIBRARY_PATH`; without the
module loaded it fails with `cannot open shared object file`, which looks like a broken
venv and is not.

    export MPLCONFIGDIR="$PWD/.mplcache"       # matplotlib fails on a read-only home
    module load scanpy/1.10.1-IGB-gcc-8.2.0-Python-3.10.1
    <path>/scanpy-leiden/bin/python ./pipeline.py

Template: `igb-cluster/recipes/scanpy.sh`. Resource reality for a PBMC-3k-scale run:
12.96% CPU efficiency and 1.31 GB used at 8 CPU / 32 GB — **2 cores and 8 GB is the
honest ask**, and it queues sooner.

**Cluster counts are not portable across scanpy versions.** The same pipeline gives 8
Leiden clusters at r=1.0 under scanpy 1.10.1 here versus 9 under 1.12.4 locally, with
identical QC and HVG numbers (2700 cells in, 2638 x 13714 after QC, 1838 HVGs). The
naive/memory CD4 T split is the boundary that moves. Never present a cluster count as
version-independent.

## 10x pipelines — tier C

| Module | Versions | Newest |
|---|---|---|
| `cellranger` | **18** | `10.0.0` (2.1.0, 3.x, 4.0.0, 5.0.0, 6.x, 7.x, 8.x, 9.0.0 all present) |
| `cellranger-atac`, `cellranger-arc` | — | present |
| `spaceranger` | 10 | `4.1.0` |

**Pin the version to the one the data was generated with**, or to whatever the rest of
the study used — Cell Ranger output is not comparable across major versions, and
`module load cellranger` takes the default, which moves. None of these has been run
through this skill; treat the invocation as 10x-standard and verify.

Cell Ranger is memory-hungry and CPU-parallel: `normal` is the right partition (128
cores, 2 TB per node, short queue), not `admin`. It wants `--localcores`/`--localmem`
set to match the Slurm request rather than left to autodetect, since `os.cpu_count()`
reports the node's 128 cores and not your allocation.

Reference transcriptomes are **not** in the mirrored module set — check
`igb-reference-data`, then ask the user where the lab keeps its 10x references.

## Also present, tier C

`alevin-fry`, `velocyto` / `velocyto.R`, `CITE-seq-Count`, `MAESTRO`, `scenicplus`,
`popscle`, `vartrix`, `magic`, `ParseBioSciences-Pipeline`, `evolocity`, `Loter`,
`lorals`.

## What is verified and what is not

**Tier A:** the scanpy module's missing `leidenalg`, and the venv overlay that fixes it —
built, imported and used on this cluster.

**Tier C — present, never run here:** `cellranger` (18 versions), `spaceranger` (10),
`cellranger-atac`, `cellranger-arc`, `velocyto`, `CellBender`, and the Seurat/R path. For
the 10x tools in particular, nothing about reference transcriptome paths, `--localcores`
/ `--localmem` behaviour under Slurm, or runtime has been measured here.

**Verifying these needs real data** — a 10x run takes a real library and hours of
compute, so it only gets confirmed by someone doing their actual experiment. If that is
you, **please send back the module string, the resources you requested, and the wall
time**, either in your reply to the agent or as a PR on
`IGBIllinois/Biocluster-claude`. Cellranger sizing in particular is worth far more to the
lab as a measurement than as the guess currently written here.
