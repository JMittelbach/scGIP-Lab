"""Lightweight placeholders for Geneformer integration.

These helpers intentionally avoid heavy model loading/training in this scaffold.
Install and configure Geneformer separately before replacing TODO placeholders.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from anndata import AnnData


def check_geneformer_installation() -> dict[str, bool]:
    """Check whether core modules for future Geneformer workflow are importable.

    Note:
    - The canonical Geneformer workflow may require package installation from
      Hugging Face or a local clone.
    - This function only reports basic availability and does not run model code.
    """
    modules = ["transformers", "datasets", "torch", "geneformer"]
    status = {}
    for module in modules:
        status[module] = importlib.util.find_spec(module) is not None
    return status


def prepare_geneformer_input(adata: AnnData) -> AnnData:
    """Validate minimal AnnData requirements before tokenization.

    TODO:
    - Add normalization/ranking logic compatible with Geneformer expectations.
    - Add explicit checks for gene identifier conventions.
    """
    if adata.n_obs == 0 or adata.n_vars == 0:
        raise ValueError("AnnData is empty; cannot prepare Geneformer input.")
    if not adata.obs_names.is_unique:
        raise ValueError("adata.obs_names must be unique for stable cell mapping.")
    return adata


def tokenize_with_geneformer(adata: AnnData, output_dir: str | Path) -> Any:
    """Placeholder for Geneformer tokenization.

    Expected future workflow:
    1. Convert AnnData into Geneformer-compatible ranked gene-token inputs.
    2. Run Geneformer tokenizer.
    3. Persist tokenized dataset under output_dir.

    TODO: Replace with actual Geneformer tokenization call.
    """
    _ = (adata, output_dir)
    raise NotImplementedError(
        "TODO: Implement tokenization with Geneformer after installing required package/resources."
    )


def extract_geneformer_cell_embeddings(
    tokenized_dataset: Any,
    model_path: str,
    output_path: str | Path,
) -> Path:
    """Placeholder for embedding extraction from pretrained Geneformer.

    TODO:
    - Load pretrained Geneformer model from local path or Hugging Face model id.
    - Run forward pass on tokenized cells.
    - Save embedding matrix to output_path.
    """
    _ = (tokenized_dataset, model_path)
    out = Path(output_path)
    raise NotImplementedError(
        f"TODO: Implement extraction and write embeddings to {out}."
    )
