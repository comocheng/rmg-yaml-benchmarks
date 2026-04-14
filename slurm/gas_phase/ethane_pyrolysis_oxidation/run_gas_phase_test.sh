#!/bin/bash
#SBATCH --job-name=rmg_gas_phase_test
#SBATCH --output=/home/wang.yiray/rmg-yaml-benchmarks/results/gas_phase/ethane_pyrolysis_oxidation_test/slurm_%j.log
#SBATCH --error=/home/wang.yiray/rmg-yaml-benchmarks/results/gas_phase/ethane_pyrolysis_oxidation_test/slurm_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=80G
#SBATCH --time=00:30:00
#SBATCH --partition=west


set -euo pipefail

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate rmg_yaml_env

RMG_PY="${RMG_PY:-$HOME/RMG-Py}"
REPO_DIR="${REPO_DIR:-$HOME/rmg-yaml-benchmarks}"
INPUT="$REPO_DIR/inputs/gas_phase/ethane_pyrolysis_oxidation/test_input.py"
OUTDIR="${RESULTS_DIR:-$REPO_DIR/results/gas_phase/ethane_pyrolysis_oxidation_test}"

mkdir -p "$OUTDIR"

echo "Job ID:     $SLURM_JOB_ID"
echo "Input:      $INPUT"
echo "Output dir: $OUTDIR"
echo "RMG-Py:     $RMG_PY"
echo "Started:    $(date)"
echo ""

python "$RMG_PY/rmg.py" \
    --profile \
    --walltime 00:00:20:00 \
    --output-directory "$OUTDIR" \
    "$INPUT"

echo ""
echo "RMG test job finished: $(date)"
echo "Output in: $OUTDIR"