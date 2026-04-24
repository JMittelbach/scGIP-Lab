# Project plan

## Scope

This repository supports a compact, reproducible benchmark for pretrained Geneformer embeddings on PBMC scRNA-seq tasks. The project is intentionally staged to avoid heavy compute early and to preserve conservative biological interpretation.

## Phase 1: repository setup and h5ad summary

- Finalize scaffold, configuration, and environment.
- Place local `.h5ad` files in `data/raw/`.
- Run `scripts/01_summarize_h5ad.py` to inventory cells, genes, and metadata columns.
- Identify candidate raw label and batch/donor/dataset columns.

Deliverables:
- `data/processed/h5ad_summaries.json`
- initial metadata audit notes

## Phase 2: conservative label harmonization

- Start from `config/label_mapping_template.tsv` or drafted mapping TSV.
- Preserve raw labels exactly as provided by source datasets.
- Add harmonized levels (`harmonized_l1/l2/l3`) with confidence and action tags.
- Flag ambiguous labels for manual review.

Deliverables:
- curated label mapping TSV
- documented harmonization decisions

## Phase 3: Geneformer embedding extraction

- Install/configure Geneformer resources.
- Implement conversion/tokenization for local AnnData inputs.
- Extract fixed cell embeddings from pretrained model checkpoints.
- Save embeddings and stable cell IDs.

Deliverables:
- embedding matrices (`.npy`)
- matching cell ID tables (`.tsv`)
- reproducible extraction script config

## Phase 4: embedding probe

- Build UMAPs from Geneformer embeddings.
- Train lightweight classifiers for label prediction.
- Measure baseline separation and annotation quality.

Deliverables:
- UMAP figures
- classifier metrics and confusion matrices

## Phase 5: perturbation probe

- Define marker/regulator gene sets.
- Perform in silico rank/deletion style perturbations.
- Quantify embedding shifts by cell type and gene set.

Deliverables:
- perturbation sensitivity metrics
- per-cell-type shift plots

## Phase 6: baseline/scVI comparison

- Build PCA baseline from same input.
- Optionally train scVI latent model (if resources permit).
- Compare downstream annotation performance fairly across spaces.

Deliverables:
- cross-method metrics table
- method-specific confusion matrices/plots

## Phase 7: open-set evaluation

- Design known/unknown splits (hold-out cell type or dataset).
- Evaluate max-probability, centroid-distance, and kNN-distance rejection scores.
- Quantify AUROC and coverage-accuracy tradeoffs.

Deliverables:
- open-set AUROC
- rejection curves
- score histograms

## Phase 8: final README figures and interpretation

- Consolidate key figures and metrics across experiments.
- Update README and docs with conservative conclusions.
- Highlight uncertainty, dataset effects, and external validation needs.

Deliverables:
- polished project narrative
- reproducible figure-generation references
