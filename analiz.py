# -*- coding: utf-8 -*-
"""
Iki asamali video analizi
=========================
Asama 1: Video parcalara bolunup paralel taranir. Saniyede ~1 kare genel sayfalara
         (sheets/) konur; ayni gecista saniyede ~10 ornek icin kareler arasi fark hesaplanir.
Asama 2: Farkin ani veya surekli yukseldigi anlarin cevresinde sik kare alinir ve
         ayri sayfalara (yakin_cekim/) konur.
Cikti:   olaylar.json, olaylar.md, durum.json

Kullanim:
    python analiz.py --video <mp4> --out <klasor>
"""

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import video_scrap as vs

import ayarlar
BASE_DIR = ayarlar.cikti_koku()

HIST_CUT = 0.45       # renk histogramı sert kesme eşiği (kalibrasyon: gerçek kesmeler 0,5-0,9; komşu örnekler <0,2)
HIST_NEIGHBOR = 0.25  # komşu örnek bundan yüksekse kesme değil, süren geçiş sayılır

_LIBS = Path(__file__).resolve().parent / "libs"
if _LIBS.is_dir() and str(_LIBS) not in sys.path:
    sys.path.insert(0, str(_LIBS))


def ensure_inside(path):
    p = Path(str(path)).expanduser()
    if not p.is_absolute():
        p = BASE_DIR / p
    p = p.resolve()
    try:
        p.relative_to(BASE_DIR)
    except ValueError:
        raise RuntimeError("Cikti klasoru '%s' proje klasoru disinda: %s. "
                           "Sadece su klasorun icine yazilir: %s" % (p, p, BASE_DIR))
    return p


def _cam(prev, cur):
    pts = cv2.goodFeaturesToTrack(prev, 150, 0.01, 6)
    if pts is None or len(pts) < 12:
        return None
    nxt, st, _ = cv2.calcOpticalFlowPyrLK(prev, cur, pts, None)
    if nxt is None:
        return None
    ok = st.ravel() == 1
    if ok.sum() < 12:
        return None
    p0, p1 = pts[ok], nxt[ok]
    m, inl = cv2.estimateAffinePartial2D(p0, p1, method=cv2.RANSAC, ransacReprojThreshold=2.0)
    if m is None:
        return None
    h, w = prev.shape
    cx, cy = w / 2.0, h / 2.0
    scale = float(np.hypot(m[0, 0], m[1, 0]))
    if scale <= 0:
        return None
    dx = (m[0, 0] * cx + m[0, 1] * cy + m[0, 2] - cx) / w
    dy = (m[1, 0] * cx + m[1, 1] * cy + m[1, 2] - cy) / w
    rot = float(np.arctan2(m[1, 0], m[0, 0]))
    ratio = float(inl.sum()) / float(len(inl))
    return float(np.log(scale)), float(dx), float(dy), rot, ratio


