#!/usr/bin/env python3
"""Generate a license-safe clicky demo sound profile (pure Python, no deps)."""

from __future__ import annotations

import argparse
import json
import math
import random
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 44100


def _envelope(t: float, attack: float, decay: float) -> float:
    if t < attack:
        return t / attack if attack > 0 else 1.0
    if t < attack + decay:
        return 1.0 - (t - attack) / decay
    return 0.0


def synthesize(
    duration: float,
    *,
    base_freq: float,
    click_freq: float,
    noise_amount: float,
    attack: float,
    decay: float,
    seed: int,
) -> list[float]:
    rng = random.Random(seed)
    n = int(SAMPLE_RATE * duration)
    samples: list[float] = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = _envelope(t, attack, decay)
        # Body tone + high click transient + filtered-ish noise
        body = 0.35 * math.sin(2 * math.pi * base_freq * t)
        click = 0.55 * math.sin(2 * math.pi * click_freq * t) * math.exp(-t * 80)
        noise = noise_amount * (rng.random() * 2 - 1) * math.exp(-t * 40)
        samples.append(max(-1.0, min(1.0, env * (body + click + noise))))
    return samples


def write_wav(path: Path, samples: list[float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        frames = bytearray()
        for sample in samples:
            frames.extend(struct.pack("<h", int(sample * 32767)))
        wf.writeframes(frames)


def generate_profile(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    specs = {
        "press.wav": dict(
            duration=0.08,
            base_freq=180.0,
            click_freq=2400.0,
            noise_amount=0.25,
            attack=0.001,
            decay=0.07,
            seed=1,
        ),
        "generic.wav": dict(
            duration=0.075,
            base_freq=190.0,
            click_freq=2300.0,
            noise_amount=0.22,
            attack=0.001,
            decay=0.065,
            seed=2,
        ),
        "release.wav": dict(
            duration=0.05,
            base_freq=140.0,
            click_freq=1600.0,
            noise_amount=0.12,
            attack=0.001,
            decay=0.045,
            seed=3,
        ),
        "enter.wav": dict(
            duration=0.1,
            base_freq=150.0,
            click_freq=2000.0,
            noise_amount=0.28,
            attack=0.001,
            decay=0.09,
            seed=4,
        ),
        "space.wav": dict(
            duration=0.09,
            base_freq=120.0,
            click_freq=1800.0,
            noise_amount=0.2,
            attack=0.002,
            decay=0.08,
            seed=5,
        ),
        "backspace.wav": dict(
            duration=0.085,
            base_freq=170.0,
            click_freq=2100.0,
            noise_amount=0.24,
            attack=0.001,
            decay=0.075,
            seed=6,
        ),
    }

    for filename, kwargs in specs.items():
        write_wav(output_dir / filename, synthesize(**kwargs))

    config = {
        "id": "demo_blue",
        "name": "Demo Blue (clicky)",
        "author": "mechkey",
        "license": "Apache-2.0",
        "default": "generic.wav",
        "sound": "press.wav",
        "keyup_sound": "release.wav",
        "defines": {
            "enter": "enter.wav",
            "space": "space.wav",
            "backspace": "backspace.wav",
        },
    }
    (output_dir / "config.json").write_text(
        json.dumps(config, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    default_out = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "mechkey"
        / "assets"
        / "profiles"
        / "demo_blue"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=default_out,
        help=f"Output profile directory (default: {default_out})",
    )
    args = parser.parse_args()
    generate_profile(args.output)
    print(f"Wrote demo profile to {args.output}")


if __name__ == "__main__":
    main()
