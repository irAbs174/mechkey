"""Global keyboard listener built on pynput."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pynput import keyboard


KeyHandler = Callable[[str], None]
ReleaseHandler = Callable[[], None]
HotkeyHandler = Callable[[], None]


def key_to_id(key: Any) -> str:
    """Map a pynput key to a logical sound id."""
    if isinstance(key, keyboard.KeyCode):
        char = key.char
        if char is not None and char.isprintable():
            return "generic"
        return "generic"

    special_map = {
        keyboard.Key.enter: "enter",
        keyboard.Key.space: "space",
        keyboard.Key.backspace: "backspace",
        keyboard.Key.tab: "generic",
        keyboard.Key.esc: "generic",
        keyboard.Key.delete: "backspace",
    }
    return special_map.get(key, "generic")


def parse_hotkey(spec: str) -> set[str]:
    """
    Parse a hotkey string like 'ctrl+alt+m' into normalized modifier/key tokens.
    """
    parts = [p.strip().lower() for p in spec.split("+") if p.strip()]
    aliases = {
        "control": "ctrl",
        "ctl": "ctrl",
        "option": "alt",
        "cmd": "cmd",
        "super": "cmd",
        "win": "cmd",
        "meta": "cmd",
    }
    return {aliases.get(p, p) for p in parts}


class KeyboardListener:
    """Listen for key press/release and optional mute hotkey."""

    def __init__(
        self,
        on_press: KeyHandler,
        on_release: ReleaseHandler | None = None,
        mute_hotkey: str = "ctrl+alt+m",
        on_mute_toggle: HotkeyHandler | None = None,
    ) -> None:
        self._on_press = on_press
        self._on_release = on_release
        self._on_mute_toggle = on_mute_toggle
        self._hotkey_parts = parse_hotkey(mute_hotkey)
        self._pressed_modifiers: set[str] = set()
        self._pressed_keys: set[Any] = set()
        self._listener: keyboard.Listener | None = None
        self._hotkey_latched = False

    def _modifier_name(self, key: Any) -> str | None:
        mapping = {
            keyboard.Key.ctrl: "ctrl",
            keyboard.Key.ctrl_l: "ctrl",
            keyboard.Key.ctrl_r: "ctrl",
            keyboard.Key.alt: "alt",
            keyboard.Key.alt_l: "alt",
            keyboard.Key.alt_r: "alt",
            keyboard.Key.alt_gr: "alt",
            keyboard.Key.shift: "shift",
            keyboard.Key.shift_l: "shift",
            keyboard.Key.shift_r: "shift",
            keyboard.Key.cmd: "cmd",
            keyboard.Key.cmd_l: "cmd",
            keyboard.Key.cmd_r: "cmd",
        }
        return mapping.get(key)

    def _key_token(self, key: Any) -> str | None:
        mod = self._modifier_name(key)
        if mod:
            return mod
        if isinstance(key, keyboard.KeyCode) and key.char:
            return key.char.lower()
        if key == keyboard.Key.space:
            return "space"
        return None

    def _hotkey_active(self, key: Any) -> bool:
        if not self._hotkey_parts or self._on_mute_toggle is None:
            return False
        token = self._key_token(key)
        if token is None:
            return False
        current = set(self._pressed_modifiers)
        if token not in {"ctrl", "alt", "shift", "cmd"}:
            current.add(token)
        return self._hotkey_parts.issubset(current | ({token} if token else set()))

    def _handle_press(self, key: Any) -> None:
        if key in self._pressed_keys:
            return
        self._pressed_keys.add(key)

        mod = self._modifier_name(key)
        if mod:
            self._pressed_modifiers.add(mod)

        if self._hotkey_active(key) and not self._hotkey_latched:
            self._hotkey_latched = True
            if self._on_mute_toggle:
                self._on_mute_toggle()
            return

        # Skip pure modifier keys for typing sounds
        if mod:
            return

        self._on_press(key_to_id(key))

    def _handle_release(self, key: Any) -> None:
        self._pressed_keys.discard(key)
        mod = self._modifier_name(key)
        if mod:
            self._pressed_modifiers.discard(mod)

        token = self._key_token(key)
        if token and token in self._hotkey_parts:
            self._hotkey_latched = False

        if mod:
            return
        if self._on_release:
            self._on_release()

    def start(self) -> None:
        self._listener = keyboard.Listener(
            on_press=self._handle_press,
            on_release=self._handle_release,
        )
        self._listener.start()

    def join(self) -> None:
        if self._listener is not None:
            self._listener.join()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
