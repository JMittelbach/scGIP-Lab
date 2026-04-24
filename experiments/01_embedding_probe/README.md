# Experiment 01: Embedding Probe

## Biological/computational question

Do pretrained Geneformer cell embeddings separate PBMC immune cell types without task-specific training?

## Inputs

- Local PBMC `.h5ad` files (`data/raw/`)
- Conservatively harmonized labels (`harmonized_l1/l2/l3`)
- Precomputed Geneformer embeddings (to be generated in later phase)

## Planned analysis

- Build UMAPs from fixed Geneformer embeddings.
- Quantify separation by label level.
- Train a lightweight classifier baseline (e.g., Logistic Regression).

## Outputs

- UMAP figures
- Label-separation and classifier metrics
- Confusion matrices

## Notes

- Raw labels must remain unchanged.
- Harmonized labels are tracked separately and should include confidence/review flags.
