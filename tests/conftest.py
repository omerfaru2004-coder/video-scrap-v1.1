# -*- coding: utf-8 -*-
"""Testler icin gecici kok klasor: gercek videolar/ ve ayarlar.json'a dokunulmaz."""

import os
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK))

_GECICI = Path(tempfile.mkdtemp(prefix="vs_test_"))
os.environ["VIDEO_SCRAP_HOME"] = str(_GECICI)

import ayarlar  # noqa: E402

ayarlar.DOSYA = _GECICI / "ayarlar.json"

TEST_KOK = _GECICI
