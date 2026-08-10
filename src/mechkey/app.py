"""Application wiring for the mechanical keyboard sound simulator."""

from __future__ import annotations

import signal
import sys

from mechkey.audio.player import SoundPlayer
from mechkey.config import Config, load_config
from mechkey.listener import KeyboardListener
from mechkey.profiles.loader import ProfileError, load_profile


class MechkeyApp:
    """Coordinate config, profile audio, and the global keyboard listener."""

    def __init__(self, config: Config | None = None, player: SoundPlayer | None = None) -> None:
        self.config = (config or load_config()).normalized()
        self.player = player or SoundPlayer()
        self._listener: KeyboardListener | None = None
        self._play_release = self.config.play_release

    def setup(self, profile_id: str | None = None, volume: int | None = None) -> None:
        if profile_id:
            self.config.profile = profile_id
        if volume is not None:
            self.config.volume = volume
        self.config = self.config.normalized()
        self._play_release = self.config.play_release

        profile = load_profile(self.config.profile)
        self.player.load_profile(profile)
        self.player.set_volume(self.config.volume)

    def _on_press(self, key_id: str) -> None:
        self.player.play_press(key_id)

    def _on_release(self) -> None:
        if self._play_release:
            self.player.play_release()

    def _on_mute_toggle(self) -> None:
        muted = self.player.toggle_mute()
        state = "muted" if muted else "unmuted"
        print(f"mechkey: {state}", file=sys.stderr)

    def run(self) -> int:
        try:
            self.setup()
        except ProfileError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

        self._listener = KeyboardListener(
            on_press=self._on_press,
            on_release=self._on_release if self._play_release else None,
            mute_hotkey=self.config.mute_hotkey,
            on_mute_toggle=self._on_mute_toggle,
        )

        def _shutdown(signum: int, frame: object) -> None:
            del signum, frame
            self.stop()

        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)

        print(
            f"mechkey: playing profile '{self.config.profile}' "
            f"(volume={self.config.volume}%, mute={self.config.mute_hotkey})",
            file=sys.stderr,
        )
        print("mechkey: press Ctrl+C to stop", file=sys.stderr)

        self._listener.start()
        try:
            self._listener.join()
        finally:
            self.stop()
        return 0

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
        self.player.close()
