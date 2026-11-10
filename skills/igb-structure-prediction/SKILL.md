---
name: igb-structure-prediction
description: "Protein structure prediction, docking and molecular dynamics on IGB Biocluster 4 — AlphaFold 2 and 3 with their mirrored databases and the Apptainer container invocation, AutoDock-Vina, GROMACS. Records the 2022-09-28 template cutoff, how to resolve a sequence offline, and that Rosetta, PyMOL, foldseek and the RNA-folding tools did not survive the migration. Load before predicting a structure, docking a ligand or running MD here."
---

# Structure prediction on Biocluster 4

Load `igb-cluster` first for partitions, ceilings and submission rules.

## What is here

| Module | Version | Notes |
|---|---|---|
| `alphafold` | 2.3.2, 3.0.4 | container-based; needs a mirrored database module |
| `AutoDock-Vina` | 1.2.7 | ligand docking, CPU |
| `GROMACS` | 2026.4 | molecular dynamics |

## What is not here

**Rosetta, PyRosetta, PyMOL, hhsuite, ViennaRNA, RNAstructure and mfold are all gone**
since the Biocluster 4 migration. Biocluster 3 had every one of them. If a user asks for
a Rosetta protocol or an RNA secondary-structure fold, say plainly that the module no
longer exists and offer a route — a personal venv on the login node, a container, or
doing it elsewhere — rather than improvising a module name.

**`foldseek` is gone but `foldseek-db/20230921` is still mirrored.** The database is
there and the search binary is not, which is a trap: the module loads, the path resolves,
and there is nothing to run against it. Installing `foldseek` into a venv or container
is the only way to use that mirror.

There is no ESMFold, OmegaFold, Boltz or Chai module. ESM-2 has been installed by hand
under `~/models` — see `igb-gpu-ml`.

## AlphaFold 3

Verified to run on Biocluster 4 on 2026-11-01 (`alphafold/3.0.4`, A40, slurm 16638).
Working script: `igb-cluster/recipes/af3_monomer.sh`.

### The setup

    module purge
    module load alphafold/3.0.4
    module load alphafold3-db/20250520

- `$EBROOTALPHAFOLD` = `/home/apps/software/alphafold/3.0.4`, containing
  **`alphafold.sif`**.
- The database module sets **both** `$BIODB` and `$EBROOTALPHAFOLD3MINDB` to
  `/private_stores/mirror/alphafold3-db/20250520`. Either works.
- Weights are at `$BIODB/parameters`.

Run it through Apptainer — no module needed for the container runtime:

    apptainer exec --nv "$EBROOTALPHAFOLD/alphafold.sif" \
      python /app/alphafold/run_alphafold.py \
        --json_path input.json --output_dir ./af3_out \
        --db_dir "$BIODB" --model_dir "$BIODB/parameters"

### Resolve the sequence on the cluster, not in the transcript

`$BIODB/pdb_seqres_2022_09_28.fasta` is a reliable offline SEQRES source, with headers
like `>1ubq_A mol:protein length:76`:

    SEQ=$(awk '/^>1ubq_A /{getline; print; exit}' "$BIODB/pdb_seqres_2022_09_28.fasta")

Build `input.json` on the cluster from that. **Never type a protein sequence from
memory** — this is the cheapest possible way to introduce a silent error into a result.

### The template cutoff

**2022-09-28.** The sequence databases are `uniref90_2022_05`, `mgy_clusters_2022_05`
and `uniprot_all_2021_04`. Any PDB entry deposited before that date is **template-informed,
not a blind fold** — say so whenever you report an AF3 result on a known structure, or
the user will read a recall as a prediction.

### Timing

Measured stage timings from the 2026-11-01 run of a 76-residue monomer, 1 seed:

| Stage | Time |
|---|---|
| jackhmmer vs `bfd-first_non_consensus_sequences.fasta` | 83.6 s |
| jackhmmer vs `uniref90_2022_05.fa` | 283.0 s |

The four jackhmmer searches run concurrently with `--cpu 8`, so MSA wall-clock is set by
the slowest, not the sum.

**Total wall-clock on Biocluster 4 is not yet recorded** — the measuring session lost its
connection to the cluster before the job finished. Treat the total as tier B. On
Biocluster 3 the same target on `alphafold/3.0.2` took **33 min 37 s**, of which roughly
23.5 min was the **template** stage rather than the MSA — so do not size this job from
sequence length alone, and do not quote the Biocluster 3 number as if it were measured
here.

To close this gap, run `recipes/af3_monomer.sh` and report back:

    sacct -j <jobid> -X -o State,Elapsed
    grep -oE "took [0-9.]+ seconds" run.log | tail -20

### Resources

`-n 8 --mem=16g --gres=gpu:1` is the honest ask for a small monomer. On Biocluster 3 a
596-token dimer used **6.42 GB** of a 56 GB reservation at 9.73% CPU efficiency — IGB's
own documentation suggests `--mem=128g`, which is roughly a 20x over-reservation and
costs the user real money. Start at 16 GB, check `seff`, and raise only if it was killed.

## AlphaFold 2

`alphafold/2.3.2` with `alphafold-db/20240213` (also 20210917, 20220118, 20230405).
`$EBROOTALPHAFOLDMINDB` contains `params`, `pdb_mmcif`, `pdb_seqres`, `uniref30`,
`mgnify`, `pdb70`, `uniprot`, `small_bfd`.

Tier C — present and the database layout is confirmed, but no AF2 run has been done on
Biocluster 4. Prefer AF3 unless the user specifically needs AF2 outputs.

## Docking and MD

`AutoDock-Vina/1.2.7` and `GROMACS/2026.4` are CPU work for `normal`. Tier C: installed,
versions confirmed, nothing run here.

GROMACS builds vary in whether they carry GPU and MPI support. Check before planning a
multi-node run:

    module load GROMACS/2026.4-IGB-gcc-15.2.0
    gmx --version | grep -E "GPU support|MPI"

Note there is no ligand-preparation toolkit on this cluster — `rdkit` is gone — so
prepare ligands elsewhere or install RDKit into a venv on the login node.
