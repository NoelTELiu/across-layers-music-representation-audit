"""CPU-only frozen scientific consistency checks; no model or inferential runs."""
import argparse
import csv
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
import numpy as np


def verify(root):
    def rows(n, required=()):
        with (root / n).open(encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
                raise ValueError('Missing/duplicate table columns: ' + n)
            if not set(required).issubset(reader.fieldnames):
                raise ValueError('Missing scientific columns: ' + n)
            return list(reader)
    conditions = ('original', 'plus2', 'harpsichord', 'tempo150', 'pc_permutation')
    if conditions != ('original', 'plus2', 'harpsichord', 'tempo150', 'pc_permutation'):
        raise ValueError('Condition IDs changed')
    expected_order = [(i, c) for i in range(1, 31) for c in conditions]
    dataset = rows('results/dataset_manifest.csv')
    if [(int(r['formal_sample_index']), r['condition']) for r in dataset] != expected_order:
        raise ValueError('Expected 150 ordered formal instances')
    sample = rows('results/sample_manifest.csv')
    refs = rows('results/per_piece_primary.csv')
    if len(sample) != 30 or len(refs) != 30 or [int(r['formal_sample_index']) for r in refs] != list(range(1, 31)):
        raise ValueError('Expected 30 ordered pieces')
    if [int(r['formal_sample_index']) for r in sample] != list(range(1, 31)) or len({r['canonical_unit_id'] for r in sample}) != 30 or len({r['sampling_family_id'] for r in sample}) != 30:
        raise ValueError('Sample identity schema/order mismatch')
    if any(r['state'] != '12' or r['canonical_unit_id'] != sample[i]['canonical_unit_id'] for i, r in enumerate(refs)):
        raise ValueError('Frozen per-piece identity/state mismatch')
    layers = rows('results/per_piece_layers.csv')
    if len(layers) != 390 or {(int(r['formal_sample_index']), int(r['state'])) for r in layers} != {(i, s) for i in range(1, 31) for s in range(13)}:
        raise ValueError('Layer output schema/count mismatch')
    secondary = rows('results/secondary_summary.csv', ('comparator', 'mean_paired_difference', 'raw_sign_flip_p', 'holm_adjusted_p'))
    rsa = rows('results/rsa_results.csv', ('descriptor_family', 'state', 'observed_rho', 'raw_p', 'bh_adjusted_p'))
    if len(secondary) != 3 or [r['comparator'] for r in secondary] != list(conditions[1:4]):
        raise ValueError('Secondary schema/count mismatch')
    if len(rsa) != 26 or {(r['descriptor_family'], int(r['state'])) for r in rsa} != {(family, state) for family in ('symbolic', 'audio') for state in range(13)}:
        raise ValueError('RSA schema/count mismatch')
    vectors = rows('results/state12_vectors.csv')
    if [(int(r['formal_sample_index']), r['condition']) for r in vectors] != expected_order:
        raise ValueError('Vector mapping mismatch')
    z = np.array([[float(r[f'v{k:03d}']) for k in range(768)] for r in vectors], dtype=np.float64).reshape(30, 5, 768)
    sys.path.insert(0, str(root))
    from src.scientific_metrics import state12_metrics
    raw, denominator, normalized, surface, effects = state12_metrics(z)
    # Exact arithmetic/order and round-trip .17g exports reproduce saved floats.
    expected_raw = np.array([[float(r[c + '_raw_cosine_distance']) for c in conditions[1:]] for r in refs])
    expected_norm = np.array([[float(r[c + '_normalized_sensitivity']) for c in conditions[1:]] for r in refs])
    for a, b in ((raw, expected_raw), (normalized, expected_norm),
                 (denominator, np.array([float(r['between_piece_denominator']) for r in refs])),
                 (surface, np.array([float(r['surface_preserving_mean']) for r in refs])),
                 (effects, np.array([float(r['structure_discrimination']) for r in refs]))):
        if not np.array_equal(a, b):
            raise ValueError('Formal metric does not exactly reproduce frozen 4A')
    primary = json.loads((root / 'results/primary_result.json').read_bytes())
    fixed = dict(estimate=0.07988889023048976, bootstrap_95_ci=[0.005651311249042015, 0.16302219828769984], sign_flip_p=0.05959404059594041, conclusion='PRIMARY NON-CONFIRMING')
    if float(effects.mean()) != fixed['estimate'] or primary['primary_estimate'] != fixed['estimate'] or primary['bootstrap_percentile_95_ci'] != fixed['bootstrap_95_ci'] or primary['two_sided_sign_flip_p'] != fixed['sign_flip_p']:
        raise ValueError('Frozen primary result mismatch')
    if not (fixed['sign_flip_p'] > .05 and fixed['conclusion'] == 'PRIMARY NON-CONFIRMING'):
        raise ValueError('Primary conclusion changed')
    robustness = json.loads((root / 'results/robustness/summary.json').read_bytes())
    if robustness['classification'] != 'POST-FREEZE / POST-HOC / EXPLORATORY':
        raise ValueError('Robustness evidence label changed')
    if robustness['original_primary']['conclusion'] != fixed['conclusion']:
        raise ValueError('Robustness primary conclusion changed')
    if robustness['original_primary']['sign_flip_p'] != fixed['sign_flip_p'] or robustness['original_primary']['estimate'] != fixed['estimate']:
        raise ValueError('Robustness original-primary mismatch')
    if robustness['raw_distance']['mean'] != 0.00746987408086919 or robustness['raw_distance']['sign_flip_p'] != 0.025397460253974602:
        raise ValueError('Saved robustness result changed')
    if len(rows('results/robustness/raw_per_piece.csv')) != 30 or len(rows('results/robustness/leave_one_out.csv')) != 30 or len(rows('results/robustness/normalization_decomposition.csv')) != 117:
        raise ValueError('Robustness count mismatch')
    return dict(status='PASS', pieces=30, formal_instances=150,
                formal_no_clipping_metric_exact_match=True, hypothesis_tests_executed=False,
                original_primary='PRIMARY NON-CONFIRMING',
                robustness='POST-FREEZE / POST-HOC / EXPLORATORY',
                tempo150='150 BPM (1.25× faster than 120 BPM), natural 16 s')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.root.resolve()), sort_keys=True))
    except (ValueError, KeyError, OSError) as error:
        print('FAIL: ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
