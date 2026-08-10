# mechkey

Mechanical keyboard sound simulator for Python. Play realistic switch samples on every keystroke with a global keyboard listener.

## Features

- System-wide key press / release sounds
- Sample-based switch profiles (Mechvibes-style `config.json`)
- Bundled license-safe **Demo Blue** clicky profile
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
mechkey run --profile demo_blue --volume 80

# Press sounds only
mechkey run --no-release

# List profiles
mechkey list-profiles

# Config
mechkey config show
mechkey config set volume 60
mechkey config set profile demo_blue
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

Example `config.json`:

```json
{
  "id": "my_switches",
  "name": "My Switches",
  "author": "you",
  "license": "CC0-1.0",
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

User profiles with the same `id` override bundled ones.

### Regenerate the demo profile

```bash
python3 scripts/generate_demo_profile.py
```

The demo samples are synthesized (Apache-2.0). Drop in your own legally obtained WAVs for authentic switch recordings.

## Configuration

`~/.config/mechkey/config.toml`:

```toml
profile = "demo_blue"
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
