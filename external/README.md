# External Dependencies

This directory is reserved for large external model repositories that are used
locally during analysis, such as Geneformer.

## Policy

- External model repositories may be cloned here for local use.
- Large model files and external repositories must not be committed to GitHub.
- Keep this project repository focused on analysis code, configuration, and
  documentation.

## Geneformer local path

Expected local path for Geneformer:

`external/Geneformer`

Install/update Geneformer using:

```bash
bash scripts/setup_geneformer.sh
python scripts/check_geneformer.py
```
