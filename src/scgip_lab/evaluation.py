from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split
from sklearn.neighbors import NearestNeighbors


def classification_summary(y_true, y_pred) -> dict[str, float]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": float(
            f1_score(y_true, y_pred, average="weighted", zero_division=0)
        ),
    }


def per_class_metrics(y_true, y_pred) -> pd.DataFrame:
    labels = np.unique(np.concatenate([np.asarray(y_true), np.asarray(y_pred)]))
    p, r, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, zero_division=0
    )
    return pd.DataFrame(
        {
            "label": labels,
            "precision": p,
            "recall": r,
            "f1": f1,
            "support": support,
        }
    )


def confusion_matrix_df(y_true, y_pred) -> pd.DataFrame:
    labels = np.unique(np.concatenate([np.asarray(y_true), np.asarray(y_pred)]))
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    return pd.DataFrame(cm, index=labels, columns=labels)


def train_test_logistic_probe(
    X,
    y,
    test_size: float = 0.2,
    seed: int = 42,
    class_weight: str | dict | None = "balanced",
    max_iter: int = 1000,
):
    X_arr = np.asarray(X, dtype=float)
    y_arr = np.asarray(y).astype(str)

    if X_arr.ndim != 2:
        raise ValueError(f"X must be 2D, got shape {X_arr.shape}")
    if len(X_arr) != len(y_arr):
        raise ValueError(f"X and y length mismatch: {len(X_arr)} vs {len(y_arr)}")

    unique_labels, counts = np.unique(y_arr, return_counts=True)
    if len(unique_labels) < 2:
        raise ValueError("Need at least two labels for logistic probe.")

    stratify = y_arr if np.min(counts) >= 2 else None
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X_arr,
            y_arr,
            test_size=test_size,
            random_state=seed,
            stratify=stratify,
        )
    except ValueError:
        X_train, X_test, y_train, y_test = train_test_split(
            X_arr,
            y_arr,
            test_size=test_size,
            random_state=seed,
            stratify=None,
        )

    clf = LogisticRegression(
        max_iter=max_iter,
        class_weight=class_weight,
        multi_class="auto",
    )
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)

    metrics = classification_summary(y_test, y_pred)
    metrics["number_of_cells_used"] = int(len(y_arr))
    metrics["number_of_labels_used"] = int(len(np.unique(y_arr)))

    per_class_df = per_class_metrics(y_test, y_pred)
    cm_df = confusion_matrix_df(y_test, y_pred)
    return metrics, per_class_df, cm_df


def knn_label_purity(X, y, k: int = 15, max_cells: int = 10000, seed: int = 42) -> float:
    X_arr = np.asarray(X, dtype=float)
    y_arr = np.asarray(y).astype(str)
    if len(X_arr) != len(y_arr):
        raise ValueError(f"X and y length mismatch: {len(X_arr)} vs {len(y_arr)}")
    if len(X_arr) < 2:
        return float("nan")

    if len(X_arr) > max_cells:
        rng = np.random.default_rng(seed)
        idx = np.sort(rng.choice(np.arange(len(X_arr)), size=max_cells, replace=False))
        X_arr = X_arr[idx]
        y_arr = y_arr[idx]

    k_eff = min(k, len(X_arr) - 1)
    nn = NearestNeighbors(n_neighbors=k_eff + 1)
    nn.fit(X_arr)
    neigh = nn.kneighbors(X_arr, return_distance=False)[:, 1:]
    purity = []
    for i, idxs in enumerate(neigh):
        purity.append(float(np.mean(y_arr[idxs] == y_arr[i])))
    return float(np.mean(purity))

