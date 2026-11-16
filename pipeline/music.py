#!/usr/bin/env python3
"""Genera una base musical original estilo synthwave (sin samples) en build/music.wav."""
import wave
from pathlib import Path

import numpy as np

SR, BPM = 44100, 100
BEAT = 60 / BPM
OUT = Path(__file__).resolve().parent.parent / "build" / "music.wav"
# La menor - Fa - Do - Sol, dos compases por acorde
CHORDS = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]
rng = np.random.default_rng(6)


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same")


def note(freq, dur, shape="saw", decay=4.0):
    t = np.arange(int(dur * SR)) / SR
    if shape == "saw":
        w = sum(np.sin(2 * np.pi * freq * n * t) / n for n in range(1, 7))
    else:
        w = np.sin(2 * np.pi * freq * t) + 0.4 * np.sin(2 * np.pi * freq * 1.005 * t)
    return w * np.exp(-decay * t) * np.minimum(1, t / 0.005)


def main():
    bars = len(CHORDS) * 2
    total = int(bars * 4 * BEAT * SR)
    mix = np.zeros((total, 2), np.float32)

    def add(sig, at, gain, pan=0.0):
        i = int(at * SR)
        sig = sig[: max(0, total - i)]
        mix[i:i + len(sig), 0] += sig * gain * (1 - pan) / 2 * 2 ** 0.5
        mix[i:i + len(sig), 1] += sig * gain * (1 + pan) / 2 * 2 ** 0.5

    for ci, chord in enumerate(CHORDS):
        t0 = ci * 8 * BEAT
        t = np.arange(int(8 * BEAT * SR)) / SR
        pad = sum(np.sin(2 * np.pi * hz(n) * t) + np.sin(2 * np.pi * hz(n) * 1.004 * t) for n in chord)
        pad *= np.minimum(1, t / 0.6) * np.minimum(1, (t[-1] - t) / 0.6)
        add(pad, t0, 0.05)
        for e in range(16):  # bajo en corcheas
            add(lowpass(note(hz(chord[0] - 24), BEAT / 2, "saw", 7), 24), t0 + e * BEAT / 2, 0.22)
        arp = [chord[0], chord[1], chord[2], chord[1] + 12, chord[2], chord[1], chord[0] + 12, chord[1]]
        for s in range(32):  # arpegio en semicorcheas
            add(note(hz(arp[s % 8] + 12), BEAT / 4 * 1.8, "sine", 9), t0 + s * BEAT / 4, 0.07, pan=0.5 if s % 2 else -0.5)
        for b in range(8):
            tk = np.arange(int(0.22 * SR)) / SR
            kick = np.sin(2 * np.pi * (48 + 90 * np.exp(-30 * tk)) * tk) * np.exp(-14 * tk)
            add(kick, t0 + b * BEAT, 0.3)
            hat = rng.standard_normal(int(0.05 * SR)) * np.exp(-90 * np.arange(int(0.05 * SR)) / SR)
            add(hat - lowpass(hat, 8), t0 + b * BEAT + BEAT / 2, 0.05, pan=0.2)

    mix /= np.abs(mix).max() / 0.8
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    print(f"music.wav: {total / SR:.1f}s")


if __name__ == "__main__":
    main()
