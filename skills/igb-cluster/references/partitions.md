# Partitions — IGB Biocluster 4

Measured on **2026-10-31** from `biologin-0.igb.illinois.edu` with `sinfo -a`,
`scontrol show partition` and `scontrol show node`, on an account in
`biocluster_queue`. The two partitions documented here are the ones that group opens;
nothing in this file depends on any other group membership.

This file is the **only** place in the repository that carries partition hardware
numbers. Software skills state *which* partition to use and why; they do not restate
core counts or memory ceilings, so that there is one thing to update when the hardware
changes.

## How access actually works

Membership is by **Unix group**, checked against the partition's `AllowGroups`. Run
`id` and compare:

| Unix group | Opens |
|---|---|
| `biocluster_queue` | `normal`, `gpu` |

`biocluster_queue` is the group an ordinary IGB account is in, and those two partitions
are what it gets. There is no Slurm `AdminLevel` on this cluster and the only QOS is
`Priority=0`, so there is no priority-bump route and none is needed.

**`sinfo -a` lists partitions you cannot use.** The reliable access test is:

    scontrol show partition <name>

which returns **empty** for a partition the account has no claim on, while `sinfo -a`
still shows it, sometimes with idle nodes. **Listing is not access.** Of the fifteen
partitions `sinfo -a` reports, an ordinary account can submit to two.

## The two general-access partitions

| | `normal` | `gpu` |
|---|---|---|
| AllowGroups | `biocluster_queue` | `biocluster_queue` |
| Configured nodes | `compute-1-[0-6]` (7) | `compute-0-[0-2]` (3) |
| Total CPUs | 896 | 96 |
| CPU per node | 128 (AMD EPYC 7543) | 32 |
| RealMemory per node | 2,000,000 MB (~2 TB) | 250,000 MB (~250 GB) |
| GRES | none | `gpu:A40:2` |
| MaxTime | UNLIMITED | UNLIMITED |
| MaxMemPerNode | UNLIMITED | UNLIMITED |
| Up on 2026-10-31 | **2 of 7** (`compute-1-0`, `compute-1-2`) | **1 of 3** (`compute-0-0`) |

**Units:** `RealMemory` above is in **MB as Slurm reports it**, and the `g` suffix in
`--mem=16g` is **GiB**. GPU VRAM is quoted in decimal GB (47.7 GB = 44.4 GiB, which is
what `torch` prints if you divide by 2**30). Mixing the two is an easy way to
mis-size a job by ~7%.

Because `MaxMemPerNode=UNLIMITED` and `DefaultTime=NONE`, the binding constraint is
always the node's `RealMemory`. A `--mem` above the per-node ceiling does **not** error:
the job pends forever with `Reason=Resources`.

**Only a fraction of the configured nodes are usually up.** Size the request against
what `sinfo` reports as idle, not against the configured total.

### GPU hardware, measured

    NVIDIA A40 | sm_86 | 47.7 GB VRAM
    torch 2.14.1+cu130, cuDNN 92400
    4000x4000 matmul: 0.255 s

`nvidia-smi` **is** on `PATH` on the GPU compute nodes (`/usr/bin/nvidia-smi`). On
Biocluster 3 it was not, and skills carried a preflight guard that would have aborted
every GPU job; that guard has been removed.

### Queue depth

Do not quote a wait time from this file. Biocluster 3 showed 22-32 h GPU waits; across
a full day of Biocluster 4 testing the GPU queue was **empty**, with jobs starting in
under 20 s. The queue is the thing most likely to have changed since this was written:

    squeue -p gpu -t PENDING -o "%.12i %.10u %.20S %R"

## The other fourteen partitions — do not use them

`sinfo -a` reports **fifteen** partitions (re-counted 2026-11-09; a `test` partition present on 2026-10-31 has since been removed). Thirteen belong to specific labs, projects,
teaching allocations or IGB staff, and an ordinary `biocluster_queue` account cannot
submit to any of them.

**They are the single most likely thing to recommend by mistake**, because `sinfo` shows
their hardware to everyone and several of them sit idle advertising GPUs and
large-memory nodes that look better than anything in `normal` or `gpu`. An idle node you
cannot submit to is not capacity.

**Only ever put `-p normal` or `-p gpu` in a job script.** If something makes another
partition look necessary, that is a sign the job needs resizing or a conversation with
IGB — not a different `-p`.

Before naming any partition not in the table above, confirm it with:

    scontrol show partition <name>

Empty output means no access. Do not fall back to `sinfo`, which lists everything
regardless, and do not infer access from a partition appearing idle.

## Choosing

| Need | Partition | Flags |
|---|---|---|
| a GPU | `gpu` | `--gres=gpu:1`, `--mem` <= 250000 |
| CPU-only, any size | `normal` | `--mem` <= 2000000 |

Never request a whole GPU node — `--gres=gpu:1`. Three GPU nodes serve the institute.

## Re-measuring this file

    id
    sinfo -a -o "%.14P %.6D %.20G %.10m %.12l %.20A"
    scontrol show partition <name> | grep -E 'AllowGroups|TotalNodes|TotalCPUs|MaxTime|Nodes='
    scontrol show node compute-0-0 | grep -E 'CPUTot|RealMemory|Gres|State'

One call, not a session of probing. Append anything new to `compute_details` for
`ssh:igb` as well as here.
