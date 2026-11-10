# Failure modes on IGB Biocluster 4

Each row cost a session to find. The order is roughly the order a naive run hits them.

Rows marked **[BC4]** were found or re-confirmed on Biocluster 4 after the October 2026
migration. Rows without a marker are transport- or harness-level and are independent of
which cluster generation is behind the target.

## Resources and scheduling

| # | Symptom | Diagnosis -> fix |
|---|---|---|
| 1 | **PENDING forever, `Reason=Resources`, no error** | `--mem` over the node's RealMemory (2,000,000 MB on `normal`, 250,000 MB on `gpu`). `scontrol show job <id> \| grep -E 'Reason\|TRES'`. **The only silent failure mode on this cluster** |
| 2 | Job PENDING for a long time | Queue depth varies by orders of magnitude. Biocluster 3 showed 22-32 h GPU waits; Biocluster 4 has been observed starting GPU jobs in under 20 s. **Measure, do not quote**: `squeue -p gpu -t PENDING`. Size `run_timeout_s` against what you measure, because queue time counts against it |
| 3 | Job got 2 CPUs when the node has 128 | A job that does not ask gets a minimal default slice. Always state `-n` and `--mem` explicitly |
| 4 | **[BC4]** Job dies in a temp-file step, or a tool scribbles into `$HOME` | **Inside a job, Slurm provides a node-local `/scratch/$SLURM_JOB_ID` and sets `TMPDIR` to it** (measured on `compute-0-0`, job 17991). **On the login node there is no `/scratch` and `TMPDIR` is unset** — which is what makes this confusing, and what an earlier version of this table got wrong. Write `: "${TMPDIR:=$PWD/tmp}"; mkdir -p "$TMPDIR"; export TMPDIR` so the job uses Slurm's scratch when present and a workdir fallback when not. Note node-local scratch is not shared between nodes and is cleaned at job end — copy anything you need into the workdir before exiting |

## Modules and environments

| # | Symptom | Diagnosis -> fix |
|---|---|---|
| 5 | A command after `module load` runs against the **system** python, or fails with `libpython...so: cannot open shared object file` | `module load` was **piped** (`\| head`, `\| tee`) or command-substituted, so it ran in a subshell and the load was discarded. `module list` will say "No modules loaded". Run `module load` bare on its own line |
| 6 | **[BC4]** `module load` of a tool that worked on Biocluster 3 fails with "Unable to locate a modulefile" | The stack shrank from 927 module names to **173**. `snakemake`, `scanpy`, `rosetta`/`PyRosetta`, `hhsuite`, `pymol`, `rdkit`, `ViennaRNA`, `SPAdes`, `Trinity`, `salmon`, `RepeatMasker`, `cromwell`, `toil`, standalone `foldseek`, `transformers`, `jax` and `Anaconda3` are all **gone**. Check `module avail` before promising a tool; the fallback is a venv on the login node or a container |
| 7 | **[BC4]** A Biocluster 3 module name with `-IGB-gcc-8.2.0` is not found | Biocluster 4 has a single toolchain generation, `IGB-gcc-15.2.0`. Strip the old suffix and re-resolve the version from `module avail` |
| 8 | **[BC4]** `pip install` or a download fails inside a job | Compute nodes have **no internet**. Confirmed on Biocluster 4: a `pooch` dataset fetch failed inside a job and succeeded on `biologin-0`. Stage on the login node, load in the job |
| 9 | matplotlib warns or fails on a read-only home | `export MPLCONFIGDIR="$PWD/.mplcache"` |
| 10 | Looking for a pre-built conda env, or told conda does not work here | **[BC4]** That was a Biocluster 3 finding and is now false. `module load Miniconda3/26.9.4` puts `conda` on `PATH`. The pattern actually exercised here is still a venv layered on an IGB module |

## GPU and deep learning

