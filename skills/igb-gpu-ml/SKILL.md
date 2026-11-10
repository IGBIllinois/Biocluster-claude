---
name: igb-gpu-ml
description: "GPU and deep-learning work on IGB Biocluster 4 — which framework modules actually see the GPU, how to layer a venv on an IGB PyTorch module, how to run a model from an Apptainer container, and the measured traps (TensorFlow cannot see the A40, FP8 is unavailable on this card, torch.load defaults changed). Covers installing and running foundation models such as ESM-2, Segment Anything, DINOv2 and Evo 2. Load before writing any job that requests --gres=gpu."
---

# GPU and deep learning on Biocluster 4

Load `igb-cluster` first — it owns the partition table, the memory ceilings and the
submission rules. This skill covers only what is specific to GPU work.

Use `-p gpu --gres=gpu:1`. **Never request a whole GPU node.**

## The card

    NVIDIA A40 | compute capability sm_86 | 47.7 GB VRAM

Two per node. The VRAM figure and the compute capability are stated here because they
decide whether a model fits and whether a kernel will build; node CPU and RAM ceilings
live in the hub's partition table, not here.

`nvidia-smi` is on `PATH` at `/usr/bin/nvidia-smi`. Earlier versions of these skills
carried an `nvidia-smi || exit 1` preflight because it was *not* on PATH on Biocluster 3
— that guard would have aborted every GPU job and has been removed. Do not reintroduce it.

**sm_86 has no FP8.** Anything that assumes an H100/L40S and enables FP8 unconditionally
will fail with `Device compute capability 8.9 or higher required for FP8 execution`.
See the Evo 2 section for the fix.

## Which framework sees the GPU — measured, 2026-10-31 (tier A)

| Module | Loaded how | Result |
|---|---|---|
| `PyTorch/2.14.1-IGB-gcc-15.2.0-Python-3.14.0` | alone | **works** — `torch 2.14.1+cu130`, cuDNN 92400, `is_available: True`, A40 detected |
| `TensorFlow/2.21.0` | alone | **`GPUs visible: 0`** |
| `TensorFlow/2.21.0` | + `CUDA/13.1.0` + `cuDNN/9.17.1.4-CUDA-13.1.0` | **`GPUs visible: 0`** |

**TensorFlow has no working GPU path on Biocluster 4.** On Biocluster 3 the fix was to
add the CUDA and cuDNN modules; here that does not help, because the cluster ships only
**CUDA 13.x** and TensorFlow 2.21 is built against CUDA 12. There is no module pairing
that closes the gap.

Consequences, and please state them to the user rather than quietly absorbing them:

- **Use PyTorch for GPU work.** It is the only framework verified to reach the card.
- A TensorFlow job will run to completion on the CPU, slowly, with no error — it is a
  silent performance failure, not a crash.
- If a user needs TensorFlow on a GPU here, that is a request for IGB, not something to
  work around by burning GPU hours.

Benchmark for scale: a 4000x4000 float32 matmul takes **0.255 s** on the A40 under
torch 2.14.1.

## Building a GPU environment

Compute nodes have no internet. Build on the login node, load in the job.

The pattern that works, and the one all four model installs below used, is a **venv
layered on the IGB PyTorch module** — it inherits the module's CUDA-matched torch
instead of pulling a second multi-gigabyte copy from PyPI:

    module load PyTorch/2.14.1-IGB-gcc-15.2.0-Python-3.14.0
    python -m venv --system-site-packages ~/models/venv
    source ~/models/venv/bin/activate
    pip install <packages>          # login node only

`conda` also works now (`module load Miniconda3/26.9.4`), reversing the Biocluster 3
finding, but the venv route is the one with measured results behind it.

**Two installation traps, both paid for:**

1. **`pip install` of anything torch-adjacent will try to replace torch.** Use
   `--no-deps` and let the module supply it. `torchvision 0.29.2+cu132` installed with
   `--no-deps` works correctly against the module's `torch 2.14.1+cu130` —
   `batched_nms` was verified — despite the CUDA minor-version mismatch in the wheel tag.
2. **The Python here is 3.14.** Some wheels have no 3.14 build. `tokenizers` turned out
   to be fine (it ships a `cp310-abi3` wheel that 3.14 can load), so check for an abi3
   wheel before concluding a package is unavailable.

## Running a model from a container

For anything whose dependency stack cannot be satisfied against Python 3.14, pull an
NGC container on the login node and build the venv with the **container's** Python:

    apptainer pull docker://nvcr.io/nvidia/pytorch:25.12-py3     # 8.1 GB SIF

That image gives Python 3.12.3, `torch 2.10.0a0+...nv25.12` on CUDA 13.1,
Transformer Engine 2.10.0 and flash-attn 2.7.4. Apptainer needs no module —
`/usr/bin/apptainer` 1.5.3 is on every node, with a `singularity` alias.

