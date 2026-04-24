"""Project-wide constants."""

LABEL_COLUMN_KEYWORDS = [
    "label",
    "celltype",
    "cell_type",
    "cell type",
    "annotation",
    "cluster",
    "identity",
    "ident",
]

BATCH_COLUMN_KEYWORDS = [
    "batch",
    "donor",
    "sample",
    "dataset",
    "study",
    "patient",
    "replicate",
    "library",
    "lane",
]

EXPECTED_HARMONIZED_COLUMNS = [
    "harmonized_l1",
    "harmonized_l2",
    "harmonized_l3",
]

MAPPING_TEMPLATE_COLUMNS = [
    "dataset",
    "raw_label",
    "harmonized_l1",
    "harmonized_l2",
    "harmonized_l3",
    "confidence",
    "action",
    "notes",
]
