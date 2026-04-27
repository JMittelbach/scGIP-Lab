#!/usr/bin/env python
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
from typing import Any

import anndata as ad
import yaml

ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compact readiness check for Experiment 01. "
            "Default output is short: stage + next steps."
        )
    )
    parser.add_argument("--h5ad", default=None, help="Path to one h5ad file (optional).")
    parser.add_argument("--dataset-name", default=None, help="Dataset name override (optional).")
    parser.add_argument("--label-col", default=None, help="Preferred label column (optional).")
    parser.add_argument("--strict", action="store_true", help="Exit with code 1 if blockers exist.")
    parser.add_argument("--json", action="store_true", help="Print JSON summary.")
    parser.add_argument("--verbose", action="store_true", help="Print detailed diagnostics.")
    return parser.parse_args()


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def check_modules(modules: list[str]) -> tuple[list[str], list[str]]:
    ok: list[str] = []
    missing: list[str] = []
    for module in modules:
        if importlib.util.find_spec(module) is None:
            missing.append(module)
        else:
            ok.append(module)
    return ok, missing


def find_h5ad(path: str | None) -> tuple[Path | None, str]:
    if path:
        p = Path(path)
        if not p.is_absolute():
            p = ROOT / p
        if not p.exists():
            return None, f"Provided h5ad path does not exist: {p}"
        return p, "ok"

    raw_dir = ROOT / "data" / "raw"
    files = sorted(raw_dir.glob("*.h5ad"))
    if len(files) == 0:
        return None, f"No .h5ad files found in {raw_dir}"
    if len(files) == 1:
        return files[0], "ok"
    return files[0], f"Multiple h5ad files found in {raw_dir}; using first: {files[0].name}"


def read_obs_var_columns(h5ad_path: Path) -> tuple[list[str], list[str]]:
    adata = ad.read_h5ad(h5ad_path, backed="r")
    try:
        obs_cols = [str(c) for c in adata.obs.columns]
        var_cols = [str(c) for c in adata.var.columns]
    finally:
        if getattr(adata, "isbacked", False):
            try:
                adata.file.close()
            except Exception:
                pass
    return obs_cols, var_cols


def detect_label_candidates(obs_cols: list[str]) -> list[str]:
    priority = ["celltype.l2", "celltype.l1", "cell_type", "celltype", "annotation", "label"]
    found: list[str] = []
    for marker in priority:
        for col in obs_cols:
            if marker in col.lower() and col not in found:
                found.append(col)
    return found


def detect_count_candidates(obs_cols: list[str]) -> list[str]:
    preferred = ["n_counts", "nCount_RNA", "total_counts", "nCount_SCT", "nCount"]
    out: list[str] = []
    for key in preferred:
        if key in obs_cols and key not in out:
            out.append(key)
    for col in obs_cols:
        low = col.lower()
        if ("ncount" in low or "total_count" in low or ("umi" in low and "count" in low)) and col not in out:
            out.append(col)
    return out


def var_names_look_ensembl(h5ad_path: Path) -> bool:
    try:
        adata = ad.read_h5ad(h5ad_path, backed="r")
        try:
            sample = [str(x) for x in adata.var_names[:100]]
        finally:
            if getattr(adata, "isbacked", False):
                try:
                    adata.file.close()
                except Exception:
                    pass
    except Exception:
        return False

    if not sample:
        return False
    hits = sum(1 for x in sample if x.startswith("ENSG"))
    return (hits / len(sample)) >= 0.9


def dedupe(items: list[str]) -> list[str]:
    out: list[str] = []
    for item in items:
        if item not in out:
            out.append(item)
    return out


def get_stage_name(has_embeddings: bool, has_results: bool, has_h5ad: bool, has_tokenized: bool) -> str:
    if has_results:
        return "E1_DONE"
    if has_embeddings:
        return "READY_TO_RUN_E1"
    if has_tokenized:
        return "TOKENIZED_NEEDS_EMBEDDINGS"
    if has_h5ad:
        return "NEEDS_PREPROCESSING"
    return "NEEDS_DATA"


def vprint(enabled: bool, message: str) -> None:
    if enabled:
        print(message)


