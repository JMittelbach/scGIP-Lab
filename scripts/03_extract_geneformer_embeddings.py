#!/usr/bin/env python
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from geneformer_immune_benchmark.geneformer_utils import check_geneformer_installation


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
    print("Geneformer embedding extraction")

    try:
        geneformer_cfg = load_geneformer_config(config_path)
    except Exception as exc:
        print(f"[ERROR] Could not load config: {exc}")
        return 1

    install_dir = ROOT / geneformer_cfg.get("install_dir", "external/Geneformer")
    model_dir = ROOT / geneformer_cfg.get("model_dir", "external/Geneformer")
    model_source = geneformer_cfg.get("model_source", "ctheodoris/Geneformer")

    print(f"[INFO] config: {config_path}")
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
        print("[WARN] Geneformer not ready")
        print("[INFO] bash scripts/setup_geneformer.sh")
        print("[INFO] python scripts/check_geneformer.py")

    print("Planned steps:")
    print("1) validate AnnData input")
    print("2) tokenize")
    print("3) run pretrained embedding pass")
    print("4) save .npy embeddings + cell IDs")
    print("Status: extraction not implemented in this script.")

    return 0 if is_installed else 1


if __name__ == "__main__":
    raise SystemExit(main())
