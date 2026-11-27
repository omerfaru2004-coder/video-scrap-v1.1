# -*- coding: utf-8 -*-
"""
Video Scrap
===========
Bir videonun karelerini cikarir ve her 40 kareyi tek bir "kontak sayfasi"
(contact sheet) fotografiga yerlestirir. Boylece bir yapay zeka modeline
videoyu tek tek kare olarak gondermek yerine birkac yogun gorsel gonderirsin.

Kullanim:
    python video_scrap.py                  -> arayuz acilir
    python video_scrap.py --video a.mp4    -> komut satirindan calisir
"""

import argparse
import csv
import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

APP_NAME = "Video Scrap"
APP_VERSION = "1.1"

VIDEO_EXTS = (".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v", ".mpg", ".mpeg", ".wmv", ".flv", ".ts")

MODES = {
    "all": "Her kare (tam kayit)",
    "every_n": "Her N. kare",
    "fps": "Saniyede N kare",
    "scene": "Sahne degisimi (otomatik)",
}

MODE_KEYS = list(MODES.keys())


# --------------------------------------------------------------------------
# Yardimcilar
# --------------------------------------------------------------------------

def fmt_ts(seconds):
    """Saniyeyi SS:DD:SS.mmm bicimine cevirir."""
    if seconds is None or seconds < 0:
        seconds = 0.0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return "%02d:%02d:%06.3f" % (h, m, s)


def fmt_dur(seconds):
    """Insan okunur sure."""
    seconds = max(0.0, float(seconds or 0))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h:
        return "%d sa %02d dk %02d sn" % (h, m, s)
    if m:
        return "%d dk %02d sn" % (m, s)
    return "%.1f sn" % seconds


_FONT_CACHE = {}


def load_font(size):
    size = int(size)
    if size in _FONT_CACHE:
        return _FONT_CACHE[size]
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ]
    font = None
    for path in candidates:
        try:
            if os.path.exists(path):
                font = ImageFont.truetype(path, size)
                break
        except Exception:
            continue
    if font is None:
        try:
            font = ImageFont.load_default(size=size)
        except Exception:
            font = ImageFont.load_default()
    _FONT_CACHE[size] = font
    return font


def safe_name(text):
    keep = []
    for ch in str(text):
        if ch.isalnum() or ch in " -_.()[]":
            keep.append(ch)
        else:
            keep.append("_")
    out = "".join(keep).strip().replace(" ", "_")
    return out or "video"


# --------------------------------------------------------------------------
# Video bilgisi
# --------------------------------------------------------------------------

def probe_video(path):
    path = str(path)
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError("Video acilamadi: %s" % path)
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    cap.release()
    if fps <= 0:
        fps = 25.0
    duration = (count / fps) if count > 0 else 0.0
    return {
        "path": path,
        "name": os.path.basename(path),
        "fps": fps,
        "frame_count": count,
        "width": width,
        "height": height,
        "duration": duration,
        "size_mb": os.path.getsize(path) / (1024.0 * 1024.0) if os.path.exists(path) else 0.0,
    }


# --------------------------------------------------------------------------
# Kontak sayfasi uretici
# --------------------------------------------------------------------------

