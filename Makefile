PYTHON ?= python
EXPERIMENT ?=
H5AD ?=
DATASET ?=
LABEL_COL ?=
VERBOSE ?=

.PHONY: help check check-experiment-1 check-e1 experiment-1 e1 experiment 1

help:
	@echo "Targets:"
	@echo "  make check EXPERIMENT=1 [H5AD=/abs/path/file.h5ad] [DATASET=name] [LABEL_COL=col] [VERBOSE=1]"
	@echo "  make check-experiment-1 [H5AD=/abs/path/file.h5ad] [DATASET=name] [LABEL_COL=col] [VERBOSE=1]"
	@echo "  make check-e1 (alias: experiment-1, e1)"

check:
ifeq ($(EXPERIMENT),1)
	@$(MAKE) check-experiment-1 H5AD="$(H5AD)" DATASET="$(DATASET)" LABEL_COL="$(LABEL_COL)"
else
	@echo "[INFO] No experiment selected."
	@echo "[INFO] Use: make check EXPERIMENT=1"
	@echo "[INFO] Optional: H5AD=... DATASET=... LABEL_COL=..."
endif

check-experiment-1:
	@echo "[RUN] $(PYTHON) scripts/check_experiment_1_readiness.py ..."
	@$(PYTHON) scripts/check_experiment_1_readiness.py \
		$(if $(H5AD),--h5ad "$(H5AD)",) \
		$(if $(DATASET),--dataset-name "$(DATASET)",) \
		$(if $(LABEL_COL),--label-col "$(LABEL_COL)",) \
		$(if $(VERBOSE),--verbose,)

check-e1: check-experiment-1
e1: check-experiment-1
experiment-1: check-experiment-1

# Convenience aliases so a typo like `make check experiment 1` does not fail.
experiment: check-experiment-1
1:
	@true
