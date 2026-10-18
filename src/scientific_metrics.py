"""Formal float64 audit metrics; no clipping, epsilon, repair or inference."""
import numpy as np

CONDITIONS = ('original', 'plus2', 'harpsichord', 'tempo150', 'pc_permutation')


def cosine(a, b):
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if a.shape != b.shape or a.shape[-1:] != (768,):
        raise ValueError('Expected equal vectors with 768 features')
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Nonfinite vector')
    na, nb = np.linalg.norm(a, axis=-1), np.linalg.norm(b, axis=-1)
    if not (np.isfinite(na).all() and np.isfinite(nb).all()
            and (na > 0).all() and (nb > 0).all()):
        raise ValueError('Nonfinite or nonpositive norm')
    value = 1.0 - np.sum(a * b, axis=-1) / (na * nb)
    if not np.isfinite(value).all():
        raise ValueError('Nonfinite distance')
    return value


def state12_metrics(vectors):
    vectors = np.asarray(vectors, dtype=np.float64)
    if vectors.shape != (30, 5, 768):
        raise ValueError('Expected 30 ordered pieces and five conditions')
    raw = np.stack([cosine(vectors[:, 0], vectors[:, j]) for j in range(1, 5)], axis=1)
    denominator = np.array([
        np.median(cosine(np.broadcast_to(vectors[i, 0], (29, 768)),
                         np.delete(vectors[:, 0], i, axis=0))) for i in range(30)])
    if not np.isfinite(denominator).all() or not (denominator > 0).all():
        raise ValueError('Nonfinite or nonpositive reference denominator')
    normalized = raw / denominator[:, None]
    surface = normalized[:, :3].mean(axis=1)
    effect = normalized[:, 3] - surface
    return raw, denominator, normalized, surface, effect
