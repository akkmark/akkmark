#!/usr/bin/env python3
"""Escribe guion.md y metadata.md (título, descripción, etiquetas) de cada vídeo en output/."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
data = json.loads((ROOT / "content" / "videos.json").read_text())
ch = data["channel"]
FOOT = (
    "Información basada en lo publicado antes del lanzamiento (noviembre de 2026). "
    "Lo que es rumor o estimación se indica como tal en el vídeo.\n\n"
    f"{ch['name']} es un canal de fans. No está afiliado a Rockstar Games ni a Take-Two Interactive. "
    "Grand Theft Auto y GTA son marcas de sus respectivos propietarios."
)

for v in data["videos"]:
    out = ROOT / "output" / f"{v['id']}-{v['slug']}"
    out.mkdir(parents=True, exist_ok=True)
    tm_path = ROOT / "build" / v["id"] / "timings.json"
    tm = json.loads(tm_path.read_text()) if tm_path.exists() else None

    guion = [f"# {v['title']}", ""]
    chapters = []
    for i, s in enumerate(v["scenes"]):
        lines = list(s["lines"]) + ([ch["outro"]] if s["widget"]["type"] == "outro" else [])
        stamp = ""
        if tm:
            sec = int(tm["scenes"][i]["start"]) if i else 0
            stamp = f"{sec // 60}:{sec % 60:02d}"
            chapters.append(f"{stamp} {s['headline']}")
        guion += [f"## {s['headline']}" + (f" ({stamp})" if stamp else ""), f"*En pantalla: {s['kicker']} · {s['widget']['type']}*", "", " ".join(lines), ""]
    (out / "guion.md").write_text("\n".join(guion))

    desc = v["description"] + "\n\n" + ("\n".join(chapters) + "\n\n" if chapters else "") + FOOT
    hashtags = "#GTA6 #GTAVI #ViceCity"
    meta = [
        f"# {v['title']}", "",
        "## Título", "", v["title"], "",
        "## Descripción", "", "```", desc + "\n\n" + hashtags, "```", "",
        "## Etiquetas", "", ", ".join(v["tags"]), "",
        "## Búsquedas a las que responde", "", *[f"- {q}" for q in v["search"]], "",
        "## Archivos", "", "- `video.mp4` (1920×1080, 30 fps)", "- `miniatura.jpg`", "- `guion.md`", "",
    ]
    (out / "metadata.md").write_text("\n".join(meta))
    print(out.name)
