#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${REPO_ROOT}/environment.yml"

MODE="quick"
RUN_CHECKS=1

usage() {
  cat <<'EOF'
Usage: bash scripts/setup_project.sh [--quick|--full] [--no-checks]

  --quick     Fast path. Reuse existing env and skip reinstall steps when possible. (default)
  --full      Force full sync: env update, editable install, Geneformer setup.
  --no-checks Skip final diagnostics.

Notes:
  - The script checks for git-lfs before Geneformer setup.
  - If missing, it attempts: conda install -n base -c conda-forge git-lfs -y
EOF
}

for arg in "$@"; do
  case "$arg" in
    --quick)
      MODE="quick"
      ;;
    --full)
      MODE="full"
      ;;
    --no-checks)
      RUN_CHECKS=0
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[ERROR] Unknown argument: $arg"
      usage
      exit 1
      ;;
  esac
done

if ! command -v conda >/dev/null 2>&1; then
  echo "[ERROR] conda not found in PATH."
  exit 1
fi

if ! command -v git >/dev/null 2>&1; then
  echo "[ERROR] git not found in PATH."
  exit 1
fi

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "[ERROR] environment.yml not found: ${ENV_FILE}"
  exit 1
fi

ENV_NAME="$(awk '/^name:/{print $2; exit}' "${ENV_FILE}")"
if [[ -z "${ENV_NAME}" ]]; then
  ENV_NAME="scgip-lab"
fi
TARGET_PY="3.11"
ACTIVE_ENV="${CONDA_DEFAULT_ENV:-}"
ENV_CREATED=0

echo "[INFO] Repo: ${REPO_ROOT}"
echo "[INFO] Env: ${ENV_NAME}"
echo "[INFO] Mode: ${MODE}"

mkdir -p "/tmp/scgip-lab-cache/numba" "/tmp/scgip-lab-cache/matplotlib"
export NUMBA_DISABLE_JIT=1
export NUMBA_CACHE_DIR="/tmp/scgip-lab-cache/numba"
export MPLCONFIGDIR="/tmp/scgip-lab-cache/matplotlib"

env_exists() {
  conda info --envs | awk '{print $1}' | grep -Fxq "$1"
}

env_python_minor() {
  conda run -n "$1" python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null \
    | awk 'NF{last=$0} END{print last}'
}

ensure_git_lfs() {
  if git lfs version >/dev/null 2>&1; then
    echo "[INFO] git-lfs found."
    return 0
  fi

  echo "[WARN] git-lfs is missing. Attempting installation via conda base..."
  if conda install -n base -c conda-forge git-lfs -y; then
    hash -r
  else
    echo "[ERROR] Automatic git-lfs install failed."
    echo "[ERROR] Install git-lfs manually, then rerun setup:"
    echo "[ERROR]   conda install -n base -c conda-forge git-lfs -y"
    return 1
  fi

  if git lfs version >/dev/null 2>&1; then
    echo "[OK] git-lfs installed successfully."
    return 0
  fi

  echo "[ERROR] git-lfs still unavailable after installation attempt."
  echo "[ERROR] Confirm PATH and run:"
  echo "[ERROR]   git lfs install"
  return 1
}

if env_exists "${ENV_NAME}"; then
  CURRENT_PY="$(env_python_minor "${ENV_NAME}")"
  if [[ -z "${CURRENT_PY}" ]]; then
    echo "[WARN] Could not detect Python version for ${ENV_NAME}. Keeping existing environment."
  elif [[ "${CURRENT_PY}" != "${TARGET_PY}" ]]; then
    echo "[WARN] Environment ${ENV_NAME} uses Python ${CURRENT_PY}, expected ${TARGET_PY}."
    if [[ "${ACTIVE_ENV}" == "${ENV_NAME}" ]]; then
      echo "[ERROR] ${ENV_NAME} is currently active."
      echo "[ERROR] Run 'conda deactivate' and rerun setup."
      exit 2
    fi
    echo "[INFO] Recreating ${ENV_NAME} with the project-pinned Python version..."
    conda env remove -n "${ENV_NAME}" -y
    conda env create -n "${ENV_NAME}" -f "${ENV_FILE}"
    ENV_CREATED=1
  elif [[ "${MODE}" == "full" ]]; then
    echo "[INFO] Updating conda environment..."
    conda env update -n "${ENV_NAME}" -f "${ENV_FILE}" --prune
  else
    echo "[INFO] Reusing existing environment."
  fi
else
  echo "[INFO] Creating conda environment..."
  conda env create -n "${ENV_NAME}" -f "${ENV_FILE}"
  ENV_CREATED=1
fi

if [[ "${MODE}" == "full" || "${ENV_CREATED}" -eq 1 ]]; then
  echo "[INFO] Installing local package..."
  conda run -n "${ENV_NAME}" python -m pip install -e "${REPO_ROOT}" --no-deps
else
  echo "[INFO] Skipping local package install (already set up)."
fi

GENEFORMER_READY=0
if [[ -d "${REPO_ROOT}/external/Geneformer/.git" ]]; then
  if conda run -n "${ENV_NAME}" python -m pip show geneformer >/dev/null 2>&1; then
    GENEFORMER_READY=1
  fi
fi

if [[ "${MODE}" == "full" || "${ENV_CREATED}" -eq 1 || "${GENEFORMER_READY}" -ne 1 ]]; then
  if ! ensure_git_lfs; then
    exit 1
  fi
  echo "[INFO] Running Geneformer setup..."
  conda run -n "${ENV_NAME}" bash "${REPO_ROOT}/scripts/setup_geneformer.sh"
else
  echo "[INFO] Skipping Geneformer setup (already present)."
fi

if [[ "${RUN_CHECKS}" -eq 1 ]]; then
  echo "[INFO] Running environment checks..."
  conda run -n "${ENV_NAME}" python "${REPO_ROOT}/scripts/00_check_environment.py"
  conda run -n "${ENV_NAME}" python "${REPO_ROOT}/scripts/check_geneformer.py"
else
  echo "[INFO] Checks skipped."
fi

echo "[OK] Setup complete."
echo "[OK] Activate with: conda activate ${ENV_NAME}"
