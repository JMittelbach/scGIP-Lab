from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from anndata import AnnData


def check_geneformer_installation() -> dict[str, bool]:
    modules = ["transformers", "datasets", "torch", "geneformer"]
    status = {}
    for module in modules:
        status[module] = importlib.util.find_spec(module) is not None
    return status


def prepare_geneformer_input(adata: AnnData) -> AnnData:
    if adata.n_obs == 0 or adata.n_vars == 0:
        raise ValueError("AnnData is empty; cannot prepare Geneformer input.")
    if not adata.obs_names.is_unique:
        raise ValueError("adata.obs_names must be unique for stable cell mapping.")
    return adata


def tokenize_with_geneformer(adata: AnnData, output_dir: str | Path) -> Any:
    _ = (adata, output_dir)
    raise NotImplementedError("Tokenization is not implemented.")


def extract_geneformer_cell_embeddings(
    tokenized_dataset: Any,
    model_path: str,
    output_path: str | Path,
) -> Path:
    _ = (tokenized_dataset, model_path)
    out = Path(output_path)
    raise NotImplementedError(f"Embedding extraction is not implemented: {out}")
