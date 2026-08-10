"""Sound profile data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Profile:
    """A folder of WAV samples plus a Mechvibes-style config."""

    id: str
    name: str
    directory: Path
    author: str = ""
    license: str = ""
    default_sound: str = "generic.wav"
    press_sound: str = "press.wav"
    release_sound: str | None = "release.wav"
    defines: dict[str, str] = field(default_factory=dict)

    def resolve(self, filename: str) -> Path:
        path = self.directory / filename
        if not path.is_file():
            raise FileNotFoundError(f"Missing sound file in profile {self.id}: {filename}")
        return path

    def sound_for_key(self, key_id: str) -> Path:
        """Return the press sound path for a logical key id."""
        filename = self.defines.get(key_id) or self.press_sound or self.default_sound
        try:
            return self.resolve(filename)
        except FileNotFoundError:
            return self.resolve(self.default_sound)

    def release_path(self) -> Path | None:
        if not self.release_sound:
            return None
        path = self.directory / self.release_sound
        return path if path.is_file() else None
