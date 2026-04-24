# Experiment 01: Geneformer Embedding Probe

## Main question
Do pretrained Geneformer cell embeddings capture major PBMC immune-cell structure without task-specific fine-tuning?

## Rationale
This experiment tests fixed pretrained Geneformer cell embeddings. The goal is not to train a new model, but to measure whether major PBMC immune-cell structure is already represented in embedding space.

## Practical issue: heterogeneous PBMC labels
Local/public PBMC `.h5ad` files often differ in `.obs` label columns and label naming. This workflow preserves raw labels and creates one conservative broad PBMC label column for evaluation.

## Recommended start strategy
1. Start with one well-annotated PBMC dataset.
2. Run the same analysis separately on 2-3 datasets.
3. Optionally combine datasets only after broad-label behavior is stable.

## Minimal outputs
This experiment intentionally produces only a few high-value outputs:
- UMAP colored by broad PBMC label
- UMAP colored by dataset
- confusion matrix for broad-label logistic probe
- compact metrics JSON
- per-class F1 table
- run summary JSON

## What this experiment does not do
- no Geneformer pretraining
- no Geneformer fine-tuning
- no in silico perturbation
- no open-set rejection
- no scVI comparison
- no large benchmark reporting

## Recommended commands
```bash
python scripts/01_summarize_h5ad.py
python experiments/01_embedding_probe/run_embedding_probe.py --dry-run
python experiments/01_embedding_probe/run_embedding_probe.py
```

