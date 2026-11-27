# -*- coding: utf-8 -*-
"""
Video Scrap MCP sunucusu
========================
video_scrap.py'yi bir MCP araci olarak sunar. Yapay zeka, sohbet icinden
dogrudan video isleyip ciktisini istedigi klasore yazabilir ve uretilen
kontak sayfalarini kendisi goruntuleyebilir.

Calistirma (stdio):
    python mcp_server.py

Onemli: stdout MCP protokolune aittir, tum gunluk kayitlar stderr'e yazilir.
"""

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp.server.mcpserver import MCPServer, Image
from mcp.server.mcpserver.exceptions import ToolError

import incele
import video_scrap

import ayarlar

BASE_DIR = ayarlar.cikti_koku()

mcp = MCPServer(
    name="video-scrap",
    title="Video Scrap",
    version=video_scrap.APP_VERSION,
    instructions=(
        "Video karelerini kontak sayfalarina cevirir. Kullanici bir video linki verirse "
        "incele_video'yu cagir (videolar/ klasorune indirir ve analiz eder), job_status ile bekle, "
        "olaylar.md'yi oku, view_sheet ile sadece gereken sayfalari ac. Kisa kare cikarma icin scrap_video. "
        "Her karede zaman damgasi ve kare numarasi vardir; sayfa okuma sirasi soldan saga, "
        "yukaridan asagiya ve videonun kronolojik akisidir."
    ),
)


def log(msg):
    sys.stderr.write("[video-scrap] %s\n" % msg)
    sys.stderr.flush()


def resolve(path, must_exist=True):
    p = Path(str(path)).expanduser()
    if not p.is_absolute():
        p = BASE_DIR / p
    p = p.resolve()
    if must_exist and not p.exists():
        raise ToolError("Bulunamadi: %s" % p)
    return p


def inside_base(path):
    p = Path(str(path)).expanduser()
    if not p.is_absolute():
        p = BASE_DIR / p
    p = p.resolve()
    try:
        p.relative_to(BASE_DIR.resolve())
    except ValueError:
        raise ToolError("Yazma sadece proje klasoru icinde yapilir (%s). Reddedilen yol: %s" % (BASE_DIR, p))
    return p


@mcp.tool(
    name="download_video",
    description="YouTube (veya yt-dlp destekli herhangi bir) linkten videoyu yerel diske indirir "
                "ve dosya yolunu dondurur. Sonra scrap_video ile analiz et. "
                "max_height ile cozunurluk siniri verilir (varsayilan 720).",
)
def download_video(url: str, out_dir: str = "indirilenler", max_height: int = 720) -> dict:
    import subprocess
    link = incele.url_dogrula(url)
    dest = inside_base(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    tmpl = str(dest / "%(title).80s [%(id)s].%(ext)s")
    js = ["--js-runtimes", "node"] if __import__("shutil").which("node") else []
    cmd = [sys.executable, "-m", "yt_dlp"] + js + ["--no-playlist", "--restrict-filenames",
           "-f", "bv*[height<=%d]+ba/b[height<=%d]/b" % (max_height, max_height),
           "--merge-output-format", "mp4", "--print", "after_move:filepath",
           "--no-simulate", "-o", tmpl, "--", link]
    log("indiriliyor: %s" % link)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=1800,
                           creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0))
    except subprocess.TimeoutExpired:
        raise ToolError("Indirme 1800 sn icinde bitmedi; islem durduruldu.")
    lines = [l.strip() for l in r.stdout.splitlines() if l.strip()]
    if r.returncode != 0 or not lines:
        raise ToolError("Indirme basarisiz: %s" % incele.yt_hata(r.stderr))
    yollar = [l for l in lines if Path(l).suffix.lower() in incele.VIDEO_EXT and Path(l).is_file()]
    if not yollar:
        raise ToolError("Indirme bitti ama video dosyasi bulunamadi: %s" % dest)
    return {"video_path": yollar[-1], "folder": str(dest)}


