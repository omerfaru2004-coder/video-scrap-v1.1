# -*- coding: utf-8 -*-
"""ayarlar.py: atomik yazim ve ayar turu."""

import json

import ayarlar
from conftest import TEST_KOK


def test_atomik_yaz_gecerli_json_birakir():
    hedef = TEST_KOK / "atomik.json"
    for i in range(50):
        ayarlar.atomik_yaz(hedef, json.dumps({"i": i, "dolu": "x" * 400}))
        assert json.loads(hedef.read_text(encoding="utf-8"))["i"] == i


def test_atomik_yaz_gecici_dosya_birakmaz():
    hedef = TEST_KOK / "atomik2.json"
    ayarlar.atomik_yaz(hedef, "{}")
    assert [p.name for p in TEST_KOK.glob("*.tmp")] == []


def test_kaydet_oku_turu():
    ayarlar.kaydet(cikti_klasoru=str(TEST_KOK / "cikti"), arka_plan="")
    veri = ayarlar.oku()
    assert veri["cikti_klasoru"] == str(TEST_KOK / "cikti")
    assert ayarlar.cikti_koku() == (TEST_KOK / "cikti").resolve()
    ayarlar.kaydet(cikti_klasoru="", arka_plan="")


def test_bilinmeyen_anahtar_yazilmaz():
    ayarlar.kaydet(olmayan_anahtar="x")
    assert "olmayan_anahtar" not in ayarlar.oku()
