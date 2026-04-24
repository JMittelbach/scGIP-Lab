a. Für Experiment 1 sollten wir nicht zehn Tabellen und acht Plots produzieren. Besser: wenige Outputs, aber sauber interpretierbar.

Ich würde den Output auf 3 Plots + 2 Tabellen/JSONs begrenzen:

results/
  figures/
    01_umap_geneformer_broad_label.png
    02_umap_geneformer_dataset.png
    03_confusion_matrix_geneformer_broad_label.png
  metrics/
    embedding_probe_metrics.json
    per_class_f1.tsv
  logs/
    run_summary.json

Damit hast du alles Wesentliche:

Output	Aussage
UMAP nach broad label	Trennt Geneformer PBMC-Zelltypen?
UMAP nach Dataset	Clustert es biologisch oder nur nach Dataset?
Confusion Matrix	Welche Zelltypen sind linear trennbar/verwechselt?
metrics JSON	zentrale Kennzahlen: accuracy, macro-F1, balanced accuracy, kNN purity
per-class F1	welche Zelltypen funktionieren gut/schlecht

Hier ist der angepasste Codex-Prompt:

You are working in the repository:

scgip-lab

Project title:
scGIP-Lab: single-cell Geneformer Immune Probing Lab

Focus only on Experiment 01.

Experiment 01 title:
Geneformer Embedding Probe

Main scientific question:
Do pretrained Geneformer cell embeddings capture major PBMC immune-cell structure without task-specific fine-tuning?

Important scope limitation:
This task is only about Experiment 01. Do not implement perturbation analysis, open-set recognition, scVI comparison, Geneformer fine-tuning, or Geneformer pretraining. Those are later experiments.

Scientific context:
Geneformer is a pretrained transcriptome transformer for single-cell data. In this experiment, we use Geneformer only as a fixed pretrained embedding model. The goal is to test whether its cell embeddings contain biologically meaningful PBMC immune-cell structure.

The user has multiple PBMC `.h5ad` datasets already available locally on a Mac. However, public PBMC datasets often differ in their `.obs` label columns and label names. For this first experiment, keep the workflow conservative and simple:
1. Preserve raw labels unchanged.
2. Detect candidate label columns.
3. Allow a selected raw label column via CLI.
4. Create one simple broad PBMC label column.
5. Keep uncertain labels as `UNKNOWN`.

Do not build a large benchmark yet. Keep outputs minimal and high quality. The user prefers fewer, cleaner results over many TSVs, reports, and plots.

The broad PBMC label set for this first experiment should be:
- CD4_T
- CD8_T
- T_CELL
- B_CELL
- NK_CELL
- MONOCYTE
- DC
- PLATELET
- UNKNOWN

Expected workflow:
1. Place local PBMC `.h5ad` files in `data/raw/`.
2. Summarize available `.h5ad` files and detect likely label columns.
3. Load precomputed Geneformer cell embeddings from `data/processed/embeddings/`.
4. Attach embeddings to `adata.obsm["X_geneformer"]`.
5. Compute one UMAP from Geneformer embeddings.
6. Plot UMAP colored by broad PBMC labels.
7. Plot the same UMAP colored by dataset.
8. Train one simple Logistic Regression classifier on fixed Geneformer embeddings using broad PBMC labels.
9. Save one confusion matrix plot.
10. Save one compact metrics JSON and one per-class F1 table.
11. Save one run summary JSON.

Do not download Geneformer models or datasets.
Do not run heavy Geneformer embedding extraction.
Do not generate excessive output files.

============================================================
1. experiments/01_embedding_probe/README.md
============================================================

Write a detailed but focused README explaining only Experiment 01.

Include these sections:

# Experiment 01: Geneformer Embedding Probe

## Main question
Do pretrained Geneformer cell embeddings capture major PBMC immune-cell structure without task-specific fine-tuning?

## Rationale
Explain that the goal is to test fixed Geneformer cell embeddings, not to train a new model. The experiment asks whether major PBMC cell types are organized in a biologically meaningful way in Geneformer embedding space.

## Practical issue: heterogeneous PBMC labels
Explain that local/public PBMC `.h5ad` files often use different `.obs` columns and different cell-type naming schemes. This experiment therefore preserves raw labels and creates only one simple broad PBMC label column for evaluation.

## Recommended start strategy
Explain:
1. Start with one well-annotated PBMC dataset.
2. Then run the same analysis separately on 2–3 datasets.
3. Only then optionally combine datasets using broad labels.

## Minimal outputs
Explain that this experiment intentionally produces only a small number of high-value outputs:
- UMAP colored by broad PBMC label
- UMAP colored by dataset
- confusion matrix for broad-label logistic probe
- compact metrics JSON
- per-class F1 table
- run summary JSON

## What this experiment does not do
Explicitly state:
- no Geneformer pretraining
- no Geneformer fine-tuning
- no in silico perturbation
- no open-set rejection
- no scVI comparison
- no large benchmark reporting

## Recommended commands
Include:
python scripts/01_summarize_h5ad.py
python experiments/01_embedding_probe/run_embedding_probe.py --dry-run
python experiments/01_embedding_probe/run_embedding_probe.py

