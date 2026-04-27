#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import os
import re
from importlib.util import find_spec
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
CACHE_ROOT = Path("/tmp/scgip-lab-cache")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("NUMBA_CACHE_DIR", str(CACHE_ROOT / "numba"))
os.environ.setdefault("MPLCONFIGDIR", str(CACHE_ROOT / "matplotlib"))


def print_status(level: str, message: str) -> None:
    print(f"[{level}] {message}")


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_repo_path(path: str | Path) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return ROOT / p


def load_geneformer_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    if "geneformer" not in config:
        raise ValueError("Missing top-level key 'geneformer' in config YAML.")
    return config["geneformer"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tokenize local h5ad files and extract Geneformer cell embeddings."
    )
    parser.add_argument("--config", default="config/geneformer.example.yml")

    parser.add_argument("--tokenize", action="store_true")
    parser.add_argument("--extract-embeddings", action="store_true")

    parser.add_argument("--input-dir", default="data/raw")
    parser.add_argument("--input-file", default=None)
    parser.add_argument("--input-identifier", default="")
    parser.add_argument(
        "--count-col",
        default=None,
        help="Column to use as source for obs['n_counts'] if n_counts is missing (default: auto-detect).",
    )
    parser.add_argument(
        "--prepared-dir",
        default="data/processed/prepared_h5ad",
        help="Directory for auto-prepared h5ad files used for Geneformer tokenization.",
    )
    parser.add_argument(
        "--disable-auto-prepare",
        action="store_true",
        help="Disable auto-preparation of h5ad (n_counts / ensembl_id fixes).",
    )
    parser.add_argument("--tokenized-dir", default=None)
    parser.add_argument("--tokenized-prefix", default="pbmc_tokenized")
    parser.add_argument("--nproc", type=int, default=4)
    parser.add_argument("--model-version", choices=["V1", "V2"], default=None)
    parser.add_argument("--use-h5ad-index", action="store_true")
    parser.add_argument(
        "--cell-id-col",
        default="cell_id",
        help="obs column used as stable cell IDs during tokenization when available.",
    )

    parser.add_argument("--tokenized-dataset", default=None)
    parser.add_argument("--model-dir", default=None)
    parser.add_argument("--dataset-name", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--output-tag", default=None)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--max-cells", type=int, default=None)
    parser.add_argument("--embedding-layer", type=int, default=None)
    parser.add_argument("--cell-ids-from-h5ad", default=None)
    parser.add_argument("--allow-synthetic-cell-ids", action="store_true")
    return parser.parse_args()


def list_h5ad_files(input_dir: Path, identifier: str = "") -> list[Path]:
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {input_dir}")
    pattern = f"*{identifier}*.h5ad" if identifier else "*.h5ad"
    return sorted(input_dir.glob(pattern))


def _close_adata_handle(adata: ad.AnnData) -> None:
    if getattr(adata, "isbacked", False):
        try:
            adata.file.close()
        except Exception:
            pass


def _read_h5ad_obs_var_columns(path: Path) -> tuple[set[str], set[str]]:
    adata = ad.read_h5ad(path, backed="r")
    try:
        obs_cols = {str(c) for c in adata.obs.columns}
        var_cols = {str(c) for c in adata.var.columns}
    finally:
        _close_adata_handle(adata)
    return obs_cols, var_cols


def check_h5ad_schema(path: Path, use_h5ad_index: bool) -> tuple[bool, str]:
    try:
        obs_cols, var_cols = _read_h5ad_obs_var_columns(path)
    except Exception as exc:
        return False, f"Could not inspect {path.name}: {exc}"

    if "n_counts" not in obs_cols:
        return False, f"{path.name}: missing obs['n_counts'] required by Geneformer tokenizer."

    if not use_h5ad_index and "ensembl_id" not in var_cols:
        return False, (
            f"{path.name}: missing var['ensembl_id']. "
            "Use --use-h5ad-index only if var.index contains Ensembl IDs."
        )

    return True, "ok"


def is_ensembl_like(values: list[str], min_fraction: float = 0.9) -> bool:
    if not values:
        return False
    pattern = re.compile(r"^ENSG\d+")
    hits = sum(1 for v in values if pattern.match(v))
    return (hits / len(values)) >= min_fraction