@mcp.tool(
    name="incele_video",
    description=(
        "ILK TERCIH: kullanici bir video linki (veya yerel dosya) verdiginde bunu cagir. "
        "videolar/ klasorunu gerekirse acar, videoyu kendi klasorune indirir (kisa/shorts videolar "
        "videolar/shortsN, digerleri videolar/videoN) ve analizi arka planda baslatir; cikti "
        "<klasor>/analiz/ icine yazilir. Ayni link tekrar verilirse yeniden indirmez, bitmis analizi kullanir. "
        "Sonra job_status(analiz_klasoru) ile bekle; bitince olaylar.md'yi oku, sadece orada adi gecen "
        "sayfalari view_sheet ile ac. yeniden=True analizi zorla tekrarlar."
    ),
)
def incele_video(kaynak: str, max_height: int = 720, yeniden: bool = False) -> dict:
    try:
        res = incele.prepare(kaynak, max_height, log=log)
    except incele.IncelemeHatasi as exc:
        raise ToolError(str(exc))
    if res["analiz_durumu"] == "done" and not yeniden:
        res["not"] = "Analiz zaten bitmis; job_status ile olaylar.md'yi oku."
        return res
    if res["analiz_durumu"] == "running" and not yeniden:
        res["not"] = "Analiz suruyor; job_status ile takip et."
        return res
    try:
        incele.start_analysis(res["video_path"], res["analiz_klasoru"], zorla=yeniden)
    except incele.IncelemeHatasi as exc:
        raise ToolError(str(exc))
    res["analiz_durumu"] = "running"
    res["not"] = "Analiz baslatildi; job_status(analiz_klasoru) ile takip et."
    return res


@mcp.tool(
    name="videolari_listele",
    description="videolar/ klasorundeki daha once indirilmis/analiz edilmis videolari listeler.",
)
def videolari_listele() -> dict:
    return {"videolar": incele.list_videos(), "kok": str(incele.VIDEOLAR)}


@mcp.tool(
    name="video_info",
    description="Bir video dosyasinin sure, fps, cozunurluk ve kare sayisini dondurur. "
                "Islem yapmadan once maliyeti tahmin etmek icin kullan.",
)
def video_info(video_path: str) -> dict:
    path = resolve(video_path)
    info = video_scrap.probe_video(str(path))
    info["duration_text"] = video_scrap.fmt_dur(info["duration"])
    return info


@mcp.tool(
    name="scrap_video",
    description=(
        "Videoyu karelerine ayirir ve her sayfada cols*rows kare olacak sekilde kontak "
        "sayfalari (JPEG) uretir. Cikti klasorune sheets/, prompt.txt, rapor.md ve "
        "manifest.csv yazar. mode: all (her kare), every_n (her n. kare), fps (saniyede "
        "target_fps kare), scene (sahne degisimi). Uzun videolarda every_n veya fps kullan."
    ),
)
def scrap_video(
    video_path: str,
    out_dir: str = "",
    mode: str = "every_n",
    n: int = 5,
    target_fps: float = 2.0,
    cols: int = 8,
    rows: int = 5,
    thumb_w: int = 320,
    quality: int = 88,
    sharpen: bool = True,
    save_frames: bool = False,
    max_frames: int = 0,
) -> dict:
    path = resolve(video_path)
    if mode not in video_scrap.MODE_KEYS:
        raise ToolError("Gecersiz mode: %s (gecerli: %s)" % (mode, ", ".join(video_scrap.MODE_KEYS)))

    out = inside_base(out_dir) if str(out_dir).strip() else inside_base(BASE_DIR / "calisma" / video_scrap.safe_name(path.stem))

    log("scrap_video: %s -> %s (mode=%s)" % (path.name, out, mode))

    try:
        summary = video_scrap.process_video(
            str(path), str(out),
            mode=mode, n=n, target_fps=target_fps,
            cols=cols, rows=rows, thumb_w=thumb_w, quality=quality,
            save_frames=save_frames, sharpen=sharpen, max_frames=max_frames,
            log=log,
        )
    except ToolError:
        raise
    except Exception as exc:
        raise ToolError("Video islenemedi: %s" % exc)

    sheets = []
    for sheet in summary["sheets"]:
        sheets.append({
            "name": sheet["name"],
            "path": sheet["path"],
            "frames": sheet["count"],
            "from": video_scrap.fmt_ts(sheet["first_ts"]),
            "to": video_scrap.fmt_ts(sheet["last_ts"]),
        })

    return {
        "video": summary["video"]["name"],
        "out_dir": summary["out_dir"],
        "mode": summary["mode"],
        "mode_text": summary["mode_text"],
        "frames_read": summary["frames_read"],
        "frames_kept": summary["frames_kept"],
        "sheet_count": len(sheets),
        "frames_per_sheet": cols * rows,
        "sheets": sheets,
        "prompt_file": str(Path(summary["out_dir"]) / "prompt.txt"),
        "report_file": str(Path(summary["out_dir"]) / "rapor.md"),
        "manifest_file": str(Path(summary["out_dir"]) / "manifest.csv"),
        "elapsed_sec": round(summary["elapsed"], 2),
    }


