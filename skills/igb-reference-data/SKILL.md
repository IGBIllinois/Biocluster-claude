---
name: igb-reference-data
description: "Reference databases already mirrored on the IGB biocluster as loadable modules - BLAST nt/nr, GenBank, RefSeq, UniProt, Pfam, InterPro, GTDB, SILVA, Kraken2, CheckM/CheckM2/CheckV, BUSCO, HUMAnN/ChocoPhlAn, MetaPhlAn4, MEGARes, CARD, the GATK resource bundle, AlphaFold 2 and 3 databases, foldseek, Dorado basecalling models and more. Load this BEFORE downloading or staging any reference genome, annotation, BLAST database or model weights for cluster work, and whenever a tool needs a --db/--database path on IGB."
---

# Reference data on the IGB biocluster

**Do not download a reference. Load it.** 29 databases are mirrored as modules. Compute
nodes have **no internet**, so a download inside a job fails; and the data is usually
already here, which means downloading also wastes quota at $8.78/TB/month.

    module load pfam/37.3
    echo "$EBROOTPFAM"          # /private_stores/mirror/pfam/37.3
    hmmscan --domtblout out.tbl "$EBROOTPFAM/Pfam-A.hmm" query.faa

## A module's root is not always the path your tool wants

**16 of the 29 databases need a subdirectory, not the module root** — see the bolded
cells in the catalogue below. Some nest the tool-ready package several levels down, so
the root looks like the wrong shape and the data appears missing when it is not.

**Use `ls`, never `find`, on these mirrors.** They are multi-terabyte NFS trees:
`find "$EBROOT<NAME>" -maxdepth 3` exceeded the login-node command timeout, and the same
walk inside a job produced 18 lines in seven minutes before it was cancelled. Step down
one level at a time instead:

    ls "$EBROOT<NAME>"                 # one level, returns in seconds
    ls "$EBROOT<NAME>/<subdir>"        # repeat only if the shape is still wrong

The worked case — **tier A, verified 2026-10-13** — is GTDB-Tk. `module load gtdb/226`
sets `$EBROOTGTDB` to `/private_stores/mirror/gtdb/226`, which holds only the plain GTDB
release (taxonomy, metadata, MSAs, `genomic_files_*`) and **no GTDB-Tk layout at all**.
The GTDB-Tk reference package is two levels deeper:

    module purge                      # the GTDBTk module's own message forbids others
    module load GTDBTk/2.6.1
    export GTDBTK_DATA_PATH=/private_stores/mirror/gtdb/226/auxillary_files/gtdbtk_package/full_package/release226
    gtdbtk check_install              # run this FIRST - see the caveat below
    gtdbtk classify_wf --genome_dir ./bins --out_dir ./out \
      --extension fa --cpus 32 --skip_ani_screen

That directory carries exactly the layout `classify_wf` expects — `markers masks
metadata mrca_red msa pplacer radii skani split taxonomy` — and
`metadata/metadata.txt` reads `VERSION_DATA=r226`. Permissions are `drwxrwxr-x
datamover:datamover`, world-readable, so point at it in place; copying it into `$HOME`
duplicates ~110 GB of unbacked-up storage for nothing.

Two siblings under `.../gtdbtk_package/`:

- `split_package/` — `gtdbtk_r226_data.tar.gz.part_aa` … `part_an` (14 parts) plus
  `HOWTO.txt`. The archive form; only of use to someone who wants a private copy.
- `mockup_db/r226_mockup/` — the same ten directories, tiny. Use it to smoke-test
  pipeline plumbing before committing a real run.

`gtdb/207` and `gtdb/214` have **no** `gtdbtk_package` — R226 is the only release
mirrored in GTDB-Tk-ready form.

**Caveat:** `GTDBTk/2.6.1` against r226 has **not** been confirmed with
`gtdbtk check_install` (the verification job failed on the submit transport, not on the
data). Run it as the first line of your job. The module also prints "There is a newer
version of GTDB-Tk available: v2.8.0" on load — cosmetic, and unrelated to the data
release. `--skip_ani_screen` avoids needing a separate Mash database; drop it and pass
`--mash_db <path>` if you want the ANI prescreen. The skani database inside the package
is used for the species-level step either way.

## Five modules hand you a path that does not exist

`chocophlan`, `clusterblast`, `gatkbundle`, `interpro` and `silva` set their root to
`/home/mirrors/...`. **There is no `/home/mirrors` on this cluster.** The directory is
`/home/mirror` — singular — and it is a symlink to `/private_stores/mirror/`. The data
is present and complete; the module variable has an extra `s`.

So if `$EBROOT<NAME>` starts with `/home/mirrors/`, strip the `s`, or use the real
location directly:

    module load silva/138.1
    echo "$EBROOTSILVA"                      # /home/mirrors/silva/138.1  <- does not exist
    DB=/private_stores/mirror/silva/138.1    # <- use this
    ls "$DB"                                 # ARB_files Exports Fields_description ...

