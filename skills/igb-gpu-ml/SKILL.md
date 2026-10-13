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

This is where most time is lost. **Tier B** — read from `module avail`, not run here.

| Framework | Versions present | Newest |
|---|---|---|
| `CUDA` | 13 | `12.8.0` (also 12.5.1, 11.8.0, 11.3.0, 11.2.2, 11.1.0, 11.0.3, 10.x, 9.x, 8.x) |
| `PyTorch` | 15 | `2.7.0-IGB-gcc-8.2.0-Python-3.10.1` |
| `Tensorflow` | 5 | `2.9.1-IGB-gcc-8.2.0-Python-3.7.2` |
| `cuDNN`, `PyCUDA`, `numba`, `jax-unirep`, `transformers`, `detectron2`, `pytorch-geometric`, `xgboost`, `h2o` | — | present, tier C |

Rules that follow from the inventory:

1. **Load the framework module and let it pull its own CUDA.** The IGB builds encode the
   toolchain and Python version in the name; loading a second CUDA by hand is how you get
   a mismatch.
2. **Stay inside one toolchain generation.** `PyTorch/2.7.0-IGB-gcc-8.2.0-Python-3.10.1`
   and anything `-IGB-gcc-4.9.4` cannot share a job. The older PyTorch builds (0.3-1.6)
   are all gcc-4.9.4 and Python 3.6/2.7 — treat them as legacy.
3. **`Tensorflow-GPU` is a separate module** from `Tensorflow`. Check which you loaded.
4. The driver is CUDA 12.8, so a `CUDA/12.x` build is safe; older builds generally run
   under a newer driver, not the reverse.

## Always prove the GPU is visible before the real work

Put this at the top of the job, not after an hour of data loading:

    nvidia-smi || { echo "no GPU visible"; exit 1; }
    python -c "import torch; assert torch.cuda.is_available(); \
      print(torch.cuda.get_device_name(0), torch.version.cuda)"

Observed on `admin`: `NVIDIA RTX A6000`, 49140 MiB. On `gpu`: `NVIDIA A40`, 46068 MiB.

## No internet on compute nodes

`pip install` and any model-weight download **fail inside a job**. Pre-stage weights
from the login node, or use a mirrored module (`dorado-db` for Dorado models — see
`igb-reference-data`). Set `HF_HOME`/`TORCH_HOME` to a path you populated beforehand.

## Sizing

`seff <jobid>` after the first run, then size the next one from `MaxRSS`. Deep-learning
jobs on this cluster have run at single-digit CPU efficiency because the GPU is the
bottleneck — 8 CPUs is usually plenty, and asking for more only lengthens the queue.
