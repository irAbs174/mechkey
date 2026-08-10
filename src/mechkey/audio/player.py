"""Low-latency polyphonic WAV playback via pygame.mixer."""

from __future__ import annotations

import os
from pathlib import Path

# Hide the pygame community greeting on CLI startup.
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from mechkey.profiles.models import Profile


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

    def load_profile(self, profile: Profile) -> None:
        self.init()
        self._press.clear()

        default_path = profile.resolve(profile.default_sound)
        self._default_press = pygame.mixer.Sound(str(default_path))

        press_path = profile.directory / profile.press_sound
        if press_path.is_file():
            self._press["__press__"] = pygame.mixer.Sound(str(press_path))
        else:
            self._press["__press__"] = self._default_press

        for key_id, filename in profile.defines.items():
            path = profile.directory / filename
            if path.is_file():
                self._press[key_id] = pygame.mixer.Sound(str(path))

        release_path = profile.release_path()
        self._release = (
            pygame.mixer.Sound(str(release_path)) if release_path is not None else None
        )
        self._apply_volume()

    def play_press(self, key_id: str) -> None:
        if self._muted or not self._initialized:
            return
        sound = self._press.get(key_id) or self._press.get("__press__") or self._default_press
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