def _worker(args):
    video, start, end, stride, ov_step, thumb_w, thumb_h = args
    cap = cv2.VideoCapture(video)
    first = max(0, start - stride)
    first -= first % stride
    if first:
        cap.set(cv2.CAP_PROP_POS_FRAMES, first)
    idx = first
    prev = None
    prev_hist = None
    diffs = []
    ov = []
    cams = []
    prev_g = None
    try:
        while idx < end:
            if not cap.grab():
                break
            if idx % stride == 0:
                ok, frame = cap.retrieve()
                if not ok:
                    break
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                small = cv2.resize(gray, (64, 36), interpolation=cv2.INTER_AREA)
                g = cv2.resize(gray, (160, 90), interpolation=cv2.INTER_AREA)
                hsv = cv2.cvtColor(cv2.resize(frame, (64, 36), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2HSV)
                hist = cv2.calcHist([hsv], [0, 1], None, [16, 8], [0, 180, 0, 256])
                cv2.normalize(hist, hist, 1, 0, cv2.NORM_L1)
                if prev is not None and idx >= start:
                    dv = float(np.mean(cv2.absdiff(small, prev))) / 255.0
                    hd = float(cv2.compareHist(prev_hist, hist, cv2.HISTCMP_BHATTACHARYYA))
                    diffs.append((idx, dv, hd))
                    if dv < 0.12 and prev_g is not None:
                        c = _cam(prev_g, g)
                        if c is not None:
                            cams.append((idx,) + c)
                prev = small
                prev_hist = hist
                prev_g = g
                if idx >= start and idx % ov_step == 0:
                    ov.append((idx, cv2.resize(frame, (thumb_w, thumb_h), interpolation=cv2.INTER_AREA)))
            idx += 1
    finally:
        cap.release()
    return start, diffs, ov, cams


def _runs(mask):
    runs = []
    i = 0
    n = len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j + 1 < n and mask[j + 1]:
                j += 1
            runs.append((i, j))
            i = j + 1
        else:
            i += 1
    return runs


def detect_events(samples, fps, cut, soft):
    if len(samples) < 3:
        return []
    ts = np.array([s[0] / fps for s in samples])
    d = np.array([s[1] for s in samples])
    events = []
    for i, j in _runs(d >= cut):
        k = i + int(np.argmax(d[i:j + 1]))
        events.append({"type": "keskin", "start": float(ts[i]), "end": float(ts[j]),
                       "peak": float(ts[k]), "strength": float(d[k])})
    # Renk histogramı: gri farkı eşiğin altında kalan (örn. açık oda -> açık oda) ama rengi bir anda
    # değişen tek örneklik sert kesmeleri ekler. Yalnız ekleme yapar, mevcut olayları silmez.
    if len(samples[0]) >= 3:
        hd = np.array([s[2] for s in samples])
        for i in range(len(d)):
            if hd[i] < HIST_CUT or d[i] >= cut:
                continue
            nb = [hd[k] for k in (i - 1, i + 1) if 0 <= k < len(d)]
            if nb and max(nb) >= HIST_NEIGHBOR:
                continue
            if any(ev["start"] - 0.3 <= ts[i] <= ev["end"] + 0.3 for ev in events if ev["type"] == "keskin"):
                continue
            events.append({"type": "keskin", "start": float(ts[i]), "end": float(ts[i]),
                           "peak": float(ts[i]), "strength": float(max(d[i], 0.5 * hd[i])),
                           "kaynak": "renk"})
    win = 5
    sm = np.convolve(d, np.ones(win) / win, mode="same")
    for i, j in _runs(sm >= soft):
        if j - i + 1 < win:
            continue
        s, e = float(ts[i]), float(ts[j])
        if any(ev["start"] - 0.5 <= e and s <= ev["end"] + 0.5 for ev in events if ev["type"] == "keskin"):
            continue
        k = i + int(np.argmax(sm[i:j + 1]))
        events.append({"type": "yumusak", "start": s, "end": e,
                       "peak": float(ts[k]), "strength": float(sm[k])})
    events.sort(key=lambda ev: ev["start"])
    return events


def _dir_text(dx, dy):
    parts = []
    if abs(dx) >= 0.03:
        parts.append("sola" if dx < 0 else "saga")
    if abs(dy) >= 0.03 * 9 / 16:
        parts.append("yukari" if dy < 0 else "asagi")
    return "+".join(parts) if parts else "yok"


def detect_camera(cams, fps, zoom_thr=0.008, pan_thr=0.010, gap=2, min_len=4, cuts=()):
    if not cams:
        return []
    mag = np.array([max(abs(c[1]) / zoom_thr, np.hypot(c[2], c[3]) / pan_thr) for c in cams])
    active = mag >= 1.0
    for n, c in enumerate(cams):
        if abs(c[1]) > 0.25 or abs(c[4]) > 0.35:
            active[n] = False
    idxs = [c[0] for c in cams]
    cut_after = set()
    for n in range(len(cams)):
        lo = idxs[n - 1] / fps if n else idxs[n] / fps - 0.2
        hi = idxs[n] / fps
        if any(lo < t <= hi for t in cuts):
            active[n] = False
            cut_after.add(n)
    stride = max(1, min([b - a for a, b in zip(idxs, idxs[1:]) if b > a] or [1]))
    runs = _runs(active)
    merged = []
    for r in runs:
        if merged and r[0] - merged[-1][1] <= gap + 1 and not any(
                (cams[n + 1][0] - cams[n][0]) > stride for n in range(merged[-1][1], r[0]))\
                and not any(n in cut_after for n in range(merged[-1][1] + 1, r[0] + 1))\
                and not any(abs(cams[n][1]) > 0.25 or abs(cams[n][4]) > 0.35 for n in range(merged[-1][1], r[0] + 1)):
            merged[-1] = (merged[-1][0], r[1])
        else:
            merged.append(r)
    chunks = []
    for i, j in merged:
        a = i
        for n in range(i, j + 1):
            if idxs[n] - idxs[a] >= 2.0 * fps or n == j:
                chunks.append((a, n))
                a = n + 1
    events = []
    for i, j in chunks:
        if j - i + 1 < min_len:
            continue
        seg = cams[i:j + 1]
        ls = sum(c[1] for c in seg)
        dx = sum(c[2] for c in seg)
        dy = sum(c[3] for c in seg)
        rot = sum(c[4] for c in seg)
        inl = float(np.mean([c[5] for c in seg]))
        factor = float(np.exp(ls))
        kinds = []
        if abs(ls) >= 0.08:
            kinds.append("zoom-in" if ls > 0 else "zoom-out")
        if np.hypot(dx, dy) >= 0.03:
            kinds.append("kaydirma")
        if abs(rot) >= 0.05:
            kinds.append("donme")
        if not kinds or inl < 0.7 or not (0.33 <= factor <= 3.0) or abs(rot) > 0.5:
            continue
        s, e = idxs[i] / fps, idxs[j] / fps
        events.append({
            "type": "kamera", "alt_tur": "+".join(kinds), "start": s, "end": e,
            "peak": (s + e) / 2.0,
            "strength": 0.12,
            "olcek_carpani": round(factor, 3), "kayma_x": round(float(dx), 3),
            "kayma_y": round(float(dy), 3), "yon": _dir_text(dx, dy),
            "donme_derece": round(float(np.degrees(rot)), 1), "guvenilirlik": round(inl, 2),
        })
    return events


def find_cuts(video, events, threshold=40.0, progress=None):
    try:
        from scenedetect import detect, ContentDetector
    except Exception:
        sys.stderr.write("UYARI: scenedetect kurulu degil; sert kesme dogrulamasi atlandi "
                         "(kurulum icin OKU_BENI/01_KURULUM.md dosyasina bak).\n")
        return []
    cuts = []
    for n, ev in enumerate(events):
        if progress and n % 10 == 0:
            try:
                progress(n, len(events))
            except Exception:
                pass
        try:
            scenes = detect(video, ContentDetector(threshold=threshold, min_scene_len=3),
                            start_time=ev["start"], end_time=ev["end"], show_progress=False)
        except Exception:
            continue
        cuts.extend(sc[0].seconds for sc in scenes[1:])
    return sorted(set(round(t, 3) for t in cuts))


def refine_camera(video, events, width=640, min_inliers=25):
    if not events:
        return events
    cap = cv2.VideoCapture(video)
    orb = cv2.ORB_create(1500)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    def grab(t):
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000.0)
        ok, f = cap.read()
        if not ok:
            return None
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        return cv2.resize(g, (width, int(width * g.shape[0] / g.shape[1])))

    out = []
    try:
        for ev in events:
            ev["olcek_kaynak"] = "toplam(yaklasik)"
            a, b = grab(ev["start"]), grab(ev["end"])
            if a is not None and b is not None:
                k1, d1 = orb.detectAndCompute(a, None)
                k2, d2 = orb.detectAndCompute(b, None)
                if d1 is not None and d2 is not None:
                    m = bf.match(d1, d2)
                    if len(m) >= min_inliers:
                        p0 = np.float32([k1[x.queryIdx].pt for x in m])
                        p1 = np.float32([k2[x.trainIdx].pt for x in m])
                        M, inl = cv2.estimateAffinePartial2D(p0, p1, method=cv2.RANSAC, ransacReprojThreshold=3)
                        if M is not None and int(inl.sum()) >= min_inliers:
                            sc = float(np.hypot(M[0, 0], M[1, 0]))
                            rot = float(np.arctan2(M[1, 0], M[0, 0]))
                            ev["olcek_carpani"] = round(sc, 3)
                            ev["donme_derece"] = round(float(np.degrees(rot)), 1)
                            ev["olcek_kaynak"] = "dogrudan"
                            kinds = [k for k in ev["alt_tur"].split("+") if not k.startswith("zoom")]
                            if abs(np.log(sc)) >= 0.08:
                                kinds = ["zoom-in" if sc > 1 else "zoom-out"] + kinds
                            if not kinds:
                                continue
                            ev["alt_tur"] = "+".join(kinds)
            out.append(ev)
    finally:
        cap.release()
    return out