def detect_count_source_column(obs_cols: list[str], preferred: str | None) -> str | None:
    if "n_counts" in obs_cols:
        return "n_counts"
    if preferred is not None and preferred in obs_cols:
        return preferred

    common = [
        "nCount_RNA",
        "total_counts",
        "nCount_SCT",
        "nCount",
        "umi_count",
        "umis",
    ]
    for c in common:
        if c in obs_cols:
            return c

    lowered = {c.lower(): c for c in obs_cols}
    for key in lowered:
        if "ncount" in key or "total_count" in key or ("umi" in key and "count" in key):
            return lowered[key]
    return None


def validate_prepared_h5ad(path: Path, use_h5ad_index: bool) -> bool:
    ok, _ = check_h5ad_schema(path, use_h5ad_index=use_h5ad_index)
    return ok


def prepare_single_h5ad_for_tokenizer(
    source_path: Path,
    prepared_dir: Path,
    use_h5ad_index: bool,
    preferred_count_col: str | None,
) -> Path:
    prepared_path = prepared_dir / source_path.name
    if prepared_path.exists() and prepared_path.stat().st_mtime >= source_path.stat().st_mtime:
        if validate_prepared_h5ad(prepared_path, use_h5ad_index):
            print_status("INFO", f"Reusing prepared h5ad: {prepared_path}")
            return prepared_path

    adata = ad.read_h5ad(source_path)
    changed = False

    obs_cols = [str(c) for c in adata.obs.columns]
    count_source = detect_count_source_column(obs_cols, preferred_count_col)
    if "n_counts" not in adata.obs.columns:
        if count_source is None:
            raise ValueError(
                f"{source_path.name}: missing obs['n_counts'] and no alternative count column detected."
            )
        adata.obs["n_counts"] = adata.obs[count_source].astype(float)
        changed = True
        print_status("INFO", f"{source_path.name}: added obs['n_counts'] from obs['{count_source}'].")

    if "ensembl_id" not in adata.var.columns:
        var_names = [str(v) for v in adata.var_names.tolist()]
        if use_h5ad_index or is_ensembl_like(var_names):
            adata.var["ensembl_id"] = var_names
            changed = True
            print_status("INFO", f"{source_path.name}: added var['ensembl_id'] from var_names.")
        else:
            raise ValueError(
                f"{source_path.name}: missing var['ensembl_id'] and var_names do not look like Ensembl IDs."
            )

    if changed:
        ensure_dir(prepared_dir)
        adata.write_h5ad(prepared_path)
        print_status("OK", f"Prepared h5ad written: {prepared_path}")
        return prepared_path

    return source_path


def has_obs_column(path: Path, column: str) -> bool:
    try:
        obs_cols, _ = _read_h5ad_obs_var_columns(path)
    except Exception:
        return False
    return column in obs_cols


def check_geneformer_ready(install_dir: Path) -> bool:
    required_modules = ["geneformer", "datasets", "torch", "transformers"]
    missing = [m for m in required_modules if find_spec(m) is None]
    if missing:
        print_status("ERROR", f"Missing Python modules: {', '.join(missing)}")
        print_status("INFO", "Run: bash scripts/setup_geneformer.sh")
        return False
    if not install_dir.exists():
        print_status("ERROR", f"Geneformer directory not found: {install_dir}")
        print_status("INFO", "Run: bash scripts/setup_geneformer.sh")
        return False
    return True


def normalize_emb_layer(layer: int) -> int:
    if layer in {-1, 0}:
        return layer
    if layer == -2:
        return -1
    raise ValueError(
        f"Unsupported embedding layer setting: {layer}. "
        "Use -2/-1 (second-to-last) or 0 (last layer for EmbExtractor)."
    )


def infer_dataset_name(args: argparse.Namespace, tokenized_dataset_path: Path) -> str:
    if args.dataset_name:
        return args.dataset_name
    if args.input_file:
        return Path(args.input_file).stem
    if args.cell_ids_from_h5ad:
        return Path(args.cell_ids_from_h5ad).stem
    return tokenized_dataset_path.stem


def choose_h5ad_source_for_ids(args: argparse.Namespace) -> Path | None:
    if args.cell_ids_from_h5ad:
        return resolve_repo_path(args.cell_ids_from_h5ad)
    if args.input_file:
        return resolve_repo_path(args.input_file)
    return None


