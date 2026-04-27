#!/usr/bin/env python
from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PREPROCESS_SCRIPT = ROOT / "scripts" / "03_extract_geneformer_embeddings.py"
PROBE_SCRIPT = ROOT / "experiments" / "01_embedding_probe" / "run_embedding_probe.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Experiment 01 orchestrator: optional Geneformer preprocessing "
            "(tokenize/extract embeddings) + embedding probe run."
        )
    )

    parser.add_argument("--h5ad", default=None, help="Path to one input .h5ad file.")
    parser.add_argument("--dataset-name", default=None)
    parser.add_argument("--label-col", default=None)

    parser.add_argument(
        "--config",
        default="experiments/01_embedding_probe/config.yml",
        help="Config for run_embedding_probe.py",
    )
    parser.add_argument(
        "--geneformer-config",
        default="config/geneformer.example.yml",
        help="Config for 03_extract_geneformer_embeddings.py",
    )

    parser.add_argument(
        "--prepare",
        action="store_true",
        help="Shortcut for --tokenize --extract-embeddings",
    )
    parser.add_argument("--tokenize", action="store_true")
    parser.add_argument("--extract-embeddings", action="store_true")
    parser.add_argument(
        "--preprocess-only",
        action="store_true",
        help="Run preprocessing steps and stop before the embedding probe.",
    )

    parser.add_argument("--tokenized-prefix", default=None)
    parser.add_argument("--model-version", choices=["V1", "V2"], default=None)
    parser.add_argument("--use-h5ad-index", action="store_true")
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--max-cells", type=int, default=None)
    parser.add_argument("--embedding-layer", type=int, default=None)

    parser.add_argument("--skip-classifier", action="store_true")
    parser.add_argument("--save-extra-plots", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def print_cmd(cmd: list[str]) -> None:
    print("[RUN] " + shlex.join(cmd))


def run_cmd(cmd: list[str]) -> int:
    print_cmd(cmd)
    proc = subprocess.run(cmd)
    return int(proc.returncode)


def infer_prefix(args: argparse.Namespace) -> str:
    if args.tokenized_prefix:
        return args.tokenized_prefix
    if args.dataset_name:
        return args.dataset_name
    if args.h5ad:
        return Path(args.h5ad).stem
    return "pbmc_tokenized"


def maybe_run_preprocessing(args: argparse.Namespace) -> int:
    do_tokenize = args.tokenize or args.prepare
    do_extract = args.extract_embeddings or args.prepare
    if not do_tokenize and not do_extract:
        return 0

    cmd = [
        sys.executable,
        str(PREPROCESS_SCRIPT),
        "--config",
        args.geneformer_config,
    ]
    if do_tokenize:
        cmd.append("--tokenize")
    if do_extract:
        cmd.append("--extract-embeddings")

    tokenized_prefix = infer_prefix(args)
    cmd += ["--tokenized-prefix", tokenized_prefix]

    if args.h5ad:
        cmd += ["--input-file", args.h5ad]
    if args.dataset_name:
        cmd += ["--dataset-name", args.dataset_name]
    if args.model_version:
        cmd += ["--model-version", args.model_version]
    if args.use_h5ad_index:
        cmd.append("--use-h5ad-index")
    if args.batch_size is not None:
        cmd += ["--batch-size", str(args.batch_size)]
    if args.max_cells is not None:
        cmd += ["--max-cells", str(args.max_cells)]
    if args.embedding_layer is not None:
        cmd += ["--embedding-layer", str(args.embedding_layer)]

    return run_cmd(cmd)


def run_probe(args: argparse.Namespace) -> int:
    cmd = [
        sys.executable,
        str(PROBE_SCRIPT),
        "--config",
        args.config,
    ]
    if args.h5ad:
        cmd += ["--h5ad", args.h5ad]
    if args.dataset_name:
        cmd += ["--dataset-name", args.dataset_name]
    if args.label_col:
        cmd += ["--label-col", args.label_col]
    if args.skip_classifier:
        cmd.append("--skip-classifier")
    if args.save_extra_plots:
        cmd.append("--save-extra-plots")
    if args.dry_run:
        cmd.append("--dry-run")
    return run_cmd(cmd)


def main() -> int:
    args = parse_args()

    if not PREPROCESS_SCRIPT.exists():
        print(f"[ERROR] Missing preprocessing script: {PREPROCESS_SCRIPT}")
        return 1
    if not PROBE_SCRIPT.exists():
        print(f"[ERROR] Missing probe script: {PROBE_SCRIPT}")
        return 1

    rc = maybe_run_preprocessing(args)
    if rc != 0:
        print(f"[ERROR] Preprocessing step failed with exit code {rc}")
        return rc

    if args.preprocess_only:
        print("[OK] Preprocessing finished (--preprocess-only).")
        return 0

    rc = run_probe(args)
    if rc != 0:
        print(f"[ERROR] Embedding probe failed with exit code {rc}")
        return rc

    print("[OK] Experiment 01 pipeline completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
