---
name: igb-gpu-ml
description: "GPU and deep-learning work on the IGB biocluster - which CUDA module pairs with which PyTorch, Tensorflow or JAX build, choosing between the idle RTX A6000 on the admin partition and the backlogged A40s on gpu, requesting --gres correctly, and checking the GPU is actually visible from inside the job. Load this before submitting any job that needs a GPU, trains or fine-tunes a model, or imports torch, tensorflow, jax, transformers or detectron2 on IGB."
---

# GPU and deep learning on the IGB biocluster

## Pick the GPU first — the counter-intuitive part

| Need | Partition | Hardware | Memory ceiling | Queue |
|---|---|---|---|---|
| GPU, ≤60 GB RAM | `admin` | 1x RTX A6000, 48 GB VRAM | **60 GB** | starts in <1 min |
| GPU, >60 GB RAM | `gpu` | 2x A40 per node, 46 GB VRAM, 3 nodes | 250 GB | **22-32 h observed** |

**The idle GPU partition has the smallest host memory on the cluster.** A6000 and A40
are both compute capability 8.6 / driver 570.86.15 / CUDA 12.8, so for most work `admin`
is strictly better — it is the same generation of card and it starts immediately. Go to
`gpu` only when you need >60 GB host RAM or two GPUs.

Never request a whole GPU node: `--gres=gpu:1`. Three GPU nodes serve the institute.

    #SBATCH -p admin
    #SBATCH -n 8
    #SBATCH --mem=32g
    #SBATCH --gres=gpu:1

`gpu` honours `--cpus-per-task` exactly; `normal` does not.

## Version pairing — 13 CUDA x 15 PyTorch

**Tier A — every row below was run on an A6000 on `admin`, 2026-10-13.** The two
frameworks need *opposite* treatment, which is the single most expensive thing to get
wrong here.

| Module | Reports | GPU usable? | Notes |
|---|---|---|---|
| `PyTorch/2.7.0-IGB-gcc-8.2.0-Python-3.10.1` | torch 2.7.0+cu126, cuDNN 9.5.1 | **yes** | 4000² matmul in **0.38 s**. Use this one |
| `PyTorch/1.13.1-IGB-gcc-8.2.0-Python-3.10.1` | torch 1.13.1+cu117, cuDNN 8.9.2 | **yes** | same matmul **2.68 s** — 7x slower than 2.7.0 |
| `PyTorch/1.12.1-IGB-gcc-8.2.0-Python-3.10.1` | torch 1.12.1+cu102, cuDNN 7.6.5 | **NO — and it lies** | see below |
| `Tensorflow/2.9.1-IGB-gcc-8.2.0-Python-3.7.2` alone | tf 2.9.1 | **no** | `GPUs visible: 0`, silently runs on CPU |
| `Tensorflow/2.9.1` **+ `CUDA/11.2.2` + `cuDNN/8.1.1.33-CUDA-11.2.2`** | tf 2.9.1 | **yes** | `GPUs visible: 1`, matmul on GPU. Either load order works |
| `Tensorflow/2.8.2` + the same two | tf 2.8.2 | **yes** | same |

### PyTorch: do NOT load a CUDA module

The `PyTorch` modules bundle their own CUDA runtime. 2.7.0 and 1.13.1 both found the
A6000 with nothing else loaded. Adding a `CUDA/x` module on top is how you create a
mismatch.

### TensorFlow: you MUST load CUDA and cuDNN

The opposite. On its own, `Tensorflow/2.9.1` prints `Skipping registering GPU devices`
and reports **zero** GPUs — then trains on CPU without ever failing, so the job
"succeeds" and is simply ~100x too slow. Pair it explicitly:

    module purge
    module load Tensorflow/2.9.1-IGB-gcc-8.2.0-Python-3.7.2
    module load CUDA/11.2.2 cuDNN/8.1.1.33-CUDA-11.2.2

