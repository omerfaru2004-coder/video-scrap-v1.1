# -*- coding: utf-8 -*-
"""mcp_server.py: arac listesi ve yol guvenligi."""

import re
from pathlib import Path

import pytest
from mcp.server.mcpserver.exceptions import ToolError

import mcp_server

KOK = Path(__file__).resolve().parent.parent


def test_arac_sayisi_claude_md_ile_uyusuyor():
    kaynak = (KOK / "mcp_server.py").read_text(encoding="utf-8")
    gercek = re.findall(r'@mcp\.tool\(\s*\n\s*name="([^"]+)"', kaynak)
    metin = (KOK / "CLAUDE.md").read_text(encoding="utf-8")
    yazilan = int(re.search(r"\((\d+)\s*ara[cç]\)", metin).group(1))
    assert yazilan == len(gercek) == 14


def test_inside_base_proje_disini_reddeder(tmp_path):
    disari = tmp_path.parent / "vs_test_disari"
    with pytest.raises(ToolError):
        mcp_server.inside_base(str(disari))


def test_inside_base_goreli_yolu_koke_baglar():
    assert mcp_server.inside_base("calisma") == (mcp_server.BASE_DIR / "calisma").resolve()


def test_view_sheet_gecersiz_klasoru_reddeder():
    with pytest.raises(ToolError):
        mcp_server.view_sheet("calisma", folder="../sheets")


def test_view_sheet_olmayan_klasorde_hata_verir():
    with pytest.raises(ToolError):
        mcp_server.view_sheet("calisma", folder="sheets")


def test_view_sheet_sayfa_adi_dizin_gecisini_kabul_etmez():
    out = mcp_server.BASE_DIR / "calisma" / "vs_sheet_test"
    (out / "sheets").mkdir(parents=True, exist_ok=True)
    with pytest.raises(ToolError):
        mcp_server.view_sheet(str(out), sheet_name="../../gizli.jpg")
