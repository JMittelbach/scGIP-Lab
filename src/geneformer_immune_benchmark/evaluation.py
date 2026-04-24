from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)


def classification_metrics(y_true, y_pred) -> dict[str, float]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
    }


def per_class_metrics(y_true, y_pred) -> pd.DataFrame:
    labels = np.unique(np.concatenate([np.asarray(y_true), np.asarray(y_pred)]))
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, zero_division=0
    )
    return pd.DataFrame(
        {
            "label": labels,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
        }
    )


def confusion_matrix_dataframe(y_true, y_pred) -> pd.DataFrame:
    labels = np.unique(np.concatenate([np.asarray(y_true), np.asarray(y_pred)]))
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    return pd.DataFrame(cm, index=labels, columns=labels)


def openset_scores_from_probabilities(probabilities: np.ndarray) -> dict[str, np.ndarray]:
    probs = np.asarray(probabilities, dtype=float)
    if probs.ndim != 2:
        raise ValueError(f"Expected 2D probability matrix, got shape {probs.shape}")
    eps = 1e-12
    max_prob = probs.max(axis=1)
    entropy = -(probs * np.log(probs + eps)).sum(axis=1)
    return {"max_probability": max_prob, "entropy": entropy}


def evaluate_rejection_curve(
    y_true,
    y_pred,
    confidence: np.ndarray,
    thresholds: np.ndarray,
) -> pd.DataFrame:
    y_true_arr = np.asarray(y_true)
    y_pred_arr = np.asarray(y_pred)
    conf_arr = np.asarray(confidence, dtype=float)

    rows = []
    n_total = len(y_true_arr) if len(y_true_arr) else 1
    for t in thresholds:
        keep = conf_arr >= float(t)
        n_kept = int(keep.sum())
        coverage = n_kept / n_total
        if n_kept == 0:
            acc = np.nan
        else:
            acc = float(accuracy_score(y_true_arr[keep], y_pred_arr[keep]))
        rows.append(
            {
                "threshold": float(t),
                "coverage": float(coverage),
                "accepted_accuracy": acc,
                "n_accepted": n_kept,
                "n_rejected": int(n_total - n_kept),
            }
        )
    return pd.DataFrame(rows)
