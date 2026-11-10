---
name: igb-reference-data
description: "The 29 reference-database modules mirrored on IGB Biocluster 4 — BLAST, UniProt, Pfam, InterPro, GTDB, SILVA, Kraken2, CheckM/CheckV, BUSCO, HUMAnN, AlphaFold and others. Carries the non-guessable EBROOT variable rule, the four modulefiles whose paths are broken, the eleven that need a subdirectory rather than the module root, and the verified GTDB-Tk setup. Load before pointing any tool at a reference database, and before even considering downloading one."
---

# Reference databases on Biocluster 4

**Never download a reference database.** IGB mirrors them under
`/private_stores/mirror` and exposes each as a module. Compute nodes have no internet,
so this is not a convenience — it is the only way to get a reference onto a compute node
without staging it by hand. Downloading one also costs the user storage they are billed
for, and none of these appear on the IGB Applications wiki page, so a newcomer who
trusts that page will pay twice.

All 29 modules were opened and inspected on **2026-10-31** (tier A).

## The variable name rule

    EBROOT + <module name uppercased, every "-" replaced by "MIN">

So `ncbi-blastdb` sets `$EBROOTNCBIMINBLASTDB` and `alphafold3-db` sets
`$EBROOTALPHAFOLD3MINDB`. The rule held for **all 29 with zero exceptions**.

    module load gtdb/226
    echo "$EBROOTGTDB"

Load the module and echo the variable. Do not hardcode a path — the mirror layout has
already changed once.

**Never pipe `module load`.** `module load gtdb/226 | head` runs in a subshell and the
variable is silently never set; you then get an empty path and a confusing downstream
error. This is easy to do by accident even when you know about it.

## The 29 modules

Newest version of each, as of 2026-10-31.

| Module | Newest | Variable | Where to point the tool |
|---|---|---|---|
| `alphafold-db` | `20240213` | `$EBROOTALPHAFOLDMINDB` | module root is correct |
| `alphafold3-db` | `20250520` | `$EBROOTALPHAFOLD3MINDB` | module root is correct |
| `bart2-db` | `20240302` | `$EBROOTBART2MINDB` | module root is correct |
| `BUSCO-db` | `5` | `$EBROOTBUSCOMINDB` | point the tool at `lineages/` |
| `card-prevalence` | `4.0.1` | `$EBROOTCARDMINPREVALENCE` | point the tool at `db/` |
| `checkm-db` | `20150116` | `$EBROOTCHECKMMINDB` | module root is correct |
| `checkm2-db` | `20230511` | `$EBROOTCHECKM2MINDB` | point the tool at `CheckM2_database/` |
| `checkv-db` | `1.5` | `$EBROOTCHECKVMINDB` | point the tool at `checkv-db-v1.5/` |
| `chocophlan` | `0.1.1` | `$EBROOTCHOCOPHLAN` | **path does not exist** |
| `clusterblast` | `20170105` | `$EBROOTCLUSTERBLAST` | **path does not exist** |
| `dorado-db` | `20261012` | `$EBROOTDORADOMINDB` | module root is correct |
| `foldseek-db` | `20230921` | `$EBROOTFOLDSEEKMINDB` | module root is correct |
| `funannotate-db` | `20240515` | `$EBROOTFUNANNOTATEMINDB` | module root is correct |
| `gatkbundle` | `20191118` | `$EBROOTGATKBUNDLE` | **path does not exist** |
| `genbank` | `250` | `$EBROOTGENBANK` | module root is correct |
| `gtdb` | `226` | `$EBROOTGTDB` | point the tool at `auxillary_files/` |
| `humann-db` | `201901b` | `$EBROOTHUMANNMINDB` | point the tool at `chocophlan | uniref | utility_mapping/` |
| `interpro` | `105.0` | `$EBROOTINTERPRO` | module root is correct |
| `KneadData-db` | `20230405` | `$EBROOTKNEADDATAMINDB` | module root is correct |
| `kraken2-db` | `20260226` | `$EBROOTKRAKEN2MINDB` | module root is correct |
| `megares-db` | `3.00` | `$EBROOTMEGARESMINDB` | point the tool at `db/` |
| `metaphlan4-db` | `20260509` | `$EBROOTMETAPHLAN4MINDB` | module root is correct |
| `ncbi-blastdb` | `20260622` | `$EBROOTNCBIMINBLASTDB` | point the tool at `blastdb_v5 | db | diamond/` |
| `pfam` | `37.3` | `$EBROOTPFAM` | module root is correct |
| `pgap-db` | `2021-07-01.build5508` | `$EBROOTPGAPMINDB` | module root is correct |
| `refseq-db` | `230` | `$EBROOTREFSEQMINDB` | point the tool at `db/` |
| `silva` | `138.1` | `$EBROOTSILVA` | **path does not exist** |
| `tailseeker-db` | `20161215` | `$EBROOTTAILSEEKERMINDB` | point the tool at `refdb/` |
| `uniprot` | `2025_02` | `$EBROOTUNIPROT` | point the tool at `blastdb_v5 | db | diamond/` |

## The four broken modulefiles

These point at **`/home/mirrors`**, which does not exist. The real mount is
`/home/mirror` — a symlink into `/private_stores/mirror`. The module loads without
complaint and the tool fails later with a confusing error.

