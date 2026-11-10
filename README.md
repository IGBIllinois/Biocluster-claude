# igb-cluster skills

**New here? Read [ARCHITECTURE.md](ARCHITECTURE.md) first** — what each file is for, how
the agent picks which one to read, and how much of it has actually been tested on the
cluster.

Claude Science skills for **IGB Biocluster 4** at the University of Illinois
Urbana-Champaign. Import them and a new session already knows the cluster: which
partitions that account can use, which databases are already mirrored, which module
versions pair with which, and which failures are silent.

**Start here: [INSTALL.md](INSTALL.md)** — three steps, about ten minutes.

> **Rebuilt for Biocluster 4 on 2026-11-01.** Biocluster 4 replaced Biocluster 3 in
> October 2026: new login node (`biologin-0`), new hardware, Slurm 25.05.1, and a module
> stack that shrank from 927 names to 173. Every number in this repository was
> re-measured on the new cluster. If you are reading a fork or a cached copy that
> mentions `biologin-3`, the `IGB-gcc-8.2.0` toolchain, or `/scratch`, it is out of date.

## The seven skills

| Skill | Load it for |
|---|---|
| `igb-cluster` | always — partitions, site policy, module rules, job skeleton, audit commands |
| `igb-reference-data` | before downloading any reference genome, annotation or database |
| `igb-structure-prediction` | AlphaFold 2/3, docking, molecular dynamics |
| `igb-gpu-ml` | anything needing a GPU; PyTorch, and the foundation models installed here |
| `igb-single-cell` | Cell Ranger, Space Ranger, nanopore and PacBio |
| `igb-workflows` | Nextflow, Apptainer/Singularity, conda |
| `igb-ngs-pipelines` | ordinary sequencing work, plus an index of all 173 modules |

`igb-cluster` is the hub and is always loaded first; the other six assume it. It also
ships `kernel.py`, which turns the site rules into callable helpers — **GitHub import
excludes sidecar files**, so that file is not installed by the steps in
[INSTALL.md](INSTALL.md) and the skill documents are written to stand alone without it.

They are the **site layer** only — which module, which database, which partition,
measured wall-clock, known failures. For the science itself the agent loads the tool's
own skill (`alphafold2`, `boltz`, `scvi-tools`, `proteinmpnn`, …) alongside.

## The three facts that cost the most to learn

**Reference databases are already here, as modules.** 29 of them — BLAST nt/nr,
GenBank, RefSeq, UniProt, Pfam, InterPro, GTDB, SILVA, Kraken2, CheckM, BUSCO, the GATK
bundle, the AlphaFold 2 and 3 databases. **None appears on the IGB Applications wiki
page.** Compute nodes have no internet, so loading the module is not the convenient
route — it is the only one. The variable name is not guessable either: `EBROOT` plus the
module name uppercased with every `-` replaced by `MIN`, so `alphafold3-db` sets
`$EBROOTALPHAFOLD3MINDB`. Four of the 29 modulefiles point at a directory that does not
exist; the corrected paths are in `igb-reference-data`.

**The software stack shrank by 80% in the migration.** 927 module names became **173**.
`SPAdes`, `Trinity`, `salmon`, `scanpy`, `snakemake`, `rosetta`, `pymol`, `rdkit`,
`ViennaRNA`, `RepeatMasker`, `cromwell` and `toil` are all **gone**. A workflow that ran
on Biocluster 3 may have nothing to load. Always `module avail <name>` before promising a
tool — and say so plainly when it is absent rather than substituting something silently.

**TensorFlow cannot see the GPU.** Measured on 2026-10-31: `TensorFlow/2.21.0` reports
`GPUs visible: 0` both alone and with `CUDA/13.1.0` + `cuDNN/9.17.1.4` loaded. The
cluster ships only CUDA 13.x and TF 2.21 is built against CUDA 12, so no module pairing
fixes it. A TensorFlow job will train on the CPU, slowly, with no error. **Use PyTorch**,
which works correctly against the A40.

## Confidence tiers

Every claim is tagged, so the agent knows what to trust:

- **A — verified** on this cluster; the recipe is the one that worked, with timings.
- **B — documented**: the module exists and the invocation comes from `module show` or
  IGB's docs, but nobody has run it here.
- **C — listed**: the module is present. Nothing further is claimed.

As of 2026-11-01, **tier A**: the hub, the partition map, all 29 reference-database
paths, GTDB-Tk against r226, the GPU framework results, the AlphaFold 3 recipe, and the
four foundation-model installs (ESM-2, Segment Anything, DINOv2, Evo 2). **Tier B**: the
10x pipelines and Nextflow, where the modules and invocations are verified but no full
run has been done here. **Tier C**: most of the 88 NGS modules.

**What remains at C cannot be promoted from a desk.** Those claims are about tools
producing correct output on real input, and the only way to settle one is to run it on
the cluster with your own data. **If you do, open a PR** adding the command you used and
the runtime you saw — that is how this stops being a catalogue and becomes a manual.

Verification sweeps have repeatedly found claims that were *wrong*, not merely
unverified: reference databases whose module variable points at a path that does not
exist, an `nvidia-smi` preflight that would have aborted every GPU job, and a PyTorch
build that passed `torch.cuda.is_available()` and then crashed. Assume the tier C rows
contain errors of the same kind.

## Provenance

Rebuilt from live measurement on **`biologin-0.igb.illinois.edu`** (Biocluster 4,
Slurm 25.05.1) on **2026-10-31 and 2026-11-01**: `module avail` (173 names, 212
versions), `scontrol show partition` against an account's Unix groups, all 29 database
modules opened and their contents listed, a GPU framework probe on an A40, and an
AlphaFold 3 monomer run. The full module inventory ships inside the repo at
`skills/igb-ngs-pipelines/references/module-index.csv`.
