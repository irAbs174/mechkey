"""CLI smoke tests."""

from __future__ import annotations

from pathlib import Path

from mechkey.cli import main


def test_list_profiles(capsys) -> None:
    assert main(["list-profiles"]) == 0
    out = capsys.readouterr().out
    assert "demo_blue" in out
    assert "cherry_mx_brown" in out


def test_config_show_and_set(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    assert main(["config", "show"]) == 0
    assert "cherry_mx_brown" in capsys.readouterr().out

    assert main(["config", "set", "volume", "33"]) == 0
    assert main(["config", "show"]) == 0
    assert "volume = 33" in capsys.readouterr().out


def test_version(capsys) -> None:
    try:
        main(["--version"])
    except SystemExit as exc:
        assert exc.code == 0
    assert "mechkey" in capsys.readouterr().out