**Triton inside a container cannot find `libcuda.so`.** Pass:

    apptainer exec --nv --env TRITON_LIBCUDA_PATH=/.singularity.d/libs <sif> ...

## `torch.load` and checkpoint security

PyTorch >= 2.6 defaults `torch.load` to `weights_only=True`. Checkpoints that pickle
arbitrary objects now raise instead of loading. For ESM-2:

    import argparse, torch
    torch.serialization.add_safe_globals([argparse.Namespace])

Only do this for a checkpoint whose provenance you trust. Do not reach for
`weights_only=False` as a blanket fix.

## Foundation models installed here (tier A)

All four were installed under `~/models` on 2026-10-31 and run on the `gpu` partition.
Weights are **not** shared — a new user repeats the download on the login node.

| Model | How it is installed | Weights |
|---|---|---|
| **ESM-2 650M** | `pip install fair-esm` into the module venv | `~/models/esm2`, 2.6 GB |
| **Segment Anything (ViT-H)** | `pip install --no-deps segment-anything torchvision` | `~/models/sam`, 2.4 GB |
| **DINOv2-large** | `pip install transformers` | `~/models/hf`, 1.2 GB |
| **Evo 2 7B** | container venv, `pip install --no-deps evo2 vtx` | `~/models/evo2`, 13 GB |

### ESM-2

`fair-esm` 2.0.0 is pure Python and installs cleanly. Weights come from
`dl.fbaipublicfiles.com` — **`HEAD` returns 403 while `GET` returns 200**, so a
downloader that probes with HEAD first will wrongly report the file as missing.

Measured: all 1,444 single substitutions of a 76-residue protein scored by masked
marginals in **1.6 s of GPU time** (23 s wall including staging).

### Segment Anything

Install `segment-anything` and `torchvision` with `--no-deps`.

**`min_mask_region_area` must be 0.** Any value above zero makes the mask generator
`import cv2`, which is not installed; the error names OpenCV and not the parameter.

Measured: 391 raw masks from one 512x512 microscopy image in **10.7 s**.

### DINOv2 — and why not DINOv3

**Every DINOv3 checkpoint on Hugging Face is gated** (`"gated": "manual"`); `config.json`
returns **401** without an approved token. `dinov3-vits16-pretrain-lvd1689m`, `-vitb16-`
and `-vitl16-` were all checked.

DINOv2-large (`facebook/dinov2-large`, 304M params, 1024-dim, patch 14) is ungated and
was substituted **with the user's explicit approval**. If you make a substitution like
this, say so in every output that depends on it — do not let a DINOv2 number be read as
a DINOv3 number.

To switch to DINOv3 once a token exists, change the model id in the script and set
`HF_TOKEN`; nothing else in the pipeline changes.

### Evo 2

Runs from the NGC container above. `pip install --no-deps evo2 vtx` gives
**evo2 0.6.0 + vtx 1.1.0** under the container's Python 3.12; on Python 3.14 pip silently
falls back to evo2 **0.3.0**, which is not the version you want. Weights
(`arcinstitute/evo2_7b`) are ungated, 13 GB on disk.

**Two A40-specific fixes are mandatory:**

1. `vortex/model/layers.py` enables `te.fp8_autocast` unconditionally. Set
   `use_fp8_input_projections: false` in the model's config YAML. Note that
   **`evo2_7b` resolves to `evo2-7b-1m.yml`, not the `8k` file** — editing the wrong
   one changes nothing and the assertion persists.
2. Pass `--env TRITON_LIBCUDA_PATH=/.singularity.d/libs`.

**The 40B, 20B and 1B Evo 2 models cannot run on this hardware at all** — they require
FP8 and therefore a Hopper-class GPU. Only the 7B models work, in bfloat16. Do not
promise a user the 40B model on Biocluster 4.

Measured: 25 sequences of 219 bp scored in **7.4 s of GPU time** (54 s wall).

## Sizing a GPU job

Across all four models the total GPU time was **under 25 seconds**; everything else was
weight loading and data staging. Size for data movement, not for the arithmetic, and do
not reserve a GPU for hours because the model name sounds expensive.

A reasonable starting ask for inference on a single model:

    #SBATCH -p gpu
    #SBATCH --gres=gpu:1
    #SBATCH -n 4
    #SBATCH --mem=24g
    #SBATCH -t 00:30:00

Check `seff <jobid>` afterwards and tell the user what it actually used.

## What is not here

No `jax`, no `transformers` module (pip it into a venv), no `detectron2`, no `PyCUDA`,
no `Tensorflow-GPU` module. `numba`, `umap-learn`, `hmmlearn`, `coniii` and `ssqueezepy`
exist as modules. Check `module avail` before promising anything.
