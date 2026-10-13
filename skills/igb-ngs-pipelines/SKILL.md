---
name: igb-ngs-pipelines
description: "Standard sequencing analysis on the IGB biocluster - genome assembly, read alignment and QC, variant calling, RNA-seq, metagenomics, genome annotation and phylogenetics, covering 523 installed modules including bwa, STAR, samtools, GATK, SPAdes, Trinity, salmon, kraken2, RepeatMasker, HMMER, MMseqs2 and IQ-TREE. Load this when running any ordinary command-line bioinformatics tool on IGB, when checking whether a tool is installed and at which version, or when sizing CPU and memory for a sequencing job."
---

# Sequencing pipelines on the IGB biocluster

523 modules across seven families. **Tier C**: every one is installed and the version
list is accurate; none has been run through this skill. The value here is not per-tool
instructions — load the tool's own documentation for that — it is the four site
decisions that are the same for all of them.

## 1. Is it installed, and at which version?

`references/module-index.csv` lists all **927** cluster modules with family, version
count, newest version, whether the IGB wiki knows about it, and a short description.
Search it before concluding anything is missing, and before installing anything.

    module avail 2>&1 | grep -i <name>      # the live check; the CSV is a snapshot

| Family | Modules | Examples |
|---|---|---|
| genome assembly | 98 | `BUSCO`, `Canu`, `CheckM`, `Flye`, `SPAdes`, `quast`, `3d-dna`, `454`, `ABySS`, `AGEnt` |
| read alignment qc | 96 | `BLAST`, `BLAST+`, `BWA`, `Bismark`, `Bowtie2`, `DIAMOND`, `FastQC`, `HISAT2`, `MultiQC`, `SAMtools`, `Subread`, `Trimmomatic` |
| variant calling | 73 | `BCFtools`, `FreeBayes`, `GATK`, `MACS2`, `VCFtools`, `BS-Snper`, `BreakSeq2`, `CNVkit`, `CNVnator`, `COPIES` |
| rnaseq transcriptomics | 58 | `HTSeq`, `STAR`, `Salmon`, `StringTie`, `Trinity`, `kallisto`, `stringtie`, `ASEr`, `CHEUI`, `CLASS2` |
| metagenomics microbiome | 64 | `Kraken2`, `humann`, `metaphlan`, `sortmerna`, `Anacapa`, `BamM`, `BiG-SCAPE`, `Bracken`, `CONCOCT`, `DAS_Tool` |
| annotation databases | 77 | `BRAKER`, `HMMER`, `InterProScan`, `MAKER`, `MMseqs2`, `MUSCLE`, `Prodigal`, `RepeatMasker`, `prokka`, `AGAT` |
| phylogenetics comparative | 57 | `FastTree`, `MAFFT`, `RAxML`, `iqtree`, `AMPHORA2`, `ANIcalculator`, `AdmixTools`, `Arlequin`, `BEAST2`, `BayeScan` |

## 2. Pin the version and stay in one toolchain generation

`module load samtools` takes whatever the default is, and the default moves. Name the
version. And never mix `-IGB-gcc-4.9.4` with `-IGB-gcc-8.2.0` in one job — they are
separate stacks with separate Python builds, and mixing them produces linker errors that
point nowhere near the cause. Prefer `gcc-8.2.0`.

## 3. Load the reference database rather than downloading it

Compute nodes have **no internet**. Most references are already mirrored as modules —
BLAST nt/nr, GenBank, RefSeq, UniProt, Pfam, InterPro, GTDB, SILVA, Kraken2, CheckM,
BUSCO, the GATK bundle and more. See **`igb-reference-data`**. A job that tries to
download a reference fails; a user who downloads one by hand usually did not need to.

## 4. Size the request, then correct it from the first run

Partition `normal` is 7 nodes x 128 cores x 2 TB, with a short queue and no wall-time
limit — the right home for essentially all of this. `admin` (60 GB) and `gpu` (22-32 h
queue) are for GPU work only.

**A job that does not ask for resources gets 2 CPUs**, however large the node. Always
set `-n` and `--mem` explicitly.

Starting points, then `seff <jobid>` and size the next run from `MaxRSS`:

| Work | Request |
|---|---|
| QC, trimming, indexing, small utilities | `-n 4 --mem=16g` |
| alignment, RNA-seq quantification, variant calling | `-n 8 --mem=32g` |
| de novo assembly, large-genome annotation, metagenome assembly | `-n 16 --mem=128g` (scale with genome size; `normal` goes to 2 TB) |
| anything long | no wall-time limit on `normal`, but be considerate — this is shared institute hardware |

`normal` does **not** honour `--cpus-per-task` exactly; `-n` is the reliable form.

## Reporting

Hand the user the commands to watch it themselves rather than only your summary:
`squeue -u $USER`, `tail -f <workdir>/run.log`, `seff <jobid>` when it finishes.
