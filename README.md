# mechkey

Mechanical keyboard sound simulator for Python. Play realistic switch samples on every keystroke with a global keyboard listener.

## Features

- System-wide key press / release sounds
- Sample-based switch profiles (Mechvibes-style `config.json`)
- Bundled **Cherry MX Brown** sprite profile (default) plus license-safe **Demo Blue**
- User-installable custom profiles
- Volume, mute hotkey, and persistent config (`~/.config/mechkey/config.toml`)

## Requirements

- Python 3.10+
- A working audio output
- On Linux: an environment where [pynput](https://pypi.org/project/pynput/) can read keyboard events (X11 generally works; Wayland may need accessibility permissions or an XWayland session)

## Install

```bash
git clone https://github.com/unique/mechkey.git
cd mechkey
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

```bash
# Start the simulator (uses saved config / defaults)
mechkey
# or
mechkey run

# Choose a profile and volume for this session
mechkey run --profile cherry_mx_brown --volume 80
mechkey run --profile demo_blue --volume 80

# Press sounds only
mechkey run --no-release

# List profiles
mechkey list-profiles

# Config
mechkey config show
mechkey config set volume 60
mechkey config set profile cherry_mx_brown
mechkey config set mute_hotkey ctrl+alt+m
```

Default mute toggle: `Ctrl+Alt+M`. Stop with `Ctrl+C`.

You can also run without installing the console script:

```bash
python -m mechkey list-profiles
python -m mechkey run
```

## Sound profiles

Bundled profiles live in [`src/mechkey/assets/profiles/`](src/mechkey/assets/profiles/).

User profiles go in:

```text
~/.local/share/mechkey/profiles/<profile_id>/
  config.json
  *.wav
```

### Multi-file profile (`key_define_type: "multi"`)

```json
{
  "id": "my_switches",
  "name": "My Switches",
  "author": "you",
  "license": "CC0-1.0",
  "key_define_type": "multi",
  "default": "generic.wav",
  "sound": "press.wav",
  "keyup_sound": "release.wav",
  "defines": {
    "enter": "enter.wav",
    "space": "space.wav",
    "backspace": "backspace.wav"
  }
}
```

### Single-sprite profile (`key_define_type: "single"`)

One master WAV plus millisecond slices per Mechvibes/iohook keycode:

```json
{
  "id": "my_sprite",
  "name": "My Sprite Pack",
  "key_define_type": "single",
  "sound": "sound.wav",
  "keyup_sound": false,
  "defines": {
    "30": [1200, 180],
    "57": [5400, 200]
  }
}
```

User profiles with the same `id` override bundled ones.

### Regenerate the demo profile

```bash
python3 scripts/generate_demo_profile.py
```

### Re-import Cherry MX Brown from a local MP3

```bash
python3 scripts/import_cherry_mx_brown.py [path/to/cherry-mx-brown.mp3]
```

The demo samples are synthesized (Apache-2.0). The Cherry MX Brown pack is imported from a local recording — verify redistribution rights before publishing forks.

## Configuration

`~/.config/mechkey/config.toml`:

```toml
profile = "cherry_mx_brown"
volume = 70
play_release = true
mute_hotkey = "ctrl+alt+m"
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

Apache License 2.0. See [LICENSE](LICENSE).
