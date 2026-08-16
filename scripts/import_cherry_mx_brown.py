#!/usr/bin/env python3
"""Import cherry-mx-brown.mp3 as a bundled Mechvibes single-sprite profile."""

from __future__ import annotations

import array
import json
import math
import subprocess
import sys
from pathlib import Path

# Standard Mechvibes keycodes from CherryMX Brown - PBT (order preserved).
MECHVIBES_KEYCODES = [
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "11",
    "12",
    "13",
    "14",
    "15",
    "16",
    "17",
    "18",
    "19",
    "20",
    "21",
    "22",
    "23",
    "24",
    "25",
    "26",
    "27",
    "28",
    "29",
    "30",
    "31",
    "32",
    "33",
    "34",
    "35",
    "36",
    "37",
    "38",
    "39",
    "40",
    "41",
    "42",
    "43",
    "44",
    "45",
    "46",
    "47",
    "48",
    "49",
    "50",
    "51",
    "52",
    "53",
    "54",
    "55",
    "56",
    "57",
    "58",
    "59",
    "60",
    "61",
    "62",
    "63",
    "64",
    "65",
    "66",
    "67",
    "68",
    "69",
    "70",
    "71",
    "72",
    "73",
    "74",
    "75",
    "76",
    "77",
    "78",
    "79",
    "80",
    "81",
    "82",
    "83",
    "87",
    "88",
    "3612",
    "3613",
    "3637",
    "3639",
    "3640",
    "3653",
    "3655",
    "3657",
    "3663",
    "3665",
    "3666",
    "3667",
    "3675",
    "3676",
    "3677",
    "57416",
    "57419",
    "57421",
    "57424",
    "60999",
    "61000",
    "61001",
    "61003",
    "61005",
    "61007",
    "61008",
    "61009",
    "61010",
    "61011",
]

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MP3 = ROOT / "cherry-mx-brown.mp3"
OUT_DIR = ROOT / "src" / "mechkey" / "assets" / "profiles" / "cherry_mx_brown"
SLICE_MS = 180
MIN_ONSET_GAP_MS = 80


def _detect_onsets(wav_path: Path, rate: int = 44100) -> list[int]:
    """Return onset times in milliseconds from a mono/stereo WAV via ffmpeg PCM."""
    raw_path = wav_path.with_suffix(".onset.raw")
    try:
        subprocess.check_call(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(wav_path),
                "-f",
                "s16le",
                "-acodec",
                "pcm_s16le",
                "-ac",
                "1",
                "-ar",
                str(rate),
                str(raw_path),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        data = raw_path.read_bytes()
    finally:
        if raw_path.exists():
            raw_path.unlink()

    samples = array.array("h")
    samples.frombytes(data)
    if not samples:
        raise RuntimeError(f"No PCM data decoded from {wav_path}")

    win = max(1, int(rate * 0.01))  # 10 ms windows
    rms: list[float] = []
    for i in range(0, len(samples) - win, win):
        chunk = samples[i : i + win]
        energy = math.sqrt(sum(x * x for x in chunk) / len(chunk))
        rms.append(energy)

    if not rms:
        raise RuntimeError("Failed to compute energy envelope")

    threshold = max(rms) * 0.12
    peaks: list[int] = []
    above = False
    last_ms = -MIN_ONSET_GAP_MS
    for i, value in enumerate(rms):
        ms = i * 10
        if value >= threshold and not above:
            if ms - last_ms >= MIN_ONSET_GAP_MS:
                peaks.append(ms)
                last_ms = ms
            above = True
        elif value < threshold * 0.4:
            above = False
    return peaks


def _convert_mp3_to_wav(mp3: Path, wav: Path) -> None:
    wav.parent.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(mp3),
            "-acodec",
            "pcm_s16le",
            "-ar",
            "44100",
            "-ac",
            "2",
            str(wav),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _build_defines(onsets: list[int], duration_ms: int) -> dict[str, list[int]]:
    if not onsets:
        raise RuntimeError("No onsets detected; cannot build defines")

    defines: dict[str, list[int]] = {}
    for index, keycode in enumerate(MECHVIBES_KEYCODES):
        start = onsets[index % len(onsets)]
        # Clamp duration so we do not read past EOF.
        remaining = max(1, duration_ms - start)
        dur = min(SLICE_MS, remaining)
        defines[keycode] = [start, dur]
    return defines


def _wav_duration_ms(wav_path: Path) -> int:
    import wave

    with wave.open(str(wav_path), "rb") as handle:
        return int(handle.getnframes() * 1000 / handle.getframerate())


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    mp3 = Path(args[0]) if args else DEFAULT_MP3
    if not mp3.is_file():
        print(f"error: MP3 not found: {mp3}", file=sys.stderr)
        return 1

    out_dir = OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    wav_path = out_dir / "sound.wav"

    print(f"converting {mp3} -> {wav_path}")
    _convert_mp3_to_wav(mp3, wav_path)

    duration_ms = _wav_duration_ms(wav_path)
    print(f"detecting onsets in {wav_path} ({duration_ms} ms)")
    onsets = _detect_onsets(wav_path)
    print(f"found {len(onsets)} onsets")

    defines = _build_defines(onsets, duration_ms)
    config = {
        "id": "cherry_mx_brown",
        "name": "Cherry MX Brown",
        "author": "imported",
        "license": "verify-before-redistribute",
        "key_define_type": "single",
        "includes_numpad": False,
        "sound": "sound.wav",
        "keyup_sound": False,
        "defines": defines,
    }
    config_path = out_dir / "config.json"
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {config_path} ({len(defines)} defines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
