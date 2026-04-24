#!/usr/bin/env python
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scgip_lab.io import (
    detect_candidate_label_columns,
    find_h5ad_files,
    read_h5ad,
    summarize_adata,
    write_json,
    write_tsv,
)


def main() -> None:
    input_dir = ROOT / "data" / "raw"
    out_json = ROOT / "data" / "processed" / "h5ad_summary.json"
    out_tsv = ROOT / "data" / "processed" / "h5ad_summary.tsv"

    files = find_h5ad_files(input_dir)
    if not files:
        print(f"No .h5ad files found in {input_dir}")
        try:
            write_json({}, out_json)
            write_tsv(pd.DataFrame(), out_tsv)
        except PermissionError as exc:
            print(f"[WARN] Could not write summary outputs: {exc}")
        return

    summary_dict: dict[str, dict] = {}
    tsv_rows: list[dict] = []

    for path in files:
        adata = read_h5ad(path)
        summary = summarize_adata(adata, dataset_name=path.stem)
        summary_dict[path.name] = summary

        print(f"\n=== {path.name} ===")
        print(f"cells: {summary['n_cells']}")
        print(f"genes: {summary['n_genes']}")
        print(f"obs columns: {summary['obs_columns']}")
        print(f"candidate label columns: {summary['candidate_label_columns']}")
        print(f"candidate batch columns: {summary['candidate_batch_columns']}")

        for col in detect_candidate_label_columns(adata):
            print(f"top 20 for '{col}':")
            top_values = summary["label_top_values"].get(col, {})
            for value, count in top_values.items():
                print(f"  - {value}: {count}")

        tsv_rows.append(
            {
                "file_name": path.name,
                "dataset_name": path.stem,
                "n_cells": summary["n_cells"],
                "n_genes": summary["n_genes"],
                "candidate_label_columns": ";".join(summary["candidate_label_columns"]),
                "candidate_batch_columns": ";".join(summary["candidate_batch_columns"]),
            }
        )

    try:
        write_json(summary_dict, out_json)
        write_tsv(pd.DataFrame(tsv_rows), out_tsv)
    except PermissionError as exc:
        print(f"[ERROR] Could not write summary outputs: {exc}")
        return
    print(f"\nSaved: {out_json}")
    print(f"Saved: {out_tsv}")


if __name__ == "__main__":
    main()
