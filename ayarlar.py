# -*- coding: utf-8 -*-
"""
Video Scrap ayarlari (sadece standart kutuphane).

Ayarlar `ayarlar.json` dosyasinda tutulur (uygulama klasorunde):
    cikti_klasoru : videolar/ ve calisma/ klasorlerinin acilacagi ust klasor
    arka_plan     : arayuz basliginda gosterilecek gorsel (bos = renk gecisi)

Cikti kokunun onceligi: ayarlar.json > VIDEO_SCRAP_HOME ortam degiskeni > uygulama klasoru.
"""

import json
import os
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOSYA = HERE / "ayarlar.json"
VARSAYILAN = {"cikti_klasoru": "", "arka_plan": ""}


def atomik_yaz(yol, metin):
    """Ayni dosyayi okuyan baska bir surec yarim icerik gormesin: gecici dosya + os.replace."""
    yol = Path(yol)
    yol.parent.mkdir(parents=True, exist_ok=True)
    gecici = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(yol.parent),
                                         prefix=yol.name + ".", suffix=".tmp", delete=False) as f:
            gecici = Path(f.name)
            f.write(metin)
        os.replace(str(gecici), str(yol))
    finally:
        if gecici is not None and gecici.exists():
            try:
                gecici.unlink()
            except OSError:
                pass


def oku():
    veri = dict(VARSAYILAN)
    if DOSYA.is_file():
        try:
            ham = json.loads(DOSYA.read_text(encoding="utf-8"))
            if isinstance(ham, dict):
                for k in VARSAYILAN:
                    if isinstance(ham.get(k), str):
                        veri[k] = ham[k]
        except Exception:
            pass
    return veri


def kaydet(**degisen):
    veri = oku()
    for k, v in degisen.items():
        if k in VARSAYILAN:
            veri[k] = str(v or "")
    atomik_yaz(DOSYA, json.dumps(veri, ensure_ascii=False, indent=1))
    return veri


def cikti_koku():
    secili = oku()["cikti_klasoru"].strip()
    if secili:
        return Path(secili).expanduser().resolve()
    env = os.environ.get("VIDEO_SCRAP_HOME")
    return Path(env).resolve() if env else HERE
