# -*- coding: utf-8 -*-
"""
Video Scrap kurulum betigi: tek komut, tekrar calistirilabilir.

Kullanim:
    python kur.py              # eksikleri kurar; her sey kuruluysa hicbir sey indirmez
    python kur.py --kontrol    # sadece kontrol eder, hicbir sey kurmaz
    python kur.py --yenile     # paketleri bastan kurar (pip install -r)

Yaptigi: proje icindeki .venv sanal ortamini acar, requirements.txt paketlerini kurar ve
ffmpeg'i imageio-ffmpeg ile .venv icine getirir. Sistem Python'una, PATH'e ve baska
klasorlere dokunmaz; elle dosya kopyalamak gerekmez.

Cikis kodu 0 = hazir, 1 = eksik ya da hata var.
"""

import argparse
import os
import subprocess
import sys
import venv
from pathlib import Path

HERE = Path(__file__).resolve().parent
VENV = HERE / ".venv"
PY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
MIN_PY = (3, 9)

MODULLER = [
    ("cv2", "opencv-python"),
    ("PIL", "pillow"),
    ("numpy", "numpy"),
    ("mcp", "mcp"),
    ("yt_dlp", "yt-dlp"),
    ("scenedetect", "scenedetect"),
    ("imageio_ffmpeg", "imageio-ffmpeg"),
]


def yaz(mesaj=""):
    print(mesaj, flush=True)


def calistir(cmd, sure=1800):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=sure, cwd=str(HERE))


def venv_var():
    return PY.is_file()


def eksik_moduller(py=None):
    """Sanal ortamda import edilemeyen modulleri dondurur."""
    py = py or PY
    adlar = [m for m, _ in MODULLER]
    kod = ("import importlib\n"
           "for m in %r:\n"
           "    try:\n"
           "        importlib.import_module(m)\n"
           "    except Exception:\n"
           "        print(m)\n") % adlar
    r = calistir([str(py), "-c", kod], sure=180)
    if r.returncode != 0:
        return adlar
    return [satir.strip() for satir in r.stdout.splitlines() if satir.strip() in adlar]


def ffmpeg_yolu(py=None):
    py = py or PY
    kod = ("import imageio_ffmpeg\n"
           "print(imageio_ffmpeg.get_ffmpeg_exe())\n")
    r = calistir([str(py), "-c", kod], sure=300)
    if r.returncode != 0:
        return ""
    yol = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
    return yol if yol and Path(yol).is_file() else ""


def venv_kur():
    yaz("Sanal ortam aciliyor: %s" % VENV)
    try:
        venv.EnvBuilder(with_pip=True, clear=False).create(str(VENV))
    except Exception as exc:
        yaz("HATA: sanal ortam acilamadi: %s" % exc)
        return False
    return venv_var()


def paket_kur():
    yaz("Paketler kuruluyor (ilk seferde 1-3 dakika surer)...")
    calistir([str(PY), "-m", "pip", "install", "--upgrade", "pip", "--quiet"], sure=600)
    r = calistir([str(PY), "-m", "pip", "install", "-r", "requirements.txt"])
    if r.returncode != 0:
        yaz("HATA: paket kurulumu basarisiz.")
        kuyruk = [s for s in (r.stdout + r.stderr).splitlines() if s.strip()][-12:]
        for satir in kuyruk:
            yaz("  " + satir)
        yaz("Internet baglantisini kontrol edip tekrar dene: python kur.py")
        return False
    return True


def ozet():
    eksik = eksik_moduller()
    ff = ffmpeg_yolu()
    if eksik:
        yaz("Eksik paketler: %s" % ", ".join(eksik))
    if not ff:
        yaz("ffmpeg bulunamadi (imageio-ffmpeg kurulu degil).")
    if not eksik and ff:
        yaz("Hazir. ffmpeg: %s" % ff)
        yaz("BASLAT.bat ile uygulamayi acabilirsin.")
        return 0
    return 1


def main():
    ap = argparse.ArgumentParser(description="Video Scrap kurulumu")
    ap.add_argument("--kontrol", action="store_true", help="sadece kontrol et, kurma")
    ap.add_argument("--yenile", action="store_true", help="paketleri bastan kur")
    args = ap.parse_args()

    if sys.version_info < MIN_PY:
        yaz("HATA: Python %d.%d veya uzeri gerekli. Su an: %s"
            % (MIN_PY[0], MIN_PY[1], sys.version.split()[0]))
        yaz("https://www.python.org/downloads/ adresinden kur; kurulumda 'Add python.exe to PATH' kutusunu isaretle.")
        return 1

    if args.kontrol:
        if not venv_var():
            yaz("Sanal ortam yok: %s" % VENV)
            yaz("Kurmak icin: python kur.py")
            return 1
        return ozet()

    if not venv_var():
        if not venv_kur():
            return 1

    eksik = eksik_moduller()
    if args.yenile or eksik:
        if not paket_kur():
            return 1
    else:
        yaz("Paketler zaten kurulu, indirme yapilmadi.")

    return ozet()


if __name__ == "__main__":
    sys.exit(main())
