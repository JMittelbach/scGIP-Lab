"""Input/output helpers for local AnnData-based PBMC workflows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import anndata as ad

from .constants import BATCH_COLUMN_KEYWORDS, LABEL_COLUMN_KEYWORDS


def ensure_dir(path: str | Path) -> Path:
    """Create a directory if needed and return its Path."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def read_h5ad(path: str | Path) -> ad.AnnData:
    """Read an h5ad file with basic path validation."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"h5ad file not found: {p}")
    if p.suffix.lower() != ".h5ad":
        raise ValueError(f"Expected an .h5ad file, got: {p}")
    return ad.read_h5ad(p)


def detect_candidate_label_columns(adata: ad.AnnData) -> list[str]:
    """Heuristically detect likely label columns in adata.obs."""
    candidates: list[str] = []
    for col in adata.obs.columns:
        lowered = str(col).lower()
        if any(keyword in lowered for keyword in LABEL_COLUMN_KEYWORDS):
            candidates.append(col)
    return candidates


def detect_candidate_batch_columns(adata: ad.AnnData) -> list[str]:
    """Heuristically detect likely batch/donor/dataset columns in adata.obs."""
    candidates: list[str] = []
    for col in adata.obs.columns:
        lowered = str(col).lower()
        if any(keyword in lowered for keyword in BATCH_COLUMN_KEYWORDS):
            candidates.append(col)
    return candidates


def summarize_adata(adata: ad.AnnData) -> dict[str, Any]:
    """Return a compact summary of matrix dimensions and selected obs metadata."""
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
    """Write JSON with stable formatting and parent directory creation."""
    p = Path(path)
    ensure_dir(p.parent)
    with p.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
