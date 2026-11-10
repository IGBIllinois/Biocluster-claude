#!/bin/bash
# GPU inference on IGB Biocluster 4 using a venv layered on the IGB PyTorch module.
# This is the shape that ran ESM-2, Segment Anything and DINOv2 successfully
# (2026-10-31). See skills/igb-gpu-ml/SKILL.md for the traps.
#
# Build the venv ON THE LOGIN NODE first — compute nodes have no internet:
#
#   module load PyTorch/2.14.1-IGB-gcc-15.2.0-Python-3.14.0
#   python -m venv --system-site-packages ~/models/venv
#   source ~/models/venv/bin/activate
#   pip install <packages>          # use --no-deps for anything torch-adjacent
#
#SBATCH -p gpu
#SBATCH -N 1
#SBATCH -n 4
#SBATCH --mem=24g
#SBATCH --gres=gpu:1
#SBATCH -t 00:30:00
#SBATCH -J gpujob

cd "$SLURM_SUBMIT_DIR"
: "${TMPDIR:=$PWD/tmp}"; mkdir -p "$TMPDIR"; export TMPDIR
export MPLCONFIGDIR="$PWD/.mplcache"

module purge
module load PyTorch/2.14.1-IGB-gcc-15.2.0-Python-3.14.0
source "$HOME/models/venv/bin/activate"

python - <<'PY' 2>&1 | tee -a ./run.log
import torch
print("torch", torch.__version__, "| cuda", torch.version.cuda)
assert torch.cuda.is_available(), "no GPU visible - check --gres=gpu:1"
p = torch.cuda.get_device_properties(0)
print(f"device {p.name} sm_{p.major}{p.minor} {p.total_memory/2**30:.1f} GB")
PY

# <your work here>  2>&1 | tee -a ./run.log

# Afterwards: seff $SLURM_JOB_ID — report what it actually used, not what you reserved.
#
# Do NOT add an `nvidia-smi || exit 1` preflight. nvidia-smi IS on PATH on Biocluster 4;
# that guard was a Biocluster 3 artefact and would abort every job.
