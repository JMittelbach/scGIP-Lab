#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/scgip-lab-cache/numba")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/scgip-lab-cache/matplotlib")
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scgip_lab.embeddings import (
    attach_embeddings_to_adata,
    get_embedding_matrix,
    load_embedding_files,
    subsample_adata,
)
from scgip_lab.evaluation import knn_label_purity, train_test_logistic_probe
from scgip_lab.io import (
    detect_candidate_label_columns,
    ensure_dir,
    find_h5ad_files,
    read_h5ad,
    write_json,
    write_tsv,
)
from scgip_lab.labels import add_pbmc_broad_label, choose_label_column, summarize_label_counts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="experiments/01_embedding_probe/config.yml",
    )
    parser.add_argument("--h5ad", default=None)
    parser.add_argument("--label-col", default=None)
    parser.add_argument("--dataset-name", default=None)
    parser.add_argument("--skip-classifier", action="store_true")
    parser.add_argument("--save-extra-plots", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def load_config(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_h5ad_files(args: argparse.Namespace, cfg: dict) -> list[Path]:
    if args.h5ad is not None:
        p = Path(args.h5ad)
        if not p.exists():
            raise FileNotFoundError(f"h5ad file not found: {p}")
        return [p]

    input_dir = ROOT / cfg["paths"]["input_h5ad_dir"]
    return find_h5ad_files(input_dir)


def infer_dataset_name(path: Path, override: str | None = None) -> str:
    return override if override is not None else path.stem


def expected_embedding_paths(cfg: dict, dataset: str) -> tuple[Path, Path]:
    emb = ROOT / cfg["paths"]["embeddings_dir"] / cfg["embedding"]["file_pattern"].format(
        dataset=dataset
    )
    cell_ids = (
        ROOT
        / cfg["paths"]["embeddings_dir"]
        / cfg["embedding"]["cell_id_pattern"].format(dataset=dataset)
    )
    return emb, cell_ids


def print_dry_run_plan(files: list[Path], cfg: dict, args: argparse.Namespace) -> None:
    output_dir = ROOT / cfg["paths"]["output_dir"]
    print("Dry run:")
    print("Input h5ad files:")
    for path in files:
        print(f"- {path}")
        adata = read_h5ad(path)
        candidates = detect_candidate_label_columns(adata)
        dataset = infer_dataset_name(path, args.dataset_name)
        emb_path, ids_path = expected_embedding_paths(cfg, dataset)
        print(f"  candidate label columns: {candidates}")
        print(f"  expected embedding file: {emb_path}")
        print(f"  expected cell-id file: {ids_path}")

    print("Outputs:")
    print(f"- {output_dir / 'figures/01_umap_geneformer_broad_label.png'}")
    print(f"- {output_dir / 'figures/02_umap_geneformer_dataset.png'}")
    print(f"- {output_dir / 'figures/03_confusion_matrix_geneformer_broad_label.png'}")
    print(f"- {output_dir / 'metrics/embedding_probe_metrics.json'}")
    print(f"- {output_dir / 'metrics/per_class_f1.tsv'}")
    print(f"- {output_dir / 'logs/run_summary.json'}")


def load_and_prepare_dataset(
    h5ad_path: Path,
    cfg: dict,
    args: argparse.Namespace,
) -> tuple[ad.AnnData, dict]:
    dataset_name = infer_dataset_name(h5ad_path, args.dataset_name)
    adata = read_h5ad(h5ad_path)

    dataset_col = cfg["adata"]["dataset_col"]
    broad_col = cfg["adata"]["broad_label_col"]

    if dataset_col not in adata.obs.columns:
        adata.obs[dataset_col] = dataset_name
    else:
        adata.obs[dataset_col] = adata.obs[dataset_col].astype(str).fillna(dataset_name)

    selected_label_col = (
        args.label_col
        if args.label_col is not None
        else cfg["adata"].get("raw_label_col", None)
    )
    selected_label_col = choose_label_column(adata, selected_label_col)

    adata.obs["cell_type_original"] = adata.obs[selected_label_col].astype(str).values
    add_pbmc_broad_label(adata, raw_label_col="cell_type_original", output_col=broad_col)

    max_cells = int(cfg["filtering"]["max_cells_per_dataset"])
    adata = subsample_adata(
        adata,
        max_cells=max_cells,
        seed=int(cfg["experiment"]["random_seed"]),
        stratify_col=broad_col,
    )

    emb_path, ids_path = expected_embedding_paths(cfg, dataset_name)
    if not emb_path.exists() or not ids_path.exists():
        raise FileNotFoundError(
            f"Missing Geneformer embeddings for dataset '{dataset_name}'. "
            f"Expected files: {emb_path}, {ids_path}. "
            "Run preprocessing first:\n"
            "  1) bash scripts/setup_geneformer.sh\n"
            "  2) python scripts/03_extract_geneformer_embeddings.py --tokenize\n"
            "  3) generate embeddings and cell-id TSV into data/processed/embeddings/"
        )

    embeddings, cell_ids = load_embedding_files(emb_path, ids_path)
    attach_embeddings_to_adata(
        adata,
        embeddings=embeddings,
        cell_ids=cell_ids,
        embedding_key=cfg["embedding"]["key"],
    )

    info = {
        "dataset_name": dataset_name,
        "h5ad_file": str(h5ad_path),
        "selected_raw_label_col": selected_label_col,
        "n_cells_after_subsample": int(adata.n_obs),
        "broad_label_counts": adata.obs[broad_col].astype(str).value_counts().to_dict(),
    }
    return adata, info


def main() -> int:
    args = parse_args()
    cfg = load_config(ROOT / args.config)

    files = get_h5ad_files(args, cfg)
    if not files:
        print("No .h5ad files found.")
        return 1
    if args.dataset_name is not None and len(files) > 1 and args.h5ad is None:
        print("[ERROR] --dataset-name can only be used with one input file.")
        return 1

    if args.dry_run:
        print_dry_run_plan(files, cfg, args)
        return 0

    output_dir = ROOT / cfg["paths"]["output_dir"]
    figures_dir = ensure_dir(output_dir / "figures")
    metrics_dir = ensure_dir(output_dir / "metrics")
    logs_dir = ensure_dir(output_dir / "logs")

    prepared: list[ad.AnnData] = []
    dataset_infos: list[dict] = []
    broad_col = cfg["adata"]["broad_label_col"]
    dataset_col = cfg["adata"]["dataset_col"]
    embedding_key = cfg["embedding"]["key"]
    random_seed = int(cfg["experiment"]["random_seed"])

    for h5ad_path in files:
        try:
            adata_i, info_i = load_and_prepare_dataset(h5ad_path, cfg, args)
        except FileNotFoundError as exc:
            print(f"[ERROR] {exc}")
            return 1
        except (KeyError, ValueError) as exc:
            print(f"[ERROR] Failed while preparing {h5ad_path.name}: {exc}")
            return 1

        prepared.append(adata_i)
        dataset_infos.append(info_i)

    if len(prepared) == 1:
        adata = prepared[0]
    else:
        adata = ad.concat(prepared, join="outer", merge="first", index_unique=None)

    exclude_labels = set(cfg["filtering"].get("exclude_broad_labels", []))
    min_cells_per_label = int(cfg["filtering"]["min_cells_per_label"])

    labels = adata.obs[broad_col].astype(str)
    counts_pre = labels.value_counts()
    keep = ~labels.isin(exclude_labels)

    for label, count in counts_pre.items():
        if int(count) < min_cells_per_label:
            keep &= labels != label

    adata = adata[keep].copy()
    broad_counts = adata.obs[broad_col].astype(str).value_counts()

    unknown_frac = float(
        (adata.obs[broad_col].astype(str) == "UNKNOWN").mean() if adata.n_obs > 0 else 0.0
    )
    if unknown_frac > 0.3:
        print("[WARN] More than 30% of labels are UNKNOWN after mapping.")

    if adata.n_obs == 0:
        print("[ERROR] No cells remain after label filtering.")
        return 1

    from scgip_lab.plotting import (
        plot_confusion_matrix,
        plot_label_counts,
        plot_per_class_f1,
        plot_umap_from_embedding,
    )

    plot_umap_from_embedding(
        adata,
        embedding_key=embedding_key,
        color_col=broad_col,
        output_path=figures_dir / "01_umap_geneformer_broad_label.png",
        title="Geneformer UMAP by broad PBMC label",
        max_points=int(cfg["plots"]["max_points_umap"]),
        seed=random_seed,
    )
    plot_umap_from_embedding(
        adata,
        embedding_key=embedding_key,
        color_col=dataset_col,
        output_path=figures_dir / "02_umap_geneformer_dataset.png",
        title="Geneformer UMAP by dataset",
        max_points=int(cfg["plots"]["max_points_umap"]),
        seed=random_seed,
    )

    if args.save_extra_plots:
        plot_umap_from_embedding(
            adata,
            embedding_key=embedding_key,
            color_col="cell_type_original",
            output_path=figures_dir / "umap_geneformer_original_label.png",
            title="Geneformer UMAP by original label",
            max_points=int(cfg["plots"]["max_points_umap"]),
            seed=random_seed,
        )
        plot_label_counts(
            adata,
            label_col=broad_col,
            output_path=figures_dir / "label_counts_broad_label.png",
            title="Broad PBMC label counts",
        )

    X = get_embedding_matrix(adata, embedding_key=embedding_key)
    y = adata.obs[broad_col].astype(str).values
    purity = knn_label_purity(
        X,
        y,
        k=15,
        max_cells=10000,
        seed=random_seed,
    )

    classifier_name = "skipped" if args.skip_classifier else "logistic_regression"
    probe_metrics: dict[str, float] = {
        "accuracy": float("nan"),
        "balanced_accuracy": float("nan"),
        "macro_f1": float("nan"),
        "weighted_f1": float("nan"),
        "number_of_cells_used": int(len(y)),
        "number_of_labels_used": int(len(np.unique(y))),
    }
    per_class_df = pd.DataFrame(columns=["label", "precision", "recall", "f1", "support"])

    if not args.skip_classifier:
        try:
            probe_metrics, per_class_df, cm_df = train_test_logistic_probe(
                X,
                y,
                test_size=float(cfg["classifier"]["test_size"]),
                seed=random_seed,
                class_weight=cfg["classifier"]["class_weight"],
                max_iter=int(cfg["classifier"]["max_iter"]),
            )
            plot_confusion_matrix(
                cm_df,
                output_path=figures_dir / "03_confusion_matrix_geneformer_broad_label.png",
                title="Confusion matrix (broad PBMC labels)",
            )
            if args.save_extra_plots:
                plot_per_class_f1(
                    per_class_df,
                    output_path=figures_dir / "per_class_f1_broad_label.png",
                    title="Per-class F1 (broad PBMC labels)",
                )
        except ValueError as exc:
            print(f"[WARN] Classifier skipped: {exc}")
            classifier_name = "skipped_not_enough_labels"

    metrics_json = {
        "dataset_names": [info["dataset_name"] for info in dataset_infos],
        "n_datasets": len(dataset_infos),
        "n_cells_total_after_filtering": int(adata.n_obs),
        "n_cells_used_for_classifier": int(probe_metrics.get("number_of_cells_used", 0)),
        "broad_label_counts": {str(k): int(v) for k, v in broad_counts.items()},
        "accuracy": probe_metrics.get("accuracy"),
        "balanced_accuracy": probe_metrics.get("balanced_accuracy"),
        "macro_f1": probe_metrics.get("macro_f1"),
        "weighted_f1": probe_metrics.get("weighted_f1"),
        "knn_label_purity": float(purity),
        "classifier": classifier_name,
        "embedding_key": embedding_key,
        "random_seed": random_seed,
    }
    write_json(metrics_json, metrics_dir / "embedding_probe_metrics.json")
    write_tsv(per_class_df, metrics_dir / "per_class_f1.tsv")

    run_summary = {
        "experiment": cfg["experiment"]["name"],
        "dataset_infos": dataset_infos,
        "broad_label_counts": summarize_label_counts(adata, [broad_col]).get(broad_col, {}),
        "unknown_fraction_after_filtering": unknown_frac,
        "outputs": {
            "figures": [
                str(figures_dir / "01_umap_geneformer_broad_label.png"),
                str(figures_dir / "02_umap_geneformer_dataset.png"),
                str(figures_dir / "03_confusion_matrix_geneformer_broad_label.png"),
            ],
            "metrics_json": str(metrics_dir / "embedding_probe_metrics.json"),
            "per_class_f1_tsv": str(metrics_dir / "per_class_f1.tsv"),
        },
    }
    write_json(run_summary, logs_dir / "run_summary.json")

    print("[OK] Experiment 01 completed.")
    print(f"[OK] Metrics: {metrics_dir / 'embedding_probe_metrics.json'}")
    print(f"[OK] Summary: {logs_dir / 'run_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
