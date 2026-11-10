# Skill tests

Fourteen prompts. Each is a realistic request where the obvious answer is **wrong on
Biocluster 4**, and the correction lives in one of these skills. Run them after any
change to the repository; a wrong answer names the file to fix.

Ask them in a fresh session with the skills imported and the `igb` compute target
configured. Do not prime the agent — paste the prompt as written.

> Most of these do not need a job to be submitted. The agent should answer from the
> skills. If it starts probing the cluster to answer something that is written down,
> that is itself a finding: the fact is in the wrong file, or the description does not
> match the question.

---

### 1. Partition access

> *"What GPU partitions can I use on igb, and what's the memory ceiling on each?"*

**Pass:** `gpu` only — A40s, 250 GB node ceiling. Mentions that `sinfo -a` lists others
which are not accessible.
**Fail:** offers **any** partition other than `gpu` — including a staff or lab
partition that appears idle in `sinfo`. Also a fail if it quotes a queue wait as fact
without saying it should be measured.
→ `igb-cluster/references/partitions.md`

### 2. Reference databases

> *"I need to BLAST a few thousand sequences against nr on the cluster. How do I get the
> database?"*

**Pass:** `module load ncbi-blastdb/20260622`, then a subdirectory of
`$EBROOTNCBIMINBLASTDB` (`blastdb_v5` for BLAST+). No download.
**Fail:** proposes downloading nr, or passes the module root directly.
→ `igb-reference-data`

### 3. TensorFlow on the GPU

> *"Write me a job script to train a small CNN on the GPU with TensorFlow on igb."*

**Pass:** states plainly that TensorFlow 2.21.0 **cannot see the A40** — measured both
alone and with the CUDA/cuDNN modules — and that there is no CUDA 12 module to pair it
with. Offers PyTorch, or escalation to IGB.
**Fail:** writes a TF GPU script, or suggests loading `CUDA/13.1.0` as the fix. That was
the Biocluster 3 answer and it does not work here.
→ `igb-gpu-ml`

### 4. A tool that no longer exists

> *"Set up a scanpy clustering pipeline on igb for my 10x data."*

**Pass:** says there is no `scanpy` module on Biocluster 4, and offers the two honest
routes (venv on the login node, or count on the cluster and analyse elsewhere).
**Fail:** writes `module load scanpy/...`, or references a `cs/scanpy-leiden` shared
environment. Both are Biocluster 3 artefacts.
→ `igb-single-cell`

### 5. A workflow manager that no longer exists

> *"I have a Snakemake workflow. How do I run it on igb?"*

**Pass:** says `snakemake` is not a module here, offers a personal venv or plain Slurm
jobs, and does not invent a module name.
**Fail:** `module load snakemake`.
→ `igb-workflows`

### 6. AlphaFold 3 and the template cutoff

> *"Predict the structure of ubiquitin (PDB 1UBQ) with AlphaFold 3 on igb."*

**Pass:** uses `alphafold/3.0.4` + `alphafold3-db/20250520`, resolves the sequence from
`pdb_seqres_2022_09_28.fasta` on the cluster rather than typing it, and **volunteers
that 1UBQ is inside the 2022-09-28 template set**, so the result is template-informed.
**Fail:** types the sequence from memory; omits the template caveat; quotes a
Biocluster 3 wall-clock as if measured on Biocluster 4.
→ `igb-structure-prediction`

### 7. Version sorting

> *"What's the newest InterPro on igb?"*

**Pass:** **105.0**.
**Fail:** 68.0 — the answer you get from sorting versions as strings.
→ `igb-reference-data`

### 8. A broken modulefile

> *"Load the SILVA database on igb and show me what's in it."*

**Pass:** notes the modulefile points at `/home/mirrors/silva/138.1`, which does not
exist, and substitutes `/private_stores/mirror/silva/138.1`.
**Fail:** reports the database as missing or broken, or hands back the dead path.
→ `igb-reference-data`

### 9. Scratch space

> *"Write me a sorting job that needs a lot of temp space on igb."*

**Pass:** uses `$TMPDIR` if Slurm set it and falls back to a workdir path if not, e.g.
`: "${TMPDIR:=$PWD/tmp}"; mkdir -p "$TMPDIR"`. Bonus if it notes node-local scratch is
wiped at job end.
**Fail:** asserts there is no `/scratch` on Biocluster 4 (false inside a job — Slurm
provides `/scratch/$SLURM_JOB_ID`), or writes temp files into `$HOME`.
→ `igb-cluster`

### 10. Nextflow

> *"Run an nf-core RNA-seq pipeline on igb."*

**Pass:** launches from the **login node** (not wrapped in `sbatch`), sets `NXF_HOME`,
pre-pulls containers into `NXF_SINGULARITY_CACHEDIR`, and mentions IGB's 3-pipeline
concurrency limit.
**Fail:** wraps the whole run in an `sbatch` allocation, or sets `executor = 'local'`.
→ `igb-workflows`

### 11. A model that will not fit

> *"Can I run Evo 2 40B on igb?"*

**Pass:** **no** — it needs FP8, which requires a Hopper-class GPU; the A40 is sm_86.
Only the 7B models run here, in bfloat16.
**Fail:** says yes, or proposes a memory workaround. The limit is the instruction set,
not the VRAM.
→ `igb-gpu-ml`

### 12. An expensive validation step

> *"Before I run GTDB-Tk, check the database install is OK."*

**Pass:** gives the `GTDBTK_DATA_PATH` under `auxillary_files`, and warns that
`check_install` takes about **an hour** (`skani/` alone has 143,617 files) and is a
once-per-release check, not a per-job preflight.
**Fail:** puts `check_install` in the job script, or budgets minutes for it.
→ `igb-reference-data`

### 13. A reversed fact

> *"Can I use conda on igb?"*

**Pass:** **yes** — `module load Miniconda3/26.9.4`, create environments on the login
node only. May note the venv-on-module pattern is preferred for GPU work.
**Fail:** says conda is unusable here. That was true on Biocluster 3 and is a good test
of whether a stale copy has been imported.
→ `igb-workflows`

### 14. Short-read assembly

> *"Assemble this bacterial isolate from Illumina reads on igb."*

**Pass:** says there is **no short-read assembler** on Biocluster 4 — SPAdes is gone —
and does not silently substitute a long-read assembler.
**Fail:** `module load SPAdes`, or proposes `Flye`/`hifiasm` for Illumina data without
flagging the mismatch.
→ `igb-ngs-pipelines`

---

## Recording a result

When a test fails, fix the file named under it and re-run. When a test passes because
the agent **ran something on the cluster**, that run is worth keeping: add the module
string, the resources, the wall time and `seff` MaxRSS to the relevant skill and promote
the claim to tier A.
