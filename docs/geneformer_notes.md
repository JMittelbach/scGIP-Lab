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