def derive_cell_ids_from_h5ad(path: Path, expected_n: int) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"h5ad file for cell IDs not found: {path}")

    adata = ad.read_h5ad(path, backed="r")
    try:
        obs_names = pd.Index(adata.obs_names).astype(str)
        if len(obs_names) == expected_n:
            return obs_names.tolist()

        if "filter_pass" in adata.obs.columns:
            filter_pass = pd.Series(adata.obs["filter_pass"]).fillna(0).astype(int)
            filtered = obs_names[filter_pass.values == 1]
            if len(filtered) == expected_n:
                return filtered.tolist()

    finally:
        _close_adata_handle(adata)

    raise ValueError(
        f"Could not align cell IDs from {path}. "
        f"Expected {expected_n} rows but found neither full obs_names nor filter_pass subset with matching length."
    )


def resolve_embedding_matrix(emb_df: pd.DataFrame) -> np.ndarray:
    numeric_cols = [
        col for col in emb_df.columns if pd.api.types.is_numeric_dtype(emb_df[col])
    ]
    if not numeric_cols:
        raise ValueError("Could not find numeric embedding columns in Geneformer output.")
    matrix = emb_df[numeric_cols].to_numpy(dtype=np.float32)
    if matrix.ndim != 2:
        raise ValueError(f"Embedding matrix must be 2D, got shape {matrix.shape}")
    return matrix


def run_tokenization(
    args: argparse.Namespace,
    tokenized_dir: Path,
    model_version: str,
) -> Path:
    try:
        from geneformer import TranscriptomeTokenizer
    except Exception as exc:
        raise RuntimeError(f"Could not import TranscriptomeTokenizer: {exc}") from exc

    prepared_dir = resolve_repo_path(args.prepared_dir)

    if args.input_file:
        input_file = resolve_repo_path(args.input_file)
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        if args.disable_auto_prepare:
            working_file = input_file
        else:
            working_file = prepare_single_h5ad_for_tokenizer(
                source_path=input_file,
                prepared_dir=prepared_dir,
                use_h5ad_index=args.use_h5ad_index,
                preferred_count_col=args.count_col,
            )
        input_dir = working_file.parent
        input_identifier = args.input_identifier if args.input_identifier else working_file.stem
    else:
        input_dir = resolve_repo_path(args.input_dir)
        input_identifier = args.input_identifier

    h5ad_files = list_h5ad_files(input_dir, identifier=input_identifier)
    if not h5ad_files:
        raise FileNotFoundError(
            f"No .h5ad files found in {input_dir} with identifier '{input_identifier}'."
        )

    print_status("INFO", f"Tokenization input files: {len(h5ad_files)}")
    for f in h5ad_files:
        print_status("INFO", f" - {f}")
        ok, msg = check_h5ad_schema(f, args.use_h5ad_index)
        if not ok:
            raise ValueError(msg)

    custom_attr_name_dict = None
    if args.cell_id_col:
        if all(has_obs_column(f, args.cell_id_col) for f in h5ad_files):
            custom_attr_name_dict = {args.cell_id_col: "cell_id"}
            print_status(
                "INFO",
                f"Using obs column '{args.cell_id_col}' as stable 'cell_id' metadata during tokenization.",
            )
        else:
            print_status(
                "WARN",
                f"obs column '{args.cell_id_col}' not found in every input file. "
                "Tokenization will continue without explicit cell_id metadata.",
            )

    ensure_dir(tokenized_dir)
    tokenizer = TranscriptomeTokenizer(
        custom_attr_name_dict=custom_attr_name_dict,
        nproc=args.nproc,
        use_h5ad_index=args.use_h5ad_index,
        model_version=model_version,
    )
    tokenizer.tokenize_data(
        data_directory=str(input_dir),
        output_directory=str(tokenized_dir),
        output_prefix=args.tokenized_prefix,
        file_format="h5ad",
        input_identifier=input_identifier,
    )
    out_path = (tokenized_dir / args.tokenized_prefix).with_suffix(".dataset")
    print_status("OK", f"Tokenized dataset written: {out_path}")
    return out_path


