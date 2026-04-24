from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import scanpy as sc
from anndata import AnnData
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def load_embedding_matrix(path: str | Path) -> np.ndarray:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Embedding file not found: {p}")
    if p.suffix.lower() != ".npy":
        raise ValueError(f"Expected .npy embedding matrix, got: {p}")
    arr = np.load(p)
    if arr.ndim != 2:
        raise ValueError(f"Expected 2D embedding matrix, got shape {arr.shape}")
    return arr


def align_embeddings_to_obs(adata: AnnData, embeddings: np.ndarray | pd.DataFrame) -> np.ndarray:
    if isinstance(embeddings, pd.DataFrame):
        missing = set(adata.obs_names) - set(embeddings.index)
        if missing:
            raise ValueError(f"Missing embeddings for {len(missing)} cells.")
        return embeddings.loc[adata.obs_names].to_numpy()

    if embeddings.shape[0] != adata.n_obs:
        raise ValueError(
            f"Embedding rows ({embeddings.shape[0]}) do not match adata.n_obs ({adata.n_obs})."
        )
    return embeddings


def compute_umap_from_embeddings(adata: AnnData, embedding_key: str) -> AnnData:
    if embedding_key not in adata.obsm:
        raise KeyError(f"Embedding key not found in adata.obsm: {embedding_key}")
    sc.pp.neighbors(adata, use_rep=embedding_key)
    sc.tl.umap(adata)
    return adata


def train_logistic_regression_classifier(X_train: np.ndarray, y_train: np.ndarray):
    clf = make_pipeline(
        StandardScaler(with_mean=True),
        LogisticRegression(
            max_iter=2000,
            multi_class="auto",
            n_jobs=None,
        ),
    )
    clf.fit(X_train, y_train)
    return clf
