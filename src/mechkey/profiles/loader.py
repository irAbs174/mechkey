"""Discover and load sound profiles from bundled and user directories."""

from __future__ import annotations

import json
from pathlib import Path

from mechkey.config import user_profiles_dir
from mechkey.profiles.models import Profile


class ProfileError(ValueError):
    """Raised when a profile cannot be loaded."""


def bundled_profiles_dir() -> Path:
    """Return the filesystem path to package-bundled profiles."""
    candidate = Path(__file__).resolve().parents[1] / "assets" / "profiles"
    if candidate.is_dir():
        return candidate
    raise ProfileError("Bundled profiles directory not found")


def _profile_roots() -> list[Path]:
    roots: list[Path] = []
    try:
        roots.append(bundled_profiles_dir())
    except ProfileError:
        pass

    user_dir = user_profiles_dir()
    if user_dir.is_dir():
        roots.append(user_dir)
    return roots


def _parse_defines(
    defines_raw: dict,
    key_define_type: str,
    config_file: Path,
) -> dict[str, str | tuple[int, int]]:
    defines: dict[str, str | tuple[int, int]] = {}
    for key, value in defines_raw.items():
        key_id = str(key).lower()
        if value is None:
            continue
        if key_define_type == "single":
            if isinstance(value, (list, tuple)) and len(value) >= 2:
                defines[key_id] = (int(value[0]), int(value[1]))
            else:
                raise ProfileError(
                    f"Sprite define for '{key_id}' must be [start_ms, duration_ms] "
                    f"in {config_file}"
                )
        else:
            defines[key_id] = str(value)
    return defines


def _load_from_directory(directory: Path) -> Profile:
    config_file = directory / "config.json"
    if not config_file.is_file():
        raise ProfileError(f"Missing config.json in {directory}")

    try:
        raw = json.loads(config_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ProfileError(f"Invalid JSON in {config_file}: {exc}") from exc

    profile_id = str(raw.get("id") or directory.name)
    name = str(raw.get("name") or profile_id)
    defines_raw = raw.get("defines") or {}
    if not isinstance(defines_raw, dict):
        raise ProfileError(f"'defines' must be an object in {config_file}")

    key_define_type = str(raw.get("key_define_type") or "multi").lower()
    if key_define_type not in {"single", "multi"}:
        raise ProfileError(
            f"'key_define_type' must be 'single' or 'multi' in {config_file}"
        )

    defines = _parse_defines(defines_raw, key_define_type, config_file)
    keyup = raw.get("keyup_sound")
    release_sound = None if keyup in (None, "", False) else str(keyup)

    if key_define_type == "single":
        press_sound = str(raw.get("sound") or "sound.wav")
        default_sound = str(raw.get("default") or press_sound)
    else:
        default_sound = str(raw.get("default") or "generic.wav")
        press_sound = str(raw.get("sound") or raw.get("default") or "press.wav")

    return Profile(
        id=profile_id,
        name=name,
        directory=directory,
        author=str(raw.get("author") or ""),
        license=str(raw.get("license") or ""),
        key_define_type=key_define_type,
        default_sound=default_sound,
        press_sound=press_sound,
        release_sound=release_sound,
        defines=defines,
    )


def discover_profiles() -> dict[str, Profile]:
    """
    Discover all profiles.

    User profiles override bundled ones when ids collide.
    """
    found: dict[str, Profile] = {}
    for root in _profile_roots():
        for child in sorted(p for p in root.iterdir() if p.is_dir()):
            if not (child / "config.json").is_file():
                continue
            try:
                profile = _load_from_directory(child)
            except ProfileError:
                continue
            found[profile.id] = profile
    return found


def load_profile(profile_id: str) -> Profile:
    """Load a single profile by id or raise ProfileError."""
    profiles = discover_profiles()
    if profile_id not in profiles:
        available = ", ".join(sorted(profiles)) or "(none)"
        raise ProfileError(f"Unknown profile '{profile_id}'. Available: {available}")
    return profiles[profile_id]
