#!/bin/bash
#SBATCH --job-name=prep_rmg_yaml
#SBATCH --time=01:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --output=prep_rmg_yaml-%j.out
#SBATCH --error=prep_rmg_yaml-%j.err

set -eo pipefail

BENCHMARK="${BENCHMARK:-catalytic/co2_hydrog_long}"
RMG_PATH="${RMG_PATH:-$HOME/RMG-Py}"
CONDA_ENV="${CONDA_ENV:-rmg_env2}"
RMG_WALLTIME="${RMG_WALLTIME:-00:02:00:00}"
RMG_SLURM_TIME="${RMG_SLURM_TIME:-02:10:00}"
PARTITION="${PARTITION:-short}"

BENCH_DIR="$SLURM_SUBMIT_DIR"
INPUT_DIR="${BENCH_DIR}/inputs/${BENCHMARK}"
RUN_BASE="${BENCH_DIR}/rmg_runs/${BENCHMARK}"
RUN_DIR=""

copy_prep_logs() {
    if [ -n "$RUN_DIR" ] && [ -d "$RUN_DIR" ]; then
        cp "${BENCH_DIR}/prep_rmg_yaml-${SLURM_JOB_ID}.out" "$RUN_DIR/prep-${SLURM_JOB_ID}.out" 2>/dev/null || true
        cp "${BENCH_DIR}/prep_rmg_yaml-${SLURM_JOB_ID}.err" "$RUN_DIR/prep-${SLURM_JOB_ID}.err" 2>/dev/null || true
    fi
}

handle_error() {
    exit_code=$?
    line_no="$1"

    echo "ERROR: prep job failed on line ${line_no} with exit code ${exit_code}"

    if [ -n "$RUN_DIR" ] && [ -d "$RUN_DIR" ]; then
        {
            echo "prep_failed: true"
            echo "failed_line: ${line_no}"
            echo "exit_code: ${exit_code}"
            echo "timestamp: $(date -Is)"
            echo "slurm_job_id: ${SLURM_JOB_ID}"
            echo "slurm_node: ${SLURMD_NODENAME:-UNKNOWN}"
            echo "benchmark: ${BENCHMARK}"
            echo "run_dir: ${RUN_DIR}"
        } > "$RUN_DIR/prep_failure_summary.txt"

        copy_prep_logs
    fi

    exit "$exit_code"
}

trap 'handle_error $LINENO' ERR
trap 'copy_prep_logs' EXIT

if [ ! -f "${INPUT_DIR}/input.py" ]; then
    echo "ERROR: Missing input file: ${INPUT_DIR}/input.py"
    exit 1
fi

mkdir -p "${RUN_BASE}"

n=1
while true; do
    RUN_DIR=$(printf "%s/run_%03d" "$RUN_BASE" "$n")
    if [ ! -e "$RUN_DIR" ]; then
        break
    fi
    n=$((n + 1))
done

mkdir -p "$RUN_DIR"
cp "${INPUT_DIR}/input.py" "${RUN_DIR}/input.py"

echo "Created run directory: $RUN_DIR"

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$CONDA_ENV"
cd "$RMG_PATH"

git fetch upstream
git checkout yaml_writer_addition
git reset --hard upstream/yaml_writer_addition

RMG_HASH=$(git rev-parse HEAD)
RMG_SHORT=$(git rev-parse --short HEAD)
RMG_BRANCH=$(git rev-parse --abbrev-ref HEAD)
RMG_DATE=$(git log -1 --pretty=%ci)
RMG_MESSAGE=$(git log -1 --pretty=%s)
RMG_UPSTREAM_HASH=$(git rev-parse upstream/yaml_writer_addition)
RMG_ORIGIN_HASH=$(git rev-parse origin/yaml_writer_addition 2>/dev/null || echo UNKNOWN)

cat > "${RUN_DIR}/rmg_git_info.txt" <<EOF
branch: ${RMG_BRANCH}
remote_used: upstream
remote_branch_used: upstream/yaml_writer_addition
commit_hash: ${RMG_HASH}
short_hash: ${RMG_SHORT}
commit_date: ${RMG_DATE}
commit_message: ${RMG_MESSAGE}
upstream_yaml_writer_addition_hash: ${RMG_UPSTREAM_HASH}
origin_yaml_writer_addition_hash: ${RMG_ORIGIN_HASH}
rmg_path: ${RMG_PATH}
benchmark: ${BENCHMARK}
run_dir: ${RUN_DIR}
prep_slurm_job_id: ${SLURM_JOB_ID}
prep_slurm_node: ${SLURMD_NODENAME:-UNKNOWN}

EOF

echo "Wrote RMG git info to ${RUN_DIR}/rmg_git_info.txt"

make

echo "Submitting RMG job..."

RMG_JOB_ID=$(sbatch \
    -p "$PARTITION" \
    --parsable \
    --time="$RMG_SLURM_TIME" \
    --output="${RUN_DIR}/rmg_yaml_run-%j.out" \
    --error="${RUN_DIR}/rmg_yaml_run-%j.err" \
    --export=ALL,RUN_DIR="$RUN_DIR",RMG_PATH="$RMG_PATH",CONDA_ENV="$CONDA_ENV",RMG_WALLTIME="$RMG_WALLTIME" \
    "${BENCH_DIR}/slurm/run_rmg_job.sh")

echo "Submitted RMG job: $RMG_JOB_ID"


cat >> "${RUN_DIR}/rmg_git_info.txt" <<EOF
rmg_slurm_job_id: ${RMG_JOB_ID}
EOF

echo "Submitting analysis job..."

ANALYSIS_JOB_ID=$(sbatch \
    -p "$PARTITION" \
    --parsable \
    --dependency=afterany:${RMG_JOB_ID} \
    --output="${RUN_DIR}/analysis-%j.out" \
    --error="${RUN_DIR}/analysis-%j.err" \
    --export=ALL,RUN_DIR="$RUN_DIR",CONDA_ENV="$CONDA_ENV",BENCH_DIR="$BENCH_DIR" \
    "${BENCH_DIR}/slurm/run_analysis_job.sh")

echo "Submitted analysis job: $ANALYSIS_JOB_ID"

cat >> "${RUN_DIR}/rmg_git_info.txt" <<EOF
analysis_slurm_job_id: ${ANALYSIS_JOB_ID}
EOF

copy_prep_logs