| # | Symptom | Diagnosis -> fix |
|---|---|---|
| 11 | **[BC4]** TensorFlow trains slowly and reports `GPUs visible: 0` | **TensorFlow 2.21.0 cannot see the A40 on Biocluster 4** — measured with the module loaded alone *and* with `CUDA/13.1.0` + `cuDNN/9.17.1.4-CUDA-13.1.0` added. Biocluster 4 ships only CUDA 13.x and TF 2.21 is built against CUDA 12, so there is no module pairing that fixes it. **Use PyTorch for GPU work**; if TensorFlow is required, raise it with IGB rather than burning GPU hours on a CPU fallback |
| 12 | **[BC4]** `torch.load` of a downloaded checkpoint raises `UnpicklingError` / `Weights only load failed` | PyTorch >= 2.6 defaults `torch.load` to `weights_only=True`. For ESM-2 checkpoints: `torch.serialization.add_safe_globals([argparse.Namespace])` before loading. Only do this for a checkpoint you trust the provenance of |
| 13 | **[BC4]** `AssertionError: Device compute capability 8.9 or higher required for FP8 execution` | The A40 is **sm_86** and has no FP8. Evo 2 enables `te.fp8_autocast` unconditionally — set `use_fp8_input_projections: false` in the model's config YAML. Note `evo2_7b` resolves to `evo2-7b-1m.yml`, not the `8k` file. **The Evo 2 40B, 20B and 1B models cannot run on the A40 at all**; only the 7B models work, in bfloat16 |
| 14 | **[BC4]** Triton fails to find `libcuda.so` inside an Apptainer container | Pass `--env TRITON_LIBCUDA_PATH=/.singularity.d/libs` to `apptainer exec` |
| 15 | **[BC4]** `import cv2` ModuleNotFoundError from a library you never told to use OpenCV | Segment Anything imports cv2 lazily when `min_mask_region_area > 0`. Set it to **0**, or install opencv into the venv |
| 16 | A model repository returns **401** on `config.json` | The repo is gated and needs manual approval plus a token — e.g. every DINOv3 checkpoint. Do not silently substitute a different model: ask the user, and label the substitution in every output if they approve one |
| 17 | `nvidia-smi: command not found` in a preflight guard | **[BC4]** That was a Biocluster 3 defect. `nvidia-smi` **is** on `PATH` at `/usr/bin/nvidia-smi` on Biocluster 4 GPU nodes. Any `nvidia-smi \|\| exit 1` guard carried over from the old skills should be deleted, not fixed |

## Reference data

| # | Symptom | Diagnosis -> fix |
|---|---|---|
| 18 | A database module loads but the tool reports the path does not exist | **Four of the 29 database modules point at `/home/mirrors`, which does not exist** — the real mount is `/home/mirror`, a symlink into `/private_stores/mirror`. Affected: `chocophlan`, `clusterblast`, `gatkbundle`, `silva`. Substitute the corrected path from the `igb-reference-data` skill |
| 19 | A tool rejects the module root as a database directory | **11 of the 29 need a subdirectory**, e.g. `BUSCO-db` -> `lineages`, `checkv-db` -> `checkv-db-v1.5`, `ncbi-blastdb` -> `blastdb_v5`. Full map in `igb-reference-data`. Always `ls` the `EBROOT` variable before passing it on |
| 20 | Guessing the environment variable for a database module | It is `EBROOT` + the module name uppercased with every `-` replaced by `MIN`. Verified against all 29 with zero exceptions on 2026-10-31 |
| 21 | A reference-data validation job is killed partway | Validation over the mirrors is slow — `gtdbtk check_install` took **1 h 07 m** and `skani/` alone holds 143,617 files. Budget hours, and treat it as a once-per-release check, never a per-job preflight |

## Transport and harness

