"""Command-line interface for mechkey."""

from __future__ import annotations

import argparse
import os
import sys

# Must be set before pygame is imported transitively.
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from mechkey import __version__
from mechkey.app import MechkeyApp
from mechkey.config import config_path, load_config, save_config, update_config
from mechkey.profiles.loader import discover_profiles


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mechkey",
        description="Mechanical keyboard sound simulator",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"mechkey {__version__}",
    )

    sub = parser.add_subparsers(dest="command")

    run_parser = sub.add_parser("run", help="Start the sound simulator (default)")
    run_parser.add_argument("--profile", help="Sound profile id to use")
    run_parser.add_argument(
        "--volume",
        type=int,
        metavar="N",
        help="Volume 0–100 (overrides config for this session)",
    )
    run_parser.add_argument(
        "--no-release",
        action="store_true",
        help="Play press sounds only (skip key-up samples)",
    )

    sub.add_parser("list-profiles", help="List installed sound profiles")

    config_parser = sub.add_parser("config", help="Show or update configuration")
    config_sub = config_parser.add_subparsers(dest="config_command", required=True)
    config_sub.add_parser("show", help="Print the current configuration")

    set_parser = config_sub.add_parser("set", help="Update a configuration value")
    set_parser.add_argument(
        "key",
        choices=["profile", "volume", "play_release", "mute_hotkey"],
        help="Config key to change",
    )
    set_parser.add_argument("value", help="New value")

    return parser


def _cmd_run(args: argparse.Namespace) -> int:
    config = load_config()
    if args.profile:
        config.profile = args.profile
    if args.volume is not None:
        if not 0 <= args.volume <= 100:
            print("error: volume must be between 0 and 100", file=sys.stderr)
            return 2
        config.volume = args.volume
    if getattr(args, "no_release", False):
        config.play_release = False

    app = MechkeyApp(config=config)
    return app.run()


def _cmd_list_profiles() -> int:
    profiles = discover_profiles()
    if not profiles:
        print("No profiles found.")
        return 0

    width = max(len(p.id) for p in profiles.values())
    for profile_id in sorted(profiles):
        profile = profiles[profile_id]
        author = f" — {profile.author}" if profile.author else ""
        print(f"{profile.id:<{width}}  {profile.name}{author}")
        print(f"{'':<{width}}  {profile.directory}")
    return 0


def _cmd_config_show() -> int:
    config = load_config()
    path = config_path()
    print(f"config_file = {path}")
    print(f"profile = {config.profile}")
    print(f"volume = {config.volume}")
    print(f"play_release = {str(config.play_release).lower()}")
    print(f"mute_hotkey = {config.mute_hotkey}")
    return 0


def _parse_bool(value: str) -> bool:
    lowered = value.strip().lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    raise ValueError("expected true/false")


def _cmd_config_set(args: argparse.Namespace) -> int:
    key = args.key
    raw = args.value
    try:
        if key == "volume":
            value: object = int(raw)
            if not 0 <= value <= 100:
                raise ValueError("volume must be between 0 and 100")
        elif key == "play_release":
            value = _parse_bool(raw)
        else:
            value = raw
        update_config(**{key: value})
    except (ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"Updated {key}. Config written to {config_path()}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    command = args.command
    if command is None:
        # Bare `mechkey` behaves like `mechkey run`
        args.profile = getattr(args, "profile", None)
        args.volume = getattr(args, "volume", None)
        args.no_release = False
        # Re-parse as run with global flags not present; use defaults
        run_args = argparse.Namespace(profile=None, volume=None, no_release=False)
        return _cmd_run(run_args)

    if command == "run":
        return _cmd_run(args)
    if command == "list-profiles":
        return _cmd_list_profiles()
    if command == "config":
        if args.config_command == "show":
            # Ensure a config file exists with defaults for first-time users
            if not config_path().is_file():
                save_config(load_config())
            return _cmd_config_show()
        if args.config_command == "set":
            return _cmd_config_set(args)

    parser.error(f"Unknown command: {command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
