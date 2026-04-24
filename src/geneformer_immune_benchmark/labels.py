"""Conservative label harmonization helpers.

Expected AnnData obs columns:
- A dataset/study column (for dataset-specific mapping rows).
- A raw annotation column to preserve as immutable source labels.
- Optional harmonized columns (added by this module).
"""

from __future__ import annotations

import pandas as pd
from anndata import AnnData

from .constants import EXPECTED_HARMONIZED_COLUMNS, MAPPING_TEMPLATE_COLUMNS


def load_label_mapping(path: str) -> pd.DataFrame:
    """Load a TSV label mapping template and validate required columns."""
    mapping_df = pd.read_csv(path, sep="\t")
    missing = [c for c in MAPPING_TEMPLATE_COLUMNS if c not in mapping_df.columns]
    if missing:
        raise ValueError(f"Missing required mapping columns: {missing}")
    return mapping_df


def apply_label_mapping(
    adata: AnnData,
    mapping_df: pd.DataFrame,
    dataset_col: str,
    raw_label_col: str,
) -> AnnData:
    """Apply conservative mapping without touching raw labels.

    The function appends harmonized columns and tracking flags, preserving the
    original raw label column exactly as provided in adata.obs.
    """
    if dataset_col not in adata.obs.columns:
        raise KeyError(f"dataset_col not found in adata.obs: {dataset_col}")
    if raw_label_col not in adata.obs.columns:
        raise KeyError(f"raw_label_col not found in adata.obs: {raw_label_col}")

    # Keep a stable local copy of the source label columns.
    obs_df = adata.obs.copy()
    obs_df["_dataset_for_mapping"] = obs_df[dataset_col].astype(str)
    obs_df["_raw_label_for_mapping"] = obs_df[raw_label_col].astype(str)

    map_df = mapping_df.copy()
    map_df["dataset"] = map_df["dataset"].astype(str)
    map_df["raw_label"] = map_df["raw_label"].astype(str)

    merged = obs_df.merge(
        map_df,
        how="left",
        left_on=["_dataset_for_mapping", "_raw_label_for_mapping"],
        right_on=["dataset", "raw_label"],
    )

    for col in EXPECTED_HARMONIZED_COLUMNS + ["confidence", "action", "notes"]:
        out_col = f"mapping_{col}" if col in {"confidence", "action", "notes"} else col
        adata.obs[out_col] = merged[col].values if col in merged.columns else pd.NA

    add_unmapped_label_flags(adata)
    return adata


def add_unmapped_label_flags(adata: AnnData) -> AnnData:
    """Mark rows needing manual harmonization review."""
    if "harmonized_l1" not in adata.obs.columns:
        adata.obs["needs_label_review"] = True
        return adata

    action_col = adata.obs["mapping_action"] if "mapping_action" in adata.obs.columns else pd.Series(index=adata.obs.index, dtype="object")
    is_unmapped = adata.obs["harmonized_l1"].isna()
    is_review = action_col.astype(str).str.lower().isin({"review", "skip", "unknown"})
    adata.obs["needs_label_review"] = is_unmapped | is_review
    return adata


def summarize_label_mapping(adata: AnnData) -> pd.DataFrame:
    """Summarize harmonization coverage by level."""
    rows = []
    n_total = float(adata.n_obs) if adata.n_obs else 1.0
    for col in EXPECTED_HARMONIZED_COLUMNS:
        if col not in adata.obs.columns:
            rows.append({"column": col, "non_null": 0, "coverage": 0.0})
            continue
        non_null = int(adata.obs[col].notna().sum())
        rows.append({"column": col, "non_null": non_null, "coverage": non_null / n_total})
    if "needs_label_review" in adata.obs.columns:
        review_count = int(adata.obs["needs_label_review"].sum())
        rows.append(
            {
                "column": "needs_label_review",
                "non_null": review_count,
                "coverage": review_count / n_total,
            }
        )
    return pd.DataFrame(rows)
