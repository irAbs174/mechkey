"""Sound profile data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# Filename aliases used by multi profiles (demo_blue) when the listener
# emits Mechvibes/iohook keycodes.
KEYCODE_TO_LOGICAL = {
    "14": "backspace",
    "28": "enter",
    "57": "space",
}


@dataclass(frozen=True)
class Profile:
    """A folder of WAV samples plus a Mechvibes-style config."""

    id: str
    name: str
    directory: Path
    author: str = ""
    license: str = ""
    key_define_type: str = "multi"
    default_sound: str = "generic.wav"
    press_sound: str = "press.wav"
    release_sound: str | None = "release.wav"
    # multi: filename str; single: (start_ms, duration_ms)
    defines: dict[str, str | tuple[int, int]] = field(default_factory=dict)

    @property
    def is_sprite(self) -> bool:
        return self.key_define_type == "single"

    def resolve(self, filename: str) -> Path:
        path = self.directory / filename
        if not path.is_file():
            raise FileNotFoundError(f"Missing sound file in profile {self.id}: {filename}")
        return path

    def sound_for_key(self, key_id: str) -> Path:
        """Return the press sound path for a multi-file profile key id."""
        if self.is_sprite:
            return self.resolve(self.press_sound)

        logical = KEYCODE_TO_LOGICAL.get(key_id, key_id)
        filename = self.defines.get(logical) or self.defines.get(key_id)
        if isinstance(filename, str):
            try:
                return self.resolve(filename)
            except FileNotFoundError:
                pass
        try:
            return self.resolve(self.press_sound)
        except FileNotFoundError:
            return self.resolve(self.default_sound)

    def slice_for_key(self, key_id: str) -> tuple[int, int] | None:
        """Return (start_ms, duration_ms) for a sprite profile key id."""
        if not self.is_sprite:
            return None
        value = self.defines.get(key_id)
        if isinstance(value, tuple) and len(value) == 2:
            return value
        return None

    def release_path(self) -> Path | None:
        if not self.release_sound:
            return None
        path = self.directory / self.release_sound
        return path if path.is_file() else None