class SheetBuilder:
    """Kareleri izgaraya yerlestirip JPEG kontak sayfalari uretir."""

    def __init__(self, out_dir, cols, rows, thumb_w, quality, video_w, video_h,
                 prefix="sheet", sharpen=False):
        self.out_dir = Path(out_dir)
        self.cols = max(1, int(cols))
        self.rows = max(1, int(rows))
        self.thumb_w = max(48, int(thumb_w))
        self.quality = int(quality)
        self.prefix = prefix
        self.sharpen = bool(sharpen)

        ratio = (video_h / video_w) if video_w else 9.0 / 16.0
        self.thumb_h = max(32, int(round(self.thumb_w * ratio)))
        self.label_h = max(16, int(round(self.thumb_w * 0.075)))
        self.cell_w = self.thumb_w
        self.cell_h = self.thumb_h + self.label_h
        self.font = load_font(max(10, int(self.label_h * 0.62)))

        self.sheet = None
        self.draw = None
        self.index = 0
        self.sheets = []
        self._first_ts = None
        self._last_ts = None
        self._cells = []

    def _new_sheet(self):
        w = self.cols * self.cell_w
        h = self.rows * self.cell_h
        self.sheet = Image.new("RGB", (w, h), (16, 16, 18))
        self.draw = ImageDraw.Draw(self.sheet)
        self.index = 0
        self._first_ts = None
        self._last_ts = None
        self._cells = []

    def add(self, frame_bgr, ts, frame_idx):
        if self.sheet is None:
            self._new_sheet()

        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        if img.size != (self.thumb_w, self.thumb_h):
            img = img.resize((self.thumb_w, self.thumb_h), Image.LANCZOS)
        if self.sharpen:
            img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=130, threshold=2))

        col = self.index % self.cols
        row = self.index // self.cols
        x = col * self.cell_w
        y = row * self.cell_h

        self.sheet.paste(img, (x, y))

        bar_y = y + self.thumb_h
        self.draw.rectangle([x, bar_y, x + self.cell_w - 1, bar_y + self.label_h - 1], fill=(0, 0, 0))
        label = "%s  #%d" % (fmt_ts(ts), frame_idx)
        self.draw.text((x + 4, bar_y + 1), label, font=self.font, fill=(255, 235, 120))

        if self._first_ts is None:
            self._first_ts = ts
        self._last_ts = ts
        self._cells.append((row, col, frame_idx, ts))
        self.index += 1

        if self.index >= self.cols * self.rows:
            self.flush()

    def flush(self):
        if self.sheet is None or self.index == 0:
            self.sheet = None
            self.draw = None
            return None
        self.out_dir.mkdir(parents=True, exist_ok=True)
        name = "%s_%04d.jpg" % (self.prefix, len(self.sheets) + 1)
        path = self.out_dir / name
        self.sheet.save(str(path), "JPEG", quality=self.quality, optimize=True, subsampling=1)
        info = {
            "path": str(path),
            "name": name,
            "count": self.index,
            "first_ts": self._first_ts,
            "last_ts": self._last_ts,
            "cells": list(self._cells),
        }
        self.sheets.append(info)
        self.sheet = None
        self.draw = None
        self.index = 0
        self._cells = []
        return info


# --------------------------------------------------------------------------
# Ana islem
# --------------------------------------------------------------------------

