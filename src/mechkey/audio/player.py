"""Low-latency polyphonic WAV playback via pygame.mixer."""

from __future__ import annotations

import os
import wave
from pathlib import Path

# Hide the pygame community greeting on CLI startup.
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from mechkey.profiles.models import KEYCODE_TO_LOGICAL, Profile


def _slice_wav_pcm(path: Path, start_ms: int, duration_ms: int) -> bytes:
    """Extract raw PCM bytes from a WAV for the given millisecond window."""
    with wave.open(str(path), "rb") as handle:
        rate = handle.getframerate()
        n_channels = handle.getnchannels()
        sample_width = handle.getsampwidth()
        total_frames = handle.getnframes()

        start_frame = max(0, int(rate * start_ms / 1000.0))
        frame_count = max(1, int(rate * duration_ms / 1000.0))
        if start_frame >= total_frames:
            start_frame = max(0, total_frames - frame_count)
        frame_count = min(frame_count, total_frames - start_frame)

        handle.setpos(start_frame)
        pcm = handle.readframes(frame_count)

        # pygame mixer is initialized as stereo 16-bit; expand mono if needed.
        if n_channels == 1 and sample_width == 2:
            # Interleave each mono sample into L/R.
            expanded = bytearray(len(pcm) * 2)
            for i in range(0, len(pcm), 2):
                sample = pcm[i : i + 2]
                expanded[i * 2 : i * 2 + 2] = sample
                expanded[i * 2 + 2 : i * 2 + 4] = sample
            return bytes(expanded)
        return pcm


class SoundPlayer:
    """Preloads profile sounds and plays them without blocking."""

    def __init__(self, frequency: int = 44100, channels: int = 32) -> None:
        self._frequency = frequency
        self._channels = channels
        self._volume = 0.7
        self._muted = False
        self._press: dict[str, pygame.mixer.Sound] = {}
        self._release: pygame.mixer.Sound | None = None
        self._default_press: pygame.mixer.Sound | None = None
        self._initialized = False

    def init(self) -> None:
        if self._initialized:
            return
        pygame.mixer.pre_init(self._frequency, size=-16, channels=2, buffer=512)
        pygame.mixer.init()
        pygame.mixer.set_num_channels(self._channels)
        self._initialized = True

    def close(self) -> None:
        if self._initialized:
            pygame.mixer.quit()
            self._initialized = False
        self._press.clear()
        self._release = None
        self._default_press = None

    @property
    def muted(self) -> bool:
        return self._muted

    def set_muted(self, muted: bool) -> None:
        self._muted = muted

    def toggle_mute(self) -> bool:
        self._muted = not self._muted
        return self._muted

    def set_volume(self, volume: int) -> None:
        """Set volume from 0–100."""
        self._volume = max(0.0, min(1.0, volume / 100.0))
        self._apply_volume()

    def _apply_volume(self) -> None:
        for sound in self._press.values():
            sound.set_volume(self._volume)
        if self._default_press is not None:
            self._default_press.set_volume(self._volume)
        if self._release is not None:
            self._release.set_volume(self._volume)

    def _sound_from_slice(
        self, master: Path, start_ms: int, duration_ms: int
    ) -> pygame.mixer.Sound:
        pcm = _slice_wav_pcm(master, start_ms, duration_ms)
        return pygame.mixer.Sound(buffer=pcm)

    def _load_sprite_profile(self, profile: Profile) -> None:
        master = profile.resolve(profile.press_sound)
        self._press.clear()
        self._default_press = None

        for key_id, value in profile.defines.items():
            if not isinstance(value, tuple):
                continue
            start_ms, duration_ms = value
            sound = self._sound_from_slice(master, start_ms, duration_ms)
            self._press[key_id] = sound
            if self._default_press is None:
                self._default_press = sound

        if self._default_press is None:
            # Entire file as a last resort (should not happen for valid packs).
            self._default_press = pygame.mixer.Sound(str(master))

        self._press["__press__"] = self._default_press
        self._release = None

    def _load_multi_profile(self, profile: Profile) -> None:
        self._press.clear()

        default_path = profile.resolve(profile.default_sound)
        self._default_press = pygame.mixer.Sound(str(default_path))

        press_path = profile.directory / profile.press_sound
        if press_path.is_file():
            self._press["__press__"] = pygame.mixer.Sound(str(press_path))
        else:
            self._press["__press__"] = self._default_press

        for key_id, filename in profile.defines.items():
            if not isinstance(filename, str):
                continue
            path = profile.directory / filename
            if path.is_file():
                self._press[key_id] = pygame.mixer.Sound(str(path))

        release_path = profile.release_path()
        self._release = (
            pygame.mixer.Sound(str(release_path)) if release_path is not None else None
        )

    def load_profile(self, profile: Profile) -> None:
        self.init()
        if profile.is_sprite:
            self._load_sprite_profile(profile)
        else:
            self._load_multi_profile(profile)
        self._apply_volume()

    def play_press(self, key_id: str) -> None:
        if self._muted or not self._initialized:
            return
        logical = KEYCODE_TO_LOGICAL.get(key_id)
        sound = (
            self._press.get(key_id)
            or (self._press.get(logical) if logical else None)
            or self._press.get("__press__")
            or self._default_press
        )
        if sound is not None:
            sound.play()

    def play_release(self) -> None:
        if self._muted or not self._initialized or self._release is None:
            return
        self._release.play()

    def play_file(self, path: Path) -> None:
        """Play an arbitrary WAV (mainly for testing)."""
        self.init()
        sound = pygame.mixer.Sound(str(path))
        sound.set_volume(self._volume)
        if not self._muted:
            sound.play()
