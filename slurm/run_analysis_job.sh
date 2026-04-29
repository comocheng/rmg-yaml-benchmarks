#!/bin/bash
#SBATCH --job-name=analyze_rmg_yaml
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G

set -eo pipefail

RUN_DIR="${RUN_DIR:?Missing RUN_DIR}"
CONDA_ENV="${CONDA_ENV:-rmg_env2}"
BENCH_DIR="${BENCH_DIR:-$SLURM_SUBMIT_DIR}"

echo "Running analysis"
echo "BENCH_DIR: $BENCH_DIR"
echo "RUN_DIR: $RUN_DIR"
echo "SLURM_JOB_ID: $SLURM_JOB_ID"

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$CONDA_ENV"

cd "$BENCH_DIR"

python scripts/analyze_run.py \
  --run-dir "$RUN_DIR" \
  --history-csv results/benchmark_history.csv \
  --allow-missing-profile

cat >> "${RUN_DIR}/rmg_git_info.txt" <<EOF
analysis_completed: true
analysis_job_id: ${SLURM_JOB_ID}
analysis_finished_at: $(date -Is)
EOF

git add "$RUN_DIR" results/benchmark_history.csv

if git diff --cached --quiet; then
    echo "No benchmark changes to commit."
else
    SHORT_HASH=$(grep "^short_hash:" "$RUN_DIR/rmg_git_info.txt" | cut -d ":" -f 2- | xargs || echo UNKNOWN)
    MESSAGE=$(grep "^commit_message:" "$RUN_DIR/rmg_git_info.txt" | cut -d ":" -f 2- | xargs || echo UNKNOWN)

    git commit -m "Benchmark run ${SHORT_HASH}: ${MESSAGE}"
fi

echo "Analysis and commit complete"