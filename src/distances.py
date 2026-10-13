"""Paired cosine distance for time-mean-pooled hidden states."""
import numpy as np


def cosine_distances(original, transformed):
    a, b = np.asarray(original, dtype=np.float64), np.asarray(transformed, dtype=np.float64)
    if a.ndim != 2 or a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Expected finite, equal [state, feature] arrays')
    denom = np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1)
    if np.any(denom == 0):
        raise ValueError('Cosine distance is undefined for zero vectors')
    return np.clip(1.0 - np.sum(a * b, axis=1) / denom, 0.0, 2.0)
