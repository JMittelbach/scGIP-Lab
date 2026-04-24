#!/usr/bin/env python
"""Safe scaffold for future Geneformer embedding extraction workflow."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from geneformer_immune_benchmark.geneformer_utils import check_geneformer_installation  # noqa: E402


def load_geneformer_config(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    if "geneformer" not in config:
        raise ValueError("Missing top-level key 'geneformer' in config YAML.")
    return config["geneformer"]


def main() -> int:
    config_path = ROOT / "config" / "geneformer.example.yml"
    print("Geneformer embedding extraction scaffold")
    print("=" * 40)

    try:
        geneformer_cfg = load_geneformer_config(config_path)
    except Exception as exc:
        print(f"[ERROR] Could not load config: {exc}")
        print("[INFO] Expected config file: config/geneformer.example.yml")
        return 1

    install_dir = ROOT / geneformer_cfg.get("install_dir", "external/Geneformer")
    model_dir = ROOT / geneformer_cfg.get("model_dir", "external/Geneformer")
    model_source = geneformer_cfg.get("model_source", "ctheodoris/Geneformer")

    print(f"[INFO] Config: {config_path}")
    print(f"[INFO] install_dir: {install_dir}")
    print(f"[INFO] model_dir: {model_dir}")
    print(f"[INFO] model_source: {model_source}")

    module_status = check_geneformer_installation()
    print("[INFO] Python module availability:")
    for name, is_available in module_status.items():
        state = "OK" if is_available else "MISSING"
        print(f"  - {name}: {state}")

    is_installed = install_dir.exists() and module_status.get("geneformer", False)
    if not is_installed:
        print("[WARN] Geneformer is not fully installed/configured yet.")
        print("[WARN] Run these commands first:")
        print("       bash scripts/setup_geneformer.sh")
        print("       python scripts/check_geneformer.py")

    print("")
    print("Intended workflow (safe scaffold):")
    print("1. Read local .h5ad files and validate expected AnnData columns.")
    print("2. Convert transcriptomes to Geneformer-compatible token input.")
    print("3. Tokenize transcriptomes using the installed Geneformer tooling.")
    print("4. Extract pretrained cell embeddings from selected model layer.")
    print("5. Save embeddings (.npy) and matching cell IDs (.tsv).")
    print("")
    print("TODO:")
    print("- Implement robust AnnData -> Geneformer preprocessing.")
    print("- Implement tokenization call into Geneformer package.")
    print("- Implement batched embedding extraction and output writing.")
    print("")
    print("No heavy embedding extraction is run by this script yet.")

    return 0 if is_installed else 1


if __name__ == "__main__":
    raise SystemExit(main())
