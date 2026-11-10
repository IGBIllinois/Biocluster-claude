---
name: igb-ngs-pipelines
description: "Sequencing analysis on IGB Biocluster 4 — assembly, read alignment and search, QC, variant calling, RNA-seq, metagenomics, annotation and phylogenetics. Carries the module-index table of all 173 Biocluster 4 modules, the tools that did not survive the migration from Biocluster 3, and the job shapes that fit this hardware. Load before writing any sequencing job here."
---

# Sequencing pipelines on Biocluster 4

Load `igb-cluster` first for partitions, ceilings and submission rules. Almost
everything here is CPU work and belongs on `normal`.

Full searchable table of all 173 modules: `references/module-index.csv`
(columns: module, n_versions, versions, newest, category, skill).

## First: check the tool is still here

The stack shrank from **927 module names on Biocluster 3 to 173**. Confirmed gone:

    SPAdes  Trinity  salmon  RepeatMasker  snakemake  hhsuite  ViennaRNA  RNAstructure
    mfold  rosetta  PyRosetta  pymol  rdkit  foldseek (standalone)  cromwell  toil

`module avail <name>` before you promise anything. If a tool is absent, say so and offer
a present alternative by name rather than substituting one silently.

## What is here, by job type

### Assembly and genome QC

| Need | Module |
|---|---|
| HiFi assembly | `hifiasm/0.25.0` |
| ONT/long-read assembly | `Flye/2.9.6` |
| lightweight long-read assembly | `miniasm`, `Raven` |
| polishing | `Racon`, `medaka` (see `igb-single-cell`) |
| bacterial assembly reconciliation | `Trycycler` |
| assembly QC | `QUAST`, `BUSCO/6.1.0` + `BUSCO-db/5` |
| k-mer / ploidy | `Jellyfish`, `KMC`, `FastK`, `smudgeplot` |
| ANI / distance | `FastANI`, `Mash` |
| graph handling | `gfatools` |

**There is no short-read assembler** — SPAdes is gone. For short-read de novo work this
cluster no longer has a module; flag it rather than improvising.

### Alignment and search

`BWA/0.7.19`, `Bowtie2`, `HISAT2`, `STAR/2.7.11b`, `minimap2/2.30`, `miniprot`,
`MMseqs2`, `DIAMOND`, `BLAST+`, `BLAST`. Multiple aligners, `MAFFT`, `MUSCLE`,
`Clustal-Omega`, `trimAL`. Profile search: `HMMER`, `Infernal`, `MEME`.

For BLAST and DIAMOND, **use the mirrored databases** — `ncbi-blastdb/20260622`,
`uniprot/2025_02`, `refseq-db/230`, `genbank/250`. Each needs a subdirectory, not the
module root; see `igb-reference-data`.

### Read QC and preprocessing

`FastQC`, `MultiQC`, `fastp`, `cutadapt`, `Filtlong`, `seqtk`, `BBMap`, `SortMeRNA`,
`CD-HIT`.

### Variant calling

`GATK/4.6.2.0`, `BCFtools`, `VCFtools`, `picard`, `CNVkit`, `breseq`, `sentieon/202503`.

`gatkbundle/20191118` is mirrored but its **modulefile path is broken** — substitute
`/private_stores/mirror/gatkbundle/20191118`. See `igb-reference-data`.

`sentieon` is a licensed accelerated re-implementation of the GATK best-practices
pipeline. If throughput matters, ask the user whether they are entitled to use it before
building a workflow around it.

### RNA-seq and epigenomics

`STAR`, `RSEM`, `Subread` (featureCounts), `SUPPA`, `deepTools`, `MACS3`.

**`salmon` and `Trinity` are gone.** For transcript quantification the remaining route is
`STAR` + `RSEM` or `Subread`; for de novo transcriptome assembly there is no module.

### Metagenomics

`Kraken2/2.17.1` + `kraken2-db/20260226`, `metaphlan/4.2.5` + `metaphlan4-db/20260509`,
`humann-db`, `chocophlan`, `GTDBTk/2.8.0` + `gtdb/226`, `CheckM`/`checkm2-db`,
`checkv-db`, `CoverM`, `MetaEuk`, `vsearch`, `QIIME2/2026.7`, `biom-format`, `MinCED`,
`barrnap`, `ITSx`, `KneadData-db`, `megares-db`, `card-prevalence`.

GTDB-Tk has a verified setup and a **1 h 07 m** `check_install` — see
`igb-reference-data` before running it.

### Annotation

`prokka`, `augustus`, `eggnog-mapper`, `Prodigal`, `ARAGORN`, `phobius`, `table2asn`,
`gffread`, plus `pgap-db`, `funannotate-db`, `interpro/105.0`, `pfam/37.3`.

**`interpro` has six versions and the newest is 105.0, not 68.0.** Sort numerically — a
string sort picks the seven-year-old release. That mistake has been made here before.

### Phylogenetics

`iqtree3`, `FastTree`, `DendroPy`, `LSD2`, `phylophlan`, `SEPP`.

### Libraries and file tools

`SAMtools/1.22`, `BamTools`, `BEDTools`, `HTSlib`, `Pysam`, `pybedtools`, `pyBigWig`,
`Biopython/1.88`, `BioPerl`.

## Job shape

`normal` nodes are large, so the usual mistake here is asking for too little rather than
too much. **A job that does not ask gets 2 CPUs.** Core counts and the memory ceiling are
in the hub's partition table — check `--mem` against it before submitting.

    #!/bin/bash
    #SBATCH -p normal
    #SBATCH -N 1
    #SBATCH -n 16
    #SBATCH --mem=64g
    #SBATCH -t 24:00:00

    : "${TMPDIR:=$PWD/tmp}"; mkdir -p "$TMPDIR"; export TMPDIR
    module purge
    module load SAMtools/1.22-IGB-gcc-15.2.0

    <work> 2>&1 | tee -a ./run.log

Three things that make a difference:

1. **Match the tool's thread flag to `-n`.** `-@`, `-t`, `--threads` — a tool left at
   its default will use one core of the sixteen you reserved.
2. **Guard `TMPDIR`.** Slurm sets it to a node-local `/scratch/$SLURM_JOB_ID` inside a
   job, but not on the login node. Write `: "${TMPDIR:=$PWD/tmp}"; mkdir -p "$TMPDIR"`
   so sorting and alignment tools never fall back to `$HOME`.
3. **Check `seff` afterwards and report it.** Measured efficiency is the only way these
   numbers stop being guesses, and the user is billed for what was reserved.

## Module naming

One toolchain generation: `IGB-gcc-15.2.0` (plus a few `GCCcore-15.2.0`). Python-linked
modules carry `-Python-3.14.0`. Biocluster 3's `-IGB-gcc-8.2.0` suffix does not exist
here — strip it and re-resolve from `module avail`.

**Never pipe `module load`.** It runs in a subshell, the load is discarded, and you fall
through to the system Python with an error that points nowhere near the cause.

## Confidence

Tier C for most of this skill: the modules are present at the versions listed, verified
2026-10-31. The job shape, the `TMPDIR` requirement and the database pairings are tier A.
Individual pipelines have not been run end to end on Biocluster 4 — when you run one,
report the timing and `seff` so it can be promoted.
