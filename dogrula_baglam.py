# -*- coding: utf-8 -*-
"""
CLAUDE.md baglam dosyasini, hicbir yapay zeka oturumu ve kredi harcamadan dogrular.

Kullanim:
    python dogrula_baglam.py
    python dogrula_baglam.py --ayrintili

Yaptigi: CLAUDE.md icindeki iddialari (arac sayisi, dosya yollari, git disi klasorler,
giris noktalari) gercek depoyla karsilastirir. Cikis kodu 0 = hepsi gecti, 1 = hata var.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BAGLAM = HERE / "CLAUDE.md"

sonuclar = []


def ekle(ad, gecti, detay=""):
    sonuclar.append((ad, bool(gecti), detay))


def oku(yol):
    return yol.read_text(encoding="utf-8", errors="replace")


def mcp_araclari():
    """mcp_server.py icindeki @mcp.tool(name=...) adlarini toplar."""
    kaynak = oku(HERE / "mcp_server.py")
    return re.findall(r'@mcp\.tool\(\s*\n\s*name="([^"]+)"', kaynak)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ayrintili", action="store_true", help="her kontrolun ayrintisini yaz")
    args = ap.parse_args()

    if not BAGLAM.exists():
        print("HATA: CLAUDE.md bulunamadi: %s" % BAGLAM)
        return 1
    metin = oku(BAGLAM)

    # 1) Dosya var ve bos degil
    ekle("CLAUDE.md var", True, "%d satir, %d karakter" % (metin.count("\n") + 1, len(metin)))

    # 2) Baska bir urunun baglami sizmamis
    sizan = re.findall(r"(?i)abacus", metin)
    ekle("CLAUDE.md icinde 'abacus' gecmiyor", not sizan, "%d eslesme" % len(sizan))

    # 3) MCP arac listesi gercek sunucuyla ayni
    gercek = mcp_araclari()
    m = re.search(r"\((\d+)\s*ara[cç]\)", metin)
    yazilan = int(m.group(1)) if m else -1
    ekle("CLAUDE.md arac sayisi gercekle uyuyor", yazilan == len(gercek),
         "CLAUDE.md: %s | mcp_server.py: %d" % (yazilan if yazilan >= 0 else "yazmiyor", len(gercek)))
    eksik = [a for a in gercek if a not in metin]
    ekle("CLAUDE.md tum araclari sayiyor", not eksik,
         "eksik: %s" % ", ".join(eksik) if eksik else "%d arac" % len(gercek))

    # 4) Giris noktasi tablosundaki dosyalar gercekten var
    beklenen = ["video_scrap.py", "arayuz.py", "incele.py", "analiz.py", "ses.py",
                "mcp_server.py", "mcp_kaydet.py", "ayarlar.py",
                "kur.py", "KUR.bat", "BASLAT.bat"]
    yok = [d for d in beklenen if not (HERE / d).exists()]
    ekle("giris noktalari mevcut", not yok, "eksik: %s" % ", ".join(yok) if yok else "%d dosya" % len(beklenen))

    # 5) Rehber klasoru ve dosyalari
    rehber = ["00_BENI_OKU.md", "01_KURULUM.md", "02_KULLANIM_KILAVUZU.md",
              "03_YAPAY_ZEKAYA_BAGLAMA.md", "04_GITHUB_YAYIN.md", "05_TEKNIK_DETAYLAR.md"]
    yok = [d for d in rehber if not (HERE / "OKU_BENI" / d).exists()]
    ekle("OKU_BENI rehberleri mevcut", not yok, "eksik: %s" % ", ".join(yok) if yok else "%d dosya" % len(rehber))

    # 5b) Diger CLI'larin baglam dosyalari CLAUDE.md'ye yonlendiriyor
    for ad in ["AGENTS.md", "GEMINI.md"]:
        yol = HERE / ad
        var = yol.exists() and "CLAUDE.md" in oku(yol)
        ekle("%s CLAUDE.md'ye yonlendiriyor" % ad, var,
             "yonlendirme var" if var else "dosya yok veya yonlendirme yok")

    # 5c) Tek baslatici: BASLAT.* dosyalarindan yalnizca biri olmali
    baslaticilar = sorted(x.name for x in HERE.glob("BASLAT.*"))
    ekle("tek baslatici var", baslaticilar == ["BASLAT.bat"], ", ".join(baslaticilar) or "yok")

    # 5d) Kaynak dosyalarda sabit kullanici yolu olmamali (baska cihazda kirilir)
    sabit = []
    desen = re.compile(r"(?i)(C:[\\/]+Users[\\/]+[A-Za-z0-9._-]+|/home/[A-Za-z0-9._-]+)")
    taranan = [d for d in sorted(HERE.glob("*.py")) if d.name != Path(__file__).name]
    for dosya in taranan:
        if desen.search(oku(dosya)):
            sabit.append(dosya.name)
    ekle("kaynakta sabit kullanici yolu yok", not sabit,
         "sabit yol: %s" % ", ".join(sabit) if sabit else "%d dosya tarandi" % len(taranan))

    # 5e) Kurulum betigi sanal ortami ve requirements'i kuruyor mu (KUR.bat -> kur.py)
    kur = ""
    for ad in ["KUR.bat", "kur.py"]:
        yol = HERE / ad
        if yol.exists():
            kur += oku(yol)
    eksik = [d for d in [".venv", "requirements.txt"] if d not in kur]
    ekle("KUR.bat .venv ve requirements kuruyor", not eksik,
         "eksik: %s" % ", ".join(eksik) if eksik else "ikisi de var")

    # 5e-2) ffmpeg elle kurulmuyor, paketle geliyor
    req = oku(HERE / "requirements.txt") if (HERE / "requirements.txt").exists() else ""
    ekle("requirements.txt ffmpeg paketini iceriyor", "imageio-ffmpeg" in req,
         "imageio-ffmpeg var" if "imageio-ffmpeg" in req else "eksik")

    # 5f) Testler ve gelistirme bagimliliklari yerinde mi
    testler = sorted((HERE / "tests").glob("test_*.py")) if (HERE / "tests").is_dir() else []
    ekle("tests/ testleri mevcut", len(testler) >= 3, "%d test dosyasi" % len(testler))
    dev = oku(HERE / "requirements-dev.txt") if (HERE / "requirements-dev.txt").exists() else ""
    ekle("requirements-dev.txt pytest iceriyor", "pytest" in dev, dev.strip() or "dosya yok")

    # 6) .gitignore, CLAUDE.md'nin "git disi" dedigi yollari gercekten disliyor
    gi = oku(HERE / ".gitignore") if (HERE / ".gitignore").exists() else ""
    disli = ["videolar/", "calisma/", "libs/", ".venv/", "ayarlar.json", "__pycache__/"]
    eksik = [d for d in disli if d not in gi]
    ekle(".gitignore git disi yollari kapsiyor", not eksik,
         "eksik kural: %s" % ", ".join(eksik) if eksik else "%d kural" % len(disli))

    # 7) Bu yollar gercekten izlenmiyor
    try:
        izlenen = subprocess.run(["git", "ls-files"], cwd=str(HERE), capture_output=True,
                                 text=True, encoding="utf-8", errors="replace").stdout
    except OSError:
        izlenen = ""
    sizan_yol = [d for d in ["videolar/", "calisma/", "libs/", ".venv/", "ayarlar.json"]
                 if any(satir.startswith(d) for satir in izlenen.splitlines())]
    ekle("kullanici verisi git'e girmemis", not sizan_yol,
         "izlenen: %s" % ", ".join(sizan_yol) if sizan_yol else "%d dosya izleniyor" % len(izlenen.splitlines()))

    # 8) CLAUDE.md'deki komutlar gercekten calisiyor (hafif olanlar)
    for betik, olcu in [("mcp_kaydet.py", ["--goster"]), ("incele.py", ["--help"])]:
        r = subprocess.run([sys.executable, str(HERE / betik)] + olcu, cwd=str(HERE),
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        ekle("%s calisiyor" % betik, r.returncode == 0, "cikis kodu: %d" % r.returncode)

    # 9) MCP kaydi bu klasoru gosteriyor mu
    kayit = Path.home() / ".abacusai" / "mcp.json"
    if kayit.exists():
        try:
            veri = json.loads(kayit.read_text(encoding="utf-8-sig"))
            sunucu = (veri.get("mcpServers") or {}).get("video-scrap") or {}
            args_ = sunucu.get("args") or []
            yol = str(args_[0]) if args_ else ""
            ayni = yol.replace("\\", "/").lower().startswith(str(HERE).replace("\\", "/").lower())
            ekle("MCP kaydi bu klasoru gosteriyor", ayni, yol or "kayit yok")
        except Exception as hata:  # noqa: BLE001
            ekle("MCP kaydi okunabiliyor", False, str(hata))
    else:
        ekle("MCP kaydi var", False, "dosya yok: %s" % kayit)

    # Rapor
    gecen = sum(1 for _, g, _ in sonuclar if g)
    print("")
    print("CLAUDE.md baglam denetimi")
    print("=" * 60)
    for ad, gecti, detay in sonuclar:
        im = "GECTI" if gecti else "HATA "
        satir = "  [%s] %s" % (im, ad)
        if args.ayrintili or not gecti:
            satir += "  -> %s" % detay
        print(satir)
    print("=" * 60)
    print("%d/%d kontrol gecti" % (gecen, len(sonuclar)))
    if gecen != len(sonuclar):
        print("Sonuc: baglam dosyasi ile depo arasinda uyusmazlik var.")
        return 1
    print("Sonuc: baglam dosyasi depoyla tutarli.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
