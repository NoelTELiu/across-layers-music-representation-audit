"""Bundled result integrity only; no new scientific inference."""
import importlib.util
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def test_public_bundle_integrity():
    spec = importlib.util.spec_from_file_location('public_verifier', ROOT / 'scripts/verify_public_release.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.verify(ROOT)
    assert result['status'] == 'PASS'
    assert result['original_primary'] == 'NON-CONFIRMING'
    assert result['hypothesis_tests_executed'] is False
