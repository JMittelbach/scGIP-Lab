# scGIP-Lab

`scGIP-Lab` = **single-cell Geneformer Immune Probing Lab**.

Compact, reproducible research scaffold for exploring pretrained Geneformer representations on human PBMC scRNA-seq data.

## Project goal

This repository studies whether pretrained Geneformer cell embeddings can support practical PBMC immune cell annotation and exploratory open-set recognition without heavy model retraining.

## Included experiments

1. Geneformer PBMC embedding probe
2. Geneformer-inspired in silico perturbation probe
3. Geneformer vs PCA/scVI embedding comparison
4. Open-set PBMC annotation using Geneformer embeddings

Each experiment has its own directory under `experiments/`

## Label handling policy

Public PBMC datasets often use heterogeneous annotation schemes. This project uses a conservative harmonization strategy:
- Raw labels are preserved and never overwritten.
- Harmonized labels are stored in separate columns.
- Ambiguous labels should remain unresolved (`unknown` or `review`) until manually verified.

See `docs/label_harmonization_strategy.md` and `config/label_mapping_template.tsv`.

## Quick setup

```bash
bash scripts/setup_project.sh --full
conda activate scgip-lab
```

For normal daily use, you usually only need:

```bash
conda activate scgip-lab
```

If you want a fast health check without forcing reinstall/update:

```bash
bash scripts/setup_project.sh
```

## Experiment readiness check

Use the Make target to see where you are in Experiment 01 (data, tokenization, embeddings, run outputs) and what to do next:

```bash
make check EXPERIMENT=1
```

With explicit dataset inputs:

```bash
make check EXPERIMENT=1 \
  H5AD=/path/to/pbmc.h5ad \
  DATASET=hao \
  LABEL_COL=celltype.l2
```

Equivalent shortcut:

```bash
make check-experiment-1 H5AD=/path/to/pbmc.h5ad DATASET=hao LABEL_COL=celltype.l2
```

## Scientific motivation

Geneformer (Theodoris et al., 2023) treats each cell transcriptome as an ordered sequence of gene tokens, ranking genes by normalized expression relative to broad corpus-level frequencies. This offers a transfer-learning framework for extracting biologically structured embeddings from single-cell profiles. In PBMC settings, we use these embeddings as fixed features for lightweight downstream tasks:
- broad and fine-grained immune annotation,
- embedding-space structure analysis,
- sensitivity-style in silico perturbation probes,
- and exploratory unknown-cell rejection.

## Geneformer dependency note

This scaffold includes local scripts for tokenization and embedding extraction, while the Geneformer code/model stay external via Hugging Face assets.

## Geneformer installation strategy

Geneformer is not included in this repository and is treated as an external dependency.

- Geneformer is downloaded from Hugging Face with `git-lfs`.
- Large model files must not be committed to this repository.
- The expected local path is `external/Geneformer`.
- Full Geneformer pretraining is not attempted in this project.
- This repository uses pretrained Geneformer models for embedding extraction and lightweight downstream analyses.

Install and verify Geneformer locally:

```bash
bash scripts/setup_project.sh
```

Note on download size:
- Geneformer uses large `git-lfs` assets and should be treated as a multi-GB external dependency depending on selected revision/files.

## Tokenizing and extracting embeddings

Geneformer already provides a tokenizer for `.h5ad` input. This repository exposes it via:

```bash
python scripts/03_extract_geneformer_embeddings.py --tokenize --input-file data/raw/YOUR_DATASET.h5ad --tokenized-prefix YOUR_DATASET
python scripts/03_extract_geneformer_embeddings.py --extract-embeddings --input-file data/raw/YOUR_DATASET.h5ad --tokenized-prefix YOUR_DATASET --dataset-name YOUR_DATASET
```

Requirements for `.h5ad` input:
- `obs["n_counts"]` must exist.
- `var["ensembl_id"]` must exist, or run with `--use-h5ad-index` if `var.index` contains Ensembl IDs.

Tokenized output is written to:
- `data/processed/tokenized/*.dataset`

Embedding outputs are written to:
- `data/processed/embeddings/{dataset}_geneformer_v1_embeddings.npy`
- `data/processed/embeddings/{dataset}_cell_ids.tsv`

Notes:
- Upstream `EmbExtractor` currently expects CUDA for extraction.
- If `obs["cell_id"]` exists, it is propagated during tokenization for stable alignment.

## Limitations

- No causal interpretation of embedding perturbations.
- No full Geneformer pretraining.
- Label harmonization remains imperfect.
- Open-set rejection is exploratory and requires external validation.

More details are in `docs/limitations.md`.

## Citation

If you use this repository, please cite:
- this repository (`CITATION.cff`), and
- Theodoris et al. (Nature, 2023): *Transfer learning enables predictions in network biology*.

Full reference is provided in `references.bib`.
