---
name: igb-structure-prediction
description: "Protein and RNA structure work on the IGB biocluster - AlphaFold 2 and AlphaFold 3 (module plus singularity container and the mirrored database), RoseTTAFold-All-Atom, Rosetta and PyRosetta, foldseek structure search, hhsuite, foldx, fpocket, pymol, rdkit, and RNA secondary structure via ViennaRNA, RNAstructure and mfold. Load this when folding, docking, inverse-folding, searching or visualising structures on IGB, or when choosing a partition and estimating wall-clock for a structure prediction job."
---

# Structure prediction on the IGB biocluster

Load the tool's own skill for the science (`alphafold2`, `boltz`, `proteinmpnn`, ...).
This skill is the site layer.

## AlphaFold 3 — tier A, verified

Working recipe, partition `admin`, measured twice. Full job script:
`igb-cluster/recipes/af3_monomer.sh`.

    #SBATCH -p admin
    #SBATCH -n 8
    #SBATCH --mem=16g
    #SBATCH --gres=gpu:1
    module load alphafold/3.0.2
    module load alphafold3-db/20250520
    singularity exec --nv "$EBROOTALPHAFOLD/alphafold.sif" \
      python /app/alphafold/run_alphafold.py --json_path input.json \
        --output_dir ./af3_out --db_dir "$BIODB" --model_dir "$BIODB/parameters"

Non-obvious points, each paid for:

- **`--mem=16g`, not 128g.** `admin` has a 60 GB ceiling; over it the job pends forever
  with `Reason=Resources` and no error. `seff` on a 596-token dimer: 6.42 GB used of 56
  GB reserved, CPU efficiency 9.7%.
- **Template cutoff is 2022-09-28** (`pdb_2022_09_28`). A target deposited before that
  date is template-informed, not a blind fold — say so when reporting.
- **Wall-clock is dominated by templates, not the MSA.** 76-residue ubiquitin: 33 min 37
  s total — MSA 539 s, **templates ~23.5 min**, inference 42.8 s. A short,
  heavily-crystallised sequence can cost more than a long obscure one. Do not estimate
  from length.
- **Resolve sequences on the cluster** from `$BIODB/pdb_seqres_2022_09_28.fasta` rather
  than transcribing residues.
- Guard the `/scratch/$SLURM_JOB_ID` step; nodes report `TmpDisk=0`.

AlphaFold 2 is also installed (`alphafold/{2.1.2,2.3.1,2.3.2}` with
`alphafold-db/{20210917,20220118,20230405,20240213}`) — **tier C**, not run here.

## Everything else — tier C

| Module | Newest | Note |
|---|---|---|
| `RoseTTAFold-All-Atom` | — | GPU; expect a container or a conda tree, unverified |
| `rosetta` / `PyRosetta` | `3.13-IGB-gcc-8.2.0` | the 2017 and 3.12 builds are gcc-4.9.4 — do not mix generations |
| `foldseek` | `8-ef4e960` | pair with `foldseek-db/20230921` via `igb-reference-data` |
| `hhsuite`, `foldx`, `fpocket`, `pymol`, `rdkit` | — | present; nothing claimed |
| `ViennaRNA`, `RNAstructure`, `mfold`, `RNAhybrid`, `randfold`, `PITA` | — | RNA secondary structure, CPU-only; `normal` is the right partition |

## Partition choice

GPU and under 60 GB → `admin` (idle, starts in under a minute). GPU and over 60 GB →
`gpu` (250 GB/node, but 22-32 h observed queue; warn the user first). CPU-only → `normal`.
`igb_choose_partition()` in the hub's `kernel.py` encodes this.