============================================================
2. experiments/01_embedding_probe/config.yml
============================================================

Create a simple config file:

experiment:
  name: "01_embedding_probe"
  random_seed: 42

paths:
  input_h5ad_dir: "data/raw"
  embeddings_dir: "data/processed/embeddings"
  output_dir: "experiments/01_embedding_probe/results"

adata:
  dataset_col: "dataset"
  raw_label_col: null
  broad_label_col: "pbmc_broad_label"

embedding:
  key: "X_geneformer"
  file_pattern: "{dataset}_geneformer_v1_embeddings.npy"
  cell_id_pattern: "{dataset}_cell_ids.tsv"

filtering:
  max_cells_per_dataset: 20000
  min_cells_per_label: 30
  exclude_broad_labels:
    - "UNKNOWN"

umap:
  n_neighbors: 15
  min_dist: 0.3
  random_state: 42

classifier:
  test_size: 0.2
  max_iter: 1000
  class_weight: "balanced"

plots:
  max_points_umap: 50000
  dpi: 200

============================================================
3. scripts/01_summarize_h5ad.py
============================================================

Implement a compact h5ad summary script.

Behavior:
- Scan `data/raw/` for `.h5ad` files.
- For each file, report:
  - file name
  - number of cells
  - number of genes
  - `.obs` columns
  - candidate label columns
  - top 20 values for candidate label columns

Candidate label columns should be detected by case-insensitive patterns:
- label
- celltype
- cell_type
- cell type
- annotation
- subtype
- predicted
- cluster

Candidate batch/dataset columns can be detected but should not produce large output:
- dataset
- donor
- subject
- individual
- sample
- batch
- patient
- library

Save only:
data/processed/h5ad_summary.json
data/processed/h5ad_summary.tsv

Do not save many separate diagnostic files.
Do not modify `.h5ad` files.

============================================================
4. src/scgip_lab/io.py
============================================================

Create or update helper functions:

- ensure_dir(path)
- find_h5ad_files(input_dir)
- read_h5ad(path)
- detect_candidate_label_columns(adata)
- detect_candidate_batch_columns(adata)
- summarize_adata(adata, dataset_name=None)
- write_json(obj, path)
- write_tsv(df, path)

Use pathlib.
Use clear error messages.
Do not print excessively inside helper functions.

============================================================
5. src/scgip_lab/labels.py
============================================================

Implement simple label helper functions for Experiment 01:

- choose_label_column(adata, preferred_col=None)
- make_pbmc_broad_labels(raw_labels)
- add_pbmc_broad_label(adata, raw_label_col, output_col="pbmc_broad_label")
- summarize_label_counts(adata, label_cols)

The broad PBMC label mapping should be conservative and rule-based.

Suggested rules:
- labels containing "cd4" -> CD4_T
- labels containing "cd8" -> CD8_T
- labels containing "nk" or "natural killer" -> NK_CELL
- labels containing "b cell", "b_cell", "b-cell", or "cd79" -> B_CELL
- labels containing "mono", "monocyte", "cd14", "fcgr3a", or "cd16 mono" -> MONOCYTE
- labels containing "dc", "dendritic", "cdc", or "pdc" -> DC
- labels containing "platelet", "megakaryocyte", "ppbp", or "pf4" -> PLATELET
- labels containing "t cell", "t_cell", "t-cell", or "cd3" but not cd4/cd8 -> T_CELL
- otherwise -> UNKNOWN

Important:
- Do not overwrite the original label column.
- Store the broad label in a new `.obs` column.
- Convert labels to strings safely.
- Return summary counts.

============================================================
6. src/scgip_lab/embeddings.py
============================================================

Implement functions:

- load_embedding_files(embedding_path, cell_id_path)
- attach_embeddings_to_adata(adata, embeddings, cell_ids, embedding_key="X_geneformer")
- subsample_adata(adata, max_cells, seed=42, stratify_col=None)
- get_embedding_matrix(adata, embedding_key="X_geneformer")

Expected embedding format:
- `.npy` file with shape `(n_cells, n_dimensions)`
- cell ID `.tsv` with a column named `cell_id`

Behavior:
- Check that number of embeddings equals number of cell IDs.
- Align embeddings to `adata.obs_names`.
- If some cell IDs are missing, raise a clear error showing:
  - number of AnnData cells
  - number of embedding rows
  - number of matching cell IDs
- Store aligned embeddings in `adata.obsm[embedding_key]`.

============================================================
7. src/scgip_lab/evaluation.py
============================================================

Implement only the minimal metrics needed for Experiment 01:

- train_test_logistic_probe(X, y, test_size=0.2, seed=42, class_weight="balanced", max_iter=1000)
- classification_summary(y_true, y_pred)
- per_class_metrics(y_true, y_pred)
- confusion_matrix_df(y_true, y_pred)
- knn_label_purity(X, y, k=15, max_cells=10000, seed=42)

Use scikit-learn.

