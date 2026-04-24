from __future__ import annotations

import re
from typing import Iterable

import pandas as pd
from anndata import AnnData

from .io import detect_candidate_label_columns


def choose_label_column(adata: AnnData, preferred_col: str | None = None) -> str:
    if preferred_col is not None:
        if preferred_col not in adata.obs.columns:
            raise KeyError(f"Preferred label column not found in adata.obs: {preferred_col}")
        return preferred_col

    candidates = detect_candidate_label_columns(adata)
    if not candidates:
        raise ValueError(
            "No candidate label columns detected. Use --label-col to specify one explicitly."
        )
    return candidates[0]


def _map_one_label(label: str) -> str:
    text = str(label).strip().lower()
    if text in {"", "nan", "none", "na"}:
        return "UNKNOWN"

    if "cd4" in text:
        return "CD4_T"
    if "cd8" in text:
        return "CD8_T"

    if "natural killer" in text or re.search(r"\bnk\b", text):
        return "NK_CELL"

    if (
        "b cell" in text
        or "b_cell" in text
        or "b-cell" in text
        or "cd79" in text
    ):
        return "B_CELL"

    if (
        "mono" in text
        or "monocyte" in text
        or "cd14" in text
        or "fcgr3a" in text
        or "cd16 mono" in text
    ):
        return "MONOCYTE"

    if "dc" in text or "dendritic" in text or "cdc" in text or "pdc" in text:
        return "DC"

    if (
        "platelet" in text
        or "megakaryocyte" in text
        or "ppbp" in text
        or "pf4" in text
    ):
        return "PLATELET"

    if (
        "t cell" in text
        or "t_cell" in text
        or "t-cell" in text
        or "cd3" in text
    ):
        return "T_CELL"

    return "UNKNOWN"


def make_pbmc_broad_labels(raw_labels: Iterable[object]) -> pd.Series:
    mapped = [_map_one_label(str(x)) for x in raw_labels]
    return pd.Series(mapped, dtype="string")


def add_pbmc_broad_label(
    adata: AnnData,
    raw_label_col: str,
    output_col: str = "pbmc_broad_label",
) -> AnnData:
    if raw_label_col not in adata.obs.columns:
        raise KeyError(f"Raw label column not found in adata.obs: {raw_label_col}")
    raw = adata.obs[raw_label_col].astype(str)
    adata.obs[output_col] = make_pbmc_broad_labels(raw).values
    return adata


def summarize_label_counts(adata: AnnData, label_cols: list[str]) -> dict[str, dict[str, int]]:
    summary: dict[str, dict[str, int]] = {}
    for col in label_cols:
        if col not in adata.obs.columns:
            continue
        counts = adata.obs[col].astype(str).value_counts(dropna=False)
        summary[col] = {str(k): int(v) for k, v in counts.items()}
    return summary

