from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import anndata as ad

from .constants import BATCH_COLUMN_KEYWORDS, LABEL_COLUMN_KEYWORDS


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def read_h5ad(path: str | Path) -> ad.AnnData:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"h5ad file not found: {p}")
    if p.suffix.lower() != ".h5ad":
        raise ValueError(f"Expected an .h5ad file, got: {p}")
    return ad.read_h5ad(p)


def detect_candidate_label_columns(adata: ad.AnnData) -> list[str]:
    candidates: list[str] = []
    for col in adata.obs.columns:
        lowered = str(col).lower()
        if any(keyword in lowered for keyword in LABEL_COLUMN_KEYWORDS):
            candidates.append(col)
    return candidates


def detect_candidate_batch_columns(adata: ad.AnnData) -> list[str]:
    candidates: list[str] = []
    for col in adata.obs.columns:
        lowered = str(col).lower()
        if any(keyword in lowered for keyword in BATCH_COLUMN_KEYWORDS):
            candidates.append(col)
    return candidates


def summarize_adata(adata: ad.AnnData) -> dict[str, Any]:
    label_cols = detect_candidate_label_columns(adata)
    batch_cols = detect_candidate_batch_columns(adata)

    summary: dict[str, Any] = {
        "n_cells": int(adata.n_obs),
        "n_genes": int(adata.n_vars),
        "obs_columns": [str(c) for c in adata.obs.columns],
        "var_columns": [str(c) for c in adata.var.columns],
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
