#!/usr/bin/env python3
"""Genera la narración de cada vídeo con Piper y calcula los tiempos de cada frase.

Uso: python pipeline/tts.py [id ...]
Salida: build/<id>/voice.wav y build/<id>/timings.json
"""
import json
import re
import sys
import wave
from pathlib import Path

import numpy as np
from piper import PiperVoice, SynthesisConfig

ROOT = Path(__file__).resolve().parent.parent
VOICE = ROOT / "pipeline" / "voices" / "es_ES-davefx-medium.onnx"
BUILD = ROOT / "build"

LEAD, LINE_GAP, SCENE_GAP, TAIL = 0.45, 0.24, 0.6, 1.8

# Cómo debe pronunciar la voz los anglicismos y siglas (el texto en pantalla no cambia).
SAY = [
    (r"GTA Online", "ge te a onláin"),
    (r"GTA", "ge te a"),
    (r"PlayStation 5", "pléi estéishon cinco"),
    (r"PS5 Pro", "pe ese cinco pro"),
    (r"PS5", "pe ese cinco"),
    (r"PS3", "pe ese tres"),
    (r"Xbox Series", "équs box síries"),
    (r"Xbox 360", "équs box trescientos sesenta"),
    (r"Xbox", "équs box"),
    (r"PC", "pe cé"),
    (r"FPS", "efe pe ese"),
    (r"Rockstar", "rócstar"),
    (r"Take-Two", "téic tu"),
    (r"Strauss Zelnick", "estráus sélnic"),
    (r"Vice City", "váis síti"),
    (r"Leonida Keys", "leonida kis"),
    (r"los Keys", "los kis"),
    (r"Grassrivers", "gras ríbers"),
    (r"Port Gellhorn", "port guélorn"),
    (r"Mount Kalaga", "máunt kalaga"),
    (r"Everglades", "évergleids"),
    (r"Miami", "maiami"),
    (r"Red Dead Redemption 2", "red ded ridémpshon dos"),
    (r"Red Dead Online", "red ded onláin"),
    (r"Jason Duval", "yéison duval"),
    (r"Jason", "yéison"),
    (r"Lucia Caminos", "lucía caminos"),
    (r"Lucia", "lucía"),
    (r"Cal Hampton", "cal jámpton"),
    (r"Boobie Ike", "bubi áik"),
    (r"Dre'Quan Priest", "dri cuán prist"),
    (r"Only Raw Records", "ónli ro récords"),
    (r"Real Dimez", "ríal dáims"),
    (r"Bae-Luxe", "bei lux"),
    (r"Roxy", "rocsi"),
    (r"Raul Bautista", "raúl bautista"),
    (r"Brian Heder", "bráian jéder"),
    (r"Standard", "estándar"),
    (r"Ultimate", "áltimet"),
    (r"Vintage", "víntach"),
    (r"Vapid Stanier", "vápid estánier"),
    (r"Albany", "ólbani"),
    (r"Bravado", "bravado"),
    (r"Declasse", "declás"),
    (r"Banshee", "banshi"),
    (r"Bison", "báison"),
    (r"Marquis", "marquís"),
    (r"Mammatus", "mamatus"),
    (r"Shamal", "shamal"),
    (r"gameplay", "guéimplei"),
    (r"online", "onláin"),
    (r"jets", "yets"),
    (r"79,99", "setenta y nueve con noventa y nueve"),
    (r"99,99", "noventa y nueve con noventa y nueve"),
    (r"del 55", "del cincuenta y cinco"),
    (r"art déco", "ar decó"),
]
SAY_RE = [(re.compile(r"(?<!\w)" + re.escape(a) + r"(?!\w)", re.I), b) for a, b in SAY]


def speech_text(text: str) -> str:
    for rx, rep in SAY_RE:
        text = rx.sub(rep, text)
    return text


def synth(voice: PiperVoice, text: str) -> np.ndarray:
    cfg = SynthesisConfig(length_scale=0.94, noise_scale=0.6, noise_w_scale=0.8)
    chunks = [c.audio_int16_array for c in voice.synthesize(speech_text(text), syn_config=cfg)]
    audio = np.concatenate(chunks).astype(np.float32) / 32768.0
    # recorta silencios de los extremos
    loud = np.where(np.abs(audio) > 0.01)[0]
    if len(loud):
        pad = int(0.03 * voice.config.sample_rate)
        audio = audio[max(0, loud[0] - pad): loud[-1] + pad]
    return audio


def main() -> None:
    data = json.loads((ROOT / "content" / "videos.json").read_text())
    only = set(sys.argv[1:])
    voice = PiperVoice.load(str(VOICE))
    sr = voice.config.sample_rate
    for video in data["videos"]:
        if only and video["id"] not in only:
            continue
        parts, scenes, t = [np.zeros(int(LEAD * sr), np.float32)], [], LEAD
        for si, scene in enumerate(video["scenes"]):
            lines = list(scene["lines"])
            if scene["widget"]["type"] == "outro":
                lines.append(data["channel"]["outro"])
            start, out = t, []
            for li, line in enumerate(lines):
                audio = synth(voice, line)
                dur = len(audio) / sr
                out.append({"text": line, "start": round(t, 3), "dur": round(dur, 3)})
                parts.append(audio)
                t += dur
                last_line = li == len(lines) - 1
                last_scene = si == len(video["scenes"]) - 1
                gap = (TAIL if last_scene else SCENE_GAP) if last_line else LINE_GAP
                parts.append(np.zeros(int(gap * sr), np.float32))
                t += gap
            scenes.append({"start": round(start, 3), "end": round(t, 3), "lines": out})
        audio = np.concatenate(parts)
        audio = audio / max(1e-6, np.abs(audio).max()) * 0.89
        out_dir = BUILD / video["id"]
        out_dir.mkdir(parents=True, exist_ok=True)
        with wave.open(str(out_dir / "voice.wav"), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes((audio * 32767).astype(np.int16).tobytes())
        total = len(audio) / sr
        (out_dir / "timings.json").write_text(json.dumps({"duration": round(total, 3), "scenes": scenes}, ensure_ascii=False, indent=1))
        print(f"{video['id']} {video['slug']}: {total:.1f}s")


if __name__ == "__main__":
    main()
