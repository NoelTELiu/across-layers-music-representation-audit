"""Exact global symbolic transposition, without timing or velocity changes."""
import mido


def transpose(source, destination, semitones=2):
    if semitones != 2:
        raise ValueError('Only +2 semitones is supported by this helper')
    midi = mido.MidiFile(source)
    for track in midi.tracks:
        for msg in track:
            if msg.type in ('note_on', 'note_off', 'polytouch'):
                # Do not clip or wrap out-of-range musical pitches.
                if not 0 <= msg.note + semitones <= 127:
                    raise ValueError(f'Out-of-range transposition: {msg.note}')
                msg.note += semitones
    midi.save(destination)


def validate_transposition(original, transformed, semitones=2):
    a, b = mido.MidiFile(original), mido.MidiFile(transformed)
    assert a.ticks_per_beat == b.ticks_per_beat and len(a.tracks) == len(b.tracks)
    count = 0
    for ta, tb in zip(a.tracks, b.tracks):
        assert len(ta) == len(tb)
        for ma, mb in zip(ta, tb):
            da, db = ma.dict(), mb.dict()
            if 'note' in da:
                assert db['note'] == da['note'] + semitones
                db['note'] -= semitones
                count += ma.type == 'note_on' and ma.velocity > 0
            assert da == db, f'Non-pitch event changed: {ma} -> {mb}'
    assert count > 0
    return {'exact_transposition': True, 'positive_note_on_events': count}
