# Geneformer notes (plain-language)

## Transcriptome as a ranked gene sequence

Geneformer represents each cell as an ordered sequence of gene tokens rather than a fixed vector of counts. Genes are ranked by expression after normalization against broad corpus-level expression patterns. This ranking emphasizes relative biological signal rather than raw scale alone.

## Masked gene prediction

The pretraining objective is conceptually similar to masked language modeling: the model learns to predict masked genes from surrounding context in the ranked sequence. This encourages embeddings that capture gene-gene and cell-state relationships.

## Cell embeddings

A pretrained Geneformer model can produce per-cell embeddings, which can be used as fixed features for downstream tasks such as cell-type annotation or outlier detection.

## Gene embeddings

Model internals also support gene-level representations. These can help exploratory interpretation but should be used cautiously in benchmarking contexts.

## Transfer learning

Transfer learning is central: the model is pretrained on large single-cell corpora, then reused for new tasks with limited task-specific training. In this project, we focus on lightweight downstream models on top of fixed embeddings.

## Why this is relevant for PBMC annotation

PBMC data contain diverse but well-studied immune populations. This makes PBMC an appropriate testbed for:
- broad and fine-grained annotation quality,
- embedding structure analysis,
- and open-set behavior when unknown classes appear.

## Why full pretraining is not attempted here

Full pretraining is computationally expensive and outside the scope of this repository scaffold. The objective here is to build a reproducible benchmark around pretrained embeddings and conservative evaluation design, not to reproduce the original large-scale training pipeline.

## Why Geneformer is an external dependency

Geneformer is handled as an external dependency instead of being vendored into this repository for several reasons:

- Reproducibility: the project can pin and document the upstream Geneformer source/revision independently from local analysis code.
- Repository size: large model files managed by `git-lfs` would make this project repository unnecessarily heavy.
- Clear separation of concerns: original model code remains separate from project-specific benchmarking and analysis code.
- Easier model updates: Geneformer can be updated locally without rewriting project history.
- Reduced risk of mistakes: this setup helps avoid accidentally committing large model files or external repositories to GitHub.