@mcp.tool(
    name="analyze_video",
    description=(
        "Iki asamali analiz baslatir (arka planda calisir, hemen is bilgisi doner): genel tarama "
        "(saniyede ~1 kare, sheets/) ve gecis/efekt anlarinin yakin cekimi (yakin_cekim/). "
        "Bitince olaylar.md okunur: hangi saniyede hangi gecis var, hangi sayfada. "
        "Durumu job_status ile sorgula; sadece olaylar.md'de adi gecen sayfalari view_sheet ile ac. "
        "cut: keskin gecis esigi (0.25), soft: yumusak gecis esigi (0.05). "
        "out_dir proje klasoru icinde olmali; bos birakilirsa calisma/<video adi> kullanilir."
    ),
)
def analyze_video(video_path: str, out_dir: str = "", cut: float = 0.25, soft: float = 0.05,
                  max_closeup: int = 400, zorla: bool = False) -> dict:
    path = resolve(video_path)
    out = inside_base(out_dir) if str(out_dir).strip() else inside_base(BASE_DIR / "calisma" / video_scrap.safe_name(path.stem))
    try:
        incele.start_analysis(path, out, cut=cut, soft=soft, max_closeup=max_closeup, zorla=zorla)
    except incele.IncelemeHatasi as exc:
        raise ToolError(str(exc))
    log("analyze_video basladi: %s -> %s" % (path.name, out))
    return {"out_dir": str(out), "state": "running",
            "next": "job_status ile durumu sorgula; bitince olaylar.md dosyasini oku"}


@mcp.tool(
    name="zoom_range",
    description=(
        "Videonun belirli bir zaman araligini (saniye) sik karelerle kontak sayfasina cevirir. "
        "olaylar.md'de bulunan bir gecis/animasyon icin kullan: step=1 her kare, 2 her 2. kare. "
        "Cikti out_dir/aralik_*/ klasorune yazilir; view_sheet ile folder='aralik_...' vererek ac. "
        "En fazla 200 kare (5 sayfa). out_dir proje klasoru icinde olmali."
    ),
)
def zoom_range(video_path: str, out_dir: str, start: float, end: float, step: int = 1,
               thumb_w: int = 320) -> dict:
    import analiz
    path = resolve(video_path)
    out = inside_base(out_dir)
    try:
        return analiz.zoom_range(str(path), str(out), start, end, step=step, thumb_w=thumb_w, log=log)
    except RuntimeError as exc:
        raise ToolError(str(exc))


def _pid_alive(pid):
    return incele.pid_canli(pid)


def _bayat_kontrol(data):
    """state=running ama islem olduyse durumu 'error' yap (takili is sonsuza kadar 'running' kalmasin)."""
    if data.get("state") != "running":
        return
    alive = _pid_alive(data.get("pid"))
    if alive is False:
        data["state"] = "error"
        data["uyari"] = "Islem (pid %s) artik calismiyor; bitmeden olmus. incele_video(yeniden=True) ile tekrar baslat." % data.get("pid")
    elif alive is None:
        # pid hic yazilmamis: baslangicta olen is. 120 sn'den eskiyse bayat say.
        try:
            age = time.time() - time.mktime(time.strptime(data.get("updated", ""), "%Y-%m-%d %H:%M:%S"))
        except Exception:
            age = 0
        if age > 120:
            data["state"] = "error"
            data["uyari"] = "Islem baslamadan durmus (pid yok, durum %d sn'dir guncellenmedi). Yeniden baslat." % age
    else:
        upd = data.get("updated")
        try:
            age = time.time() - time.mktime(time.strptime(upd, "%Y-%m-%d %H:%M:%S"))
            if age > 600:
                data["uyari"] = "Durum %d sn'dir guncellenmedi (islem canli gorunuyor, uzun aşama olabilir)." % age
        except Exception:
            pass