Verified 2026-10-13: all five exist at `/private_stores/mirror/<module>/<same version>`.
Guard it in a script rather than trusting either path:

    [ -d "$EBROOTSILVA" ] || EBROOTSILVA=${EBROOTSILVA/\/home\/mirrors\//\/private_stores\/mirror\/}

## The variable name is not guessable

`EBROOT` + the module name **uppercased**, with every `-` replaced by **`MIN`**:

| Module | Variable |
|---|---|
| `alphafold3-db` | `$EBROOTALPHAFOLD3MINDB` |
| `ncbi-blastdb` | `$EBROOTNCBIMINBLASTDB` |
| `card-prevalence` | `$EBROOTCARDMINPREVALENCE` |
| `gtdb` | `$EBROOTGTDB` |

Each module also sets `EBVERSION<NAME>`. **Load the module and `echo` the variable
before using it** — do not hardcode the path into a job script.

## Catalogue — opened and listed on the cluster 2026-10-13

**Tier A.** Every row below was produced by loading the module, reading back the
variable it actually sets, and listing the directory. `$R` below means that root.

| Module | Newest | Variable | Root path | Point your tool at | What is actually in it |
|---|---|---|---|---|---|
| `BUSCO-db` | `5` | `$EBROOTBUSCOMINDB` | `/private_stores/mirror/BUSCO-db/5` | `lineages/` | 4 entries: `lineages/`, `placement_files/`, `file_versions.tsv` |
| `KneadData-db` | `20230405` | `$EBROOTKNEADDATAMINDB` | `/private_stores/mirror/KneadData-db/20230405` | `$R/hg37dec_v0.1` (index prefix) | 19 entries: bowtie2 indexes `hg37dec_v0.1.*`, `human_hg38_refMrna.*` |
| `alphafold-db` | `20240213` | `$EBROOTALPHAFOLDMINDB` | `/private_stores/mirror/alphafold-db/20240213` | root (`--data_dir`) | `bfd mgnify params pdb70 pdb_mmcif pdb_seqres small_bfd uniprot uniref30` |
| `alphafold3-db` | `20250520` | `$EBROOTALPHAFOLD3MINDB` | `/private_stores/mirror/alphafold3-db/20250520` | root = `--db_dir`, `parameters/` = `--model_dir` | `parameters/ mmcif_files/` + MSA FASTAs; template cutoff 2022-09-28 |
| `bart2-db` | `20240302` | `$EBROOTBART2MINDB` | `/private_stores/mirror/bart2-db/20240302` | `hg38_library/` or `mm10_library/` | two species libraries (+ their tarballs) |
| `card-prevalence` | `4.0.1` | `$EBROOTCARDMINPREVALENCE` | `/private_stores/mirror/card-prevalence/4.0.1` | **`db/`** | `db/` holds `aro.json`, `aro_index.tsv`, `61_kmer_db.json` |
| `checkm-db` | `20150116` | `$EBROOTCHECKMMINDB` | `/private_stores/mirror/checkm-db/20150116` | root | `distributions genome_tree hmms hmms_ssu img pfam test_data` — correct shape |
| `checkm2-db` | `20230511` | `$EBROOTCHECKM2MINDB` | `/private_stores/mirror/checkm2-db/20230511` | **`CheckM2_database/`** | root holds only that one dir + `easybuild` |
| `checkv-db` | `1.5` | `$EBROOTCHECKVMINDB` | `/private_stores/mirror/checkv-db/1.5` | **`checkv-db-v1.5/`** | root holds the dir + its tarball |
| `chocophlan` | `0.1.1` | `$EBROOTCHOCOPHLAN` | **`/private_stores/mirror/chocophlan/0.1.1`** | root | variable points at dead `/home/mirrors`. Also inside `humann-db/201901b/chocophlan` |
| `clusterblast` | `20170105` | `$EBROOTCLUSTERBLAST` | **`/private_stores/mirror/clusterblast/20170105`** | root | variable points at dead `/home/mirrors` |
| `dorado-db` | `20261012` | `$EBROOTDORADOMINDB` | `/private_stores/mirror/dorado-db/20261012` | one model dir | **154 models**, e.g. `dna_r10.4.1_e8.2_400bps_hac@v5.0.0`; pick by chemistry+speed |
| `foldseek-db` | `20230921` | `$EBROOTFOLDSEEKMINDB` | `/private_stores/mirror/foldseek-db/20230921` | `afdb/`, `afdb-uniprot/` or `pdb/` | three separate target databases |
| `funannotate-db` | `20240515` | `$EBROOTFUNANNOTATEMINDB` | `/private_stores/mirror/funannotate-db/20240515` | root (`FUNANNOTATE_DB`) | 37 entries, flat: `dbCAN.hmm`, `dikarya/`, `busco_outgroups.tar.gz` |
| `gatkbundle` | `20191118` | `$EBROOTGATKBUNDLE` | **`/private_stores/mirror/gatkbundle/20191118`** | root | variable points at dead `/home/mirrors`. Also on disk: `2.5`, `3.8`, `example_bam_b37` |
| `genbank` | `250` | `$EBROOTGENBANK` | `/private_stores/mirror/genbank/250` | root | **5539 entries** — flat `gbbct*.seq` flatfiles plus `catalog/ daily-nc/ docs/` |
| `gtdb` | `226` | `$EBROOTGTDB` | `/private_stores/mirror/gtdb/226` | **`auxillary_files/gtdbtk_package/full_package/release226`** | root is the plain release only — see the GTDB-Tk section above |
| `humann-db` | `201901b` | `$EBROOTHUMANNMINDB` | `/private_stores/mirror/humann-db/201901b` | `chocophlan/`, `uniref/` or `utility_mapping/` | three sub-databases, one per HUMAnN stage |
| `interpro` | `**105.0**` | `$EBROOTINTERPRO` | **`/private_stores/mirror/interpro/105.0`** | root | variable points at dead `/home/mirrors`. Modules: `68.0, 101.0–105.0` |
| `kraken2-db` | `20260226` | `$EBROOTKRAKEN2MINDB` | `/private_stores/mirror/kraken2-db/20260226` | one `k2_*` subdir | **10 databases**: `k2_nt k2_pluspf k2_pluspfp k2_gtdb k2_minusb k2_eupathdb48` + 08gb/16gb capped builds |
| `megares-db` | `3.00` | `$EBROOTMEGARESMINDB` | `/private_stores/mirror/megares-db/3.00` | **`db/`** | `megares_database_v3.00.fasta` + annotation CSVs |
| `metaphlan4-db` | `20260509` | `$EBROOTMETAPHLAN4MINDB` | `/private_stores/mirror/metaphlan4-db/20260509` | root = `--bowtie2db` | index name `mpa_vFeb24_CDIFF_CHOCOPhlAnSGB_20240910`; `mpa_latest` points at it |
| `ncbi-blastdb` | `20260622` | `$EBROOTNCBIMINBLASTDB` | `/private_stores/mirror/ncbi-blastdb/20260622` | **`db/nt`**, **`db/nr`**, `db/pdbaa` | also `blastdb_v5/` and `diamond/` builds of the same data |
| `pfam` | `37.3` | `$EBROOTPFAM` | `/private_stores/mirror/pfam/37.3` | `$R/Pfam-A.hmm` | flat: `Pfam-A.hmm`, `Pfam-A.fasta`, `Pfam-A.clans.tsv`, `active_site.dat` |
| `pgap-db` | `2021-07-01.build5508` | `$EBROOTPGAPMINDB` | `/private_stores/mirror/pgap-db/2021-07-01.build5508` | root | 24 entries, flat: `16S_rRNA`, `23S_rRNA`, `CDD2/`, `AntiFamLib/` |
| `refseq-db` | `230` | `$EBROOTREFSEQMINDB` | `/private_stores/mirror/refseq-db/230` | **`db/<division>`** | `db/` splits by `archaea bacteria complete fungi invertebrate ...` |
| `silva` | `138.1` | `$EBROOTSILVA` | **`/private_stores/mirror/silva/138.1`** | `Exports/` | variable points at dead `/home/mirrors`. Holds `ARB_files/ Exports/ Fields_description/` |
| `tailseeker-db` | `20161215` | `$EBROOTTAILSEEKERMINDB` | `/private_stores/mirror/tailseeker-db/20161215` | **`refdb/`** | root holds only that dir |
| `uniprot` | `2025_02` | `$EBROOTUNIPROT` | `/private_stores/mirror/uniprot/2025_02` | **`db/knowledgebase`** | also `db/decoy`, `db/rdf`, plus `blastdb_v5/` and `diamond/` builds |

**Sixteen of the 29 need a subdirectory, not the root** — the bolded cells above. This is
the single most common way to waste a queue slot here: the job starts, the tool rejects
the path, and you have lost the wait. Confirm with `ls "$EBROOT<NAME>"` on the login node
before you submit.

**`interpro` was listed here as `68.0` until 2026-10-13 and that was a sorting bug** —
`"68.0"` sorts above `"105.0"` as text. Versions `101.0` through `105.0` are all
available as modules. If you see a suspiciously old "newest" elsewhere in these skills,
suspect the same cause.

## Two older than they look

`checkm-db/20150116` and `clusterblast/20170105` are the only versions present. If a
result depends on database recency, say so — a 2015 CheckM database is not comparable to
a current one.

## If what you need is not here

Check `module avail | grep -i <name>` first — this list is from one snapshot. If it is
genuinely absent, staging it is a **login-node** step (compute nodes have no egress) and
it belongs in the user's own space, not in a job. Say so and stop; do not try to fetch
it from inside a job script.
