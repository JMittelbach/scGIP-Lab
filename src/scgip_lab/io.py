from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import anndata as ad
import pandas as pd

LABEL_PATTERNS = [
    "label",
    "celltype",
    "cell_type",
    "cell type",
    "annotation",
    "subtype",
    "predicted",
    "cluster",
]

BATCH_PATTERNS = [
    "dataset",
    "donor",
    "subject",
    "individual",
    "sample",
    "batch",
    "patient",
    "library",
]


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def find_h5ad_files(input_dir: str | Path) -> list[Path]:
    p = Path(input_dir)
    if not p.exists():
        raise FileNotFoundError(f"Input directory not found: {p}")
    if not p.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {p}")
    return sorted(p.glob("*.h5ad"))


def read_h5ad(path: str | Path) -> ad.AnnData:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"h5ad file not found: {p}")
    if p.suffix.lower() != ".h5ad":
        raise ValueError(f"Expected .h5ad file, got: {p}")
    return ad.read_h5ad(p)


def _detect_columns(columns: list[str], patterns: list[str]) -> list[str]:
    out: list[str] = []
    for col in columns:
        lowered = str(col).lower()
        if any(pattern in lowered for pattern in patterns):
            out.append(str(col))
    return out


def detect_candidate_label_columns(adata: ad.AnnData) -> list[str]:
    return _detect_columns([str(c) for c in adata.obs.columns], LABEL_PATTERNS)


def detect_candidate_batch_columns(adata: ad.AnnData) -> list[str]:
    return _detect_columns([str(c) for c in adata.obs.columns], BATCH_PATTERNS)


def summarize_adata(adata: ad.AnnData, dataset_name: str | None = None) -> dict[str, Any]:
    label_cols = detect_candidate_label_columns(adata)
    batch_cols = detect_candidate_batch_columns(adata)

    summary: dict[str, Any] = {
        "dataset_name": dataset_name,
        "n_cells": int(adata.n_obs),
        "n_genes": int(adata.n_vars),
        "obs_columns": [str(c) for c in adata.obs.columns],
        "candidate_label_columns": label_cols,
        "candidate_batch_columns": batch_cols,
        "label_top_values": {},
    }
    for col in label_cols:
        top = adata.obs[col].astype(str).value_counts(dropna=False).head(20)
        summary["label_top_values"][col] = {str(k): int(v) for k, v in top.items()}
    return summary


def write_json(obj: Any, path: str | Path) -> None:
    p = Path(path)
    ensure_dir(p.parent)
    with p.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)


def write_tsv(df: pd.DataFrame, path: str | Path) -> None:
    p = Path(path)
    ensure_dir(p.parent)
    df.to_csv(p, sep="\t", index=False)

