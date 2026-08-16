"""Tests for sprite WAV slicing in SoundPlayer."""

from __future__ import annotations

import struct
import wave
from pathlib import Path

from mechkey.audio.player import SoundPlayer, _slice_wav_pcm
from mechkey.profiles.models import Profile


def _write_tone_wav(path: Path, duration_s: float = 1.0, rate: int = 44100) -> None:
    """Write a short stereo PCM WAV with a recognizable amplitude pattern."""
    n_frames = int(rate * duration_s)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        frames = bytearray()
        for i in range(n_frames):
            # Quiet then louder after 500ms so slices differ.
            amp = 8000 if i > rate // 2 else 1000
            sample = struct.pack("<hh", amp, amp)
            frames.extend(sample)
        handle.writeframes(frames)


def test_slice_wav_pcm_extracts_window(tmp_path: Path) -> None:
    wav = tmp_path / "tone.wav"
    _write_tone_wav(wav, duration_s=1.0)
    early = _slice_wav_pcm(wav, start_ms=0, duration_ms=100)
    late = _slice_wav_pcm(wav, start_ms=600, duration_ms=100)
    assert len(early) > 0
    assert len(late) > 0
    assert early != late


def test_sound_player_loads_sprite_profile(tmp_path: Path) -> None:
    wav = tmp_path / "sound.wav"
    _write_tone_wav(wav, duration_s=1.0)
    profile = Profile(
        id="sprite",
        name="Sprite",
        directory=tmp_path,
        key_define_type="single",
        press_sound="sound.wav",
        default_sound="sound.wav",
        release_sound=None,
        defines={"30": (0, 80), "57": (600, 80)},
    )
    player = SoundPlayer()
    try:
        player.load_profile(profile)
        player.set_volume(50)
        player.play_press("30")
        player.play_press("57")
        player.play_press("999")  # fallback
        player.play_release()  # no-op without release
    finally:
        player.close()
