# AlphaFold 3 monomer on the IGB biocluster. Verified 2026-09-28 (slurm 2413714).
# 76-residue monomer took 33 min 37 s; template loading dominates, not the MSA.
# Build input.json on the cluster from $BIODB/pdb_seqres_2022_09_28.fasta so the
# sequence never enters the transcript, and pass it as an ssh:// input locator.
#SBATCH -p admin
#SBATCH -N 1
#SBATCH -n 8
#SBATCH --mem=16g
#SBATCH --gres=gpu:1

if mkdir -p "/scratch/$SLURM_JOB_ID" 2>/dev/null && [ -w "/scratch/$SLURM_JOB_ID" ]; then
  export TMPDIR="/scratch/$SLURM_JOB_ID"
  trap 'rm -rf "/scratch/$SLURM_JOB_ID"' EXIT
else
  export TMPDIR="$PWD/tmp"; mkdir -p "$TMPDIR"
fi

module load alphafold/3.0.2
module load alphafold3-db/20250520

singularity exec --nv "$EBROOTALPHAFOLD/alphafold.sif" \
  python /app/alphafold/run_alphafold.py \
    --json_path input.json \
    --output_dir ./af3_out \
    --db_dir "$BIODB" \
    --model_dir "$BIODB/parameters" 2>&1 | tee -a ./run.log

cp ./af3_out/*/*.cif ./af3_out/*/*.json ./af3_out/*/*.csv ./ 2>/dev/null || true
ls -lh ./*.cif ./*.json ./*.csv ./run.log 2>/dev/null || true

# submit_job: outputs=['*.cif','*.json','*.csv','run.log'] harvests model + confidences.
# Template cutoff is 2022-09-28 - a pre-cutoff target is template-informed, say so.
