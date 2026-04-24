from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_distances


def define_marker_gene_sets(marker_config: dict) -> dict[str, list[str]]:
    marker_sets = {}
    for key, genes in marker_config.items():
        marker_sets[str(key)] = [str(g).upper() for g in genes]
    return marker_sets


def compute_embedding_shift(
    original_embeddings: np.ndarray,
    perturbed_embeddings: np.ndarray,
    metric: str = "cosine",
) -> np.ndarray:
    orig = np.asarray(original_embeddings, dtype=float)
    pert = np.asarray(perturbed_embeddings, dtype=float)
    if orig.shape != pert.shape:
        raise ValueError(f"Shape mismatch: original={orig.shape}, perturbed={pert.shape}")

    if metric == "cosine":
        return np.diag(cosine_distances(orig, pert))
    if metric == "euclidean":
        return np.linalg.norm(orig - pert, axis=1)
    raise ValueError("Unsupported metric. Use 'cosine' or 'euclidean'.")


def summarize_perturbation_by_cell_type(
    shift_scores: np.ndarray,
    cell_types,
) -> pd.DataFrame:
    scores = np.asarray(shift_scores, dtype=float)
    labels = pd.Series(cell_types).astype(str)
    if len(scores) != len(labels):
        raise ValueError("shift_scores and cell_types must have equal length.")

    df = pd.DataFrame({"cell_type": labels, "shift_score": scores})
    summary = (
        df.groupby("cell_type")["shift_score"]
        .agg(["count", "mean", "median", "std", "min", "max"])
        .reset_index()
        .sort_values("mean", ascending=False)
    )
    return summary
