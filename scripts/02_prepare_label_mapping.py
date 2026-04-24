#!/usr/bin/env python
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from geneformer_immune_benchmark.constants import MAPPING_TEMPLATE_COLUMNS
from geneformer_immune_benchmark.io import ensure_dir


def main() -> None:
    summary_path = ROOT / "data" / "processed" / "h5ad_summaries.json"
    output_path = ROOT / "data" / "processed" / "label_mapping_draft.tsv"
    ensure_dir(output_path.parent)

    if not summary_path.exists():
        print(f"Missing summary file: {summary_path}")
        return

    with summary_path.open("r", encoding="utf-8") as f:
        summaries = json.load(f)

    rows = []
    for dataset_name, summary in summaries.items():
        label_top_values = summary.get("label_top_values", {})
        for label_col, values in label_top_values.items():
            for raw_label in values.keys():
                rows.append(
                    {
                        "dataset": dataset_name,
                        "raw_label": raw_label,
                        "harmonized_l1": "",
                        "harmonized_l2": "",
                        "harmonized_l3": "",
                        "confidence": "low",
                        "action": "review",
                        "notes": f"Detected from column '{label_col}'. Manual harmonization required.",
                    }
                )

    if not rows:
        print("No candidate label values found.")
        return

    draft = pd.DataFrame(rows).drop_duplicates(subset=["dataset", "raw_label"])
    draft = draft[MAPPING_TEMPLATE_COLUMNS]
    draft.to_csv(output_path, sep="\t", index=False)

    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
