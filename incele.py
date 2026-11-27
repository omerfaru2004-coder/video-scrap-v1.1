# -*- coding: utf-8 -*-
"""
Tek adimda video inceleme
=========================
Bir link (veya yerel dosya) verilir; videolar/ klasoru ilk kullanimda otomatik
acilir, video kendi klasorune indirilir ve analiz o klasorun icine yazilir:

    videolar/
        kayit.json            <- video kimligi -> klasor eslesmesi (ayni link tekrar inmez)
        shorts1/  video.mp4, info.json, analiz/ (sheets, yakin_cekim, olaylar.md ...)
        shorts2/
        video1/
        video2/

Kisa (<= 180 sn veya /shorts/ linki) videolar shortsN, digerleri videoN olur.

Kullanim:
    python incele.py "https://www.youtube.com/watch?v=..."
    python incele.py "C:\\yol\\video.mp4"
"""

import argparse
import contextlib
import errno
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ayarlar

BASE_DIR = ayarlar.cikti_koku()
VIDEOLAR = BASE_DIR / "videolar"
SHORT_MAX_SEC = 180
VIDEO_EXT = {".mp4", ".mkv", ".webm", ".mov", ".avi", ".m4v"}


class IncelemeHatasi(RuntimeError):
    pass


_KILIT_IZLEK = threading.RLock()
_KILIT_DERINLIK = 0


def _load_registry():
    f = VIDEOLAR / "kayit.json"
    if f.is_file():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_registry(reg):
    ayarlar.atomik_yaz(VIDEOLAR / "kayit.json", json.dumps(reg, ensure_ascii=False, indent=1))


@contextlib.contextmanager
def _kilit():
    """kayit.json oku-degistir-yaz adimini ve klasor secimini kilitler.

    Iki katman: ayni surecteki izlekler icin threading.RLock, farkli surecler icin
    .kayit.lock uzerinde isletim sistemi kilidi. Windows'ta msvcrt kilidi surec
    genelindedir; ayni surecten ikinci kez alinirsa EDEADLK verir, bu yuzden ic ice
    cagrilarda dosya kilidi atlanir.
    """
    global _KILIT_DERINLIK
    VIDEOLAR.mkdir(parents=True, exist_ok=True)
    with _KILIT_IZLEK:
        ic_ice = _KILIT_DERINLIK > 0
        _KILIT_DERINLIK += 1
        f = None
        try:
            if not ic_ice:
                f = open(VIDEOLAR / ".kayit.lock", "a+")
                _dosya_kilidi(f, al=True)
            yield
        finally:
            _KILIT_DERINLIK -= 1
            if f is not None:
                try:
                    _dosya_kilidi(f, al=False)
                finally:
                    f.close()


def _dosya_kilidi(f, al=True):
    if os.name == "nt":
        import msvcrt
        f.seek(0)
        while True:
            try:
                msvcrt.locking(f.fileno(), msvcrt.LK_LOCK if al else msvcrt.LK_UNLCK, 1)
                return
            except OSError as exc:
                if al and exc.errno == errno.EDEADLK:
                    time.sleep(0.02)
                    continue
                if al:
                    raise
                return
    else:
        import fcntl
        fcntl.flock(f.fileno(), fcntl.LOCK_EX if al else fcntl.LOCK_UN)


def _next_folder(kind):
    nums = []
    for d in VIDEOLAR.iterdir():
        m = re.fullmatch(r"%s(\d+)" % kind, d.name)
        if d.is_dir() and m:
            nums.append(int(m.group(1)))
    return "%s%d" % (kind, (max(nums) + 1) if nums else 1)


def _find_video(folder):
    for f in sorted(folder.iterdir()):
        if f.is_file() and f.stem == "video" and f.suffix.lower() in VIDEO_EXT:
            return f
    return None


def ffmpeg_konum():
    """ffmpeg yolunu bulur: once .venv icindeki imageio-ffmpeg, sonra sistem PATH'i.

    Boylece kullanici ayrica ffmpeg kurmak/kopyalamak zorunda kalmaz.
    """
    try:
        import imageio_ffmpeg
        yol = imageio_ffmpeg.get_ffmpeg_exe()
        if yol and Path(yol).is_file():
            return yol
    except Exception:
        pass
    return shutil.which("ffmpeg")


def _yt(args, timeout=1800):
    # YouTube cikarimi icin JavaScript calistirici gerekir; node varsa kullan (uyari ve eksik format biter).
    extra = ["--js-runtimes", "node"] if shutil.which("node") else []
    ff = ffmpeg_konum()
    if ff:
        extra += ["--ffmpeg-location", ff]
    try:
        return subprocess.run([sys.executable, "-m", "yt_dlp"] + extra + args, capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=timeout,
                              creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0))
    except subprocess.TimeoutExpired:
        raise IncelemeHatasi("yt-dlp %d sn icinde bitmedi; islem durduruldu." % timeout)


def yt_hata(stderr):
    """stderr'den asil hatayi ayiklar (WARNING satirlari asil hatayi gizlemesin)."""
    lines = [l.strip() for l in (stderr or "").splitlines() if l.strip()]
    errs = [l for l in lines if l.startswith("ERROR")]
    return (errs[-1] if errs else (lines[-1] if lines else "bilinmeyen hata"))[-400:]


