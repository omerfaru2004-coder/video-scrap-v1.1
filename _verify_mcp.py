"""MCP sunucusunu gercek bir istemciyle dener.

Kullanim:
    python _verify_mcp.py                 # yalnizca arac listesini ve initialize'i dener
    python _verify_mcp.py <video-dosyasi> # ek olarak analyze_video akisini dener

Yollar bu makineye gore uretilir; baska bir bilgisayarda degistirmek gerekmez.
"""

import asyncio
import json
import sys
import time
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

HERE = Path(__file__).resolve().parent


async def main():
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(HERE / "mcp_server.py")],
        env={"VIDEO_SCRAP_HOME": str(HERE)},
    )
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            print("TOOLS:", [t.name for t in (await s.list_tools()).tools])

            if len(sys.argv) < 2:
                print("VIDEO verilmedi; analyze akisi atlandi.")
                return
            video = str(Path(sys.argv[1]).resolve())
            if not Path(video).exists():
                print("VIDEO bulunamadi:", video)
                return

            bad = await s.call_tool("analyze_video", {"video_path": video, "out_dir": "C:/tmp/vs_test/disari"})
            print("DISARI_YAZMA_HATA:", bad.is_error, bad.content[0].text[:160])

            t0 = time.time()
            res = await s.call_tool("analyze_video", {"video_path": video, "out_dir": "calisma/mcp_test"})
            print("START:", res.is_error, res.content[0].text, round(time.time() - t0, 2), "sn")
            out = json.loads(res.content[0].text)["out_dir"]
            while True:
                st = await s.call_tool("job_status", {"out_dir": out})
                d = json.loads(st.content[0].text)
                if d.get("state") != "running":
                    break
                await asyncio.sleep(10)
            print("FINAL:", d["state"], d.get("sure_sn"), d.get("olay_sayisi"),
                  d.get("genel_sayfa"), d.get("yakin_sayfa"))
            img = await s.call_tool("view_sheet", {"out_dir": out, "sheet_name": "yakin_0001.jpg",
                                                   "folder": "yakin_cekim"})
            print("VIEW:", img.is_error, img.content[0].type)


asyncio.run(main())
