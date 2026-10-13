"""Scientific consistency and independence from presentation files."""
import importlib.util
import json
from pathlib import Path
import shutil
import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('result_verifier', ROOT / 'scripts/verify_results.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_frozen_results():
    result = MODULE.verify(ROOT)
    assert result['status'] == 'PASS'
    assert result['original_primary'] == 'PRIMARY NON-CONFIRMING'
    assert result['hypothesis_tests_executed'] is False


@pytest.fixture
def result_tree(tmp_path):
    shutil.copytree(ROOT / 'results', tmp_path / 'results')
    return tmp_path


def test_documentation_is_not_a_verification_input(result_tree):
    # No report or source snapshot is needed, and added prose is harmless.
    (result_tree / 'README.md').write_text('Editable portfolio introduction')
    (result_tree / 'extra_notes.md').write_text('Additional documentation')
    assert MODULE.verify(result_tree)['status'] == 'PASS'


@pytest.mark.parametrize('target,key,value', [
    ('primary_result.json', 'two_sided_sign_flip_p', 0.01),
    ('robustness/summary.json', 'classification', 'PRIMARY'),
])
def test_changed_scientific_values_are_rejected(result_tree, target, key, value):
    path = result_tree / 'results' / target
    data = json.loads(path.read_text())
    data[key] = value
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        MODULE.verify(result_tree)


def test_missing_formal_instance_is_rejected(result_tree):
    path = result_tree / 'results/dataset_manifest.csv'
    path.write_text(''.join(path.read_text().splitlines(keepends=True)[:-1]))
    with pytest.raises(ValueError, match='150 ordered'):
        MODULE.verify(result_tree)
