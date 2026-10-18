"""Engineering fixtures only: never used as research data or MERT inputs."""
from pathlib import Path
import mido
import numpy as np
import pytest
from src.common import load_config
from src.select_segments import crop, timed_events, write_events
from src.transform_midi import transpose, validate_transposition
from src.distances import cosine_distances
from src.render_audio import render


def message(kind, **kwargs):
    return mido.Message(kind, channel=0, **kwargs)


def test_crop_carries_sustain_and_preserves_timing(tmp_path):
    source, segment = tmp_path/'source.mid', tmp_path/'segment.mid'
    events = [(18.0, message('control_change', control=64, value=127)),
              (18.5, message('note_on', note=60, velocity=80)),
              (19.0, message('note_off', note=60, velocity=0)),
              (19.5, message('note_on', note=65, velocity=90)),
              (21.0, message('note_off', note=65, velocity=0)),
              (21.5, message('control_change', control=64, value=0))]
    for i in range(20):
        events.extend([(22+i/2, message('note_on', note=70, velocity=70)),
                       (22.2+i/2, message('note_off', note=70, velocity=0))])
    events.extend([(39.5, message('note_on', note=72, velocity=75)),
                   (42.0, message('note_off', note=72, velocity=0))])
    write_events(events, source, 100.0)
    result = crop(source, segment, 100.0, load_config())
    assert result['start_s'] == 20.0 and result['carried_key_notes'] == 1
    assert result['carried_sustain_notes'] == 1
    extracted, duration = timed_events(segment)
    assert duration == pytest.approx(20)
    assert any(t == 0 and m.type == 'note_on' and m.note == 60 for t,m in extracted)
    assert any(t == 0 and m.type == 'note_off' and m.note == 60 for t,m in extracted)
    assert any(t == pytest.approx(1) and m.type == 'note_off' and m.note == 65 for t,m in extracted)
    assert any(t == pytest.approx(20) and m.type == 'note_off' and m.note == 72 for t,m in extracted)
    transformed = tmp_path/'plus2.mid'
    transpose(segment, transformed)
    assert validate_transposition(segment, transformed)['exact_transposition']


def test_sparse_window_shifts_deterministically(tmp_path):
    source, segment = tmp_path/'source.mid', tmp_path/'segment.mid'
    events = []
    for i in range(20):
        events.extend([(40+i/100, message('note_on', note=60+i, velocity=70)),
                       (40.005+i/100, message('note_off', note=60+i, velocity=0))])
    write_events(events, source, 100)
    config = load_config()
    config['minimum_onset_bins'] = 1  # Isolate the onset-count shift logic.
    result = crop(source, segment, 100, config)
    assert result['start_s'] == 21 and result['sparse_shifts'] == 1


def test_transpose_rejects_pitch_overflow(tmp_path):
    source = tmp_path/'high.mid'
    write_events([(0, message('note_on', note=126, velocity=70))], source, 1)
    with pytest.raises(ValueError, match='Out-of-range'):
        transpose(source, tmp_path/'bad.mid')


def test_cosine_known_geometry_and_degenerate_inputs():
    a = np.array([[1,0], [1,0], [1,0]])
    b = np.array([[1,0], [0,1], [-1,0]])
    np.testing.assert_allclose(cosine_distances(a,b), [0,1,2])
    with pytest.raises(ValueError):
        cosine_distances(np.zeros((1,2)), np.ones((1,2)))
    with pytest.raises(ValueError):
        cosine_distances(a, np.full_like(a, np.nan, dtype=float))


def test_render_reproducibility_and_transposition(tmp_path):
    config = load_config()
    assert Path(config['soundfont']).exists(), 'Install the documented soundfont'
    source, shifted = tmp_path/'test.mid', tmp_path/'test_plus2.mid'
    write_events([(0, message('note_on', note=60, velocity=90)),
                  (0.5, message('note_off', note=60, velocity=0))], source, 1)
    transpose(source, shifted)
    kwargs = dict(soundfont=config['soundfont'], duration=1, sample_rate=24000)
    a = render(source, tmp_path/'a.wav', **kwargs)
    b = render(source, tmp_path/'b.wav', **kwargs)
    c = render(shifted, tmp_path/'c.wav', **kwargs)
    assert a['sample_sha256'] == b['sample_sha256']
    assert a['sample_sha256'] != c['sample_sha256']
    assert a['samples'] == 24000 and a['mono_rms'] > 0 and a['stereo_peak'] < 1


def test_crop_rejects_concentrated_activity(tmp_path):
    source = tmp_path/'sparse.mid'
    events = []
    for i in range(20):
        events.extend([(22+i/100, message('note_on', note=60+i, velocity=70)),
                       (22.005+i/100, message('note_off', note=60+i, velocity=0))])
    write_events(events, source, 100)
    with pytest.raises(RuntimeError, match='No suitable segment'):
        crop(source, tmp_path/'segment.mid', 100, load_config())
