"""Tests for profile discovery and loading."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mechkey.profiles.loader import ProfileError, discover_profiles, load_profile
from mechkey.profiles.models import Profile


def test_bundled_demo_profile_discovered() -> None:
    profiles = discover_profiles()
    assert "demo_blue" in profiles
    profile = profiles["demo_blue"]
    assert profile.name.startswith("Demo Blue")
    assert profile.key_define_type == "multi"
    assert (profile.directory / "press.wav").is_file()
    assert (profile.directory / "release.wav").is_file()


def test_bundled_cherry_mx_brown_discovered() -> None:
    profiles = discover_profiles()
    assert "cherry_mx_brown" in profiles
    profile = profiles["cherry_mx_brown"]
    assert profile.is_sprite
    assert profile.key_define_type == "single"
    assert profile.release_sound is None
    assert (profile.directory / "sound.wav").is_file()
    assert isinstance(profile.defines.get("30"), tuple)
    assert profile.slice_for_key("30") is not None
    assert profile.slice_for_key("missing") is None


def test_load_profile_by_id() -> None:
    profile = load_profile("demo_blue")
    assert isinstance(profile, Profile)
    assert profile.sound_for_key("enter").name == "enter.wav"
    assert profile.sound_for_key("28").name == "enter.wav"
    assert profile.sound_for_key("unknown-key").name in {"press.wav", "generic.wav"}
    assert profile.release_path() is not None


def test_load_sprite_profile_by_id() -> None:
    profile = load_profile("cherry_mx_brown")
    assert profile.is_sprite
    assert profile.press_sound == "sound.wav"
    start, duration = profile.slice_for_key("57")  # space
    assert start >= 0
    assert duration > 0


def test_load_unknown_profile_raises() -> None:
    with pytest.raises(ProfileError, match="Unknown profile"):
        load_profile("does-not-exist")


def test_user_profile_overrides_bundled(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    user_dir = tmp_path / "data" / "mechkey" / "profiles" / "demo_blue"
    user_dir.mkdir(parents=True)

    # Minimal override profile reusing bundled wav names via stub files
    for name in ("generic.wav", "press.wav", "release.wav"):
        (user_dir / name).write_bytes(b"RIFF")

    (user_dir / "config.json").write_text(
        json.dumps(
            {
                "id": "demo_blue",
                "name": "User Override Blue",
                "default": "generic.wav",
                "sound": "press.wav",
                "keyup_sound": "release.wav",
                "defines": {},
            }
        ),
        encoding="utf-8",
    )

    profile = load_profile("demo_blue")
    assert profile.name == "User Override Blue"
    assert profile.directory == user_dir


def test_sprite_defines_parsed_from_user_profile(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    user_dir = tmp_path / "data" / "mechkey" / "profiles" / "sprite_test"
    user_dir.mkdir(parents=True)
    (user_dir / "sound.wav").write_bytes(b"RIFF")
    (user_dir / "config.json").write_text(
        json.dumps(
            {
                "id": "sprite_test",
                "name": "Sprite Test",
                "key_define_type": "single",
                "sound": "sound.wav",
                "keyup_sound": False,
                "defines": {"30": [100, 50], "57": [200, 60]},
            }
        ),
        encoding="utf-8",
    )

    profile = load_profile("sprite_test")
    assert profile.is_sprite
    assert profile.slice_for_key("30") == (100, 50)
    assert profile.release_path() is None


def test_key_to_id_mapping() -> None:
    from pynput.keyboard import Key, KeyCode

    from mechkey.listener import key_to_id

    assert key_to_id(Key.enter) == "28"
    assert key_to_id(Key.space) == "57"
    assert key_to_id(Key.backspace) == "14"
    assert key_to_id(KeyCode.from_char("a")) == "30"
    assert key_to_id(KeyCode.from_char("1")) == "2"
