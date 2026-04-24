from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def plot_label_counts(labels, title: str = "Label counts", ax=None):
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 4))
    series = pd.Series(labels).astype(str).value_counts()
    ax.bar(series.index, series.values)
    ax.set_title(title)
    ax.set_ylabel("Count")
    ax.set_xlabel("Label")
    ax.tick_params(axis="x", rotation=45)
    return ax


def plot_confusion_matrix(cm_df: pd.DataFrame, normalize: bool = False, ax=None):
    if ax is None:
        _, ax = plt.subplots(figsize=(6, 5))
    mat = cm_df.to_numpy(dtype=float)
    if normalize:
        row_sums = mat.sum(axis=1, keepdims=True) + 1e-12
        mat = mat / row_sums
    im = ax.imshow(mat, aspect="auto")
    ax.set_xticks(np.arange(cm_df.shape[1]))
    ax.set_xticklabels(cm_df.columns, rotation=45, ha="right")
    ax.set_yticks(np.arange(cm_df.shape[0]))
    ax.set_yticklabels(cm_df.index)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title("Confusion matrix" + (" (normalized)" if normalize else ""))
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    return ax


def plot_score_histogram(scores, labels=None, bins: int = 30, ax=None):
    if ax is None:
        _, ax = plt.subplots(figsize=(6, 4))
    scores_arr = np.asarray(scores, dtype=float)
    if labels is None:
        ax.hist(scores_arr, bins=bins, alpha=0.8)
    else:
        labels_arr = np.asarray(labels)
        for group in np.unique(labels_arr):
            mask = labels_arr == group
            ax.hist(scores_arr[mask], bins=bins, alpha=0.5, label=str(group))
        ax.legend()
    ax.set_title("Score histogram")
    ax.set_xlabel("Score")
    ax.set_ylabel("Frequency")
    return ax


def plot_rejection_curve(curve_df: pd.DataFrame, ax=None):
    if ax is None:
        _, ax = plt.subplots(figsize=(6, 4))
    ax.plot(curve_df["coverage"], curve_df["accepted_accuracy"], marker="o")
    ax.set_xlabel("Coverage (accepted fraction)")
    ax.set_ylabel("Accepted accuracy")
    ax.set_title("Rejection curve")
    ax.grid(True, alpha=0.3)
    return ax