def url_dogrula(url):
    """yt-dlp'ye yalnizca gercek http(s) linki gecer.

    Aksi halde tek parcalik bir metin (--exec=..., --plugin-dirs=...) yt-dlp tarafindan
    secenek olarak yorumlanir; linki modelin urettigi metin besleyebildigi icin bu kontrol sart.
    """
    u = str(url).strip()
    if not re.match(r"^https?://[^\s]+$", u, re.I):
        raise IncelemeHatasi("Gecersiz link (http:// veya https:// ile baslamali): %s" % u[:120])
    return u


def _meta(url):
    r = _yt(["--no-playlist", "--skip-download", "--print",
             "%(extractor_key)s:%(id)s\t%(duration)s\t%(title)s", "--", url])
    lines = [l for l in r.stdout.splitlines() if l.count("\t") >= 2]
    if r.returncode != 0 or not lines:
        raise IncelemeHatasi("Link okunamadi: %s" % yt_hata(r.stderr))
    vid, dur, title = lines[-1].split("\t", 2)
    try:
        dur = float(dur)
    except ValueError:
        dur = 0.0
    return vid, dur, title


def prepare(source, max_height=720, log=print):
    _lisans_kontrol()
    VIDEOLAR.mkdir(parents=True, exist_ok=True)
    local = Path(str(source)).expanduser()
    is_local = local.is_file()

    if is_local:
        sys.path.insert(0, str(HERE))
        import video_scrap
        info = video_scrap.probe_video(str(local))
        key = "dosya:%s:%d" % (local.name, local.stat().st_size)
        dur, title, url = info["duration"], local.stem, str(local)
    else:
        url = url_dogrula(source)
        key, dur, title = _meta(url)

    kind = "shorts" if ("/shorts/" in url or 0 < dur <= SHORT_MAX_SEC) else "video"

    # Kilit yalnizca kayit defteri ve klasor secimi icin tutulur; indirme kilidin disinda yapilir.
    with _kilit():
        reg = _load_registry()
        rec = reg.get(key)
        if rec:
            folder = VIDEOLAR / rec["klasor"]
            vp = _find_video(folder) if folder.is_dir() else None
            if vp:
                return _result(folder, vp, rec["tur"], True)
            if rec.get("durum") == "indiriliyor" and folder.is_dir():
                raise IncelemeHatasi("Bu link icin indirme zaten suruyor (%s). Bitmesini bekle." % folder.name)
        folder = VIDEOLAR / _next_folder(kind)
        folder.mkdir(parents=True)
        reg[key] = {"klasor": folder.name, "tur": kind, "kaynak": url, "baslik": title,
                    "durum": "indiriliyor"}
        _save_registry(reg)

    try:
        if is_local:
            vp = folder / ("video" + local.suffix.lower())
            shutil.copy2(str(local), str(vp))
        else:
            log("indiriliyor: %s" % url)
            r = _yt(["--no-playlist", "--restrict-filenames",
                     "-f", "bv*[height<=%d]+ba/b[height<=%d]/b" % (max_height, max_height),
                     "--merge-output-format", "mp4", "--print", "after_move:filepath", "--no-simulate",
                     "-o", str(folder / "video.%(ext)s"), "--", url])
            vp = _find_video(folder)
            if r.returncode != 0 or vp is None:
                raise IncelemeHatasi("Indirme basarisiz: %s" % yt_hata(r.stderr))
    except BaseException:
        # Ctrl+C dahil her durumda yarim klasoru ve kaydi temizle; ama baska bir cagrinin
        # kaydini silme (kayit hala kendi klasorumuzu gosteriyorsa sil).
        shutil.rmtree(folder, ignore_errors=True)
        with _kilit():
            reg = _load_registry()
            if reg.get(key, {}).get("klasor") == folder.name:
                reg.pop(key, None)
                _save_registry(reg)
        raise

    ayarlar.atomik_yaz(folder / "info.json", json.dumps({
        "kaynak": url, "kimlik": key, "baslik": title, "sure_sn": dur, "tur": kind,
        "indirilme": time.strftime("%Y-%m-%d %H:%M:%S"),
    }, ensure_ascii=False, indent=1))
    with _kilit():
        reg = _load_registry()
        reg[key] = {"klasor": folder.name, "tur": kind, "kaynak": url, "baslik": title}
        _save_registry(reg)
    return _result(folder, vp, kind, False)


def _result(folder, vp, kind, reused):
    analiz = folder / "analiz"
    state = None
    f = analiz / "durum.json"
    if f.is_file():
        try:
            state = json.loads(f.read_text(encoding="utf-8")).get("state")
        except Exception:
            state = None
    return {"klasor": str(folder), "ad": folder.name, "tur": kind, "video_path": str(vp),
            "analiz_klasoru": str(analiz), "yeniden_kullanildi": reused, "analiz_durumu": state}


