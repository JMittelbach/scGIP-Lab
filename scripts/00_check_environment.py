#!/usr/bin/env python
"""Check local environment dependencies for this repository."""

from __future__ import annotations

import importlib


REQUIRED = [
    "scanpy",
    "anndata",
    "pandas",
    "numpy",
    "sklearn",
    "torch",
    "transformers",
    "datasets",
]


def main() -> None:
    print("Checking required imports...")
    for mod in REQUIRED:
        try:
            module = importlib.import_module(mod)
            version = getattr(module, "__version__", "unknown")
            print(f"[OK] {mod}: {version}")
        except Exception as exc:
            print(f"[ERROR] {mod}: {exc}")

    try:
        geneformer = importlib.import_module("geneformer")
        version = getattr(geneformer, "__version__", "unknown")
        print(f"[OK] geneformer: {version}")
    except Exception:
        print("[WARN] geneformer not installed. This is expected for scaffold stage.")
        print("[WARN] Install/configure Geneformer later before embedding extraction.")


if __name__ == "__main__":
    main()
