# -*- coding: utf-8 -*-
"""
Video sesini yaziya doker (Whisper), zaman damgali.
Cikti: <out>/transcript.md, transcript.json, ses_durum.json

Kullanim:
    python ses.py --video <mp4> --out <klasor> [--model medium] [--language tr]
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ayarlar
BASE_DIR = ayarlar.cikti_koku()


def ensure_inside(path):
    p = Path(str(path)).expanduser()
    if not p.is_absolute():
        p = BASE_DIR / p
    p = p.resolve()
    try:
        p.relative_to(BASE_DIR)
    except ValueError:
        raise RuntimeError("Cikti klasoru proje klasoru disinda: %s (izinli: %s)" % (p, BASE_DIR))
    return p


def ts(sec):
    sec = max(0.0, float(sec))
    return "%02d:%02d:%05.2f" % (int(sec // 3600), int(sec % 3600 // 60), sec % 60)


def status(out, **kw):
    f = out / "ses_durum.json"
    try:
        d = json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}
    except Exception:
        d = {}
    d.update(kw)
    d["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    ayarlar.atomik_yaz(f, json.dumps(d, ensure_ascii=False, indent=1))


def transcribe(video, out_dir, model="", language="tr"):
    out = ensure_inside(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    status(out, state="running", stage="model", pid=os.getpid())
    # Whisper ffmpeg'i PATH'ten cagirir; .venv icindeki imageio-ffmpeg varsa onu one al.
    try:
        import imageio_ffmpeg
        os.environ["PATH"] = str(Path(imageio_ffmpeg.get_ffmpeg_exe()).parent) + os.pathsep + os.environ.get("PATH", "")
    except Exception:
        pass
    import whisper
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    name = model or ("medium" if device == "cuda" else "small")
    status(out, stage="model yukleniyor", model=name, device=device)
    m = whisper.load_model(name, device=device)
    status(out, stage="donusturuyor")
    res = m.transcribe(str(video), language=language or None, fp16=(device == "cuda"),
                       condition_on_previous_text=False, verbose=False)
    segs = [{"start": round(s["start"], 2), "end": round(s["end"], 2), "text": s["text"].strip()}
            for s in res["segments"]]
    (out / "transcript.json").write_text(json.dumps(segs, ensure_ascii=False, indent=1), encoding="utf-8")
    lines = ["# Konusma dokumu", "", "Video: %s | model: %s (%s) | dil: %s" % (Path(video).name, name, device, language),
             "Her satir: [baslangic-bitis] metin. Sureler video zamanidir (kontak sayfalariyla ayni).", ""]
    for s in segs:
        lines.append("[%s - %s] %s" % (ts(s["start"]), ts(s["end"]), s["text"]))
    (out / "transcript.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    status(out, state="done", stage="bitti", model=name, device=device, parca=len(segs),
           sure_sn=round(time.time() - t0, 1))
    return segs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="")
    ap.add_argument("--language", default="tr")
    a = ap.parse_args()
    try:
        transcribe(a.video, a.out, a.model, a.language)
    except Exception as exc:
        try:
            status(ensure_inside(a.out), state="error", error=str(exc))
        except Exception:
            pass
        sys.stderr.write("HATA: %s\n" % exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
