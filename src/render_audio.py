"""Offline FluidSynth rendering, with explicit fixed synthesis settings."""
import ctypes
import ctypes.util
import hashlib
import numpy as np
import soundfile as sf
import fluidsynth
from .select_segments import timed_events
from .common import sha256

import os
from pathlib import Path

def _load_fluidsynth_library():
    candidate_names = []

    found = ctypes.util.find_library('fluidsynth')
    if found:
        candidate_names.append(found)

    env_dll = os.environ.get("FLUIDSYNTH_DLL")
    if env_dll:
        candidate_names.append(env_dll)

    tried = []
    last_error = None

    for candidate in candidate_names:
        if not candidate:
            continue
        try:
            candidate_path = Path(candidate)
            if candidate_path.is_absolute() and candidate_path.exists():
                try:
                    os.add_dll_directory(str(candidate_path.parent))
                except (AttributeError, FileNotFoundError, OSError):
                    pass
            return ctypes.CDLL(candidate)
        except OSError as exc:
            tried.append(str(candidate))
            last_error = exc

    raise RuntimeError(
        "Could not load FluidSynth library. "
        f"Tried: {tried}. "
        f"Last error: {last_error}"
    )


def render(midi_path, wav_path, soundfont, sample_rate=24000, duration=20.0, gain=0.2):
    synth = fluidsynth.Synth(gain=gain, samplerate=sample_rate,
                            **{'synth.reverb.active': 0, 'synth.chorus.active': 0,
                               'synth.cpu-cores': 1, 'synth.threadsafe-api': 0})
    library = _load_fluidsynth_library()
    write_float = library.fluid_synth_write_float
    write_float.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_int,
                            ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
    write_float.restype = ctypes.c_int
    version = library.fluid_version_str
    version.restype = ctypes.c_char_p
    total = round(duration * sample_rate)
    audio = np.zeros((total, 2), dtype=np.float32)
    position = 0
    try:
        sfid = synth.sfload(str(soundfont), update_midi_preset=0)
        if sfid < 0:
            raise RuntimeError('Could not load soundfont')
        for channel in range(16):
            if synth.program_select(channel, sfid, 0, 0) != 0:
                raise RuntimeError('Could not select Acoustic Grand Piano')
        events, _ = timed_events(midi_path)
        # An end sentinel ensures the exact requested duration is rendered.
        for time, msg in events + [(duration, None)]:
            target = min(total, round(time * sample_rate))
            if target < position:
                raise ValueError('Nonmonotonic MIDI')
            count = target - position
            if count:
                block = np.zeros((count, 2), dtype=np.float32)
                result = write_float(synth.synth, count, block.ctypes.data, 0, 2, block.ctypes.data, 1, 2)
                if result != 0:
                    raise RuntimeError('FluidSynth float rendering failed')
                audio[position:target] = block
                position = target
            if msg is None or target == total:
                continue
            if msg.type == 'note_on':
                synth.noteon(msg.channel, msg.note, msg.velocity) if msg.velocity else synth.noteoff(msg.channel, msg.note)
            elif msg.type == 'note_off':
                synth.noteoff(msg.channel, msg.note)
            elif msg.type == 'control_change':
                synth.cc(msg.channel, msg.control, msg.value)
            elif msg.type == 'pitchwheel':
                synth.pitch_bend(msg.channel, msg.pitch)
            elif msg.type == 'program_change':
                if msg.program != 0:
                    raise ValueError('Only piano program 0 is permitted')
                synth.program_select(msg.channel, sfid, 0, 0)
            elif msg.type == 'aftertouch':
                synth.channel_pressure(msg.channel, msg.value)
            elif msg.type == 'polytouch':
                synth.key_pressure(msg.channel, msg.note, msg.value)
            else:
                raise ValueError(f'Unhandled MIDI event: {msg.type}')
        mono = audio.mean(axis=1, dtype=np.float32)
        peak = float(np.abs(audio).max())
        rms = float(np.sqrt(np.mean(mono.astype(np.float64)**2)))
        if not np.isfinite(audio).all() or peak >= 1.0 or rms <= 1e-6:
            raise RuntimeError(f'Invalid, silent, or clipping render: peak={peak}, rms={rms}')
        sf.write(wav_path, mono, sample_rate, subtype='FLOAT')
        return {'renderer': 'FluidSynth', 'renderer_version': version().decode(),
                'soundfont': str(soundfont), 'soundfont_license': 'GPL-2',
                'instrument': 'TimGM6mb Acoustic Grand Piano, bank 0, program 0',
                'soundfont_sha256': sha256(soundfont), 'midi_sha256': sha256(midi_path),
                'wav_sha256': sha256(wav_path), 'sample_sha256': hashlib.sha256(mono.tobytes()).hexdigest(),
                'sample_rate': sample_rate, 'samples': total, 'duration_s': duration,
                'gain': gain, 'reverb': False, 'chorus': False, 'cpu_cores': 1,
                'stereo_peak': peak, 'mono_rms': rms, 'normalization': 'none; stereo mean to mono',
                'wav_subtype': 'FLOAT'}
    finally:
        synth.delete()
