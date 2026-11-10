# Databases and application paths on Biocluster 4

Verified 2026-10-31 / 2026-11-01.

**The full detail lives in the `igb-reference-data` skill, not here.** This file is a
pointer plus the AlphaFold specifics the hub's recipe needs. If you want the table of
all 29 mirrored databases, the four broken modulefiles or the eleven that need a
subdirectory, load `igb-reference-data`.

## The one rule

    module load <db-module>/<version>
    echo "$EBROOT<MODULE NAME UPPERCASED, every - replaced by MIN>"

29 databases are mirrored under `/private_stores/mirror` and exposed as modules.
Compute nodes have no internet, so loading the module is the only way to get a
reference onto one. Never download a database that is already mirrored.

Never pipe `module load` — it runs in a subshell and the variable is silently never set.

## AlphaFold

    module avail alphafold

- Applications: `alphafold/2.3.2`, `alphafold/3.0.4`
- AF2 databases: `alphafold-db/20210917`, `20220118`, `20230405`, `20240213`
- AF3 database: `alphafold3-db/20250520`

Biocluster 3 carried `alphafold/2.1.2`, `2.3.1`, `3.0.1` and `3.0.2` as well; those
versions no longer exist.

### AF3 (`alphafold/3.0.4` + `alphafold3-db/20250520`)

| Variable | Value | Notes |
|---|---|---|
| `$EBROOTALPHAFOLD` | `/home/apps/software/alphafold/3.0.4` | holds `alphafold.sif` |
| `$BIODB` | `/private_stores/mirror/alphafold3-db/20250520` | databases + weights |
| `$EBROOTALPHAFOLD3MINDB` | same as `$BIODB` | the db module sets both |
| `$BIODB/parameters` | | model weights |

No explicit `--bind` is needed — `$BIODB` is visible inside the container.

### Snapshot dates — these bound what the model can see

| Database | Snapshot |
|---|---|
| templates | `pdb_2022_09_28` |
| uniref90 | `2022_05` |
| mgy_clusters | `2022_05` |
| uniprot_all | `2021_04` |

**Template cutoff: 2022-09-28.** A target deposited in the PDB before that date is
inside the template set, so the prediction is template-informed rather than a blind
fold. State this when reporting a result for such a target (1UBQ, for example).

## Offline sequence lookup

    $BIODB/pdb_seqres_2022_09_28.fasta

SEQRES for every PDB entry in the snapshot; headers look like
`>1ubq_A mol:protein length:76`. This is the reliable route when the local sandbox has
no network egress. Build the AF3 `input.json` **on the cluster** with a here-doc — that
keeps the sequence out of the transcript entirely and avoids transcription errors.

    SEQ=$(awk '/^>1ubq_A /{getline; print; exit}' "$BIODB/pdb_seqres_2022_09_28.fasta")

Never type a protein sequence from memory.
