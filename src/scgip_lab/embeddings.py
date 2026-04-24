from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from anndata import AnnData


def load_embedding_files(
    embedding_path: str | Path,
    cell_id_path: str | Path,
) -> tuple[np.ndarray, list[str]]:
    emb_path = Path(embedding_path)
    ids_path = Path(cell_id_path)

    if not emb_path.exists():
        raise FileNotFoundError(f"Embedding file not found: {emb_path}")
    if not ids_path.exists():
        raise FileNotFoundError(f"Cell ID file not found: {ids_path}")

    embeddings = np.load(emb_path)
    if embeddings.ndim != 2:
        raise ValueError(f"Embedding matrix must be 2D, got shape {embeddings.shape}")

    cell_df = pd.read_csv(ids_path, sep="\t")
    if "cell_id" not in cell_df.columns:
        raise ValueError(f"Cell ID table must contain a 'cell_id' column: {ids_path}")

    cell_ids = cell_df["cell_id"].astype(str).tolist()
    if embeddings.shape[0] != len(cell_ids):
        raise ValueError(
            "Embedding rows and cell IDs differ: "
            f"{embeddings.shape[0]} vs {len(cell_ids)}"
        )
    return embeddings, cell_ids


def attach_embeddings_to_adata(
    adata: AnnData,
    embeddings: np.ndarray,
    cell_ids: list[str],
    embedding_key: str = "X_geneformer",
) -> AnnData:
    if embeddings.shape[0] != len(cell_ids):
        raise ValueError(
            "Embedding rows and cell IDs differ: "
            f"{embeddings.shape[0]} vs {len(cell_ids)}"
        )

    id_to_idx: dict[str, int] = {}
    for idx, cell_id in enumerate(cell_ids):
        if cell_id in id_to_idx:
            raise ValueError(f"Duplicate cell_id in embedding file: {cell_id}")
        id_to_idx[cell_id] = idx

    obs_ids = [str(x) for x in adata.obs_names]
    matching = sum(1 for cell_id in obs_ids if cell_id in id_to_idx)
    if matching != adata.n_obs:
        raise ValueError(
            "Embedding/cell ID alignment failed. "
            f"AnnData cells: {adata.n_obs}, "
            f"embedding rows: {embeddings.shape[0]}, "
            f"matching cell IDs: {matching}"
        )

    aligned = np.vstack([embeddings[id_to_idx[cell_id]] for cell_id in obs_ids])
    adata.obsm[embedding_key] = aligned
    return adata


def subsample_adata(
    adata: AnnData,
    max_cells: int,
    seed: int = 42,
    stratify_col: str | None = None,
) -> AnnData:
    if max_cells <= 0 or adata.n_obs <= max_cells:
        return adata

    rng = np.random.default_rng(seed)
    all_idx = np.arange(adata.n_obs)

    if stratify_col is None or stratify_col not in adata.obs.columns:
        selected = np.sort(rng.choice(all_idx, size=max_cells, replace=False))
        return adata[selected].copy()

    labels = adata.obs[stratify_col].astype(str).fillna("NA")
    groups: dict[str, np.ndarray] = {
        str(lbl): np.where(labels.values == lbl)[0] for lbl in labels.unique()
    }

    selected_parts: list[np.ndarray] = []
    for _, idxs in groups.items():
        quota = max(1, int(round((len(idxs) / adata.n_obs) * max_cells)))
        k = min(len(idxs), quota)
        selected_parts.append(rng.choice(idxs, size=k, replace=False))

    selected = np.concatenate(selected_parts) if selected_parts else np.array([], dtype=int)
    selected = np.unique(selected)

    if len(selected) > max_cells:
        selected = np.sort(rng.choice(selected, size=max_cells, replace=False))
    elif len(selected) < max_cells:
        remaining = np.setdiff1d(all_idx, selected, assume_unique=False)
        extra_n = min(max_cells - len(selected), len(remaining))
        if extra_n > 0:
            extra = rng.choice(remaining, size=extra_n, replace=False)
            selected = np.sort(np.concatenate([selected, extra]))

    return adata[selected].copy()


def get_embedding_matrix(adata: AnnData, embedding_key: str = "X_geneformer") -> np.ndarray:
    if embedding_key not in adata.obsm:
        raise KeyError(f"Embedding key not found in adata.obsm: {embedding_key}")
    return np.asarray(adata.obsm[embedding_key], dtype=float)

