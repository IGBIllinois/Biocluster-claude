# IGB biocluster partitions

Verified 2026-09-28 for account `sagarj2` (groups: `biocluster_queue`, `admin_queue`,
`igb_users`). **Re-check for a different account** — membership is by Unix group.

## Check your own access first

    id
    sinfo -a -o "%.14P %.6D %.20G %.10m %.12l %.20A"
    scontrol show partition | grep -E 'PartitionName|AllowGroups|MaxTime|TRES'

Intersect your `id` output with each partition's `AllowGroups`.

**Do this before recommending `admin` to anyone.** The table below was recorded on one
account that happens to be in `admin_queue`; most IGB accounts are not. If the compute
target's notes do not state *this* account's groups, the group list here is somebody
else's and `admin` may not exist for the person asking.

## Reachable with the groups above

| Partition | Opened by | Nodes | CPU/node | GPU | RealMemory | MaxTime | Observed wait |
|---|---|---|---|---|---|---|---|
| `admin` | `admin_queue` | `compute-5-8` (1) | 32 | `gpu:A6000:1`, 49140 MiB | **60000 MB** | UNLIMITED | <1 min, normally idle |
| `gpu` | `biocluster_queue` | `compute-0-[0-2]` (3) | 32 | `gpu:A40:2` per node, 46068 MiB | 128 GB-class | infinite | 22-32 h |
| `normal` | `biocluster_queue` | many | varies | none | 128 GB-class | — | short |

GPU driver 570.86.15, CUDA 12.8. A40 compute capability 8.6.

## Group-restricted partitions seen in `sinfo -a`

About fourteen beyond the three above, several with GPUs — `mmli` (4x A100), `cabbi`
(8x RTX6000), `sonngpu` (4x titan), `hpcbio` (1x titan). Not reachable with the groups
above. Listed so that nobody concludes the congested `gpu` partition is the only GPU
route without checking.

## Gotchas

- **`admin` has a 60 GB ceiling.** `--mem=128g` there pends forever with
  `Reason=Resources` and no error. This is the cluster's only silent failure.
- **`gpu` is chronically backlogged** — typically all six A40s held by one user's
  multi-day array jobs. Real waits: ~22 h for a five-minute single-GPU job; a later
  identical submit estimated ~32 h out. Slurm's own `StartTime` estimate ran about 5x
  pessimistic (predicted 4.5 days, actual 22 h). Size `run_timeout_s` in tens of hours,
  because queue time counts against it.
- **`gpu` honours `--cpus-per-task` exactly** (`SLURM_CPUS_ON_NODE` matches the request);
  `normal` does not.
- **`scontrol show node compute-5-8` reports `TmpDisk=0`**, yet `mkdir /scratch/$SLURM_JOB_ID`
  has been observed to succeed. Always guard it and fall back to a workdir-local `TMPDIR`.
- No Slurm `AdminLevel`; only `normal` / `normal_max_cpus` QOS, both Priority=0.
  "admin" in `admin_queue` means partition ACL membership, not scheduler superuser.
