#!/usr/bin/env node
// Renderiza un vídeo: fotogramas con Playwright -> ffmpeg, y mezcla voz + música.
// Uso: node pipeline/render.js <id> [--still <segundos>] [--thumb]
const { chromium } = require("playwright");
const { spawn, execFileSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const FPS = 30;
const data = JSON.parse(fs.readFileSync(path.join(ROOT, "content/videos.json"), "utf8"));

async function main() {
  const [id, ...rest] = process.argv.slice(2);
  const video = data.videos.find((v) => v.id === id);
  if (!video) throw new Error("id desconocido: " + id);
  const build = path.join(ROOT, "build", id);
  const outDir = path.join(ROOT, "output", `${id}-${video.slug}`);
  fs.mkdirSync(outDir, { recursive: true });
  const timings = JSON.parse(fs.readFileSync(path.join(build, "timings.json"), "utf8"));

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  await page.goto("file://" + path.join(__dirname, "template.html"));

  if (rest.includes("--thumb")) {
    await page.evaluate((v) => window.thumb(v), video);
    await page.screenshot({ path: path.join(outDir, "miniatura.jpg"), type: "jpeg", quality: 92 });
    await browser.close();
    return;
  }

  await page.evaluate(([v, c, t]) => window.setup(v, c, t), [video, data.channel, timings]);

  const still = rest.indexOf("--still");
  if (still >= 0) {
    for (const s of rest[still + 1].split(",")) {
      await page.evaluate((t) => window.seek(t), +s);
      await page.screenshot({ path: path.join(build, `still-${s}.jpg`), type: "jpeg", quality: 80 });
    }
    await browser.close();
    return;
  }

  const silent = path.join(build, "silent.mp4");
  const ff = spawn("ffmpeg", ["-v", "error", "-y", "-f", "image2pipe", "-framerate", String(FPS), "-c:v", "mjpeg", "-i", "-",
    "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", "-r", String(FPS), silent], { stdio: ["pipe", "inherit", "inherit"] });
  const done = new Promise((res, rej) => ff.on("close", (c) => (c === 0 ? res() : rej(new Error("ffmpeg " + c)))));
  const frames = Math.ceil(timings.duration * FPS);
  for (let i = 0; i < frames; i++) {
    await page.evaluate((t) => window.seek(t), i / FPS);
    const buf = await page.screenshot({ type: "jpeg", quality: 93 });
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once("drain", r));
  }
  ff.stdin.end();
  await done;
  await browser.close();

  const d = timings.duration;
  execFileSync("ffmpeg", ["-v", "error", "-y", "-i", silent, "-i", path.join(build, "voice.wav"), "-stream_loop", "-1", "-i", path.join(ROOT, "build/music.wav"),
    "-filter_complex", `[1:a]aresample=44100,pan=stereo|c0=c0|c1=c0[v];[2:a]volume=0.16,afade=t=in:d=1.2,afade=t=out:st=${(d - 1.6).toFixed(2)}:d=1.6[m];[v][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]`,
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-t", d.toFixed(2), "-movflags", "+faststart", path.join(outDir, "video.mp4")]);
  console.log(`${id}: ${frames} fotogramas -> ${path.relative(ROOT, outDir)}/video.mp4`);
}

main().catch((e) => { console.error(e); process.exit(1); });
