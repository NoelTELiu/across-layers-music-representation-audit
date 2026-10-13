"""Deterministic 20-second cropping with explicit boundary-state reconstruction."""
from collections import defaultdict
import mido
from .common import sha256

TICKS_PER_BEAT = 10000  # 50 microseconds/tick at 120 BPM


def timed_events(path):
    midi = mido.MidiFile(path)
    if midi.type == 2:
        raise ValueError('Asynchronous MIDI type 2 is unsupported')
    time = 0.0
    events = []
    for msg in midi:
        time += msg.time
        if not msg.is_meta:
            events.append((time, msg.copy(time=0)))
    return events, time


def write_events(events, path, duration):
    output = mido.MidiFile(type=0, ticks_per_beat=TICKS_PER_BEAT)
    track = mido.MidiTrack()
    output.tracks.append(track)
    track.append(mido.MetaMessage('set_tempo', tempo=500000, time=0))
    last_tick = 0
    for time, msg in sorted(events, key=lambda item: item[0]):
        tick = round(time * 2 * TICKS_PER_BEAT)
        track.append(msg.copy(time=tick - last_tick))
        last_tick = tick
    final_tick = round(duration * 2 * TICKS_PER_BEAT)
    track.append(mido.MetaMessage('end_of_track', time=max(0, final_tick-last_tick)))
    output.save(path)


def crop(source, destination, metadata_duration, config):
    events, midi_duration = timed_events(source)
    duration = config['segment_duration_s']
    start = config['start_fraction'] * float(metadata_duration)
    initial_start = start
    while start + duration <= midi_duration:
        onset_count = sum(start <= t < start + duration and msg.type == 'note_on' and msg.velocity > 0 for t, msg in events)
        active_bins = len({min(19, int(t-start)) for t, msg in events
                           if start <= t < start + duration and msg.type == 'note_on' and msg.velocity > 0})
        if onset_count >= config['minimum_onsets'] and active_bins >= config['minimum_onset_bins']:
            break
        start += config['sparse_shift_s']
    else:
        raise RuntimeError('No suitable segment in the single selected piece; stop, do not select extra pieces.')
    end = start + duration
    channels = sorted({msg.channel for _, msg in events if hasattr(msg, 'channel')})
    if any(msg.type == 'control_change' and msg.control == 66 and msg.value != 0 for t, msg in events if t < end):
        raise RuntimeError('Sostenuto pedal boundary semantics require explicit implementation before proceeding.')
    # Track physical keys plus sustain-held notes; preserve controller state at the cut.
    controls, programs, wheels = {}, {}, {}
    keys, sustained = {}, {}
    sustain = defaultdict(bool)
    for t, msg in events:
        if t >= start:
            break
        ch = getattr(msg, 'channel', 0)
        if msg.type == 'program_change':
            programs[ch] = msg
        elif msg.type == 'pitchwheel':
            wheels[ch] = msg
        elif msg.type == 'control_change':
            controls[ch, msg.control] = msg
            if msg.control == 64:
                sustain[ch] = msg.value >= 64
                if not sustain[ch]:
                    sustained = {k:v for k,v in sustained.items() if k[0] != ch}
            elif msg.control in (120, 123):
                raise RuntimeError('All-notes/sound-off before crop needs explicit boundary handling')
        elif msg.type == 'note_on' and msg.velocity > 0:
            keys[ch, msg.note] = msg.velocity
            sustained.pop((ch, msg.note), None)
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            velocity = keys.pop((ch, msg.note), None)
            if velocity is not None and sustain[ch]:
                sustained[ch, msg.note] = velocity
    if any(msg.program != 0 for msg in programs.values()):
        raise RuntimeError('Selected source is not program-0 piano')
    cropped = []
    for ch in channels:
        cropped.append((0.0, programs.get(ch, mido.Message('program_change', channel=ch, program=0))))
    cropped.extend((0.0, msg) for _, msg in sorted(controls.items()))
    cropped.extend((0.0, msg) for _, msg in sorted(wheels.items()))
    for (ch, pitch), velocity in sorted({**sustained, **keys}.items()):
        cropped.append((0.0, mido.Message('note_on', channel=ch, note=pitch, velocity=velocity)))
        if (ch, pitch) not in keys:
            cropped.append((0.0, mido.Message('note_off', channel=ch, note=pitch, velocity=0)))
    cropped.extend((t-start, msg) for t, msg in events if start <= t < end)
    for ch in channels:
        for pitch in sorted({msg.note for _, msg in cropped if msg.type in ('note_on', 'note_off') and msg.channel == ch}):
            cropped.append((duration, mido.Message('note_off', channel=ch, note=pitch, velocity=0)))
        cropped.append((duration, mido.Message('control_change', channel=ch, control=64, value=0)))
    write_events(cropped, destination, duration)
    return {'start_s': start, 'end_s': end, 'duration_s': duration, 'initial_start_s': initial_start,
            'sparse_shifts': round((start-initial_start)/config['sparse_shift_s']),
            'source_duration_s': midi_duration, 'metadata_duration_s': metadata_duration,
            'onsets_in_source_window': onset_count, 'one_second_bins_with_onsets': active_bins, 'carried_key_notes': len(keys),
            'carried_sustain_notes': len(sustained), 'tick_resolution_s': 0.00005,
            'source_sha256': sha256(source), 'segment_sha256': sha256(destination)}
