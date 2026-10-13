# Databases and application paths on the IGB biocluster

Verified 2026-09-28.

## AlphaFold

    module avail alphafold

- Applications: `alphafold/2.1.2`, `2.3.1`, `2.3.2`, `3.0.1`, `3.0.2`
- AF2 databases: `alphafold-db/20210917`, `20220118`, `20230405`, `20240213`
- AF3 databases: `alphafold3-db/20250520`

### AF3 (module `alphafold/3.0.2` + `alphafold3-db/20250520`)

| Variable | Value | Notes |
|---|---|---|
| `$EBROOTALPHAFOLD` | `/home/apps/software/alphafold/3.0.2` | holds `alphafold.sif`, 5.22 GB |
| `$BIODB` | `/private_stores/mirror/alphafold3-db/20250520` | databases + weights |
| `$BIODB/parameters/af3.bin` | 1.15 GB | model weights, world-readable here |

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
`>2pv7_A mol:protein length:298`. This is the reliable route when the local sandbox has
no network egress. Build the AF3 `input.json` on the cluster with a here-doc and pass it
to `submit_job` as an `ssh://` locator — that keeps the sequence out of the transcript
entirely, and avoids transcription errors (2PV7 chain A is 298 residues, not 295).

## scanpy

`scanpy/1.10.1-IGB-gcc-8.2.0-Python-3.10.1` gives scanpy 1.10.1, anndata 0.10.7,
umap 0.5.6, scikit-learn — and **no leidenalg, no igraph**, so `sc.tl.leiden` raises.
Use `module load cs/scanpy-leiden` (manifest: `cluster/manifests/scanpy-leiden.yaml`).

Version sensitivity worth knowing: the same PBMC-3k pipeline gives identical QC and
feature-selection numbers under scanpy 1.10.1 (cluster) and 1.12.4 (laptop) — 2700
cells loaded, 2638 x 13714 after QC, 1838 HVGs — but Leiden r=1.0 yields 8 clusters on
the cluster versus 9 locally. The naive/memory CD4 T split is the boundary that does
not survive the version change. Do not treat cluster counts as portable across
scanpy versions.
