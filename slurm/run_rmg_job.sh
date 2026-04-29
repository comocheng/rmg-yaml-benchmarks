#!/bin/bash
#SBATCH --job-name=rmg_yaml_run
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G

set -eo pipefail

RUN_DIR="${RUN_DIR:?Missing RUN_DIR}"
RMG_PATH="${RMG_PATH:?Missing RMG_PATH}"
CONDA_ENV="${CONDA_ENV:-rmg_env2}"
RMG_WALLTIME="${RMG_WALLTIME:-00:06:00:00}"

handle_error() {
    exit_code=$?
    line_no="$1"

    echo "ERROR: RMG job failed on line ${line_no} with exit code ${exit_code}"

    {
        echo "rmg_failed: true"
        echo "failed_line: ${line_no}"
        echo "exit_code: ${exit_code}"
        echo "timestamp: $(date -Is)"
        echo "slurm_job_id: ${SLURM_JOB_ID}"
        echo "slurm_node: ${SLURMD_NODENAME:-UNKNOWN}"
        echo "run_dir: ${RUN_DIR}"
        echo "rmg_path: ${RMG_PATH}"
        echo "rmg_walltime: ${RMG_WALLTIME}"
    } > "${RUN_DIR}/rmg_failure_summary.txt"

    exit "$exit_code"
}

trap 'handle_error $LINENO' ERR

echo "Running RMG job"
echo "RUN_DIR: $RUN_DIR"
echo "RMG_PATH: $RMG_PATH"
echo "CONDA_ENV: $CONDA_ENV"
echo "RMG_WALLTIME: $RMG_WALLTIME"
echo "SLURM_JOB_ID: $SLURM_JOB_ID"
echo "SLURM_NODE: ${SLURMD_NODENAME:-UNKNOWN}"

cat >> "${RUN_DIR}/rmg_git_info.txt" <<EOF
actual_rmg_slurm_job_id: ${SLURM_JOB_ID}
actual_rmg_slurm_node: ${SLURMD_NODENAME:-UNKNOWN}
actual_rmg_started_at: $(date -Is)
EOF

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$CONDA_ENV"

which python
python --version

cd "$RUN_DIR"

echo "Starting RMG..."
python "${RMG_PATH}/rmg.py" input.py \
    --profile \
    --walltime "$RMG_WALLTIME"

echo "RMG finished successfully in: $RUN_DIR"

cat >> "${RUN_DIR}/rmg_git_info.txt" <<EOF
actual_rmg_finished_at: $(date -Is)
rmg_completed: true
EOF

{
    echo "rmg_completed: true"
    echo "exit_code: 0"
    echo "timestamp: $(date -Is)"
    echo "slurm_job_id: ${SLURM_JOB_ID}"
    echo "run_dir: ${RUN_DIR}"
} > "${RUN_DIR}/rmg_success_summary.txt"