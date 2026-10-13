"""CPU-only formal metric regression against exported frozen state-12 data."""
import csv
from pathlib import Path
import numpy as np
import pytest
from src.scientific_metrics import cosine, state12_metrics

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_state12_raw_reference_sensitivities_and_effects():
    data = ROOT / 'results'
    if not (data / 'state12_vectors.csv').exists():
        data = ROOT / 'dist/music-representation-audit-public-build/results'
    with (data / 'state12_vectors.csv').open(encoding='utf-8', newline='') as f:
        vectors = list(csv.DictReader(f))
    with (data / 'per_piece_primary.csv').open(encoding='utf-8', newline='') as f:
        refs = list(csv.DictReader(f))
    conditions = ('plus2', 'harpsichord', 'tempo150', 'pc_permutation')
    z = np.array([[float(r[f'v{i:03d}']) for i in range(768)] for r in vectors]).reshape(30, 5, 768)
    raw, denominator, normalized, surface, effects = state12_metrics(z)
    np.testing.assert_array_equal(raw, [[float(r[c + '_raw_cosine_distance']) for c in conditions] for r in refs])
    np.testing.assert_array_equal(denominator, [float(r['between_piece_denominator']) for r in refs])
    np.testing.assert_array_equal(normalized, [[float(r[c + '_normalized_sensitivity']) for c in conditions] for r in refs])
    np.testing.assert_array_equal(surface, [float(r['surface_preserving_mean']) for r in refs])
    np.testing.assert_array_equal(effects, [float(r['structure_discrimination']) for r in refs])


@pytest.mark.parametrize('value', [0.0, np.nan, np.inf])
def test_invalid_vectors_stop(value):
    with pytest.raises(ValueError):
        cosine(np.full(768, value), np.ones(768))


def test_cosine_has_no_clipping_or_epsilon():
    # Floating self-distance can be negative; keep the exact formal expression.
    a = np.random.default_rng(12).normal(size=(50, 768))
    expected = 1.0 - np.sum(a * a, axis=-1) / np.linalg.norm(a, axis=-1) ** 2
    np.testing.assert_array_equal(cosine(a, a), expected)
    assert (expected < 0).any()


def test_invalid_piece_condition_shape_stops():
    with pytest.raises(ValueError):
        state12_metrics(np.ones((29, 5, 768)))
