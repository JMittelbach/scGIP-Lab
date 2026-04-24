# Label harmonization strategy

## Core principles

1. Heterogeneous labels are expected across PBMC datasets.
2. Raw source labels are always preserved.
3. Harmonized labels are conservative and stored in separate columns.
4. Ambiguous labels are collapsed or assigned `unknown`/`review`.
5. Activation/state labels should not be overinterpreted as stable cell identities.

## Practical workflow

- Keep raw labels in their original `adata.obs` column.
- Build mapping table entries per dataset and raw label.
- Populate `harmonized_l1`, `harmonized_l2`, `harmonized_l3` only when evidence is clear.
- Track `confidence`, `action`, and `notes` for transparency.
- Use `needs_label_review` flags to avoid accidental over-claiming.

## Suggested broad PBMC hierarchy

- `harmonized_l1`:
  - T cell
  - NK cell
  - B cell
  - Myeloid
  - Platelet
  - Unknown
- `harmonized_l2` examples:
  - CD4 T cell
  - CD8 T cell
  - Monocyte
  - Dendritic cell
  - Plasma cell
- `harmonized_l3` examples:
  - Naive/Memory CD4 T
  - Cytotoxic CD8 T
  - CD14+ Monocyte
  - FCGR3A+ Monocyte

## Ambiguity handling recommendations

- If a source label mixes lineages, keep it unresolved (`unknown` or `review`).
- If confidence is low, avoid forced fine-grained subtype mapping.
- For rare or low-quality clusters, prefer broad-level assignment first.
