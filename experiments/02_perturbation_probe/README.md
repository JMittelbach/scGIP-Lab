# Experiment 02: Perturbation Probe

## Biological/computational question

Are Geneformer embeddings sensitive to biologically meaningful immune marker/regulator genes in a cell-type-specific way?

## Concept

We will evaluate embedding sensitivity under in silico transcriptome edits, such as:
- marker-gene deletion,
- marker rank-shift,
- or controlled masking of gene subsets.

This is an embedding-sensitivity analysis, not a causal perturbation validation.

## Inputs

- Local `.h5ad` data
- Marker gene sets (`config/marker_genes_pbmc.yml`)
- Geneformer embeddings before/after perturbation transforms

## Outputs

- Embedding-shift summaries by gene set and cell type
- Figures showing distribution of shift scores
- Metrics for relative sensitivity comparisons

## Notes

- Interpretation should remain conservative.
- Any biological claims should be externally validated.