def main() -> int:
    args = parse_args()

    os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
    os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/scgip-lab-cache/numba")
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/scgip-lab-cache/matplotlib")

    e1_cfg = load_yaml(ROOT / "experiments" / "01_embedding_probe" / "config.yml")
    gf_cfg_wrapped = load_yaml(ROOT / "config" / "geneformer.example.yml")
    gf_cfg = gf_cfg_wrapped.get("geneformer", {})

    embeddings_dir = ROOT / e1_cfg.get("paths", {}).get("embeddings_dir", "data/processed/embeddings")
    output_dir = ROOT / e1_cfg.get("paths", {}).get("output_dir", "experiments/01_embedding_probe/results")
    emb_pattern = e1_cfg.get("embedding", {}).get("file_pattern", "{dataset}_geneformer_v1_embeddings.npy")
    ids_pattern = e1_cfg.get("embedding", {}).get("cell_id_pattern", "{dataset}_cell_ids.tsv")
    tokenized_dir = ROOT / gf_cfg.get("tokenized_dir", "data/processed/tokenized")

    blockers: list[str] = []
    warnings: list[str] = []
    suggestions: list[str] = []

    e1_ok, e1_missing = check_modules(
        ["scanpy", "anndata", "numpy", "pandas", "sklearn", "matplotlib", "yaml"]
    )
    if e1_missing:
        blockers.append(f"Missing E1 dependencies: {', '.join(e1_missing)}")
        suggestions.append("conda activate scgip-lab && bash scripts/setup_project.sh --full")

    gf_ok, gf_missing = check_modules(["geneformer", "transformers", "datasets", "torch", "loompy"])
    if gf_missing:
        warnings.append(f"Missing Geneformer deps: {', '.join(gf_missing)}")
        suggestions.append("conda activate scgip-lab && bash scripts/setup_geneformer.sh")

    cuda_available = None
    if importlib.util.find_spec("torch") is not None:
        try:
            import torch

            cuda_available = bool(torch.cuda.is_available())
        except Exception:
            cuda_available = None
    if cuda_available is False:
        warnings.append(
            "CUDA not available. Upstream Geneformer EmbExtractor currently expects CUDA for embedding extraction."
        )

    h5ad_path, h5ad_msg = find_h5ad(args.h5ad)
    if h5ad_path is None:
        blockers.append(h5ad_msg)
        suggestions.append(
            "Add or symlink a local h5ad file, e.g. ln -s /path/to/data.h5ad data/raw/data.h5ad"
        )
        obs_cols: list[str] = []
        var_cols: list[str] = []
    else:
        if h5ad_msg != "ok":
            warnings.append(h5ad_msg)
        try:
            obs_cols, var_cols = read_obs_var_columns(h5ad_path)
        except Exception as exc:
            blockers.append(f"Cannot read h5ad columns: {exc}")
            obs_cols, var_cols = [], []

    label_candidates = detect_label_candidates(obs_cols)
    selected_label = args.label_col
    if selected_label:
        if selected_label not in obs_cols:
            blockers.append(f"Requested label column not in .obs: {selected_label}")
    else:
        selected_label = label_candidates[0] if label_candidates else None
        if selected_label is None and h5ad_path is not None:
            warnings.append("No obvious label column found. Pass --label-col explicitly.")

    if h5ad_path is not None:
        count_candidates = detect_count_candidates(obs_cols)
        if "n_counts" not in obs_cols:
            if count_candidates:
                warnings.append(
                    "obs['n_counts'] is missing, but a likely source column exists: "
                    f"{count_candidates[0]} (auto-prepare can map it)."
                )
            else:
                blockers.append("obs['n_counts'] is missing and no fallback count column was detected.")
        if "ensembl_id" not in var_cols:
            if var_names_look_ensembl(h5ad_path):
                warnings.append(
                    "var['ensembl_id'] missing, but var_names look like Ensembl IDs (auto-prepare can map them)."
                )
            else:
                warnings.append("var['ensembl_id'] missing. You may need --use-h5ad-index if var.index has Ensembl IDs.")

    dataset_name = args.dataset_name or (h5ad_path.stem if h5ad_path else "unknown_dataset")
    emb_path = embeddings_dir / emb_pattern.format(dataset=dataset_name)
    ids_path = embeddings_dir / ids_pattern.format(dataset=dataset_name)
    tokenized_candidates = [
        tokenized_dir / f"{dataset_name}.dataset",
        tokenized_dir / "pbmc_tokenized.dataset",
    ]
    tokenized_files = sorted(tokenized_dir.glob("*.dataset")) if tokenized_dir.exists() else []
    has_tokenized = any(p.exists() for p in tokenized_candidates) or len(tokenized_files) > 0
    has_embeddings = emb_path.exists() and ids_path.exists()
    metrics_json = output_dir / "metrics" / "embedding_probe_metrics.json"
    has_results = metrics_json.exists()

    stage = get_stage_name(
        has_embeddings=has_embeddings,
        has_results=has_results,
        has_h5ad=h5ad_path is not None,
        has_tokenized=has_tokenized,
    )

    if not has_embeddings and h5ad_path is not None:
        suggestions.append(
            "Run preprocessing: "
            f"./experiments/01_embedding_probe/experiment_1.py --prepare --preprocess-only --h5ad {h5ad_path} --dataset-name {dataset_name}"
        )
    if has_embeddings:
        run_cmd = (
            f"./experiments/01_embedding_probe/experiment_1.py --h5ad {h5ad_path} --dataset-name {dataset_name}"
            + (f" --label-col {selected_label}" if selected_label else "")
        )
        suggestions.append(f"Run E1 probe: {run_cmd}")
    if has_results:
        suggestions.append("Review results: experiments/01_embedding_probe/results/metrics/embedding_probe_metrics.json")

    suggestions = dedupe(suggestions)

    if args.verbose:
        print("Experiment 01 readiness check")
        print("-" * 30)
        print(f"[INFO] repo: {ROOT}")
        print(f"[INFO] E1 deps ok: {', '.join(e1_ok) if e1_ok else '-'}")
        print(f"[INFO] E1 deps missing: {', '.join(e1_missing) if e1_missing else '-'}")
        print(f"[INFO] Geneformer deps ok: {', '.join(gf_ok) if gf_ok else '-'}")
        print(f"[INFO] Geneformer deps missing: {', '.join(gf_missing) if gf_missing else '-'}")
        print(f"[INFO] CUDA available: {cuda_available}")
        print(f"[INFO] dataset_name: {dataset_name}")
        print(f"[INFO] selected_label: {selected_label}")
        print(f"[INFO] expected embeddings: {emb_path}")
        print(f"[INFO] expected cell IDs: {ids_path}")
        print(f"[INFO] results metrics: {metrics_json}")
        print("-" * 30)
        print(f"[STAGE] {stage}")
        print(f"[STATUS] blockers={len(blockers)} warnings={len(warnings)}")
        if blockers:
            print("[BLOCKERS]")
            for item in blockers:
                print(f"- {item}")
        if warnings:
            print("[WARNINGS]")
            for item in warnings:
                print(f"- {item}")
        print("[NEXT STEPS]")
        if suggestions:
            for i, step in enumerate(suggestions, start=1):
                print(f"{i}. {step}")
        else:
            print("1. No action needed.")
    else:
        print(f"[STAGE] {stage}")
        print("[NEXT STEPS]")
        if suggestions:
            for i, step in enumerate(suggestions, start=1):
                print(f"{i}. {step}")
        else:
            print("1. No action needed.")

    if args.json:
        payload = {
            "stage": stage,
            "blockers": blockers,
            "warnings": warnings,
            "dataset_name": dataset_name,
            "h5ad": str(h5ad_path) if h5ad_path else None,
            "label_col": selected_label,
            "paths": {
                "tokenized_dir": str(tokenized_dir),
                "embeddings_dir": str(embeddings_dir),
                "embeddings_file": str(emb_path),
                "cell_ids_file": str(ids_path),
                "results_metrics": str(metrics_json),
            },
            "next_steps": suggestions,
        }
        print("[JSON]")
        print(json.dumps(payload, indent=2))

    if args.strict and blockers:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
