# scanpy pipeline on the IGB biocluster using the shared leiden-capable env.
# The bare scanpy module has no leidenalg/igraph. ~2 cores and 8 GB is the honest
# ask for a PBMC-3k-scale run (measured: 12.96% CPU efficiency at 8 cores/32 GB).
#SBATCH -p normal
#SBATCH -N 1
#SBATCH -n 2
#SBATCH --mem=8g

export MPLCONFIGDIR="$PWD/.mplcache"
module use "$CS_SHARED_ROOT/modulefiles"
module load cs/scanpy-leiden

python ./pipeline.py 2>&1 | tee -a ./run.log
ls -lh ./out 2>/dev/null || true

# Leiden cluster counts are not portable across scanpy versions: the same PBMC-3k
# pipeline gives 8 clusters at r=1.0 under scanpy 1.10.1 here vs 9 under 1.12.4.
