# Experiment 04: Open-Set Annotation

## Biological/computational question

Can Geneformer embeddings support open-set PBMC annotation by rejecting unknown or held-out cell types?

## Methods

- Train a classifier on known labels.
- Hold out one cell type or one dataset as out-of-distribution (OOD).
- Evaluate rejection scores:
  - max class probability,
  - centroid distance,
  - kNN distance.

## Outputs

- AUROC for known vs unknown discrimination
- Rejection curves (coverage vs accepted accuracy)
- Confusion matrices before and after rejection
- Score histograms

## Notes

- This is exploratory and requires external validation.
- Split design strongly affects unknown-detection performance and should be documented.