def run_embedding_extraction(
    args: argparse.Namespace,
    geneformer_cfg: dict[str, Any],
    tokenized_dataset_path: Path,
    model_dir: Path,
    output_dir: Path,
    model_version: str,
) -> int:
    try:
        from datasets import load_from_disk
        from geneformer import EmbExtractor
        import torch
    except Exception as exc:
        print_status("ERROR", f"Missing extraction runtime dependency: {exc}")
        return 1

    if not torch.cuda.is_available():
        print_status(
            "ERROR",
            "No CUDA device detected. Upstream Geneformer EmbExtractor expects CUDA.",
        )
        print_status(
            "INFO",
            "Run embedding extraction on a CUDA-enabled machine, then copy .npy/.tsv files into data/processed/embeddings.",
        )
        return 1

    if not tokenized_dataset_path.exists():
        print_status("ERROR", f"Tokenized dataset not found: {tokenized_dataset_path}")
        return 1
    if not model_dir.exists():
        print_status("ERROR", f"Model directory not found: {model_dir}")
        return 1

    dataset_name = infer_dataset_name(args, tokenized_dataset_path)
    output_tag = args.output_tag or str(geneformer_cfg.get("output_tag", "geneformer_v1"))
    batch_size = (
        int(args.batch_size)
        if args.batch_size is not None
        else int(geneformer_cfg.get("batch_size", 8))
    )
    max_cells = (
        int(args.max_cells)
        if args.max_cells is not None
        else int(geneformer_cfg.get("max_cells_per_dataset", 10000))
    )
    raw_layer = (
        int(args.embedding_layer)
        if args.embedding_layer is not None
        else int(geneformer_cfg.get("embedding_layer", -2))
    )
    emb_layer = normalize_emb_layer(raw_layer)

    ensure_dir(output_dir)

    print_status("INFO", f"Loading tokenized dataset: {tokenized_dataset_path}")
    tokenized_ds = load_from_disk(str(tokenized_dataset_path))
    ds_features = list(tokenized_ds.features.keys())
    has_cell_id_feature = "cell_id" in ds_features
    print_status("INFO", f"Tokenized rows: {len(tokenized_ds)}")
    print_status("INFO", f"Tokenized features: {ds_features}")

    emb_label = ["cell_id"] if has_cell_id_feature else None
    if emb_label is None:
        print_status(
            "WARN",
            "Tokenized dataset has no 'cell_id' feature. Will try to recover IDs from input h5ad.",
        )

    extractor = EmbExtractor(
        model_type="Pretrained",
        num_classes=0,
        emb_mode="cell",
        max_ncells=max_cells,
        emb_layer=emb_layer,
        emb_label=emb_label,
        forward_batch_size=batch_size,
        nproc=args.nproc,
        model_version=model_version,
    )

    raw_prefix = f"{dataset_name}_{output_tag}_raw"
    print_status("INFO", "Running EmbExtractor (this may take time)...")
    try:
        emb_df = extractor.extract_embs(
            model_directory=str(model_dir),
            input_data_file=str(tokenized_dataset_path),
            output_directory=str(output_dir),
            output_prefix=raw_prefix,
            output_torch_embs=False,
        )
    except Exception as exc:
        print_status("ERROR", f"Embedding extraction failed: {exc}")
        return 1

    try:
        matrix = resolve_embedding_matrix(emb_df)
    except Exception as exc:
        print_status("ERROR", f"Could not build embedding matrix: {exc}")
        return 1

    cell_ids: list[str]
    if "cell_id" in emb_df.columns:
        cell_ids = emb_df["cell_id"].astype(str).tolist()
    else:
        h5ad_for_ids = choose_h5ad_source_for_ids(args)
        if h5ad_for_ids is not None:
            try:
                cell_ids = derive_cell_ids_from_h5ad(h5ad_for_ids, expected_n=matrix.shape[0])
                print_status("INFO", f"Recovered cell IDs from h5ad: {h5ad_for_ids}")
            except Exception as exc:
                print_status("ERROR", f"Could not recover cell IDs from h5ad: {exc}")
                return 1
        elif args.allow_synthetic_cell_ids:
            cell_ids = [f"tokenized_cell_{i:07d}" for i in range(matrix.shape[0])]
            print_status(
                "WARN",
                "Using synthetic cell IDs. These will not align to AnnData obs_names automatically.",
            )
        else:
            print_status(
                "ERROR",
                "No cell IDs found in tokenized data and no h5ad path was provided for recovery.",
            )
            print_status(
                "INFO",
                "Use --cell-ids-from-h5ad <path> or rerun tokenization with an obs cell_id column.",
            )
            return 1

    if len(cell_ids) != matrix.shape[0]:
        print_status(
            "ERROR",
            f"Cell ID count mismatch: {len(cell_ids)} vs embedding rows {matrix.shape[0]}",
        )
        return 1
    if len(set(cell_ids)) != len(cell_ids):
        print_status("ERROR", "Duplicate cell IDs detected after extraction.")
        return 1

    emb_path = output_dir / f"{dataset_name}_{output_tag}_embeddings.npy"
    ids_path = output_dir / f"{dataset_name}_cell_ids.tsv"
    summary_path = output_dir / f"{dataset_name}_{output_tag}_summary.json"

    np.save(emb_path, matrix)
    pd.DataFrame({"cell_id": cell_ids}).to_csv(ids_path, sep="\t", index=False)

    summary = {
        "dataset_name": dataset_name,
        "model_dir": str(model_dir),
        "tokenized_dataset": str(tokenized_dataset_path),
        "model_version": model_version,
        "embedding_tag": output_tag,
        "embedding_shape": [int(matrix.shape[0]), int(matrix.shape[1])],
        "batch_size": int(batch_size),
        "max_cells": int(max_cells),
        "embedding_layer_arg": int(raw_layer),
        "emb_extractor_layer": int(emb_layer),
        "cell_id_source": "tokenized_feature" if "cell_id" in emb_df.columns else "h5ad_or_synthetic",
        "output_files": {
            "embeddings_npy": str(emb_path),
            "cell_ids_tsv": str(ids_path),
            "raw_csv_from_emb_extractor": str((output_dir / raw_prefix).with_suffix(".csv")),
        },
    }
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print_status("OK", f"Saved embeddings: {emb_path}")
    print_status("OK", f"Saved cell IDs: {ids_path}")
    print_status("OK", f"Saved summary: {summary_path}")
    print_status(
        "INFO",
        "Expected by embedding probe: "
        f"{emb_path.name} and {ids_path.name}",
    )
    return 0


