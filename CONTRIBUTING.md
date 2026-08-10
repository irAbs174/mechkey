# Contributing to mechkey

Thanks for helping improve mechkey.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Project layout

- `src/mechkey/` — library and CLI
- `src/mechkey/assets/profiles/` — bundled sound profiles
- `scripts/` — maintenance utilities (demo sample generator)
- `tests/` — pytest suite

## Guidelines

- Keep the public CLI stable unless the change is intentional and documented in the README.
- Prefer small, focused pull requests.
- Add or update tests for config/profile behavior.
- Do not commit third-party sound packs unless their license clearly allows redistribution; document attribution in the profile `config.json`.
- Match existing code style: type hints, dataclasses, and concise modules.

## Tests

```bash
pytest
```

## Demo sounds

If you change the synthesizer, regenerate assets:

```bash
python3 scripts/generate_demo_profile.py
```

## License

By contributing, you agree that your contributions are licensed under the Apache License 2.0.
