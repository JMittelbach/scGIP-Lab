#!/usr/bin/env python
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from geneformer_immune_benchmark.io import (
    detect_candidate_batch_columns,
    detect_candidate_label_columns,
    ensure_dir,
    read_h5ad,
    summarize_adata,
    write_json,
)


def main() -> None:
    raw_dir = ROOT / "data" / "raw"
    out_path = ROOT / "data" / "processed" / "h5ad_summaries.json"
    ensure_dir(out_path.parent)

    files = sorted(raw_dir.glob("*.h5ad"))
    if not files:
        print(f"No .h5ad files found in {raw_dir}")
        write_json({}, out_path)
        return

    all_summaries = {}
    for h5ad_file in files:
        print(f"\n=== {h5ad_file.name} ===")
        adata = read_h5ad(h5ad_file)
        summary = summarize_adata(adata)
        all_summaries[h5ad_file.name] = summary

        print(f"cells: {summary['n_cells']}")
        print(f"genes: {summary['n_genes']}")
        print(f"obs columns: {summary['obs_columns']}")

        label_cols = detect_candidate_label_columns(adata)
        batch_cols = detect_candidate_batch_columns(adata)
        print(f"likely label columns: {label_cols}")
        print(f"likely batch/donor/dataset columns: {batch_cols}")

        for col in label_cols:
            top = adata.obs[col].astype(str).value_counts(dropna=False).head(20)
            print(f"top values for '{col}' (up to 20):")
            for k, v in top.items():
                print(f"  - {k}: {v}")

    write_json(all_summaries, out_path)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