| Module | What the modulefile says | What to use instead |
|---|---|---|
| `chocophlan/0.1.1` | `/home/mirrors/chocophlan/0.1.1` | `/private_stores/mirror/chocophlan/0.1.1` |
| `clusterblast/20170105` | `/home/mirrors/clusterblast/20170105` | `/private_stores/mirror/clusterblast/20170105` |
| `gatkbundle/20191118` | `/home/mirrors/gatkbundle/20191118` | `/private_stores/mirror/gatkbundle/20191118` |
| `silva/138.1` | `/home/mirrors/silva/138.1` | `/private_stores/mirror/silva/138.1` |

**Always `ls` the variable before passing it to a tool:**

    module load silva/138.1
    ls "$EBROOTSILVA" || echo "broken modulefile - substitute /private_stores/mirror/silva/138.1"

This is worth reporting to IGB rather than only working around.

## The eleven that need a subdirectory

Pointing a tool at the module root fails for these — it wants a specific child:

| Module | Pass this |
|---|---|
| `BUSCO-db` | `$EBROOTBUSCOMINDB/lineages` |
| `card-prevalence` | `$EBROOTCARDMINPREVALENCE/db` |
| `checkm2-db` | `$EBROOTCHECKM2MINDB/CheckM2_database` |
| `checkv-db` | `$EBROOTCHECKVMINDB/checkv-db-v1.5` |
| `gtdb` | `$EBROOTGTDB/auxillary_files` (note the spelling — it is misspelled on disk) |
| `humann-db` | `$EBROOTHUMANNMINDB/{chocophlan,uniref,utility_mapping}` |
| `megares-db` | `$EBROOTMEGARESMINDB/db` |
| `ncbi-blastdb` | `$EBROOTNCBIMINBLASTDB/{blastdb_v5,db,diamond}` |
| `refseq-db` | `$EBROOTREFSEQMINDB/db` |
| `tailseeker-db` | `$EBROOTTAILSEEKERMINDB/refdb` |
| `uniprot` | `$EBROOTUNIPROT/{blastdb_v5,db,diamond}` |

`ncbi-blastdb` and `uniprot` each offer three formats — pick `blastdb_v5` for BLAST+,
`diamond` for DIAMOND, `db` for raw FASTA. Passing the wrong one produces a format
error, not a missing-file error.

## Versions — pin them

Twelve of the 29 carry more than one version, and the newest is not always what a
published pipeline expects. The seven with the widest spread:

| Module | Versions |
|---|---|
| `interpro` | 68.0, 101.0, 102.0, 103.0, 104.0, **105.0** |
| `kraken2-db` | 20220327, 20230314, 20240112, 20250714, **20260226** |
| `alphafold-db` | 20210917, 20220118, 20230405, **20240213** |
| `ncbi-blastdb` | 20220318, 20230124, 20250211, **20260622** |
| `pfam` | 32.0, 35.0, 37.0, **37.3** |
| `gtdb` | 207, 214, **226** |
| `uniprot` | 2024_06, 2025_01, **2025_02** |
| `BUSCO-db` | 4, **5** |
| `card-prevalence` | 3.0.6, **4.0.1** |
| `dorado-db` | 20240501, **20261012** |
| `funannotate-db` | 20220428, **20240515** |
| `refseq-db` | 211, **230** |

Sort these **numerically**, not lexicographically — a string sort puts `68.0` above
`105.0` and silently selects a seven-year-old InterPro release. That mistake was made
once in this repository.

## GTDB-Tk

    module load GTDBTk
    module load gtdb/226
    export GTDBTK_DATA_PATH="$EBROOTGTDB/auxillary_files/gtdbtk_package/full_package/release226"

`gtdbtk check_install` **passed** against this path, validating all 8 bundled binaries
(`FastTree FastTreeMP guppy hmmalign hmmsearch pplacer prodigal skani`) and all 9
reference directories.

**It took 1 h 07 m.** The `skani/` directory alone holds **143,617 files**, and the
check stats every one. Run it **once per release**, never as a per-job preflight, and
give it hours — an earlier attempt was killed at 25 minutes and the timeout was
misread as a GTDB-Tk fault.

`gtdb/207` and `gtdb/214` have **no `gtdbtk_package`** — only 226 is usable with
GTDB-Tk.

## AlphaFold databases

`alphafold3-db/20250520` sets **both** `$EBROOTALPHAFOLD3MINDB` and `$BIODB` to
`/private_stores/mirror/alphafold3-db/20250520` (verified inside a running job, not a
login shell). IGB's own documentation uses `$BIODB`; either works.

A caution learned the hard way while checking this: if you probe with
`module load alphafold3-db/20250520 | head`, the load happens in a subshell and **both**
variables come back empty, which looks exactly like "the module does not set them".
Redirect to a file instead of piping.

Contents include `parameters/` (AF3 weights), `pdb_seqres_2022_09_28.fasta`,
`uniref90_2022_05.fa`, `mgy_clusters_2022_05.fa`, `uniprot_all_2021_04.fa`,
`mmcif_files/` and the RNA databases.

**The template cutoff is 2022-09-28.** Any PDB entry deposited before that date is
template-informed, not a blind fold — say so when reporting a result.

`pdb_seqres_2022_09_28.fasta` is a reliable **offline** SEQRES source (headers look like
`>1ubq_A mol:protein length:76`). Resolve a sequence on the cluster from this file
rather than transcribing residues into the transcript, and never type a sequence from
memory.

## Probing without burning a session

**Never** `find` or `du` over `/private_stores/mirror`. Those calls are killed before
they return, and `skani/` shows why. To look inside a database directory:

    ls -1U "$EBROOTGTDB" | head -20

`-1U` is unsorted, so `ls` does not read the whole directory before printing. Combined
with `head`, this cut a full 29-module sweep from 656 s to **105 s**.
