"""Tests for configuration loading and persistence."""

from __future__ import annotations

from pathlib import Path

from mechkey.config import Config, load_config, save_config, update_config


def test_load_config_defaults_when_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    config = load_config()
    assert config.profile == "cherry_mx_brown"
    assert config.volume == 70
    assert config.play_release is True
    assert config.mute_hotkey == "ctrl+alt+m"


def test_save_and_load_roundtrip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    original = Config(
        profile="custom",
        volume=42,
        play_release=False,
        mute_hotkey="ctrl+shift+m",
    )
    path = save_config(original)
    assert path.is_file()

    loaded = load_config()
    assert loaded.profile == "custom"
    assert loaded.volume == 42
    assert loaded.play_release is False
    assert loaded.mute_hotkey == "ctrl+shift+m"


def test_volume_clamped(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    save_config(Config(volume=250))
    assert load_config().volume == 100
    save_config(Config(volume=-5))
    assert load_config().volume == 0


def test_update_config(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    updated = update_config(profile="demo_blue", volume=55)
    assert updated.volume == 55
    assert load_config().volume == 55
