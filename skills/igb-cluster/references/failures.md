# Failure modes on the IGB biocluster

Each row cost a session to find. The order is roughly the order a naive run hits them.

| # | Symptom | Layer | Diagnosis -> fix |
|---|---|---|---|
| 1 | Need a sequence, sandbox has no network | local | Resolve on the cluster from `$BIODB/pdb_seqres_2022_09_28.fasta`. Never type a sequence from memory |
| 2 | Job run locally, takes forever / no GPU | local | The laptop GPU is not reachable from the sandbox. CUDA work goes to the cluster |
| 3 | Job PENDING for a day | partition | Submitted to `gpu`. Use `admin` (idle A6000) unless the A6000 is unsuitable |
| 4 | **PENDING forever, `Reason=Resources`, no error** | resources | `--mem` over the node ceiling (60 GB on `admin`). `scontrol show job <id> \| grep -E 'Reason\|TRES'`. **The only silent failure here** |
| 5 | Job dies early in a temp-file step | node | Unguarded `mkdir /scratch/$SLURM_JOB_ID`; nodes report `TmpDisk=0`. Guard it, fall back to `$PWD/tmp` |
| 6 | `submit_job` raised, but a job is queued | transport | A dead connection can follow a successful `sbatch`. **Check `sacct` for `operon-*` before resubmitting.** The uuid is in the error text; the job is unrecoverable client-side (`ledger()` stays empty, `attach_job` raises NotFound) so harvest by hand with `c.download` from `<scratch>/.claude-science/jobs/<uuid>/` once `sacct` shows COMPLETED |
| 7 | `PermissionError` reading harvested outputs | local | `hpc/<job_id>/` is outside the sandbox: the python/bash kernels cannot read or list it, though `read_file` and `save_artifacts` can. `save_artifacts` first, then read back via `host.artifact_path(version_id)` |
| 8 | Job COMPLETED, no log to read | script | `slurm-<jobid>.out` is never harvested. `tee` into a named `run.log` and name it in `outputs` |
| 9 | Outputs missing after a successful job | script | Tool wrote to an absolute path. Only files under the job workdir are transferred back |
| 9b | A command after `module load` runs against the **system** python (3.6.8), or fails with `libpython3.10.so.1.0: cannot open shared object file` | shell | `module load` was **piped** (`\| head`, `\| tee`) or command-substituted, so it ran in a subshell and the load was discarded. `module list` will say "No modules loaded". Run `module load` bare on its own line |
| 10 | `sc.tl.leiden` raises on the scanpy module | env | Module has no leidenalg/igraph. `module load cs/scanpy-leiden` |
| 11 | matplotlib warns / fails on a read-only home | env | `export MPLCONFIGDIR="$PWD/.mplcache"` |
| 12 | Job workdir holds only `cmd.sh`, `job.sh`, `_staged` | transport | Normal. `ssh://` input symlinks are created at job **start**, not at submit. Not a staging failure; not a reason to resubmit |
| 13 | Client-side timeout stopped the job | transport | It did not. The Slurm job stays queued, runs, and completes, leaving outputs plus `_status.json` in `<scratch>/.claude-science/jobs/<uuid>/`. Wait for COMPLETED and `c.download`, do not resubmit |
| 14 | A job you submitted has vanished | user | The user cancels jobs under their own uid without saying so. Re-check `squeue`/`sacct` before reasoning about it |