def main() -> int:
    args = parse_args()
    config_path = resolve_repo_path(args.config)

    print("Geneformer tokenization and embedding workflow")
    try:
        geneformer_cfg = load_geneformer_config(config_path)
    except Exception as exc:
        print_status("ERROR", f"Could not load config: {exc}")
        return 1

    install_dir = resolve_repo_path(geneformer_cfg.get("install_dir", "external/Geneformer"))
    model_dir = (
        resolve_repo_path(args.model_dir)
        if args.model_dir is not None
        else resolve_repo_path(geneformer_cfg.get("model_dir", "external/Geneformer"))
    )
    tokenized_dir = (
        resolve_repo_path(args.tokenized_dir)
        if args.tokenized_dir is not None
        else resolve_repo_path(geneformer_cfg.get("tokenized_dir", "data/processed/tokenized"))
    )
    output_dir = (
        resolve_repo_path(args.output_dir)
        if args.output_dir is not None
        else resolve_repo_path(geneformer_cfg.get("embeddings_dir", "data/processed/embeddings"))
    )
    model_version = (
        args.model_version if args.model_version is not None else str(geneformer_cfg.get("default_model_version", "V2"))
    )

    print_status("INFO", f"Config: {config_path}")
    print_status("INFO", f"Geneformer install dir: {install_dir}")
    print_status("INFO", f"Model dir: {model_dir}")
    print_status("INFO", f"Tokenized dir: {tokenized_dir}")
    print_status("INFO", f"Embeddings dir: {output_dir}")
    print_status("INFO", f"Model version: {model_version}")

    if not args.tokenize and not args.extract_embeddings:
        print_status("INFO", "No action selected.")
        print_status("INFO", "Use --tokenize, --extract-embeddings, or both.")
        return 0

    if not check_geneformer_ready(install_dir):
        return 1

    tokenized_dataset_path: Path | None = None
    if args.tokenize:
        try:
            tokenized_dataset_path = run_tokenization(
                args=args,
                tokenized_dir=tokenized_dir,
                model_version=model_version,
            )
        except Exception as exc:
            print_status("ERROR", f"Tokenization failed: {exc}")
            return 1

    if args.extract_embeddings:
        if args.tokenized_dataset is not None:
            tokenized_dataset_path = resolve_repo_path(args.tokenized_dataset)
        elif tokenized_dataset_path is None:
            tokenized_dataset_path = (tokenized_dir / args.tokenized_prefix).with_suffix(".dataset")

        return run_embedding_extraction(
            args=args,
            geneformer_cfg=geneformer_cfg,
            tokenized_dataset_path=tokenized_dataset_path,
            model_dir=model_dir,
            output_dir=output_dir,
            model_version=model_version,
        )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print_status("ERROR", f"Unexpected failure: {exc}")
        raise SystemExit(1)
