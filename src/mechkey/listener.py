"""Global keyboard listener built on pynput."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pynput import keyboard


KeyHandler = Callable[[str], None]
ReleaseHandler = Callable[[], None]
HotkeyHandler = Callable[[], None]

# Mechvibes / iohook-style keycodes (US QWERTY).
_CHAR_TO_KEYCODE = {
    "a": "30",
    "b": "48",
    "c": "46",
    "d": "32",
    "e": "18",
    "f": "33",
    "g": "34",
    "h": "35",
    "i": "23",
    "j": "36",
    "k": "37",
    "l": "38",
    "m": "50",
    "n": "49",
    "o": "24",
    "p": "25",
    "q": "16",
    "r": "19",
    "s": "31",
    "t": "20",
    "u": "22",
    "v": "47",
    "w": "17",
    "x": "45",
    "y": "21",
    "z": "44",
    "1": "2",
    "2": "3",
    "3": "4",
    "4": "5",
    "5": "6",
    "6": "7",
    "7": "8",
    "8": "9",
    "9": "10",
    "0": "11",
    "-": "12",
    "=": "13",
    "[": "26",
    "]": "27",
    "\\": "43",
    ";": "39",
    "'": "40",
    "`": "41",
    ",": "51",
    ".": "52",
    "/": "53",
    " ": "57",
}

_SPECIAL_TO_KEYCODE = {
    keyboard.Key.esc: "1",
    keyboard.Key.backspace: "14",
    keyboard.Key.tab: "15",
    keyboard.Key.enter: "28",
    keyboard.Key.caps_lock: "58",
    keyboard.Key.space: "57",
    keyboard.Key.f1: "59",
    keyboard.Key.f2: "60",
    keyboard.Key.f3: "61",
    keyboard.Key.f4: "62",
    keyboard.Key.f5: "63",
    keyboard.Key.f6: "64",
    keyboard.Key.f7: "65",
    keyboard.Key.f8: "66",
    keyboard.Key.f9: "67",
    keyboard.Key.f10: "68",
    keyboard.Key.f11: "87",
    keyboard.Key.f12: "88",
    keyboard.Key.insert: "3666",
    keyboard.Key.delete: "3667",
    keyboard.Key.home: "3655",
    keyboard.Key.end: "3663",
    keyboard.Key.page_up: "3657",
    keyboard.Key.page_down: "3665",
    keyboard.Key.up: "57416",
    keyboard.Key.left: "57419",
    keyboard.Key.right: "57421",
    keyboard.Key.down: "57424",
    keyboard.Key.num_lock: "69",
    keyboard.Key.scroll_lock: "70",
    keyboard.Key.print_screen: "3639",
    keyboard.Key.pause: "3653",
    keyboard.Key.menu: "3677",
}


def key_to_id(key: Any) -> str:
    """Map a pynput key to a Mechvibes/iohook keycode string."""
    if isinstance(key, keyboard.KeyCode):
        char = key.char
        if char is not None:
            mapped = _CHAR_TO_KEYCODE.get(char.lower())
            if mapped is not None:
                return mapped
        # Fallback: use vk when available (platform-specific).
        vk = getattr(key, "vk", None)
        if vk is not None:
            return str(int(vk))
        return "30"  # generic letter fallback (A)

    mapped = _SPECIAL_TO_KEYCODE.get(key)
    if mapped is not None:
        return mapped
    return "30"


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
