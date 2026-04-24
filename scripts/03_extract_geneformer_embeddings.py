#!/usr/bin/env python
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import anndata as ad
import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
CACHE_ROOT = Path("/tmp/scgip-lab-cache")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("NUMBA_CACHE_DIR", str(CACHE_ROOT / "numba"))
os.environ.setdefault("MPLCONFIGDIR", str(CACHE_ROOT / "matplotlib"))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from geneformer_immune_benchmark.geneformer_utils import check_geneformer_installation
from geneformer_immune_benchmark.io import ensure_dir


def load_geneformer_config(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    if "geneformer" not in config:
        raise ValueError("Missing top-level key 'geneformer' in config YAML.")
    return config["geneformer"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tokenize", action="store_true")
    parser.add_argument("--input-dir", default="data/raw")
    parser.add_argument("--output-dir", default="data/processed/tokenized")
    parser.add_argument("--output-prefix", default="pbmc_tokenized")
    parser.add_argument("--nproc", type=int, default=4)
    parser.add_argument("--model-version", choices=["V1", "V2"], default="V2")
    parser.add_argument("--use-h5ad-index", action="store_true")
    return parser.parse_args()


def check_h5ad_ready(input_dir: Path, use_h5ad_index: bool) -> tuple[bool, str]:
    files = sorted(input_dir.glob("*.h5ad"))
    if not files:
        return False, f"No .h5ad files found in {input_dir}"

    sample = files[0]
    try:
        adata = ad.read_h5ad(sample)
    except Exception as exc:
        return False, f"Could not read {sample}: {exc}"

    if "n_counts" not in adata.obs.columns:
        return False, f"{sample.name} is missing obs['n_counts'] required by Geneformer tokenizer."
    if not use_h5ad_index and "ensembl_id" not in adata.var.columns:
        return False, (
            f"{sample.name} is missing var['ensembl_id']. "
            "Use --use-h5ad-index only if var index contains Ensembl IDs."
        )
    return True, f"{len(files)} h5ad files detected."


def run_tokenization(
    input_dir: Path,
    output_dir: Path,
    output_prefix: str,
    nproc: int,
    model_version: str,
    use_h5ad_index: bool,
) -> int:
    try:
        from geneformer import TranscriptomeTokenizer
    except Exception as exc:
        print(f"[ERROR] Could not import TranscriptomeTokenizer: {exc}")
        print("[INFO] Run: bash scripts/setup_geneformer.sh")
        return 1

    ok, msg = check_h5ad_ready(input_dir, use_h5ad_index)
    if not ok:
        print(f"[ERROR] {msg}")
        return 1
    print(f"[INFO] {msg}")

    ensure_dir(output_dir)
    try:
        tokenizer = TranscriptomeTokenizer(
            custom_attr_name_dict=None,
            nproc=nproc,
            use_h5ad_index=use_h5ad_index,
            model_version=model_version,
        )
        tokenizer.tokenize_data(
            data_directory=str(input_dir),
            output_directory=str(output_dir),
            output_prefix=output_prefix,
            file_format="h5ad",
        )
    except Exception as exc:
        print(f"[ERROR] Tokenization failed: {exc}")
        return 1

    out_path = (output_dir / output_prefix).with_suffix(".dataset")
    print(f"[OK] Tokenized dataset: {out_path}")
    return 0


def main() -> int:
    args = parse_args()
    config_path = ROOT / "config" / "geneformer.example.yml"

    print("Geneformer workflow")
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
    print("[INFO] module check:")
    for name, is_available in module_status.items():
        print(f"  - {name}: {'OK' if is_available else 'MISSING'}")

    if not (install_dir.exists() and module_status.get("geneformer", False)):
        print("[WARN] Geneformer not ready.")
        print("[INFO] Run: bash scripts/setup_project.sh")
        return 1

    if args.tokenize:
        return run_tokenization(
            input_dir=ROOT / args.input_dir,
            output_dir=ROOT / args.output_dir,
            output_prefix=args.output_prefix,
            nproc=args.nproc,
            model_version=args.model_version,
            use_h5ad_index=args.use_h5ad_index,
        )

    print("Planned steps:")
    print("1) tokenize h5ad")
    print("2) extract embeddings")
    print("3) save .npy + cell IDs")
    print("Embedding extraction is not implemented yet.")
    print("Run tokenization now with: --tokenize")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