def build_windows(events, duration, pad, closeup_step, fps, max_frames):
    wins = [[max(0.0, ev["start"] - pad), min(duration, ev["end"] + pad), ev["strength"]] for ev in events]

    def merge(ws):
        ws = sorted(ws, key=lambda w: w[0])
        out = []
        for w in ws:
            if out and w[0] <= out[-1][1]:
                out[-1][1] = max(out[-1][1], w[1])
                out[-1][2] = max(out[-1][2], w[2])
            else:
                out.append(list(w))
        return out

    def count(ws):
        return sum(int((w[1] - w[0]) * fps / closeup_step) + 1 for w in ws)

    wins = merge(wins)
    dropped = 0
    while wins and count(wins) > max_frames:
        weakest = min(range(len(wins)), key=lambda i: wins[i][2])
        wins.pop(weakest)
        dropped += 1
    return wins, dropped


def locate(sheets, ts, tol):
    best = None
    best_d = None
    for sh in sheets:
        for (row, col, fi, cts) in sh["cells"]:
            dist = abs(cts - ts)
            if best_d is None or dist < best_d:
                best_d = dist
                best = (sh["name"], row + 1, col + 1)
    if best is None or best_d > tol:
        return None
    return best


def write_status(out_dir, **kw):
    path = Path(out_dir) / "durum.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    except Exception:
        data = {}
    data.update(kw)
    data["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    ayarlar.atomik_yaz(path, json.dumps(data, ensure_ascii=False, indent=1))


def analyze(video, out_dir, cut=0.25, soft=0.05, pad=0.7, closeup_step=3,
            max_closeup=400, part_sec=180, workers=4, cols=8, rows=5, thumb_w=256,
            quality=85, log=print):
    out_dir = ensure_inside(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    info = vs.probe_video(str(video))
    fps = info["fps"]
    total = info["frame_count"]
    stride = max(1, int(round(fps / 10.0)))
    ov_step = stride * max(1, int(round(fps / stride)))
    seg_len = max(ov_step, int(round(part_sec * fps / ov_step)) * ov_step)
    segs = [(s, min(total, s + seg_len)) for s in range(0, total, seg_len)]
    workers = max(1, min(int(workers), len(segs), os.cpu_count() or 1))

    write_status(out_dir, state="running", stage="asama1", pid=os.getpid(), video=info["name"],
                 duration=info["duration"], parts=len(segs), workers=workers)
    log("Video: %s | %dx%d | %.2f fps | %s" % (info["name"], info["width"], info["height"],
                                              fps, vs.fmt_dur(info["duration"])))
    log("Asama 1: %d parca, %d isci" % (len(segs), workers))

    builder = vs.SheetBuilder(out_dir / "sheets", cols, rows, thumb_w, quality,
                              info["width"], info["height"], prefix="sheet")
    jobs = [(str(video), s, e, stride, ov_step, builder.thumb_w, builder.thumb_h) for s, e in segs]
    results = {}
    done = 0
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(_worker, j) for j in jobs]
        for f in as_completed(futs):
            start, diffs, ov, cams = f.result()
            results[start] = (diffs, ov, cams)
            done += 1
            write_status(out_dir, progress="%d/%d parca" % (done, len(segs)))
            log("parca %d/%d tamam" % (done, len(segs)))

    samples, overview, cam_samples = [], [], []
    for s in sorted(results):
        samples.extend(results[s][0])
        overview.extend(results[s][1])
        cam_samples.extend(results[s][2])
    for idx, thumb in overview:
        builder.add(thumb, idx / fps, idx)
    builder.flush()
    t1 = time.time()
    log("Asama 1 bitti: %d genel kare, %d sayfa, %.1f sn" % (len(overview), len(builder.sheets), t1 - t0))

    write_status(out_dir, stage="olay-tespiti", pid=os.getpid())
    events = detect_events(samples, fps, cut, soft)
    cam_events = detect_camera(cam_samples, fps)
    write_status(out_dir, stage="kesme-dogrulama", progress="%d kamera olayi" % len(cam_events))
    cuts = find_cuts(video, cam_events, progress=lambda i, n: write_status(out_dir, progress="kesme dogrulama %d/%d" % (i, n)))
    if cuts:
        cam_events = detect_camera(cam_samples, fps, cuts=cuts)
    write_status(out_dir, stage="kamera-olcum", progress="%d olay" % len(cam_events))
    cam_events = refine_camera(video, cam_events)
    log("PySceneDetect: %d sert kesme bulundu, kamera olaylari bu noktalarda bolundu" % len(cuts))
    events = sorted(events + cam_events, key=lambda ev: ev["start"])
    log("Kamera hareketi: %d olay" % len(cam_events))
    wins, dropped = build_windows(events, info["duration"], pad, closeup_step, fps, max_closeup)
    log("Olay: %d | yakin cekim penceresi: %d (elenen: %d)" % (len(events), len(wins), dropped))

    write_status(out_dir, stage="asama2", events=len(events), windows=len(wins))
    cbuilder = vs.SheetBuilder(out_dir / "yakin_cekim", cols, rows, thumb_w, quality,
                               info["width"], info["height"], prefix="yakin")
    cap = cv2.VideoCapture(str(video))
    try:
        for w in wins:
            s = int(w[0] * fps)
            s += (-s) % closeup_step
            e = min(total - 1, int(w[1] * fps))
            cap.set(cv2.CAP_PROP_POS_FRAMES, s)
            idx = s
            while idx <= e:
                if not cap.grab():
                    break
                if idx % closeup_step == 0:
                    ok, frame = cap.retrieve()
                    if not ok:
                        break
                    cbuilder.add(frame, idx / fps, idx)
                idx += 1
    finally:
        cap.release()
    cbuilder.flush()

    for ev in events:
        ov_ref = locate(builder.sheets, ev["peak"], 1.0)
        cl_ref = locate(cbuilder.sheets, ev["peak"], 0.2)
        ev["genel_sayfa"] = {"sayfa": ov_ref[0], "satir": ov_ref[1], "sutun": ov_ref[2]} if ov_ref else None
        ev["yakin_sayfa"] = {"sayfa": cl_ref[0], "satir": cl_ref[1], "sutun": cl_ref[2]} if cl_ref else None
        ev["zaman"] = vs.fmt_ts(ev["peak"])

    elapsed = time.time() - t0
    summary = {
        "video": info, "kesme_esigi": cut, "yumusak_esigi": soft, "pencere_payi_sn": pad,
        "yakin_cekim_adim": closeup_step, "genel_kare": len(overview),
        "genel_sayfa": len(builder.sheets), "yakin_kare": sum(s["count"] for s in cbuilder.sheets),
        "yakin_sayfa": len(cbuilder.sheets), "olay_sayisi": len(events),
        "elenen_pencere": dropped, "sure_sn": round(elapsed, 1), "olaylar": events,
        "pencereler": [{"baslangic": vs.fmt_ts(w[0]), "bitis": vs.fmt_ts(w[1])} for w in wins],
    }
    (out_dir / "olaylar.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")

    lines = ["# Gecis ve olay listesi", "",
             "Video: %s (%s)" % (info["name"], vs.fmt_dur(info["duration"])),
             "Genel tarama: %d kare / %d sayfa (sheets/). Yakin cekim: %d kare / %d sayfa (yakin_cekim/)." % (
                 summary["genel_kare"], summary["genel_sayfa"], summary["yakin_kare"], summary["yakin_sayfa"]),
             "Esikler: keskin >= %.2f, yumusak >= %.2f. Olay: %d. Sure: %.1f sn." % (
                 cut, soft, len(events), elapsed), "",
             "| Zaman | Tur | Guc | Detay | Genel sayfa (satir,sutun) | Yakin cekim sayfa (satir,sutun) |",
             "|---|---|---|---|---|---|"]
    for ev in events:
        g = ev["genel_sayfa"]
        c = ev["yakin_sayfa"]
        if ev.get("kaynak") == "renk":
            detay = "renk degisimi ile bulundu (gri fark esik altinda)"
        elif ev["type"] == "kamera":
            detay ="%s: olcek x%.2f, yon %s (x %.2f, y %.2f), donme %.1f derece, guven %.2f" % (
                ev["alt_tur"], ev["olcek_carpani"], ev["yon"], ev["kayma_x"], ev["kayma_y"],
                ev["donme_derece"], ev["guvenilirlik"])
        else:
            detay = "-"
        lines.append("| %s (%s-%s) | %s | %.3f | %s | %s | %s |" % (
            ev["zaman"], vs.fmt_ts(ev["start"]), vs.fmt_ts(ev["end"]), ev["type"], ev["strength"], detay,
            "%s (%d,%d)" % (g["sayfa"], g["satir"], g["sutun"]) if g else "-",
            "%s (%d,%d)" % (c["sayfa"], c["satir"], c["sutun"]) if c else "yok (limit)"))
    (out_dir / "olaylar.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_status(out_dir, state="done", stage="bitti", sure_sn=round(elapsed, 1),
                 olay_sayisi=len(events), genel_sayfa=len(builder.sheets),
                 yakin_sayfa=len(cbuilder.sheets))
    log("Bitti: %.1f sn" % elapsed)
    return summary


def zoom_range(video, out_dir, start, end, step=1, max_frames=200, cols=8, rows=5,
               thumb_w=320, quality=88, log=print):
    out_dir = ensure_inside(out_dir)
    info = vs.probe_video(str(video))
    fps = info["fps"]
    total = info["frame_count"]
    step = max(1, int(step))
    s = max(0, int(float(start) * fps))
    e_req = int(float(end) * fps)
    e = min(total - 1, e_req)
    if s > total - 1:
        raise RuntimeError("Baslangic video suresinden sonra: %s sn (video %.1f sn)" % (start, info["duration"]))
    if e < s:
        raise RuntimeError("Bitis baslangictan once: %s - %s" % (start, end))
    n = (e - s) // step + 1
    if n > max_frames:
        raise RuntimeError("Aralik %d kare uretir (limit %d). step degerini artir veya aralik daralt." % (n, max_frames))
    name = "aralik_%s_%s_adim%d" % (("%.2f" % float(start)).replace(".", "p"), ("%.2f" % float(end)).replace(".", "p"), step)
    target = out_dir / name
    b = vs.SheetBuilder(target, cols, rows, thumb_w, quality, info["width"], info["height"], prefix="kare")
    cap = cv2.VideoCapture(str(video))
    try:
        cap.set(cv2.CAP_PROP_POS_FRAMES, s)
        idx = s
        while idx <= e:
            if not cap.grab():
                break
            if (idx - s) % step == 0:
                ok, frame = cap.retrieve()
                if not ok:
                    break
                b.add(frame, idx / fps, idx)
            idx += 1
    finally:
        cap.release()
    b.flush()
    res = {"folder": name, "path": str(target), "frames": sum(x["count"] for x in b.sheets),
           "sheets": [x["name"] for x in b.sheets], "step_birimi": "kare (saniye degil): step=3 -> her 3. kare"}
    if e_req > total - 1:
        res["uyari"] = "Bitis video suresini asiyordu; %.1f sn'ye kirpildi" % ((total - 1) / fps)
    return res


def main():
    ap = argparse.ArgumentParser(description="Iki asamali video analizi")
    ap.add_argument("--video", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cut", type=float, default=0.25)
    ap.add_argument("--soft", type=float, default=0.05)
    ap.add_argument("--pad", type=float, default=0.7)
    ap.add_argument("--closeup-step", type=int, default=3)
    ap.add_argument("--max-closeup", type=int, default=400)
    ap.add_argument("--part-sec", type=int, default=180)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    try:
        analyze(a.video, a.out, cut=a.cut, soft=a.soft, pad=a.pad, closeup_step=a.closeup_step,
                max_closeup=a.max_closeup, part_sec=a.part_sec, workers=a.workers)
    except Exception as exc:
        try:
            write_status(ensure_inside(a.out), state="error", error=str(exc))
        except Exception:
            pass
        sys.stderr.write("HATA: %s\n" % exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
