"""Strict CPU-only verification of bundled frozen results/metric, not inference."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import sys
sys.dont_write_bytecode = True
import numpy as np


def verify(root):
    manifest = json.loads((root / 'MANIFEST.json').read_bytes())
    if manifest.get('schema_version') != 1:
        raise ValueError('Unknown manifest schema')
    declared = {r['path'] for r in manifest['files']}
    if len(declared) != len(manifest['files']):
        raise ValueError('Duplicate manifest path')
    # Local Git metadata is not a scientific/package artifact.
    public_paths = [p for p in root.rglob('*') if '.git' not in p.relative_to(root).parts]
    actual = {p.relative_to(root).as_posix() for p in public_paths if p.is_file()}
    if actual != declared | {'MANIFEST.json'}:
        raise ValueError('Unexpected/missing public files')
    allowed_dirs = {parent.as_posix() for n in declared for parent in Path(n).parents if str(parent) != '.'}
    if any(p.relative_to(root).as_posix() not in allowed_dirs for p in public_paths if p.is_dir()):
        raise ValueError('Unexpected directory/cache')
    for record in manifest['files']:
        p = root / record['path']
        if not p.resolve().is_relative_to(root.resolve()) or p.is_symlink():
            raise ValueError('Unsafe manifest path')
        raw = p.read_bytes()
        if len(raw) != record['bytes'] or hashlib.sha256(raw).hexdigest() != record['sha256']:
            raise ValueError('File hash mismatch: ' + record['path'])
        if p.suffix in ('.md', '.py', '.json', '.csv', '.txt'):
            s = raw.decode('utf-8')
            if '\r' in s or not raw.endswith(b'\n') or raw.startswith(b'\xef\xbb\xbf'):
                raise ValueError('Noncanonical text')
            if re.search(r'\b[A-Za-z]:[\\/]|/[h]ome/[^\s]+|Users[\\/]user|\b[c]odex\b', s, re.I):
                raise ValueError('Private/local path in public text')
            if re.search(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\bAKIA[A-Z0-9]{16}\b|\bghp_[A-Za-z0-9]{30,}\b|\bhf_[A-Za-z0-9]{30,}\b|https?://[^\s/:]+:[^\s/@]+@', s):
                raise ValueError('Potential credential in public text')
    def rows(n):
        with (root / n).open(encoding='utf-8', newline='') as f:
            return list(csv.DictReader(f))
    conditions = tuple(manifest['conditions'])
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
    if len(rows('results/secondary_summary.csv')) != 3 or len(rows('results/rsa_results.csv')) != 26:
        raise ValueError('Secondary/RSA schema/count mismatch')
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
    fixed = manifest['original_primary']
    if float(effects.mean()) != fixed['estimate'] or primary['primary_estimate'] != fixed['estimate'] or primary['bootstrap_percentile_95_ci'] != fixed['bootstrap_95_ci'] or primary['two_sided_sign_flip_p'] != fixed['sign_flip_p']:
        raise ValueError('Frozen primary result mismatch')
    if not (fixed['sign_flip_p'] > .05 and fixed['conclusion'] == 'PRIMARY NON-CONFIRMING'):
        raise ValueError('Primary conclusion changed')
    robustness = json.loads((root / 'results/robustness/summary.json').read_bytes())
    if robustness['classification'] != 'POST-FREEZE / POST-HOC / EXPLORATORY':
        raise ValueError('Robustness evidence label changed')
    if robustness['original_primary']['sign_flip_p'] != fixed['sign_flip_p'] or robustness['original_primary']['estimate'] != fixed['estimate']:
        raise ValueError('Robustness original-primary mismatch')
    if robustness['raw_distance']['mean'] != 0.00746987408086919 or robustness['raw_distance']['sign_flip_p'] != 0.025397460253974602:
        raise ValueError('Saved robustness result changed')
    if len(rows('results/robustness/raw_per_piece.csv')) != 30 or len(rows('results/robustness/leave_one_out.csv')) != 30 or len(rows('results/robustness/normalization_decomposition.csv')) != 117:
        raise ValueError('Robustness count mismatch')
    readme = (root / 'README.md').read_text(encoding='utf-8')
    if '150 BPM' not in readme or '1.25' not in readme or 'tempo150' not in readme:
        raise ValueError('tempo150 label missing')
    for p in root.rglob('*.md'):
        for url in re.findall(r'\]\(([^)]+)\)', p.read_text(encoding='utf-8')):
            if url.startswith('https://'):
                continue
            target = (p.parent / url).resolve()
            if not target.is_relative_to(root.resolve()) or not target.exists():
                raise ValueError('Broken/unsafe public link')
    return dict(status='PASS', pieces=30, formal_instances=150, files=len(actual),
                formal_no_clipping_metric_exact_4a_match=True, hypothesis_tests_executed=False,
                original_primary='NON-CONFIRMING', tempo150=manifest['tempo150'])


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
