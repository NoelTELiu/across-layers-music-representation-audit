"""Small provenance and file helpers."""
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    os.replace(temp, path)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def load_config(path=ROOT / 'configs/smoke.json'):
    c = json.loads(Path(path).read_text())
    soundfont_override = os.environ.get("TIMGM6MB_SF2")
    if soundfont_override:
        c["soundfont"] = soundfont_override
    assert c['max_pieces'] == 1, 'This engineering fixture configuration supports exactly one piece.'
    assert c['model_id'] == 'm-a-p/MERT-v1-95M'
    assert c['dataset'] == 'MAESTRO' and c['dataset_version'] == '3.0.0'
    assert c['transpose_semitones'] == 2 and c['segment_duration_s'] == 20
    assert c['sample_rate'] == 24000
    return c