def process_video(video, out_dir, mode="all", n=1, target_fps=2.0, scene_thresh=0.30,
                  scene_min_gap=0.5, cols=8, rows=5, thumb_w=256, quality=85,
                  save_frames=False, sharpen=False, max_frames=0,
                  log=None, progress=None, cancel=None):
    log = log or (lambda m: None)
    video = str(video)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    info = probe_video(video)
    fps = info["fps"]
    total = info["frame_count"]

    log("Video: %s" % info["name"])
    log("Cozunurluk: %dx%d | fps: %.3f | kare: %d | sure: %s" % (
        info["width"], info["height"], fps, total, fmt_dur(info["duration"])))

    if mode == "every_n":
        step = max(1, int(n))
        mode_text = "her %d. kare" % step
    elif mode == "fps":
        step = max(1, int(round(fps / max(0.01, float(target_fps)))))
        mode_text = "saniyede ~%.2f kare (her %d. kare)" % (fps / step, step)
    elif mode == "scene":
        step = 1
        mode_text = "sahne degisimi (esik %.2f, min aralik %.2f sn)" % (scene_thresh, scene_min_gap)
    else:
        mode = "all"
        step = 1
        mode_text = "her kare"

    log("Secim modu: %s" % mode_text)
    log("Kontak sayfasi: %d x %d = %d kare/foto" % (cols, rows, cols * rows))

    sheets_dir = out_dir / "sheets"
    frames_dir = out_dir / "frames"
    sheets_dir.mkdir(parents=True, exist_ok=True)
    if save_frames:
        frames_dir.mkdir(parents=True, exist_ok=True)

    builder = SheetBuilder(sheets_dir, cols, rows, thumb_w, quality,
                           info["width"], info["height"], sharpen=sharpen)

    cap = cv2.VideoCapture(video)
    if not cap.isOpened():
        raise RuntimeError("Video acilamadi: %s" % video)

    scene_stride = max(1, int(round(fps / 10.0))) if fps > 0 else 1
    idx = 0
    kept = 0
    prev_small = None
    last_kept_ts = -1e9
    started = time.time()
    cancelled = False

    try:
        while True:
            if cancel is not None and cancel.is_set():
                cancelled = True
                break
            ok = cap.grab()
            if not ok:
                break

            ts = idx / fps if fps > 0 else 0.0
            keep = False
            frame = None

            if mode == "scene":
                if idx % scene_stride != 0:
                    idx += 1
                    continue
                ok, frame = cap.retrieve()
                if not ok:
                    break
                small = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (64, 36),
                                   interpolation=cv2.INTER_AREA)
                if prev_small is None:
                    keep = True
                else:
                    diff = float(np.mean(cv2.absdiff(small, prev_small))) / 255.0
                    if diff >= scene_thresh and (ts - last_kept_ts) >= scene_min_gap:
                        keep = True
                prev_small = small
            else:
                keep = (idx % step == 0)
                if keep:
                    ok, frame = cap.retrieve()
                    if not ok:
                        break

            if keep:
                builder.add(frame, ts, idx)
                kept += 1
                last_kept_ts = ts
                if save_frames:
                    cv2.imwrite(str(frames_dir / ("frame_%06d.jpg" % idx)), frame,
                                [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
                if max_frames and kept >= int(max_frames):
                    log("Kare limitine ulasildi (%d), durduruldu." % int(max_frames))
                    break

            idx += 1
            if progress is not None and (idx % 10 == 0 or idx == total):
                progress(idx, total)

    finally:
        cap.release()

    builder.flush()
    elapsed = time.time() - started

    log("Bitti: %d kare okundu, %d kare secildi, %d kontak sayfasi, %.1f sn" % (
        idx, kept, len(builder.sheets), elapsed))

    summary = {
        "video": info,
        "mode": mode,
        "mode_text": mode_text,
        "frames_read": idx,
        "frames_kept": kept,
        "sheets": builder.sheets,
        "out_dir": str(out_dir),
        "elapsed": elapsed,
        "cancelled": cancelled,
        "cols": cols,
        "rows": rows,
        "thumb_w": thumb_w,
        "save_frames": save_frames,
        "sharpen": sharpen,
        "max_frames": int(max_frames or 0),
    }

    write_manifest(summary)
    write_report(summary)
    write_prompt(summary)
    return summary


# --------------------------------------------------------------------------
# Cikti dosyalari
# --------------------------------------------------------------------------

def write_manifest(summary):
    out = Path(summary["out_dir"]) / "manifest.csv"
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["sayfa", "satir", "sutun", "kare_no", "zaman", "zaman_sn"])
        for sheet in summary["sheets"]:
            for (row, col, frame_idx, ts) in sheet["cells"]:
                w.writerow([sheet["name"], row + 1, col + 1, frame_idx, fmt_ts(ts), "%.3f" % ts])
    return out


def write_report(summary):
    info = summary["video"]
    out = Path(summary["out_dir"]) / "rapor.md"
    lines = []
    lines.append("# Video Scrap raporu")
    lines.append("")
    lines.append("- **Dosya:** `%s`" % info["name"])
    lines.append("- **Sure:** %s (%.2f sn)" % (fmt_dur(info["duration"]), info["duration"]))
    lines.append("- **Cozunurluk:** %dx%d" % (info["width"], info["height"]))
    lines.append("- **fps:** %.3f" % info["fps"])
    lines.append("- **Toplam kare:** %d" % info["frame_count"])
    lines.append("- **Secim modu:** %s" % summary["mode_text"])
    lines.append("- **Okunan kare:** %d" % summary["frames_read"])
    lines.append("- **Secilen kare:** %d" % summary["frames_kept"])
    lines.append("- **Kontak sayfasi:** %d adet (%d x %d = %d kare/foto)" % (
        len(summary["sheets"]), summary["cols"], summary["rows"], summary["cols"] * summary["rows"]))
    lines.append("- **Islem suresi:** %.1f sn" % summary["elapsed"])
    lines.append("")
    lines.append("## Sayfalar")
    lines.append("")
    lines.append("| Sayfa | Kare | Baslangic | Bitis |")
    lines.append("|---|---|---|---|")
    for sheet in summary["sheets"]:
        lines.append("| `%s` | %d | %s | %s |" % (
            sheet["name"], sheet["count"], fmt_ts(sheet["first_ts"]), fmt_ts(sheet["last_ts"])))
    lines.append("")
    lines.append("## Klasorler")
    lines.append("")
    lines.append("- `sheets/` : kontak sayfalari (yapay zekaya verilecek gorseller)")
    if summary["save_frames"]:
        lines.append("- `frames/` : tek tek kareler")
    lines.append("- `manifest.csv` : her karenin hangi sayfada, hangi satir/sutunda oldugu")
    lines.append("- `prompt.txt` : yapay zekaya yapistirilacak hazir metin")
    lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def write_prompt(summary):
    info = summary["video"]
    out = Path(summary["out_dir"]) / "prompt.txt"
    per = summary["cols"] * summary["rows"]
    lines = []
    lines.append("GOREV: Asagidaki gorseller tek bir videodan uretilmis kontak sayfalaridir (contact sheet).")
    lines.append("Videoyu izlemek yerine bu sayfalari inceleyerek videoda ne oldugunu ayrintili analiz et.")
    lines.append("")
    lines.append("VIDEO BILGISI")
    lines.append("- Dosya: %s" % info["name"])
    lines.append("- Sure: %s" % fmt_dur(info["duration"]))
    lines.append("- Cozunurluk: %dx%d, %.2f fps" % (info["width"], info["height"], info["fps"]))
    lines.append("- Kare secimi: %s" % summary["mode_text"])
    lines.append("- Toplam secilen kare: %d" % summary["frames_kept"])
    lines.append("")
    lines.append("SAYFA DUZENI")
    lines.append("- Her sayfada %d sutun x %d satir = %d kare vardir." % (
        summary["cols"], summary["rows"], per))
    lines.append("- Okuma sirasi: soldan saga, yukaridan asagiya. Bu sira videonun kronolojik akisidir.")
    lines.append("- Her karenin altindaki siyah seritte SOLDAN saga: zaman damgasi (SS:DD:SS.mmm) ve kare numarasi (#) yazar.")
    lines.append("- Zaman damgasi videonun basindan itibaren gecen suredir.")
    lines.append("")
    lines.append("SAYFALAR")
    for sheet in summary["sheets"]:
        lines.append("- %s -> %s ... %s (%d kare)" % (
            sheet["name"], fmt_ts(sheet["first_ts"]), fmt_ts(sheet["last_ts"]), sheet["count"]))
    lines.append("")
    lines.append("ISTENEN CIKTI")
    lines.append("1. Videonun konusu ve genel akisi (kronolojik ozet).")
    lines.append("2. Zaman araliklarina bolunmus sahne listesi (ornek: 00:00:03.200 - 00:00:07.400 arasi ne oluyor).")
    lines.append("3. Ekranda gorunen yazi, sayi, logo ve arayuz ogeleri.")
    lines.append("4. Hareket, kamera degisimi, gecis ve kesme noktalari.")
    lines.append("5. Dikkat ceken detaylar, hatalar veya tutarsizliklar.")
    lines.append("6. Emin olmadigin yerlerde tahmin yuruttugunu acikca belirt.")
    lines.append("")
    lines.append("NOT: Kareler arasinda atlanan sure olabilir; iki kare arasindaki farki gorursen bunu belirt.")
    lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


# --------------------------------------------------------------------------
# Arayuz
# --------------------------------------------------------------------------

def run_gui():
    import arayuz
    arayuz.run_gui()


# --------------------------------------------------------------------------
# Komut satiri
# --------------------------------------------------------------------------

def run_cli(argv):
    ap = argparse.ArgumentParser(
        prog="video_scrap",
        description="Video karelerini kontak sayfalarina donusturur.")
    ap.add_argument("--video", required=True, help="video dosyasi")
    ap.add_argument("--out", default=None, help="cikti klasoru")
    ap.add_argument("--mode", default="all", choices=MODE_KEYS, help="kare secim modu")
    ap.add_argument("--n", type=int, default=1, help="every_n modunda kac karede bir")
    ap.add_argument("--fps", type=float, default=2.0, help="fps modunda saniyede kac kare")
    ap.add_argument("--scene-thresh", type=float, default=0.30, help="sahne esigi")
    ap.add_argument("--scene-gap", type=float, default=0.5, help="sahne modunda min aralik (sn)")
    ap.add_argument("--cols", type=int, default=8)
    ap.add_argument("--rows", type=int, default=5)
    ap.add_argument("--thumb", type=int, default=256)
    ap.add_argument("--quality", type=int, default=85)
    ap.add_argument("--save-frames", action="store_true")
    ap.add_argument("--sharpen", action="store_true", help="kucuk resimleri keskinlestir")
    ap.add_argument("--max-frames", type=int, default=0, help="en fazla kac kare secilsin (0 = sinirsiz)")
    args = ap.parse_args(argv)

    video = args.video
    if not os.path.exists(video):
        print("HATA: video bulunamadi: %s" % video)
        return 2
    out = args.out or str(Path(video).parent / (safe_name(Path(video).stem) + "_scrap"))

    summary = process_video(
        video, out,
        mode=args.mode, n=args.n, target_fps=args.fps,
        scene_thresh=args.scene_thresh, scene_min_gap=args.scene_gap,
        cols=args.cols, rows=args.rows, thumb_w=args.thumb,
        quality=args.quality, save_frames=args.save_frames,
        sharpen=args.sharpen, max_frames=args.max_frames,
        log=lambda m: print(m, flush=True))
    print("Cikti: %s" % summary["out_dir"])
    return 0


def main():
    if len(sys.argv) > 1:
        return run_cli(sys.argv[1:])
    try:
        run_gui()
    except Exception as hata:  # noqa: BLE001
        # Konsol penceresi olmadan baslatildiginda hata sessiz kalmasin.
        import traceback
        iz = traceback.format_exc()
        try:
            import tkinter.messagebox as mb
            mb.showerror(APP_NAME, "Arayuz acilamadi.\n\n%s\n\nAyrinti:\n%s" % (hata, iz[-1200:]))
        except Exception:  # noqa: BLE001
            print(iz, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