def pid_canli(pid):
    """True/False: pid yasiyor mu. None: pid bilinmiyor."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return None
    if os.name == "nt":
        import ctypes
        k = ctypes.windll.kernel32
        h = k.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong()
        ok = k.GetExitCodeProcess(h, ctypes.byref(code))
        k.CloseHandle(h)
        return bool(ok) and code.value == 259  # STILL_ACTIVE
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True  # baska kullanicinin sureci: yasiyor
    except OSError:
        return False


def durum_oku(out):
    f = Path(out) / "durum.json"
    if not f.is_file():
        return {}
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return {}


def calisiyor(out):
    """durum.json 'running' diyor ve islem gercekten yasiyor mu.

    pid yazilmadan once olen is (import hatasi, Popen hatasi) sonsuza kadar 'running'
    gorunmesin: pid yoksa 120 sn'den eski durum bayat sayilir.
    """
    d = durum_oku(out)
    if d.get("state") != "running":
        return False
    pid = d.get("pid")
    if pid is None:
        try:
            yas = time.time() - time.mktime(time.strptime(d.get("updated", ""), "%Y-%m-%d %H:%M:%S"))
        except Exception:
            return False
        return yas < 120
    return pid_canli(pid) is not False


def _lisans_kontrol():
    """Deneme surumu klasorde lisans.py varsa suresi dolmus mu diye bakar.

    Tam surumde lisans.py yoktur; import basarisiz olur ve kontrol atlanir.
    """
    try:
        import lisans
    except ImportError:
        return
    lisans.kontrol()


def start_analysis(video_path, out_dir, cut=0.25, soft=0.05, max_closeup=400, wait=False, zorla=False):
    _lisans_kontrol()
    out = Path(out_dir)
    if not zorla and calisiyor(out):
        raise IncelemeHatasi("Analiz zaten calisiyor: %s (zorla=True ile yine de baslatilir)" % out)
    out.mkdir(parents=True, exist_ok=True)
    logf = open(out / "analiz_log.txt", "w", encoding="utf-8")
    env = dict(os.environ)
    env["VIDEO_SCRAP_HOME"] = str(BASE_DIR)
    ayarlar.atomik_yaz(out / "durum.json", json.dumps(
        {"state": "running", "stage": "basliyor", "updated": time.strftime("%Y-%m-%d %H:%M:%S")}))
    cmd = [sys.executable, "-u", str(HERE / "analiz.py"), "--video", str(video_path), "--out", str(out),
           "--cut", str(cut), "--soft", str(soft), "--max-closeup", str(max_closeup)]
    flags = 0
    if os.name == "nt" and not wait:
        flags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    try:
        p = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT, env=env, creationflags=flags)
    except BaseException:
        ayarlar.atomik_yaz(out / "durum.json", json.dumps(
            {"state": "error", "stage": "baslatilamadi", "error": "analiz.py baslatilamadi",
             "updated": time.strftime("%Y-%m-%d %H:%M:%S")}))
        raise
    finally:
        logf.close()
    # pid'i yaz: cocuk surec kendi durumunu yazana kadar gecen boslukta is olurse
    # durum sonsuza kadar 'running' kalmasin.
    d = durum_oku(out)
    d.update({"state": "running", "pid": p.pid, "updated": time.strftime("%Y-%m-%d %H:%M:%S")})
    ayarlar.atomik_yaz(out / "durum.json", json.dumps(d, ensure_ascii=False, indent=1))
    if wait:
        p.wait()
    return p


def list_videos():
    reg = _load_registry()
    rows = []
    for key, rec in reg.items():
        folder = VIDEOLAR / rec["klasor"]
        if not folder.is_dir():
            continue
        state = None
        f = folder / "analiz" / "durum.json"
        if f.is_file():
            try:
                state = json.loads(f.read_text(encoding="utf-8")).get("state")
            except Exception:
                pass
        rows.append({"klasor": rec["klasor"], "tur": rec["tur"], "baslik": rec.get("baslik", ""),
                     "kaynak": rec.get("kaynak", ""), "analiz_durumu": state, "yol": str(folder)})
    rows.sort(key=lambda r: (r["tur"], int(re.sub(r"\D", "", r["klasor"]) or 0)))
    return rows


def main():
    ap = argparse.ArgumentParser(description="Link ver, videolar/ klasorune indir ve analiz et")
    ap.add_argument("source", help="YouTube linki veya yerel video dosyasi")
    ap.add_argument("--max-height", type=int, default=720)
    ap.add_argument("--yeniden", action="store_true", help="analiz daha once bittiyse bile tekrar calistir")
    a = ap.parse_args()
    try:
        res = prepare(a.source, a.max_height)
    except IncelemeHatasi as exc:
        sys.stderr.write("HATA: %s\n" % exc)
        return 1
    print("Klasor: %s (%s)%s" % (res["klasor"], res["tur"], " [onceden vardi]" if res["yeniden_kullanildi"] else ""))
    if res["analiz_durumu"] == "done" and not a.yeniden:
        print("Analiz zaten var: %s" % res["analiz_klasoru"])
        return 0
    start_analysis(res["video_path"], res["analiz_klasoru"], wait=True)
    print("Analiz bitti: %s" % res["analiz_klasoru"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
