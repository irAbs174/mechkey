"""User configuration for mechkey."""

from __future__ import annotations

import os
import sys
from dataclasses import asdict, dataclass, fields
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover
        import tomli as tomllib  # type: ignore[no-redef]


@dataclass
class Config:
    """Runtime settings persisted to TOML."""

    profile: str = "demo_blue"
    volume: int = 70
    play_release: bool = True
    mute_hotkey: str = "ctrl+alt+m"

    def normalized(self) -> Config:
        volume = max(0, min(100, int(self.volume)))
        return Config(
            profile=self.profile.strip() or "demo_blue",
            volume=volume,
            play_release=bool(self.play_release),
            mute_hotkey=self.mute_hotkey.strip().lower() or "ctrl+alt+m",
        )


def config_dir() -> Path:
    """Return the platform config directory for mechkey."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "mechkey"
    return Path.home() / ".config" / "mechkey"


def config_path() -> Path:
    return config_dir() / "config.toml"


def user_profiles_dir() -> Path:
    """Return the user-writable profiles directory."""
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / "mechkey" / "profiles"
    return Path.home() / ".local" / "share" / "mechkey" / "profiles"


def load_config(path: Path | None = None) -> Config:
    """Load config from disk, or return defaults if missing."""
    cfg_path = path or config_path()
    if not cfg_path.is_file():
        return Config().normalized()

    with cfg_path.open("rb") as fh:
        data = tomllib.load(fh)

    known = {f.name for f in fields(Config)}
    kwargs = {key: value for key, value in data.items() if key in known}
    return Config(**kwargs).normalized()


def save_config(config: Config, path: Path | None = None) -> Path:
    """Write config to TOML and return the path used."""
    cfg_path = path or config_path()
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    normalized = config.normalized()
    payload = asdict(normalized)
    lines = [
        f'profile = "{payload["profile"]}"',
        f"volume = {payload['volume']}",
        f"play_release = {'true' if payload['play_release'] else 'false'}",
        f'mute_hotkey = "{payload["mute_hotkey"]}"',
        "",
    ]
    cfg_path.write_text("\n".join(lines), encoding="utf-8")
    return cfg_path


def update_config(**changes: object) -> Config:
    """Load, patch, save, and return the updated config."""
    config = load_config()
    data = asdict(config)
    for key, value in changes.items():
        if key not in data:
            raise KeyError(f"Unknown config key: {key}")
        data[key] = value
    updated = Config(**data).normalized()
    save_config(updated)
    return updated