Metrics in the compact JSON:
- accuracy
- balanced_accuracy
- macro_f1
- weighted_f1
- knn_label_purity
- number_of_cells_used
- number_of_labels_used

The logistic probe should:
- use stratified splitting if possible
- handle rare classes gracefully
- not train if fewer than two labels remain after filtering
- return one compact metrics dict, one per-class metrics dataframe, and one confusion matrix dataframe

============================================================
8. src/scgip_lab/plotting.py
============================================================

Implement only four plotting functions:

- plot_umap_from_embedding(adata, embedding_key, color_col, output_path, title=None, max_points=50000, seed=42)
- plot_label_counts(adata, label_col, output_path, title=None)
- plot_confusion_matrix(cm_df, output_path, title=None)
- plot_per_class_f1(per_class_df, output_path, title=None)

However, the main Experiment 01 runner should only save these final figures by default:
1. figures/01_umap_geneformer_broad_label.png
2. figures/02_umap_geneformer_dataset.png
3. figures/03_confusion_matrix_geneformer_broad_label.png

Do not save per-class F1 plot by default unless explicitly enabled later.
Do not save original-label UMAP by default unless explicitly enabled later.
Do not create many diagnostic plots.

Requirements:
- Do not use seaborn.
- Save PNG files with dpi=200.
- Ensure output directories exist.
- UMAP should be computed from `adata.obsm[embedding_key]`.
- If too many cells, subsample deterministically for plotting only.
- Use readable figure sizes and rotated labels where needed.

============================================================
9. experiments/01_embedding_probe/run_embedding_probe.py
============================================================

Implement the main Experiment 01 runner.

Use argparse with:
--config default "experiments/01_embedding_probe/config.yml"
--h5ad optional path to one specific h5ad
--label-col optional raw label column override
--dataset-name optional dataset name override
--skip-classifier
--save-extra-plots optional flag, default false
--dry-run

Behavior:

1. Load config.
2. Find one or more `.h5ad` files.
   - If `--h5ad` is provided, analyze only that file.
   - Otherwise analyze all `.h5ad` files in `data/raw/`.
3. For each file:
   - read AnnData
   - infer dataset name from filename unless `--dataset-name` is given
   - ensure `adata.obs["dataset"]` exists
   - choose raw label column:
     - use `--label-col` if provided
     - otherwise use config value if not null
     - otherwise detect candidate label columns and pick the first
   - copy the selected label column to `adata.obs["cell_type_original"]`
   - create `adata.obs["pbmc_broad_label"]`
   - optionally subsample to `max_cells_per_dataset`, stratified by broad label
   - load Geneformer embeddings from:
     data/processed/embeddings/{dataset}_geneformer_v1_embeddings.npy
     data/processed/embeddings/{dataset}_cell_ids.tsv
   - attach embeddings to `adata.obsm["X_geneformer"]`
4. Concatenate multiple datasets if more than one is analyzed.
5. Generate output directories:
   experiments/01_embedding_probe/results/figures
   experiments/01_embedding_probe/results/metrics
   experiments/01_embedding_probe/results/logs
6. Save only these default plots:
   - figures/01_umap_geneformer_broad_label.png
   - figures/02_umap_geneformer_dataset.png
   - figures/03_confusion_matrix_geneformer_broad_label.png
7. If --save-extra-plots is set, additionally save:
   - UMAP colored by original labels
   - label count plot by broad labels
   - per-class F1 plot
8. Compute compact metrics:
   - kNN label purity for broad labels
   - Logistic Regression probe metrics for broad labels
9. Save only:
   - metrics/embedding_probe_metrics.json
   - metrics/per_class_f1.tsv
   - logs/run_summary.json

The compact metrics JSON should include:
- dataset_names
- n_datasets
- n_cells_total_after_filtering
- n_cells_used_for_classifier
- broad_label_counts
- accuracy
- balanced_accuracy
- macro_f1
- weighted_f1
- knn_label_purity
- classifier
- embedding_key
- random_seed

Dry-run mode:
- Print which h5ad files would be analyzed.
- Print detected candidate label columns.
- Print expected embedding file paths.
- Print the minimal output files that would be produced.
- Do not load embeddings, compute UMAP, or train classifiers.

Robustness:
- If Geneformer embeddings are missing, print a clear message:
  "Missing Geneformer embeddings for dataset '<dataset>'. Expected files: ... Run the Geneformer embedding extraction step first."
- Do not crash with cryptic tracebacks for expected missing files.
- If labels are messy, broad labels should still be created conservatively.
- If too many labels map to UNKNOWN, report this in run_summary.json and print a warning.

============================================================
10. Do not implement
============================================================

Do not implement:
- in silico perturbation
- rank-shift experiments
- open-set rejection
- OOD detection
- scVI comparison
- PCA baseline
- leave-one-dataset-out transfer
- label-efficiency curves
- large benchmark reports
- Geneformer tokenizer or embedding extraction internals
- model download scripts

============================================================
11. Final message
============================================================

After implementation, print:
- files created/updated
- how to run the h5ad summary
- how to run a dry run
- how to run Experiment 01 once embeddings are available
- known TODOs, especially Geneformer embedding extraction