| # | Symptom | Diagnosis -> fix |
|---|---|---|
| 22 | **`submit_job` fails with `ssh: connect to host ... port 22: Connection timed out`, while `call_command` works** | Recurring and **not** a DNS problem. Treat it as a flake on a route that demonstrably works — and **check whether the job ran**, see the next row. The practical workaround adopted here is to stage the script with `call_command` and `sbatch` it directly, which also lets you pass `-p` and `--gres` that `submit_job` cannot express |
| 23 | `submit_job` reported a transport failure, so you assume nothing ran | **Verified repeatedly: the Slurm job had dispatched and was RUNNING.** Only the client-side marker write failed, which leaves the job untracked — `ledger()` stays empty, no `compute_done` ever arrives, and `run_timeout_s` never fires. **Always** `squeue -u $USER` and `sacct -u $USER -S <date> -X` after a failed submit; the uuid prefix in the error matches the Slurm job name `operon-<first 8 chars>` |
| 24 | **Never resubmit** after a transport-level submit failure | A dead connection can follow a successful `sbatch`. Resubmitting forfeits a queue position and double-books the GPU |
| 25 | **A job script written on Windows fails with `ambiguous redirect`, or writes a file whose name ends in a carriage return** | CRLF line endings. `2>&1` becomes `1\r`, and `> out.log` creates `out.log\r`. Cost one full verification run whose real output sat in a file named `check_install.log\r`. **Write every job script with LF endings** (`open(path, "w", newline="\n")`); the repo ships a `.gitattributes` that enforces it |
| 26 | **A job shows `State=FAILED, ExitCode=124:0` with no error in its own log** | 124 is a `timeout` kill, not a tool failure. The generated `job.sh` wraps the command as `timeout <run_timeout_s + 300>`. Compare `job.sh` against the elapsed time in `sacct` before blaming the tool |
| 26b | **The SSH leg wedges entirely for minutes to hours, while the cluster itself is fine** | Observed repeatedly on 2026-11-01 and 2026-11-09: consecutive `call_command` calls — *including ones with `run_timeout_s=90`* — block past the 600 s cell ceiling and return nothing, while jobs submitted minutes earlier keep running normally and `sbatch`/`sacct` work again later. The hang is at **connection establishment**, so a short `run_timeout_s` does not bound it. Do not interpret it as a cluster outage, do not resubmit the job, and do not keep retrying on a short loop. Cancel the call, do other work, and read the results later — anything already submitted is unaffected. Budget for this when planning: a verification sweep that needs several round-trips may not complete in one sitting |
| 27 | `call_command` dies at 600 s even though you asked for more | **600 s is a hard ceiling** — `run_timeout_s=900` still failed at 600. Calls of 146 s, 200 s, 586 s and 656 s have completed, so it is not a fixed 60 s cap. Keep probes short and put long work in a job |
| 28 | A slow filesystem walk is killed | `find` and `du` over `/private_stores/mirror` or `/home` die. Prefer `ls -1U <dir> \| head` — unsorted plus `head` avoids reading a 143k-file directory. This cut a 29-module database sweep from 656 s to 105 s |
| 29 | **Streamed output is silently corrupted** | `call_command` stdout truncates near **64 KB** and inserts an ellipsis, which destroys base64 mid-stream. Keep any streamed payload under ~45 KB and chunk anything larger |
| 30 | `scp`/`sftp` to this host times out while `call_command` works | Observed repeatedly on `biologin-0`. Stream files back base64 through the command channel instead, respecting the 45 KB chunk limit |
| 31 | `PermissionError` reading harvested outputs | `hpc/<job_id>/` is outside the sandbox: the python/bash kernels cannot read it, though `read_file` and `save_artifacts` can. `save_artifacts` first, then read back via `host.artifact_path(version_id)` |
| 32 | Job COMPLETED, no log to read | `slurm-<jobid>.out` is never harvested. `tee` into a named `run.log` and name it in `outputs` |
| 33 | Outputs missing after a successful job | The tool wrote to an absolute path. Only files under the job workdir are transferred back |
| 34 | Job workdir holds only `cmd.sh`, `job.sh`, `_staged` | Normal. `ssh://` input symlinks are created at job **start**, not at submit. Not a staging failure |
| 35 | A job you submitted has vanished | The user cancels jobs under their own uid without saying so. Re-check `squeue`/`sacct` before reasoning about it |
| 36 | `cd "$(dirname "$0")"` lands somewhere unwritable | In a Slurm job that resolves to `/var/spool/slurmd/job<id>/`, which is not writable. Use `$SLURM_SUBMIT_DIR` or an explicit path |
