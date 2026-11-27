# -*- coding: utf-8 -*-
"""
Video Scrap'i yerel MCP listesine kaydeder.

Kullanim:
    python mcp_kaydet.py                     -> Abacus Desktop'a kaydeder
    python mcp_kaydet.py --hedef claude      -> Claude Desktop'a kaydeder
    python mcp_kaydet.py --kaldir            -> kaydi siler
    python mcp_kaydet.py --goster            -> mevcut kaydi gosterir

Kayit dosyalari:
    abacus : C:/Users/<kullanici>/.abacusai/mcp.json
    claude : %APPDATA%/Claude/claude_desktop_config.json
Var olan diger sunucular (ornegin browser) korunur.
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ayarlar  # noqa: E402

SERVER_NAME = "video-scrap"
HERE = Path(__file__).resolve().parent


def hedef_yolu(hedef):
    if hedef == "claude":
        appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(appdata) / "Claude" / "claude_desktop_config.json"
    return Path.home() / ".abacusai" / "mcp.json"


def load(path):
    if not path.is_file():
        return {"mcpServers": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        print("HATA: %s okunamadi (%s)" % (path, exc))
        sys.exit(1)
    if not isinstance(data, dict):
        data = {}
    data.setdefault("mcpServers", {})
    return data


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        backup = path.with_suffix(".json.bak")
        if not backup.exists():  # ilk yedegi koru, her calistirmada ezme
            shutil.copy2(path, backup)
            print("Yedek: %s" % backup)
    ayarlar.atomik_yaz(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print("Yazildi: %s" % path)


def yorumlayici():
    """Kayda yazilacak python: once .venv, yoksa mevcut yorumlayici.

    Betik .venv disi bir Python ile calistirilirsa kayit, 'mcp' modulu olmayan bir
    yorumlayiciyi gosterebilir ve istemci tarafinda sunucu hemen kapanir.
    """
    for aday in (HERE / ".venv" / "Scripts" / "python.exe", HERE / ".venv" / "bin" / "python"):
        if aday.is_file():
            return str(aday), True
    return sys.executable, False


def entry():
    py, venv = yorumlayici()
    if not venv:
        print("UYARI: .venv bulunamadi; kayit mevcut python'a yaziliyor (%s)." % py)
        print("       Once KUR.bat calistir, sonra bu betigi .venv\\Scripts\\python.exe ile tekrar calistir.")
    return {
        "command": py.replace("\\", "/"),
        "args": [str(HERE / "mcp_server.py").replace("\\", "/")],
        "type": "stdio",
        "env": {"VIDEO_SCRAP_HOME": str(HERE).replace("\\", "/")},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hedef", choices=["abacus", "claude"], default="abacus",
                    help="kayit dosyasi: abacus (varsayilan) veya claude")
    ap.add_argument("--kaldir", action="store_true", help="kaydi sil")
    ap.add_argument("--goster", action="store_true", help="mevcut kaydi goster")
    args = ap.parse_args()

    CONFIG = hedef_yolu(args.hedef)
    data = load(CONFIG)

    if args.goster:
        print(json.dumps(data.get("mcpServers", {}).get(SERVER_NAME, {}), indent=2, ensure_ascii=False))
        return 0

    if args.kaldir:
        if SERVER_NAME in data["mcpServers"]:
            del data["mcpServers"][SERVER_NAME]
            save(CONFIG, data)
            print("Kayit silindi. Uygulamayi yeniden baslat.")
        else:
            print("Kayit zaten yok.")
        return 0

    data["mcpServers"][SERVER_NAME] = entry()
    save(CONFIG, data)
    print("")
    print("Kayit eklendi: %s (%s)" % (SERVER_NAME, args.hedef))
    print("  python : %s" % entry()["command"])
    print("  sunucu : %s" % entry()["args"][0])
    print("")
    if args.hedef == "claude":
        print("Simdi Claude Desktop'i tamamen kapatip yeniden ac;")
        print("sohbet kutusundaki arac simgesinde video-scrap gorunur.")
    else:
        print("Simdi Abacus Desktop'i (veya Code oturumunu) yeniden baslat,")
        print('sonra MCP ekraninda "Iceri aktar" butonuna bas ve video-scrap listesini kontrol et.')
    return 0


if __name__ == "__main__":
    sys.exit(main())
