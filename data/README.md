# Data directory

This repository expects local `.h5ad` files and does not download large datasets by default.

## Layout

- `raw/`: place input `.h5ad` files here.
- `processed/`: generated summaries, mappings, and lightweight outputs.

## Notes

- Keep raw data immutable when possible.
- Preserve original annotation columns in `adata.obs` (do not overwrite).
- Add harmonized labels in new columns (for example: `harmonized_l1`, `harmonized_l2`, `harmonized_l3`).
