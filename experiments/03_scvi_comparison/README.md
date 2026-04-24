# Experiment 03: scVI/PCA Comparison

## Biological/computational question

How do pretrained Geneformer embeddings compare to PCA/scVI latent spaces for PBMC annotation?

## Inputs

- Local `.h5ad` PBMC datasets
- Harmonized labels
- Geneformer embeddings
- PCA embeddings (baseline)
- Optional scVI latent representation (optional future extension)

## Planned analysis

- Train comparable lightweight classifiers across embedding spaces.
- Match split strategy across methods for fair comparison.
- Compare macro-F1, per-class recall, calibration/confidence trends.

## Outputs

- Side-by-side classifier metrics
- Confusion matrices per embedding space
- UMAP/2D visual summaries

## Notes

- scVI training is optional and may be added later.
- This scaffold does not force heavy GPU workflows.