@mcp.tool(
    name="transcribe_video",
    description=(
        "Videonun SESINI zaman damgali yaziya doker (Whisper, arka planda). GPU varsa medium, yoksa small. "
        "out_dir proje klasoru icinde olmali; incele_video'nun analiz klasorunu verirsen "
        "transcript.md orada olusur. Durum: job_status(out_dir, ses=True) veya read_transcript. "
        "language varsayilan tr."
    ),
)
def transcribe_video(video_path: str, out_dir: str = "", model: str = "", language: str = "tr") -> dict:
    import subprocess
    path = resolve(video_path)
    out = inside_base(out_dir) if str(out_dir).strip() else inside_base(BASE_DIR / "calisma" / video_scrap.safe_name(path.stem))
    out.mkdir(parents=True, exist_ok=True)
    f = out / "ses_durum.json"
    if f.is_file():
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            _bayat_kontrol(d)
            if d.get("state") == "running":
                return {"out_dir": str(out), "state": "running", "not": "Zaten calisiyor; read_transcript ile takip et."}
        except Exception:
            pass
    logf = open(out / "ses_log.txt", "w", encoding="utf-8")
    env = dict(os.environ)
    env["VIDEO_SCRAP_HOME"] = str(BASE_DIR)
    f.write_text(json.dumps({"state": "running", "stage": "basliyor"}), encoding="utf-8")
    cmd = [sys.executable, "-u", str(Path(__file__).resolve().parent / "ses.py"), "--video", str(path),
           "--out", str(out), "--model", model, "--language", language]
    flags = 0
    if os.name == "nt":
        flags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT, env=env, creationflags=flags)
    logf.close()
    log("transcribe_video basladi: %s -> %s" % (path.name, out))
    return {"out_dir": str(out), "state": "running", "next": "read_transcript(out_dir) ile bekle; bitince metin gelir"}


@mcp.tool(
    name="read_transcript",
    description=(
        "transcribe_video ciktisini dondurur. Calisiyorsa durumu soyler. start/end (saniye) verilirse "
        "yalniz o araligin satirlarini getirir; bos birakilirsa tamami."
    ),
)
def read_transcript(out_dir: str, start: float = 0.0, end: float = 0.0) -> str:
    out = resolve(out_dir)
    sf = out / "ses_durum.json"
    if not sf.is_file():
        raise ToolError("ses_durum.json yok: transcribe_video once calistirilmali (%s)" % out)
    d = json.loads(sf.read_text(encoding="utf-8"))
    _bayat_kontrol(d)
    if d.get("state") == "error":
        raise ToolError("Ses dokumu hatasi: %s" % (d.get("error") or d.get("uyari")))
    if d.get("state") != "done":
        return "Durum: %s (%s). Biraz sonra tekrar cagir." % (d.get("state"), d.get("stage"))
    segs = json.loads((out / "transcript.json").read_text(encoding="utf-8"))
    if end and end > start:
        segs = [s for s in segs if s["end"] >= start and s["start"] <= end]
    import ses
    return "\n".join("[%s - %s] %s" % (ses.ts(s["start"]), ses.ts(s["end"]), s["text"]) for s in segs)


@mcp.tool(
    name="job_status",
    description="analyze_video isinin durumunu dondurur (running/done/error). Bitince olaylar.md "
                "icerigini de ekler.",
)
def job_status(out_dir: str) -> dict:
    out = resolve(out_dir)
    f = out / "durum.json"
    if not f.is_file():
        raise ToolError("durum.json yok: %s" % f)
    data = json.loads(f.read_text(encoding="utf-8"))
    _bayat_kontrol(data)
    if data.get("state") == "done":
        md = out / "olaylar.md"
        if md.is_file():
            data["olaylar_md"] = md.read_text(encoding="utf-8")
    elif data.get("state") == "running":
        lg = out / "analiz_log.txt"
        if lg.is_file():
            data["log_son"] = lg.read_text(encoding="utf-8", errors="replace")[-400:]
    return data


