---
name: igb-single-cell
description: "Single-cell, spatial and long-read work on IGB Biocluster 4 — the 10x Genomics pipelines (cellranger, cellranger-arc, cellranger-atac, spaceranger) and the nanopore/PacBio stack (dorado, pod5, modkit, medaka, nanopolish, smrtlink). Records that Biocluster 4 has no scanpy, Seurat or other downstream analysis module, and what to do instead. Load before planning a single-cell, spatial or long-read run here."
---

# Single-cell, spatial and long-read on Biocluster 4

Load `igb-cluster` first for partitions, ceilings and submission rules.

## Read this before planning an analysis

**Biocluster 4 has no downstream single-cell analysis module.** `scanpy` is gone, and so
are `velocyto`, `CellBender`, `alevin-fry`, `CITE-seq-Count`, `MAESTRO`, `scenicplus` and
`popscle`. Biocluster 3 had all of them, and earlier versions of these skills were built
around a shared `cs/scanpy-leiden` environment that **no longer has a module to layer on**.

What remains is the **vendor pipeline layer** — the 10x and long-read tools that turn
instrument output into matrices and alignments. Everything after that is now your
responsibility:

| Stage | On Biocluster 4 |
|---|---|
| BCL/FASTQ to count matrix | `cellranger` and friends — **present, tier B** |
| QC, normalisation, clustering, DE, trajectory | **no module** — pip into a venv, or work off-cluster |

If a user asks for a scanpy or Seurat pipeline here, say plainly that the module is gone
and offer the two honest routes: build a venv on the login node
(`module load Python/3.14.0-GCCcore-15.2.0`, then `python -m venv`, then `pip install
scanpy leidenalg`), or do the count step here and the analysis on their own machine.
Do not write a job script that loads a `scanpy` module.

R is available (`R/4.6.1-IGB-gcc-15.2.0`) but **Seurat is not a module** — it would need
installing into a personal library.

## The 10x pipelines

| Module | Version | For |
|---|---|---|
| `cellranger` | 9.0.0, **10.1.0** | 3'/5' gene expression |
| `cellranger-arc` | 2.0.2, **2.2.0** | multiome (GEX + ATAC) |
| `cellranger-atac` | 2.1.0, **2.2.0** | scATAC |
| `spaceranger` | 4.1.0 | Visium spatial |

Biocluster 3 carried 18 `cellranger` versions; Biocluster 4 carries **two** — and the
second appeared between 2026-10-31 and 2026-11-09, so **run `module avail cellranger`
rather than trusting this table**. A pipeline pinned to an older version will not find
it here; check with the user which version their analysis expects before rewriting.

These are CPU jobs. They belong on `normal`, not `gpu`. Cell Ranger is memory-hungry and
long-running; `normal` has the room, and `MaxTime` is unlimited.

    #SBATCH -p normal
    #SBATCH -N 1
    #SBATCH -n 16
    #SBATCH --mem=128g

    export TMPDIR="$PWD/tmp"; mkdir -p "$TMPDIR"
    module purge
    module load cellranger/10.1.0   # or 9.0.0 - pin deliberately
    cellranger count --id=run1 --transcriptome=<ref> --fastqs=<dir> \
      --localcores=16 --localmem=120 2>&1 | tee -a run.log

**Pass `--localcores` and `--localmem` explicitly.** Cell Ranger inspects the whole
machine, not the cgroup, so on a 128-core node it will try to use all of it and be
killed. Set them to match `-n` and slightly below `--mem`.

**You must supply the transcriptome reference.** There is no 10x reference among the 29
mirrored database modules — check `igb-reference-data` and you will not find one. Stage
it into the user's own space on the login node, once, and reuse it.

Tier B: the modules are present and the invocations above are standard 10x usage, but no
Cell Ranger run has been executed on Biocluster 4 through these skills. Say so, and
report real timings back when you do one.

## Long-read: nanopore

| Module | Version | For |
|---|---|---|
| `dorado` | 2.1.2 | basecalling (GPU) |
| `dorado-db` | 20261012 | basecalling models — a mirrored module, do not download |
| `pod5` | 0.3.49 | POD5 file handling |
| `modkit` | 0.6.4 | modified-base calling from BAM tags |
| `medaka` | 2.2.2 | consensus and polishing |
| `nanopolish` | 0.14.0 | signal-level polishing, methylation |

`dorado` is the one GPU tool in this skill — it belongs on `-p gpu --gres=gpu:1`.
Everything else is CPU work for `normal`.

Basecalling models are mirrored: `module load dorado-db/20261012` and use
`$EBROOTDORADOMINDB`. Do **not** let `dorado download` run on a compute node — it has no
internet and will fail.

    #SBATCH -p gpu
    #SBATCH --gres=gpu:1
    module purge
    module load dorado/2.1.2
    module load dorado-db/20261012
    dorado basecaller "$EBROOTDORADOMINDB/<model>" pod5_dir/ > calls.bam

Check the A40's 47.7 GB against the model you pick; see `igb-gpu-ml` for the card.

## Long-read: PacBio

`smrtlink/26.1.0.284828` is installed. It is a large vendor suite — consult its own
documentation for subcommands. CPU work, `normal`.

`hifiasm/0.25.0` is the assembler of choice for HiFi reads; see `igb-ngs-pipelines`.

## What to tell the user up front

1. Which stage of their analysis this cluster actually covers, and where it stops.
2. That the downstream analysis layer is gone since the Biocluster 4 migration, and
   which of the two routes above they want.
3. The reference they need to stage, if any.
4. `squeue`/`sacct`/`seff` so they can audit the run themselves.
