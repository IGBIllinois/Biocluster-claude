#!/bin/bash
# AlphaFold 3 monomer on IGB Biocluster 4. Re-verified 2026-11-01 on alphafold/3.0.4,
# A40, slurm job 16638. See skills/igb-structure-prediction/SKILL.md for the timings.
#
# Build input.json ON THE CLUSTER from the mirrored pdb_seqres file so the sequence
# never has to be transcribed into a transcript or typed from memory.
#
# Slurm sets TMPDIR to a node-local /scratch/$SLURM_JOB_ID inside a job; the guard
#SBATCH -p gpu
#SBATCH -N 1
#SBATCH -n 8
#SBATCH --mem=16g
#SBATCH --gres=gpu:1
#SBATCH -t 02:00:00
#SBATCH -J af3

cd "$SLURM_SUBMIT_DIR"
: "${TMPDIR:=$PWD/tmp}"; mkdir -p "$TMPDIR"; export TMPDIR

module purge
module load alphafold/3.0.4
module load alphafold3-db/20250520
# The db module sets both $BIODB and $EBROOTALPHAFOLD3MINDB to the same path.
DB="$EBROOTALPHAFOLD3MINDB"

# Resolve the sequence offline from the mirrored SEQRES file. Replace 1ubq_A.
SEQ=$(awk '/^>1ubq_A /{getline; print; exit}' "$DB/pdb_seqres_2022_09_28.fasta")
echo "seqlen=${#SEQ}"

cat > input.json <<JEOF
{"name":"1ubq_A","modelSeeds":[1],
 "sequences":[{"protein":{"id":"A","sequence":"$SEQ"}}],
 "dialect":"alphafold3","version":1}
JEOF

apptainer exec --nv "$EBROOTALPHAFOLD/alphafold.sif" \
  python /app/alphafold/run_alphafold.py \
    --json_path input.json \
    --output_dir ./af3_out \
    --db_dir "$DB" \
    --model_dir "$DB/parameters" > run.log 2>&1

cp ./af3_out/*/*.cif ./af3_out/*/*.json ./ 2>/dev/null || true
grep -oE "Finished [A-Za-z0-9_() .-]+ in [0-9.]+ seconds" run.log | tail -20
ls -lh ./*.cif 2>/dev/null || true

# Template cutoff is 2022-09-28 — a pre-cutoff target is template-informed, not a
# blind fold. Say so when reporting the result.
