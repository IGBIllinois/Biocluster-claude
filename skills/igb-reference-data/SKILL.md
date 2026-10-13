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

**Check one or two levels in before concluding a database is not mirrored.** Some
mirrors nest a tool-ready package under `auxillary_files/`, so the module root looks
like the wrong shape and the data appears to be missing when it is not:

    find "$EBROOT<NAME>" -maxdepth 3 -type d | head -40

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

## Catalogue (newest version as of 2026-10-13)

| Module | Newest | Root variable | Root path | Consumed by |
|---|---|---|---|---|
| `BUSCO-db` | `5` | `$EBROOTBUSCOMINDB` | `/private_stores/mirror/BUSCO-db/5` | BUSCO completeness scoring |
| `KneadData-db` | `20230405` | `$EBROOTKNEADDATAMINDB` | `/private_stores/mirror/KneadData-db/20230405` | KneadData host-read removal |
| `alphafold-db` | `20240213` | `$EBROOTALPHAFOLDMINDB` | `/private_stores/mirror/alphafold-db/20240213` | AlphaFold 2 |
| `alphafold3-db` | `20250520` | `$EBROOTALPHAFOLD3MINDB` | `/private_stores/mirror/alphafold3-db/20250520` | AlphaFold 3 |
| `bart2-db` | `20240302` | `$EBROOTBART2MINDB` | `/private_stores/mirror/bart2-db/20240302` | BART2 TF activity |
| `card-prevalence` | `4.0.1` | `$EBROOTCARDMINPREVALENCE` | `/private_stores/mirror/card-prevalence/4.0.1` | CARD / RGI resistance genes |
| `checkm-db` | `20150116` | `$EBROOTCHECKMMINDB` | `/private_stores/mirror/checkm-db/20150116` | CheckM bin quality |
| `checkm2-db` | `20230511` | `$EBROOTCHECKM2MINDB` | `/private_stores/mirror/checkm2-db/20230511` | CheckM2 bin quality |
| `checkv-db` | `1.5` | `$EBROOTCHECKVMINDB` | `/private_stores/mirror/checkv-db/1.5` | CheckV viral contig quality |
| `chocophlan` | `0.1.1` | `$EBROOTCHOCOPHLAN` | `/home/mirrors/chocophlan/0.1.1` | HUMAnN pangenome search |
| `clusterblast` | `20170105` | `$EBROOTCLUSTERBLAST` | `/home/mirrors/clusterblast/20170105` | antiSMASH clusterblast |
| `dorado-db` | `20261012` | `$EBROOTDORADOMINDB` | `/private_stores/mirror/dorado-db/20261012` | Dorado basecalling models |
| `foldseek-db` | `20230921` | `$EBROOTFOLDSEEKMINDB` | `/private_stores/mirror/foldseek-db/20230921` | foldseek structure search |
| `funannotate-db` | `20240515` | `$EBROOTFUNANNOTATEMINDB` | `/private_stores/mirror/funannotate-db/20240515` | funannotate fungal annotation |
| `gatkbundle` | `20191118` | `$EBROOTGATKBUNDLE` | `/home/mirrors/gatkbundle/20191118` | GATK resource bundle |
| `genbank` | `250` | `$EBROOTGENBANK` | `/private_stores/mirror/genbank/250` | GenBank flatfiles |
| `gtdb` | `226` | `$EBROOTGTDB` | `/private_stores/mirror/gtdb/226` | GTDB release files. **GTDB-Tk needs a deeper path — see above** |
| `humann-db` | `201901b` | `$EBROOTHUMANNMINDB` | `/private_stores/mirror/humann-db/201901b` | HUMAnN pathways |
| `interpro` | `68.0` | `$EBROOTINTERPRO` | `/home/mirrors/interpro/68.0` | InterProScan |
| `kraken2-db` | `20260226` | `$EBROOTKRAKEN2MINDB` | `/private_stores/mirror/kraken2-db/20260226` | Kraken2 classification |
| `megares-db` | `3.00` | `$EBROOTMEGARESMINDB` | `/private_stores/mirror/megares-db/3.00` | MEGARes resistance |
| `metaphlan4-db` | `20260509` | `$EBROOTMETAPHLAN4MINDB` | `/private_stores/mirror/metaphlan4-db/20260509` | MetaPhlAn 4 profiling |
| `ncbi-blastdb` | `20260622` | `$EBROOTNCBIMINBLASTDB` | `/private_stores/mirror/ncbi-blastdb/20260622` | BLAST (nt/nr etc.) |
| `pfam` | `37.3` | `$EBROOTPFAM` | `/private_stores/mirror/pfam/37.3` | Pfam HMMs / hmmscan |
| `pgap-db` | `2021-07-01.build5508` | `$EBROOTPGAPMINDB` | `/private_stores/mirror/pgap-db/2021-07-01.build5508` | NCBI PGAP prokaryotic annotation |
| `refseq-db` | `230` | `$EBROOTREFSEQMINDB` | `/private_stores/mirror/refseq-db/230` | RefSeq |
| `silva` | `138.1` | `$EBROOTSILVA` | `/home/mirrors/silva/138.1` | SILVA rRNA (QIIME, mothur) |
| `tailseeker-db` | `20161215` | `$EBROOTTAILSEEKERMINDB` | `/private_stores/mirror/tailseeker-db/20161215` | tailseeker |
| `uniprot` | `2025_02` | `$EBROOTUNIPROT` | `/private_stores/mirror/uniprot/2025_02` | UniProt |

**Tier B, except `gtdb` which is tier A.** The module names, versions and variable names
were read directly from `module avail` and `module show` on 2026-10-13. The **root paths
are derived** from the observed naming rule
(`/private_stores/mirror/<module>/<version>`, or `/home/mirrors/` for the five noted) —
several were truncated in the capture, so treat the path column as indicative and the
variable as authoritative. Only the GTDB tree has been walked on the cluster and had its
contents confirmed; the rest have not been opened or used in a job through this skill.

**The GTDB case is why the path column is only indicative.** It was listed here as
"GTDB-Tk taxonomy" with the module root as its path, and that was wrong in a way that
would have cost a user ~110 GB and a day: the module root has no GTDB-Tk layout, and a
reasonable reader would have concluded the package was not mirrored. Expect the same
shape of error in other rows. When you open one of these trees and find out what is
actually in it, **correct this table** — the path column is a hypothesis, not a finding.

## Two older than they look

`checkm-db/20150116` and `clusterblast/20170105` are the only versions present. If a
result depends on database recency, say so — a 2015 CheckM database is not comparable to
a current one.

## If what you need is not here

Check `module avail | grep -i <name>` first — this list is from one snapshot. If it is
genuinely absent, staging it is a **login-node** step (compute nodes have no egress) and
it belongs in the user's own space, not in a job. Say so and stop; do not try to fetch
it from inside a job script.
