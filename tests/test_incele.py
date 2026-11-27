# -*- coding: utf-8 -*-
"""incele.py: kayit defteri kilidi ve klasor numaralandirma."""

import json
import threading
from pathlib import Path

import incele


def test_next_folder_bos_klasorde_birden_baslar():
    incele.VIDEOLAR.mkdir(parents=True, exist_ok=True)
    for d in list(incele.VIDEOLAR.glob("video*")):
        if d.is_dir():
            d.rmdir()
    assert incele._next_folder("video") == "video1"


def test_next_folder_en_buyuk_numaradan_devam_eder():
    (incele.VIDEOLAR / "video1").mkdir(parents=True, exist_ok=True)
    (incele.VIDEOLAR / "video7").mkdir(parents=True, exist_ok=True)
    (incele.VIDEOLAR / "shorts3").mkdir(parents=True, exist_ok=True)
    assert incele._next_folder("video") == "video8"
    assert incele._next_folder("shorts") == "shorts4"


def test_kilit_eszamanli_yazimda_kayit_kaybetmez():
    incele.VIDEOLAR.mkdir(parents=True, exist_ok=True)
    (incele.VIDEOLAR / "kayit.json").unlink(missing_ok=True)

    def yaz(n):
        with incele._kilit():
            reg = incele._load_registry()
            reg["test:%d" % n] = {"klasor": "video%d" % n, "tur": "video"}
            incele._save_registry(reg)

    izlekler = [threading.Thread(target=yaz, args=(i,)) for i in range(12)]
    for t in izlekler:
        t.start()
    for t in izlekler:
        t.join()

    reg = json.loads((incele.VIDEOLAR / "kayit.json").read_text(encoding="utf-8"))
    assert len(reg) == 12


def test_bozuk_kayit_defteri_bos_doner():
    (incele.VIDEOLAR / "kayit.json").write_text("{bozuk", encoding="utf-8")
    assert incele._load_registry() == {}


def test_url_dogrula_gecerli_linki_kabul_eder():
    assert incele.url_dogrula(" https://youtu.be/abc ") == "https://youtu.be/abc"
    assert incele.url_dogrula("http://ornek.com/v") == "http://ornek.com/v"


def test_url_dogrula_yt_dlp_secenegini_reddeder():
    for kotu in ["--exec=calc", "--plugin-dirs=/tmp", "youtube.com/watch?v=1", "", "ftp://x/y"]:
        try:
            incele.url_dogrula(kotu)
        except incele.IncelemeHatasi:
            continue
        raise AssertionError("kabul edilmemeliydi: %r" % kotu)


def test_ffmpeg_konum_bulunan_yol_gercekten_var():
    yol = incele.ffmpeg_konum()
    assert yol is None or Path(yol).is_file()


def test_calisiyor_canli_pid_icin_true():
    import os
    out = incele.VIDEOLAR / "pid_test"
    out.mkdir(parents=True, exist_ok=True)
    (out / "durum.json").write_text(
        '{"state": "running", "pid": %d, "updated": "2026-01-01 00:00:00"}' % os.getpid(),
        encoding="utf-8")
    assert incele.calisiyor(out) is True


def test_calisiyor_olu_pid_icin_false():
    out = incele.VIDEOLAR / "pid_test2"
    out.mkdir(parents=True, exist_ok=True)
    (out / "durum.json").write_text(
        '{"state": "running", "pid": 999999, "updated": "2026-01-01 00:00:00"}', encoding="utf-8")
    assert incele.calisiyor(out) is False


def test_calisiyor_pidsiz_eski_durum_icin_false():
    out = incele.VIDEOLAR / "pid_test3"
    out.mkdir(parents=True, exist_ok=True)
    (out / "durum.json").write_text(
        '{"state": "running", "stage": "basliyor", "updated": "2020-01-01 00:00:00"}', encoding="utf-8")
    assert incele.calisiyor(out) is False


def test_calisiyor_bitmis_is_icin_false():
    out = incele.VIDEOLAR / "pid_test4"
    out.mkdir(parents=True, exist_ok=True)
    (out / "durum.json").write_text('{"state": "done"}', encoding="utf-8")
    assert incele.calisiyor(out) is False


def test_indiriliyor_kaydi_ikinci_klasor_acmaz():
    (incele.VIDEOLAR / "video1").mkdir(parents=True, exist_ok=True)
    (incele.VIDEOLAR / "kayit.json").write_text(json.dumps({
        "YouTube:abc": {"klasor": "video1", "tur": "video", "durum": "indiriliyor"}}), encoding="utf-8")
    eski = incele._meta
    incele._meta = lambda url: ("YouTube:abc", 120.0, "test")
    try:
        try:
            incele.prepare("https://youtu.be/abc")
        except incele.IncelemeHatasi as exc:
            assert "indirme zaten suruyor" in str(exc)
        else:
            raise AssertionError("ikinci cagri reddedilmeliydi")
    finally:
        incele._meta = eski
    assert not (incele.VIDEOLAR / "video2").exists()
