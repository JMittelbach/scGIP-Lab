#!/usr/bin/env python
from __future__ import annotations

import importlib
import importlib.util
import os
import subprocess
import sys
from importlib import metadata as importlib_metadata
from pathlib import Path

from packaging.version import Version


REPO_ROOT = Path(__file__).resolve().parents[1]
GENEFORMER_DIR = REPO_ROOT / "external" / "Geneformer"
RUNTIME_MODULES = [
    "transformers",
    "datasets",
    "torch",
    "loompy",
    "seaborn",
    "optuna",
    "peft",
    "statsmodels",
    "tdigest",
]


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
    cache_root = Path("/tmp/scgip-lab-cache")
    numba_cache = cache_root / "numba"
    mpl_cache = cache_root / "matplotlib"
    numba_cache.mkdir(parents=True, exist_ok=True)
    mpl_cache.mkdir(parents=True, exist_ok=True)

    child_env = os.environ.copy()
    child_env.setdefault("NUMBA_DISABLE_JIT", "1")
    child_env.setdefault("NUMBA_CACHE_DIR", str(numba_cache))
    child_env.setdefault("MPLCONFIGDIR", str(mpl_cache))

    cmd = [
        sys.executable,
        "-c",
        "import geneformer as g; print(getattr(g, '__version__', 'unknown'))",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env=child_env)
    if result.returncode == 0:
        version = (result.stdout or "").strip().splitlines()
        version_text = version[-1] if version else "unknown"
        print_status("OK", f"Python import succeeded: geneformer (version: {version_text})")
        return True

    combined = f"{result.stdout}\n{result.stderr}".strip()
    if "OMP: Error #15" in combined:
        print_status(
            "ERROR",
            "OpenMP runtime conflict detected while importing geneformer (libomp loaded multiple times).",
        )
        print_status(
            "INFO",
            "Use a clean conda env from scripts/setup_project.sh and avoid mixing pip/conda OpenMP runtimes.",
        )
    else:
        last_line = combined.splitlines()[-1] if combined else "unknown import error"
        print_status("ERROR", f"Could not import Python package 'geneformer': {last_line}")
    print_status("INFO", "Try: pip install -e external/Geneformer")
    return False


def check_runtime_modules() -> bool:
    ok = True
    for module_name in RUNTIME_MODULES:
        if importlib.util.find_spec(module_name) is None:
            print_status("ERROR", f"Module not found: {module_name}")
            ok = False
            continue
        try:
            version = importlib_metadata.version(module_name)
        except Exception:
            version = "unknown"
        print_status("OK", f"Module found: {module_name} ({version})")
    return ok


def check_transformers_compat() -> bool:
    if importlib.util.find_spec("transformers") is None:
        print_status("ERROR", "transformers is not installed.")
        return False

    try:
        version = Version(importlib_metadata.version("transformers"))
    except Exception:
        print_status("ERROR", "Could not determine transformers version.")
        return False

    if version.major != 4:
        print_status(
            "ERROR",
            f"transformers {version} detected. Geneformer expects transformers 4.x (recommended 4.46.*).",
        )
        return False
    if version < Version("4.46"):
        print_status(
            "WARN",
            f"transformers {version} detected. Recommended: 4.46.*",
        )
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
    print_status("INFO", f"Repo root: {REPO_ROOT}")
    print_status("INFO", f"Python: {Path(sys.executable)}")

    repo_ok = check_local_repo()
    deps_ok = check_runtime_modules()
    tf_ok = check_transformers_compat()
    import_ok = check_python_import()
    files_ok = check_expected_files() if repo_ok else False

    print("-" * 24)
    if repo_ok and deps_ok and tf_ok and import_ok and files_ok:
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
