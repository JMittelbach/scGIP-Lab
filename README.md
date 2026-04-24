# scGIP-Lab

`scGIP-Lab` = **single-cell Geneformer Immune Probing Lab**.

Compact, reproducible research scaffold for exploring pretrained Geneformer representations on human PBMC scRNA-seq data.

## Project goal

This repository studies whether pretrained Geneformer cell embeddings can support practical PBMC immune cell annotation and exploratory open-set recognition without heavy model retraining.

The repository is intentionally lightweight:
- It does not pretrain Geneformer.
- It does not run heavy training by default.
- It is designed for local `.h5ad` files that you place in `data/raw/`.

## Included experiments

1. Geneformer PBMC embedding probe
2. Geneformer-inspired in silico perturbation probe
3. Geneformer vs PCA/scVI embedding comparison
4. Open-set PBMC annotation using Geneformer embeddings

Each experiment has its own folder under `experiments/` with a dedicated README, a run script, and result directories.

## Label handling policy

Public PBMC datasets often use heterogeneous annotation schemes. This project uses a conservative harmonization strategy:
- Raw labels are preserved and never overwritten.
- Harmonized labels are stored in separate columns.
- Ambiguous labels should remain unresolved (`unknown` or `review`) until manually verified.

See `docs/label_harmonization_strategy.md` and `config/label_mapping_template.tsv`.

## Recommended first run

```bash
conda env create -f environment.yml
conda activate scGIP-Lab
python scripts/00_check_environment.py
python scripts/01_summarize_h5ad.py
```

## Scientific motivation

Geneformer (Theodoris et al., 2023) treats each cell transcriptome as an ordered sequence of gene tokens, ranking genes by normalized expression relative to broad corpus-level frequencies. This offers a transfer-learning framework for extracting biologically structured embeddings from single-cell profiles. In PBMC settings, we use these embeddings as fixed features for lightweight downstream tasks:
- broad and fine-grained immune annotation,
- embedding-space structure analysis,
- sensitivity-style in silico perturbation probes,
- and exploratory unknown-cell rejection.

## Geneformer dependency note

This scaffold includes lightweight placeholders for Geneformer integration via Hugging Face artifacts. Depending on your workflow, you may need to install Geneformer separately from its source/Hugging Face resources in addition to the packages in `environment.yml`.

## Geneformer installation strategy

Geneformer is not included in this repository and is treated as an external dependency.

- Geneformer is downloaded from Hugging Face with `git-lfs`.
- Large model files must not be committed to this repository.
- The expected local path is `external/Geneformer`.
- Full Geneformer pretraining is not attempted in this project.
- This repository uses pretrained Geneformer models for embedding extraction and lightweight downstream analyses.

Install and verify Geneformer locally:

```bash
bash scripts/setup_geneformer.sh
python scripts/check_geneformer.py
```

Note on download size:
- Geneformer uses large `git-lfs` assets and should be treated as a multi-GB external dependency depending on selected revision/files.

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