### `PyTorch/1.12.1` passes `is_available()` and then crashes

This is the trap worth remembering. The A6000 is compute capability **sm_86**; the
1.12.1 build (`+cu102`) was compiled for `sm_37 sm_50 sm_60 sm_70` only. So:

    torch.cuda.is_available()   -> True          # the usual check PASSES
    a @ b  on cuda              -> RuntimeError: CUDA error: no kernel image is
                                   available for execution on the device

`is_available()` only reports that a driver and device exist, **not that this build has
kernels for this card**. Any PyTorch older than 1.13 on IGB is suspect on the A6000/A40.

### Still true from the inventory

- **Stay inside one toolchain generation.** Anything `-IGB-gcc-4.9.4` cannot share a job
  with `-IGB-gcc-8.2.0`. The old PyTorch builds (0.3–1.6) are all gcc-4.9.4 and
  Python 3.6/2.7 — legacy, and they will hit the sm_86 wall too.
- 13 `CUDA` modules (newest `12.8.0`), 15 `PyTorch`, 5 `Tensorflow`, 11 `cuDNN`.
- The driver is CUDA 12.8, so `CUDA/12.x` is safe; older *runtimes* work under a newer
  driver, but an older *build target* (sm level) does not.
- `PyCUDA`, `numba`, `jax-unirep`, `transformers`, `detectron2`, `pytorch-geometric`,
  `xgboost`, `h2o` are present — tier C, not run here.

## Always prove the GPU is visible before the real work

**`nvidia-smi` is not on `PATH` on the compute nodes** (verified on compute-5-8,
2026-10-13) — `nvidia-smi || exit 1` as a guard will abort every GPU job you submit.
Do not use it.

**And `is_available()` is not sufficient**, per the 1.12.1 case above. The only honest
preflight is a real tensor operation. Put this at the top of the job, not after an hour
of data loading:

    python3 -c "
    import torch
    assert torch.cuda.is_available(), 'no CUDA device'
    a = torch.randn(64, 64, device='cuda')
    (a @ a).sum().item()          # fails here if the build lacks sm_86 kernels
    print('GPU OK:', torch.cuda.get_device_name(0), torch.version.cuda)
    "

For TensorFlow the equivalent is `len(tf.config.list_physical_devices('GPU')) > 0`,
which returns 0 unless you loaded CUDA and cuDNN alongside it.

Observed on `admin`: `NVIDIA RTX A6000`, 49140 MiB. On `gpu`: `NVIDIA A40`, 46068 MiB.

## No internet on compute nodes

`pip install` and any model-weight download **fail inside a job**. Pre-stage weights
from the login node, or use a mirrored module (`dorado-db` for Dorado models — see
`igb-reference-data`). Set `HF_HOME`/`TORCH_HOME` to a path you populated beforehand.

## Sizing

`seff <jobid>` after the first run, then size the next one from `MaxRSS`. Deep-learning
jobs on this cluster have run at single-digit CPU efficiency because the GPU is the
bottleneck — 8 CPUs is usually plenty, and asking for more only lengthens the queue.

## What is still unverified here

Tier A covers the three PyTorch builds and three TensorFlow builds listed above, run on
the A6000 on `admin`. **Not** verified, and listed only as present: `PyCUDA`, `numba`,
`jax-unirep`, `transformers`, `detectron2`, `pytorch-geometric`, `xgboost`, `h2o`, every
`PyTorch` build on the `-IGB-gcc-4.9.4` toolchain, and **anything at all on the `gpu`
partition's A40s** — all GPU measurements here come from the A6000.

The A40 is the same compute capability (8.6) as the A6000, so the sm_86 conclusions
should carry over, but that is an inference and has not been run.

**If you run any of these, say so.** Tell the agent in your reply, or open a PR on
`IGBIllinois/Biocluster-claude` moving the row to tier A with the module string you
loaded, whether the GPU was visible, and the runtime. A single confirmed row saves the
next person a queue wait.
