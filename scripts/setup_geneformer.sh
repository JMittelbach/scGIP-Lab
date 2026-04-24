#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
GENEFORMER_DIR="${REPO_ROOT}/external/Geneformer"
GENEFORMER_URL="https://huggingface.co/ctheodoris/Geneformer"

if command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
else
  echo "[ERROR] Python interpreter not found. Install Python first."
  exit 1
fi

echo "[INFO] Preparing local Geneformer installation."
echo "[INFO] Repository root: ${REPO_ROOT}"
echo "[INFO] Target path: ${GENEFORMER_DIR}"
echo "[INFO] This script installs Geneformer only. No datasets are downloaded."

echo "[INFO] Checking git-lfs availability..."
if ! git lfs version >/dev/null 2>&1; then
  echo "[ERROR] git-lfs is not installed or not available in PATH."
  echo "[ERROR] Install git-lfs first, then rerun this script."
  exit 1
fi

echo "[INFO] Running 'git lfs install'..."
git lfs install

mkdir -p "${REPO_ROOT}/external"

if [[ -d "${GENEFORMER_DIR}/.git" ]]; then
  echo "[INFO] Geneformer repository already exists. Updating..."
  git -C "${GENEFORMER_DIR}" pull --ff-only
  git -C "${GENEFORMER_DIR}" lfs pull
else
  if [[ -e "${GENEFORMER_DIR}" ]]; then
    echo "[ERROR] ${GENEFORMER_DIR} exists but is not a git repository."
    echo "[ERROR] Move or remove it, then rerun this script."
    exit 1
  fi
  echo "[INFO] Cloning Geneformer from Hugging Face..."
  git clone "${GENEFORMER_URL}" "${GENEFORMER_DIR}"
fi

echo "[INFO] Installing Geneformer in editable mode..."
"${PYTHON_BIN}" -m pip install -e "${GENEFORMER_DIR}"

echo "[OK] Geneformer setup completed."
echo "[OK] Run 'python scripts/check_geneformer.py' to verify diagnostics."
