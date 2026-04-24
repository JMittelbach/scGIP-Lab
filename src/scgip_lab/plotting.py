from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/scgip-lab-cache/numba")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/scgip-lab-cache/matplotlib")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scanpy as sc
from anndata import AnnData

from .io import ensure_dir


def _save_figure(output_path: str | Path, dpi: int = 200) -> Path:
    out = Path(output_path)
    ensure_dir(out.parent)
    plt.savefig(out, dpi=dpi, bbox_inches="tight")
    plt.close()
    return out


def _subsample_indices(n: int, max_points: int, seed: int) -> np.ndarray:
    if n <= max_points:
        return np.arange(n)
    rng = np.random.default_rng(seed)
    return np.sort(rng.choice(np.arange(n), size=max_points, replace=False))


def plot_umap_from_embedding(
    adata: AnnData,
    embedding_key: str,
    color_col: str,
    output_path: str | Path,
    title: str | None = None,
    max_points: int = 50000,
    seed: int = 42,
):
    if embedding_key not in adata.obsm:
        raise KeyError(f"Embedding key not found in adata.obsm: {embedding_key}")
    if color_col not in adata.obs.columns:
        raise KeyError(f"Color column not found in adata.obs: {color_col}")

    idx = _subsample_indices(adata.n_obs, max_points=max_points, seed=seed)
    sub = adata[idx].copy()

    sc.pp.neighbors(sub, use_rep=embedding_key, n_neighbors=15)
    sc.tl.umap(sub, random_state=seed)
    coords = np.asarray(sub.obsm["X_umap"], dtype=float)
    labels = sub.obs[color_col].astype(str).values

    uniq = np.unique(labels)
    cmap = plt.cm.get_cmap("tab20", max(len(uniq), 1))
    color_map = {lab: cmap(i % 20) for i, lab in enumerate(uniq)}

    plt.figure(figsize=(8, 6))
    for lab in uniq:
        mask = labels == lab
        plt.scatter(
            coords[mask, 0],
            coords[mask, 1],
            s=4,
            alpha=0.8,
            c=[color_map[lab]],
            label=lab,
            linewidths=0,
        )
    plt.xlabel("UMAP1")
    plt.ylabel("UMAP2")
    plt.title(title or f"UMAP colored by {color_col}")
    plt.legend(markerscale=2, fontsize=8, frameon=False, loc="best")
    _save_figure(output_path, dpi=200)


def plot_label_counts(
    adata: AnnData,
    label_col: str,
    output_path: str | Path,
    title: str | None = None,
):
    if label_col not in adata.obs.columns:
        raise KeyError(f"Label column not found in adata.obs: {label_col}")
    counts = adata.obs[label_col].astype(str).value_counts()

    plt.figure(figsize=(8, 4))
    plt.bar(counts.index, counts.values)
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Cells")
    plt.title(title or f"Counts by {label_col}")
    _save_figure(output_path, dpi=200)


def plot_confusion_matrix(
    cm_df: pd.DataFrame,
    output_path: str | Path,
    title: str | None = None,
):
    mat = cm_df.to_numpy(dtype=float)

    plt.figure(figsize=(7, 6))
    im = plt.imshow(mat, aspect="auto")
    plt.colorbar(im, fraction=0.046, pad=0.04)
    plt.xticks(np.arange(cm_df.shape[1]), cm_df.columns, rotation=45, ha="right")
    plt.yticks(np.arange(cm_df.shape[0]), cm_df.index)
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.title(title or "Confusion matrix")
    _save_figure(output_path, dpi=200)


def plot_per_class_f1(
    per_class_df: pd.DataFrame,
    output_path: str | Path,
    title: str | None = None,
):
    if "label" not in per_class_df.columns or "f1" not in per_class_df.columns:
        raise ValueError("per_class_df must contain 'label' and 'f1' columns.")

    plt.figure(figsize=(8, 4))
    plt.bar(per_class_df["label"].astype(str), per_class_df["f1"].astype(float))
    plt.xticks(rotation=45, ha="right")
    plt.ylim(0.0, 1.0)
    plt.ylabel("F1")
    plt.title(title or "Per-class F1")
    _save_figure(output_path, dpi=200)
