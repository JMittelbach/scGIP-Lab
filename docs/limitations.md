# Limitations

## 1) No causal conclusions from embedding shifts

In silico perturbation probes in this project evaluate embedding sensitivity under synthetic feature edits. These analyses are descriptive and do not establish causal gene-regulatory mechanisms.

## 2) Limited public label quality

Public PBMC labels are often inconsistent across studies, annotation tools, and curation versions. Even conservative harmonization cannot fully eliminate annotation uncertainty.

## 3) Dataset effects may remain

Batch, donor, platform, and study design effects can persist in embedding spaces and impact classifier performance. Residual confounding may remain even with careful split strategy.

## 4) Unknown detection depends on split design

Open-set performance can vary substantially based on how unknowns are defined (held-out class vs held-out dataset). Reported metrics should be interpreted in the context of explicit split protocols.

## 5) Geneformer embeddings are not automatically superior

Pretrained Geneformer features may or may not outperform PCA/scVI baselines depending on task definition, label quality, data preprocessing, and domain shift.

## 6) Benchmarking should expand to external datasets

Conclusions from a limited PBMC set should be treated as preliminary. Robust claims require broader external datasets and repeated evaluation across cohorts and technologies.
