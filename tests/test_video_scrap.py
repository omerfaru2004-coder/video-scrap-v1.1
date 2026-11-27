# -*- coding: utf-8 -*-
"""video_scrap.py: bicimlendirme ve dosya adi temizligi."""

import video_scrap as vs


def test_fmt_ts():
    assert vs.fmt_ts(0) == "00:00:00.000"
    assert vs.fmt_ts(65) == "00:01:05.000"
    assert vs.fmt_ts(3725.5) == "01:02:05.500"
    assert vs.fmt_ts(-3) == "00:00:00.000"
    assert vs.fmt_ts(None) == "00:00:00.000"


def test_fmt_dur():
    assert vs.fmt_dur(0) == "0.0 sn"
    assert vs.fmt_dur(75) == "1 dk 15 sn"
    assert vs.fmt_dur(3725) == "1 sa 02 dk 05 sn"
    assert vs.fmt_dur(None) == "0.0 sn"


def test_safe_name_turkce_harfi_korur_ozel_karakteri_degistirir():
    assert vs.safe_name("Çok Güzel: Video / 2") == "Çok_Güzel__Video___2"
    assert vs.safe_name("") == "video"
    assert vs.safe_name("a/b\\c") == "a_b_c"


def test_app_version():
    assert vs.APP_VERSION == "1.1"
