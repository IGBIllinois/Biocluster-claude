---
name: igb-reference-data
description: "Reference databases already mirrored on the IGB biocluster as loadable modules - BLAST nt/nr, GenBank, RefSeq, UniProt, Pfam, InterPro, GTDB, SILVA, Kraken2, CheckM/CheckM2/CheckV, BUSCO, HUMAnN/ChocoPhlAn, MetaPhlAn4, MEGARes, CARD, the GATK resource bundle, AlphaFold 2 and 3 databases, foldseek, Dorado basecalling models and more. Load this BEFORE downloading or staging any reference genome, annotation, BLAST database or model weights for cluster work, and whenever a tool needs a --db/--database path on IGB."
---

# Reference data on the IGB biocluster

**Do not download a reference. Load it.** 29 databases are mirrored as modules. Compute
nodes have **no internet**, so a download inside a job fails; and the data is usually
already here, which means downloading also wastes quota at $8.78/TB/month.

    module load gtdb/226
    gtdbtk classify_wf --genome_dir ./bins --out_dir ./out ... # uses $EBROOTGTDB

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
| `gtdb` | `226` | `$EBROOTGTDB` | `/private_stores/mirror/gtdb/226` | GTDB-Tk taxonomy |
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

**Tier B.** The module names, versions and variable names were read directly from
`module avail` and `module show` on 2026-10-13. The **root paths are derived** from the
observed naming rule (`/private_stores/mirror/<module>/<version>`, or `/home/mirrors/`
for the five noted) — several were truncated in the capture, so treat the path column as
indicative and the variable as authoritative. No database in this table has been used in
a job through this skill yet.

## Two older than they look

`checkm-db/20150116` and `clusterblast/20170105` are the only versions present. If a
result depends on database recency, say so — a 2015 CheckM database is not comparable to
a current one.

## If what you need is not here

Check `module avail | grep -i <name>` first — this list is from one snapshot. If it is
genuinely absent, staging it is a **login-node** step (compute nodes have no egress) and
it belongs in the user's own space, not in a job. Say so and stop; do not try to fetch
it from inside a job script.
