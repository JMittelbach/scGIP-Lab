#!/usr/bin/env python
from __future__ import annotations

import importlib
import os
from importlib import metadata as importlib_metadata

CACHE_ROOT = "/tmp/scgip-lab-cache"
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("NUMBA_CACHE_DIR", f"{CACHE_ROOT}/numba")
os.environ.setdefault("MPLCONFIGDIR", f"{CACHE_ROOT}/matplotlib")


REQUIRED = [
    "scanpy",
    "anndata",
    "pandas",
    "numpy",
    "sklearn",
    "torch",
    "transformers",
    "datasets",
    "loompy",
    "seaborn",
    "optuna",
    "peft",
    "statsmodels",
    "tdigest",
]


def module_version(module_name: str, module_obj) -> str:
    try:
        return importlib_metadata.version(module_name)
    except Exception:
        return getattr(module_obj, "__version__", "unknown")


def main() -> None:
    print("Checking imports")
    for mod in REQUIRED:
        try:
            module = importlib.import_module(mod)
            version = module_version(mod, module)
            print(f"[OK] {mod}: {version}")
        except Exception as exc:
            print(f"[ERROR] {mod}: {exc}")

    try:
        geneformer = importlib.import_module("geneformer")
        version = module_version("geneformer", geneformer)
        print(f"[OK] geneformer: {version}")
    except Exception:
        print("[WARN] geneformer: not installed")


if __name__ == "__main__":
    main()
