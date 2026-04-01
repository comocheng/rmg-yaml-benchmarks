#!/bin/bash
#SBATCH --job-name=rmg_gas_phase
#SBATCH --output=results/gas_phase_%j.log
#SBATCH --error=results/gas_phase_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=20       
#SBATCH --mem=120G                
#SBATCH --time=08:00:00           
#SBATCH --partition=west

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate rmg_yaml_env


RMG_PY="${RMG_PY:-$HOME/RMG-Py}"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INPUT="$REPO_DIR/inputs/gas_phase/c2h6/input.py"
OUTDIR="${RESULTS_DIR:-$REPO_DIR/results/gas_phase/c2h6}"
mkdir -p "$OUTDIR"

python "$RMG_PY/rmg.py" \
    --profile \
    --walltime 00:06:00:00 \
    --output-directory "$OUTDIR" \
    "$INPUT"

echo "Gas phase RMG job finished. Output in $OUTDIR"