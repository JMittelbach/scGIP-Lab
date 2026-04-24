#!/usr/bin/env python
from __future__ import annotations

import importlib
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
GENEFORMER_DIR = REPO_ROOT / "external" / "Geneformer"


def print_status(level: str, message: str) -> None:
    print(f"[{level}] {message}")


def check_local_repo() -> bool:
    if not GENEFORMER_DIR.exists():
        print_status("ERROR", f"Local Geneformer directory not found: {GENEFORMER_DIR}")
        print_status("INFO", "Run: bash scripts/setup_geneformer.sh")
        return False
    print_status("OK", f"Found local Geneformer directory: {GENEFORMER_DIR}")
    return True


def check_python_import() -> bool:
    try:
        module = importlib.import_module("geneformer")
    except Exception as exc:
        print_status("ERROR", f"Could not import Python package 'geneformer': {exc}")
        print_status("INFO", "Try: pip install -e external/Geneformer")
        return False
    version = getattr(module, "__version__", "unknown")
    print_status("OK", f"Python import succeeded: geneformer (version: {version})")
    return True


def check_expected_files() -> bool:
    ok = True

    required_paths = {
        "README": GENEFORMER_DIR / "README.md",
        "package directory": GENEFORMER_DIR / "geneformer",
        "git metadata": GENEFORMER_DIR / ".git",
    }

    for label, path in required_paths.items():
        if path.exists():
            print_status("OK", f"Found {label}: {path}")
        else:
            print_status("ERROR", f"Missing {label}: {path}")
            ok = False

    build_files = [GENEFORMER_DIR / "pyproject.toml", GENEFORMER_DIR / "setup.py"]
    if any(path.exists() for path in build_files):
        print_status(
            "OK",
            "Found Python build metadata (pyproject.toml or setup.py).",
        )
    else:
        print_status(
            "WARN",
            "No pyproject.toml/setup.py found. Editable install may fail.",
        )

    model_candidates = [
        GENEFORMER_DIR / "model.safetensors",
        GENEFORMER_DIR / "pytorch_model.bin",
        GENEFORMER_DIR / "Geneformer-V1-10M" / "model.safetensors",
    ]
    if any(path.exists() for path in model_candidates):
        print_status("OK", "Detected at least one local model weight file.")
    else:
        print_status(
            "WARN",
            "No known model weight file found yet. Run 'git lfs pull' if needed.",
        )

    return ok


def main() -> int:
    print("Geneformer diagnostics")
    print("-" * 24)

    repo_ok = check_local_repo()
    import_ok = check_python_import()
    files_ok = check_expected_files() if repo_ok else False

    print("-" * 24)
    if repo_ok and import_ok and files_ok:
        print_status("OK", "Geneformer installation looks ready for scaffold workflows.")
        return 0

    print_status("WARN", "Geneformer setup is incomplete. See messages above.")
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print_status("ERROR", f"Unexpected failure: {exc}")
        raise SystemExit(1)