@mcp.tool(
    name="list_outputs",
    description="Bir cikti klasorundeki kontak sayfalarini ve yardimci dosyalari listeler.",
)
def list_outputs(out_dir: str) -> dict:
    out = resolve(out_dir)
    sheets_dir = out / "sheets"
    sheets = []
    if sheets_dir.is_dir():
        for f in sorted(sheets_dir.glob("*.jpg")):
            sheets.append({"name": f.name, "size_kb": round(f.stat().st_size / 1024.0, 1)})
    files = []
    for name in ("prompt.txt", "rapor.md", "manifest.csv", "olaylar.md", "olaylar.json", "durum.json"):
        f = out / name
        if f.is_file():
            files.append({"name": name, "size_kb": round(f.stat().st_size / 1024.0, 1)})
    closeups = []
    cdir = out / "yakin_cekim"
    if cdir.is_dir():
        closeups = [f.name for f in sorted(cdir.glob("*.jpg"))]
    frames_dir = out / "frames"
    frame_count = len(list(frames_dir.glob("*.jpg"))) if frames_dir.is_dir() else 0
    return {
        "out_dir": str(out),
        "sheets": sheets,
        "sheet_count": len(sheets),
        "yakin_cekim": closeups,
        "files": files,
        "frames_saved": frame_count,
    }


@mcp.tool(
    name="view_sheet",
    description="Uretilen bir kontak sayfasini goruntu olarak dondurur, boylece videoyu "
                "dogrudan inceleyebilirsin. sheet_name bos birakilirsa ilk sayfa gelir. "
                "folder: 'sheets' (genel tarama), 'yakin_cekim' (gecis anlari) veya zoom_range'in 'aralik_...' klasoru.",
)
def view_sheet(out_dir: str, sheet_name: str = "", folder: str = "sheets"):
    out = resolve(out_dir)
    if folder not in ("sheets", "yakin_cekim") and not (folder.startswith("aralik_") and "/" not in folder and "\\" not in folder and ".." not in folder):
        raise ToolError("folder: 'sheets', 'yakin_cekim' veya 'aralik_...' olabilir")
    sheets_dir = out / folder
    if not sheets_dir.is_dir():
        raise ToolError("sheets/ klasoru yok: %s" % sheets_dir)

    if str(sheet_name).strip():
        target = (sheets_dir / Path(sheet_name).name).resolve()
        if target.parent != sheets_dir.resolve() or not target.is_file():
            raise ToolError("Sayfa bulunamadi: %s" % target)
    else:
        found = sorted(sheets_dir.glob("*.jpg"))
        if not found:
            raise ToolError("Hic sayfa yok: %s" % sheets_dir)
        target = found[0]

    log("view_sheet: %s" % target.name)
    return Image(path=str(target))


@mcp.tool(
    name="read_prompt",
    description="Cikti klasorundeki prompt.txt metnini dondurur (baska bir modele "
                "yapistirilacak hazir analiz istemi).",
)
def read_prompt(out_dir: str) -> str:
    out = resolve(out_dir)
    f = out / "prompt.txt"
    if not f.is_file():
        raise ToolError("prompt.txt yok: %s" % f)
    return f.read_text(encoding="utf-8")


@mcp.tool(
    name="read_manifest",
    description="manifest.csv icerigini dondurur: her karenin hangi sayfada, hangi "
                "satir/sutunda ve hangi zaman damgasinda oldugu. limit ile satir sayisi sinirlanir.",
)
def read_manifest(out_dir: str, limit: int = 200) -> str:
    out = resolve(out_dir)
    f = out / "manifest.csv"
    if not f.is_file():
        raise ToolError("manifest.csv yok: %s" % f)
    lines = f.read_text(encoding="utf-8-sig").splitlines()
    if limit and limit > 0:
        lines = lines[: int(limit) + 1]
    return "\n".join(lines)


def main():
    log("Video Scrap MCP baslatiliyor | kok klasor: %s" % BASE_DIR)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
