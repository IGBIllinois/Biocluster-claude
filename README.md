# igb-cluster skills

**New here? Read [ARCHITECTURE.md](ARCHITECTURE.md) first** — what each file is for, how the agent picks which one to read, and how much of it has actually been tested on the cluster.

Claude Science skills for the **IGB Biocluster** at the University of Illinois
Urbana-Champaign. Import them and a new session already knows the cluster: which
partitions that account can use, which databases are already mirrored, which module
versions pair with which, and which failures are silent.

**Start here: [INSTALL.md](INSTALL.md)** — three steps, about ten minutes.

## The seven skills

| Skill | Load it for |
|---|---|
| `igb-cluster` | always — partitions, site policy, module rules, job skeleton, audit commands |
| `igb-reference-data` | before downloading any reference genome, annotation or database |
| `igb-structure-prediction` | AlphaFold 2/3, Rosetta, foldseek, RNA secondary structure |
| `igb-gpu-ml` | anything needing a GPU; torch / tensorflow / jax |
| `igb-single-cell` | Cell Ranger, Space Ranger, scanpy |
| `igb-workflows` | Nextflow, Snakemake, Cromwell, containers |
| `igb-ngs-pipelines` | ordinary sequencing work, plus an index of all 927 modules |

`igb-cluster` is the hub and is always loaded first; the other six assume it. It also
ships `kernel.py`, which turns the site rules into callable helpers — **GitHub import
excludes sidecar files**, so that file is not installed by the steps in
[INSTALL.md](INSTALL.md) and the skill documents are written to stand alone without it. They are
the **site layer** only — which module, which database, which partition, measured
wall-clock, known failures. For the science itself the agent loads the tool's own skill
(`alphafold2`, `boltz`, `scvi-tools`, `proteinmpnn`, …) alongside.

## The two facts that cost the most to learn

**Reference databases are already here, as modules.** 29 of them — BLAST nt/nr,
GenBank, RefSeq, UniProt, Pfam, InterPro, GTDB, SILVA, Kraken2, CheckM, BUSCO, the GATK
bundle, the AlphaFold 2 and 3 databases. **None appears on the IGB Applications wiki
page.** Compute nodes have no internet, so loading the module is not the convenient
route — it is the only one. The variable name is not guessable either: `EBROOT` plus the
module name uppercased with every `-` replaced by `MIN`, so `alphafold3-db` sets
`$EBROOTALPHAFOLD3MINDB`.

**Two toolchain generations exist and must not be mixed.** 680 module versions carry
`-IGB-gcc-4.9.4`, 608 carry `-IGB-gcc-8.2.0`, 507 carry no tag. Mixing one of each in a
job gives linker and `libpython` errors that point nowhere near the cause. Prefer
`gcc-8.2.0`, and pin versions explicitly — `cellranger` has 18, `R` 14, `PyTorch` 15,
`CUDA` 13, `nextflow` 16.

## Confidence tiers

Every claim is tagged, so the agent knows what to trust:

- **A — verified** on this cluster; the recipe is the one that worked, with timings.
- **B — documented**: the module exists and the invocation comes from `module show` or
  IGB's docs, but nobody has run it here.
- **C — listed**: the module is present. Nothing further is claimed.

As of 2026-10-13, **tier A**: the hub, the AlphaFold 3 recipe, the scanpy/leidenalg
workaround, all 29 reference-database paths, GTDB-Tk against r226, the GPU framework
pairing, and nextflow/snakemake/singularity. **Tier C**: the 523 NGS modules, the 10x
single-cell tools, and structure prediction other than AlphaFold 3. There is no tier B
left — every claim that could be settled by inspection has been.

**What remains at C cannot be promoted from a desk.** Those claims are about tools
producing correct output on real input, and the only way to settle one is to run it on
the cluster with your own data. **If you do, open a PR** adding the command you used and
the runtime you saw — that is how this stops being a catalogue and becomes a manual.

Three of the four verification sweeps found claims that were *wrong*, not merely
unverified: five databases whose module variable points at a path that does not exist, a
`nvidia-smi` preflight that would have aborted every GPU job, and a PyTorch build that
passes `torch.cuda.is_available()` and then crashes. Assume the tier C rows contain
errors of the same kind.

## Provenance

Built by reconciling the [IGB Applications
page](https://help.igb.illinois.edu/Biocluster_Applications) (898 applications, 1739
versions) against live `module avail` on `biologin-3` (**927** modules, **1795**
versions) on 2026-10-13. Nothing on the page was missing from the cluster; 29 modules on
the cluster were missing from the page, and all 29 were reference databases. The full
inventory ships inside the repo at
`skills/igb-ngs-pipelines/references/module-index.csv`.
