"""
Lightweight cosine clustering for guest questions (no external ML service).

A simple single-pass greedy agglomerative clustering: each item joins the first
existing cluster whose centroid is within ``distance`` (cosine), otherwise it
starts a new cluster. Centroids are running means. Inputs are L2-normalised so
cosine distance is ``1 - dot``. Deterministic given the input order.

Used at two levels by the FAQ pipeline: a tight threshold to merge near-duplicate
questions, and a looser one over question-centroids to form categories.
"""

from __future__ import annotations

import numpy as np


def _normalize(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


def cluster(vectors: list[list[float]], distance: float) -> list[int]:
    """Assign each vector a cluster label (0..k-1).

    Args:
        vectors: list of equal-length embedding vectors.
        distance: max cosine distance (1 - cosine similarity) to join a cluster.

    Returns:
        A list of integer labels, one per input vector, in input order.
    """
    if not vectors:
        return []

    mat = _normalize(np.asarray(vectors, dtype=np.float64))
    labels = np.full(len(mat), -1, dtype=int)
    centroids: list[np.ndarray] = []  # normalised running-mean centroids
    sums: list[np.ndarray] = []       # raw sums (for incremental mean)
    counts: list[int] = []

    for i, vec in enumerate(mat):
        best, best_sim = -1, -1.0
        for c, centroid in enumerate(centroids):
            sim = float(np.dot(vec, centroid))
            if sim > best_sim:
                best, best_sim = c, sim
        if best != -1 and (1.0 - best_sim) <= distance:
            labels[i] = best
            sums[best] += vec
            counts[best] += 1
            updated = sums[best] / counts[best]
            n = np.linalg.norm(updated)
            centroids[best] = updated / (n if n else 1.0)
        else:
            labels[i] = len(centroids)
            centroids.append(vec.copy())
            sums.append(vec.copy())
            counts.append(1)

    return labels.tolist()


def centroid_of(vectors: list[list[float]]) -> list[float]:
    """Mean vector of a group (un-normalised; stored as the cluster centroid)."""
    return np.asarray(vectors, dtype=np.float64).mean(axis=0).tolist()
