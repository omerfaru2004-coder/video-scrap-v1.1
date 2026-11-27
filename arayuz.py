# -*- coding: utf-8 -*-
"""
Video Scrap v1.1 arayuzu (tkinter, tamamen yerel pencere).

Sekmeler:
    Video Incele        -> link ver / dosya sec, indir + analiz et
    Kare Cikar          -> klasik kontak sayfasi uretimi
    Ayarlar             -> kayit klasoru ve baslik gorseli
    Yapay Zekaya Bagla  -> Abacus / Claude / Gemini / ChatGPT icin hazir MCP ayari
"""

import json
import os
import queue
import subprocess
import sys
import threading
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageDraw, ImageTk

import ayarlar
import video_scrap as vs

HERE = Path(__file__).resolve().parent

NAVY = "#1D356D"
PURPLE = "#52366F"
PLUM = "#86396E"
PINK = "#C23E73"
WHITE = "#FFFFFF"
SOFT = "#F5F1F7"
LINE = "#D9CFE0"
TEXT = "#2B2540"
MUTED = "#6B6480"

BANNER_H = 104


def deneme_etiketi():
    """Deneme surumunde banner'a kalan gunu ekler; tam surumde bos doner."""
    try:
        import lisans
    except ImportError:
        return ""
    try:
        return "  |  DENEME: %s" % lisans.kisa_durum()
    except Exception:  # noqa: BLE001
        return ""


def banner_image(width, height, photo_path):
    width = max(200, int(width))
    img = None
    if photo_path and os.path.isfile(photo_path):
        try:
            src = Image.open(photo_path).convert("RGB")
            scale = max(width / src.width, height / src.height)
            src = src.resize((max(1, int(src.width * scale)), max(1, int(src.height * scale))), Image.LANCZOS)
            left = (src.width - width) // 2
            top = (src.height - height) // 2
            img = src.crop((left, top, left + width, top + height))
            tint = Image.new("RGB", (width, height), NAVY)
            img = Image.blend(img, tint, 0.55)
        except Exception:
            img = None
    if img is None:
        stops = [(0.0, (29, 53, 109)), (0.38, (82, 54, 111)), (0.7, (134, 57, 110)), (1.0, (194, 62, 115))]
        img = Image.new("RGB", (width, 1))
        px = img.load()
        for x in range(width):
            t = x / max(1, width - 1)
            for i in range(len(stops) - 1):
                a, b = stops[i], stops[i + 1]
                if a[0] <= t <= b[0]:
                    k = (t - a[0]) / (b[0] - a[0])
                    px[x, 0] = tuple(int(a[1][c] + (b[1][c] - a[1][c]) * k) for c in range(3))
                    break
        img = img.resize((width, height))
    return img


def mcp_parcalari():
    py = sys.executable.replace("\\", "/")
    server = str(HERE / "mcp_server.py").replace("\\", "/")
    return py, server


def baglanti_metni(hedef):
    py, server = mcp_parcalari()
    js = json.dumps({"mcpServers": {"video-scrap": {"command": py, "args": [server]}}}, indent=2)
    home = str(Path.home()).replace("\\", "/")
    if hedef == "Abacus Desktop":
        return ("Dosya: %s/.abacusai/mcp.json\n\nAsagidaki blogu 'mcpServers' icine elle ekle "
                "(ya da terminalde: python mcp_kaydet.py):\n\n%s" % (home, js))
    if hedef == "Claude Desktop":
        return ("Dosya (Windows): %%APPDATA%%\\Claude\\claude_desktop_config.json\n"
                "Claude Desktop > Settings > Developer > Edit Config ile de acilir.\n"
                "En kolayi: asagidaki 'Claude Desktop'a otomatik kaydet' dugmesi.\n"
                "Kaydedince Claude Desktop'i tamamen kapatip yeniden ac.\n\n%s" % js)
    if hedef == "Claude Code":
        return ("Terminalde tek komut:\n\nclaude mcp add video-scrap -- \"%s\" \"%s\"\n\n"
                "Kontrol: claude mcp list" % (py, server))
    if hedef == "Gemini CLI":
        return ("Dosya: %s/.gemini/settings.json (yoksa olustur)\n"
                "Kaydedince Gemini CLI'da /mcp yaz; video-scrap listelenmeli.\n\n%s" % (home, js))
    toml = '[mcp_servers.video-scrap]\ncommand = "%s"\nargs = ["%s"]\nstartup_timeout_sec = 30\n' % (py, server)
    return ("ChatGPT masaustu uygulamasi ve Codex ayni dosyayi kullanir: %s/.codex/config.toml\n"
            "(Web'deki chatgpt.com yerel MCP'yi dogrudan calistiramaz.)\n"
            "Dosyaya ekle, uygulamayi yeniden baslat:\n\n%s\n"
            "Ya da terminalde: codex mcp add video-scrap -- \"%s\" \"%s\"" % (home, toml, py, server))


def run_gui():
    root = tk.Tk()
    root.title("%s %s" % (vs.APP_NAME, vs.APP_VERSION))
    root.geometry("920x820")
    root.minsize(820, 700)
    root.configure(bg=WHITE)

    st = ttk.Style(root)
    try:
        st.theme_use("clam")
    except Exception:
        pass
    st.configure(".", background=WHITE, foreground=TEXT, font=("Segoe UI", 10))
    st.configure("TFrame", background=WHITE)
    st.configure("TLabel", background=WHITE, foreground=TEXT)
    st.configure("Muted.TLabel", foreground=MUTED)
    st.configure("H.TLabel", font=("Segoe UI", 11, "bold"), foreground=NAVY)
    st.configure("TLabelframe", background=WHITE, bordercolor=LINE)
    st.configure("TLabelframe.Label", background=WHITE, foreground=PURPLE, font=("Segoe UI", 10, "bold"))
    st.configure("TEntry", fieldbackground=WHITE, bordercolor=LINE, padding=5)
    st.configure("TCombobox", fieldbackground=WHITE, bordercolor=LINE, padding=4)
    st.configure("TSpinbox", fieldbackground=WHITE, bordercolor=LINE, padding=3)
    st.configure("TCheckbutton", background=WHITE)
    st.configure("TButton", background=SOFT, bordercolor=LINE, padding=(12, 6), foreground=NAVY)
    st.map("TButton", background=[("active", LINE), ("disabled", SOFT)], foreground=[("disabled", "#A59EB5")])
    st.configure("Accent.TButton", background=PINK, foreground=WHITE, bordercolor=PINK,
                 font=("Segoe UI", 10, "bold"), padding=(18, 8))
    st.map("Accent.TButton", background=[("active", PLUM), ("disabled", "#E3B6C8")],
           foreground=[("disabled", WHITE)])
    st.configure("TNotebook", background=WHITE, bordercolor=LINE, tabmargins=(0, 4, 0, 0))
    st.configure("TNotebook.Tab", background=SOFT, foreground=PURPLE, padding=(16, 8), font=("Segoe UI", 10, "bold"))
    st.map("TNotebook.Tab", background=[("selected", NAVY)], foreground=[("selected", WHITE)])
    st.configure("Treeview", background=WHITE, fieldbackground=WHITE, rowheight=26, bordercolor=LINE)
    st.configure("Treeview.Heading", background=PURPLE, foreground=WHITE, font=("Segoe UI", 10, "bold"))
    st.map("Treeview", background=[("selected", PLUM)], foreground=[("selected", WHITE)])
    st.configure("Horizontal.TProgressbar", background=PINK, troughcolor=SOFT, bordercolor=LINE)

    ayar = ayarlar.oku()

    banner = tk.Canvas(root, height=BANNER_H, highlightthickness=0, bd=0, bg=WHITE)
    banner.pack(fill="x")
    banner_ref = {}

    def draw_banner(_event=None):
        w = max(200, banner.winfo_width())
        img = banner_image(w, BANNER_H, ayar.get("arka_plan", ""))
        banner_ref["img"] = ImageTk.PhotoImage(img)
        banner.delete("all")
        banner.create_image(0, 0, anchor="nw", image=banner_ref["img"])
        banner.create_text(28, 38, anchor="w", text="Video Scrap", fill=WHITE, font=("Segoe UI", 24, "bold"))
        banner.create_text(30, 74, anchor="w", text="Videoyu az token ile analiz et  |  v%s%s" % (vs.APP_VERSION, deneme_etiketi()),
                           fill="#F1E6F3", font=("Segoe UI", 10))

    banner.bind("<Configure>", draw_banner)

    outer = ttk.Frame(root)
    outer.pack(fill="both", expand=True, padx=14, pady=(10, 8))

    nb = ttk.Notebook(outer)
    nb.pack(fill="x")

    msg_queue = queue.Queue()
    state = {"running": False, "open_target": None, "cancel": threading.Event()}

    def log(msg):
        msg_queue.put(("log", msg))

    pad = {"padx": 8, "pady": 5}

    # ---------------- Sekme 1: Video Incele ----------------
    t1 = ttk.Frame(nb)
    nb.add(t1, text="  Video İncele  ")
    t1.columnconfigure(0, weight=1)

    ttk.Label(t1, text="YouTube linki veya video dosyası", style="H.TLabel").grid(row=0, column=0, sticky="w", **pad)
    src_var = tk.StringVar()
    ttk.Entry(t1, textvariable=src_var, font=("Segoe UI", 11)).grid(row=1, column=0, sticky="ew", **pad)

    def pick_src():
        p = filedialog.askopenfilename(
            title="Video seç",
            filetypes=[("Video", " ".join("*" + e for e in vs.VIDEO_EXTS)), ("Tüm dosyalar", "*.*")])
        if p:
            src_var.set(p)

    ttk.Button(t1, text="Dosya seç", command=pick_src).grid(row=1, column=1, **pad)

    ttk.Label(t1, text="Link verince video otomatik indirilir, kendi klasörüne konur (kısa: shortsN, uzun: videoN) "
                       "ve analiz edilir. Aynı link tekrar indirilmez.",
              style="Muted.TLabel", wraplength=800, justify="left").grid(row=2, column=0, columnspan=2, sticky="w", **pad)

    btn1 = ttk.Frame(t1)
    btn1.grid(row=3, column=0, columnspan=2, sticky="w", **pad)
    inc_btn = ttk.Button(btn1, text="İncele", style="Accent.TButton")
    inc_btn.pack(side="left", padx=(0, 8))
    open1_btn = ttk.Button(btn1, text="Sonuç klasörünü aç", state="disabled")
    open1_btn.pack(side="left")

    ttk.Label(t1, text="Önceki videolar", style="H.TLabel").grid(row=4, column=0, sticky="w", **pad)
    ref_btn = ttk.Button(t1, text="Yenile")
    ref_btn.grid(row=4, column=1, **pad)

    cols = ("klasor", "tur", "baslik", "durum")
    tree = ttk.Treeview(t1, columns=cols, show="headings", height=5)
    for c, t, w in (("klasor", "Klasör", 90), ("tur", "Tür", 70), ("baslik", "Başlık", 520), ("durum", "Analiz", 90)):
        tree.heading(c, text=t)
        tree.column(c, width=w, anchor="w")
    tree.grid(row=5, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))
    tree_paths = {}

    def load_list():
        import incele
        tree.delete(*tree.get_children())
        tree_paths.clear()
        try:
            for r in incele.list_videos():
                iid = tree.insert("", "end", values=(r["klasor"], r["tur"], r["baslik"], r["analiz_durumu"] or "-"))
                tree_paths[iid] = r["yol"]
        except Exception as exc:
            log("Liste okunamadı: %s" % exc)

    def open_dir(path):
        if path and os.path.isdir(path):
            try:
                os.startfile(path)
            except Exception:
                subprocess.Popen(["explorer", path])

    def open_selected(_e=None):
        sel = tree.selection()
        if sel:
            open_dir(tree_paths.get(sel[0]))

    tree.bind("<Double-1>", open_selected)
    ref_btn.configure(command=load_list)

    # ---------------- Sekme 2: Kare Cikar ----------------
    t2 = ttk.Frame(nb)
    nb.add(t2, text="  Kare Çıkar  ")
    t2.columnconfigure(1, weight=1)

    ttk.Label(t2, text="Video dosyası").grid(row=0, column=0, sticky="w", **pad)
    video_var = tk.StringVar()
    ttk.Entry(t2, textvariable=video_var).grid(row=0, column=1, sticky="ew", **pad)
    out_var = tk.StringVar()
    info_var = tk.StringVar(value="Video seçilmedi.")

    def show_info():
        p = video_var.get().strip()
        if not p or not os.path.exists(p):
            info_var.set("Video seçilmedi.")
            return
        try:
            i = vs.probe_video(p)
            info_var.set("%s | %dx%d | %.2f fps | %s | %d kare" % (
                i["name"], i["width"], i["height"], i["fps"], vs.fmt_dur(i["duration"]), i["frame_count"]))
        except Exception as exc:
            info_var.set("Okunamadı: %s" % exc)

    def pick_video():
        p = filedialog.askopenfilename(
            title="Video seç",
            filetypes=[("Video", " ".join("*" + e for e in vs.VIDEO_EXTS)), ("Tüm dosyalar", "*.*")])
        if p:
            video_var.set(p)
            out_var.set(str(ayarlar.cikti_koku() / "calisma" / vs.safe_name(Path(p).stem)))
            show_info()

    ttk.Button(t2, text="Gözat", command=pick_video).grid(row=0, column=2, **pad)
    ttk.Label(t2, text="Çıktı klasörü").grid(row=1, column=0, sticky="w", **pad)
    ttk.Entry(t2, textvariable=out_var).grid(row=1, column=1, sticky="ew", **pad)

    def pick_out():
        p = filedialog.askdirectory(title="Çıktı klasörü seç")
        if p:
            out_var.set(p)

    ttk.Button(t2, text="Gözat", command=pick_out).grid(row=1, column=2, **pad)
    ttk.Label(t2, textvariable=info_var, style="Muted.TLabel").grid(row=2, column=0, columnspan=3, sticky="w", **pad)

    ttk.Label(t2, text="Kare seçimi").grid(row=3, column=0, sticky="w", **pad)
    mode_var = tk.StringVar(value=vs.MODES["all"])
    mode_box = ttk.Combobox(t2, textvariable=mode_var, state="readonly", values=[vs.MODES[k] for k in vs.MODE_KEYS])
    mode_box.grid(row=3, column=1, sticky="ew", **pad)
    ttk.Label(t2, text="Değer").grid(row=4, column=0, sticky="w", **pad)
    value_var = tk.StringVar(value="1")
    value_entry = ttk.Entry(t2, textvariable=value_var)
    value_entry.grid(row=4, column=1, sticky="ew", **pad)
    value_hint = ttk.Label(t2, text="", style="Muted.TLabel")
    value_hint.grid(row=4, column=2, sticky="w", **pad)

    def mode_key():
        for k, v in vs.MODES.items():
            if v == mode_var.get():
                return k
        return "all"

    def sync_mode(*_):
        k = mode_key()
        if k == "all":
            value_entry.state(["disabled"])
            value_var.set("1")
            value_hint.configure(text="her kare")
        else:
            value_entry.state(["!disabled"])
            value_var.set({"every_n": "5", "fps": "2", "scene": "0.30"}[k])
            value_hint.configure(text={"every_n": "kaç karede bir", "fps": "saniyede kaç kare",
                                       "scene": "eşik 0.05-0.90"}[k])

    mode_box.bind("<<ComboboxSelected>>", sync_mode)

    adv = ttk.LabelFrame(t2, text="Kontak sayfası")
    adv.grid(row=5, column=0, columnspan=3, sticky="ew", padx=8, pady=8)
    cols_var, rows_var = tk.StringVar(value="8"), tk.StringVar(value="5")
    thumb_var, quality_var = tk.StringVar(value="256"), tk.StringVar(value="85")
    ttk.Label(adv, text="Sütun").grid(row=0, column=0, padx=8, pady=5, sticky="w")
    ttk.Spinbox(adv, from_=1, to=20, textvariable=cols_var, width=5).grid(row=0, column=1, sticky="w")
    ttk.Label(adv, text="Satır").grid(row=0, column=2, padx=8, sticky="w")
    ttk.Spinbox(adv, from_=1, to=20, textvariable=rows_var, width=5).grid(row=0, column=3, sticky="w")
    ttk.Label(adv, text="Küçük resim genişliği").grid(row=0, column=4, padx=8, sticky="w")
    ttk.Spinbox(adv, from_=96, to=640, increment=16, textvariable=thumb_var, width=6).grid(row=0, column=5, sticky="w")
    ttk.Label(adv, text="JPEG kalite").grid(row=0, column=6, padx=8, sticky="w")
    ttk.Spinbox(adv, from_=50, to=100, increment=5, textvariable=quality_var, width=5).grid(row=0, column=7, sticky="w")
    save_frames_var, sharpen_var = tk.BooleanVar(value=False), tk.BooleanVar(value=True)
    ttk.Checkbutton(adv, text="Tek tek kareleri de kaydet (çok yer kaplar)", variable=save_frames_var).grid(
        row=1, column=0, columnspan=8, sticky="w", padx=8, pady=3)
    ttk.Checkbutton(adv, text="Küçük resimleri keskinleştir", variable=sharpen_var).grid(
        row=2, column=0, columnspan=8, sticky="w", padx=8, pady=(0, 6))

    btn2 = ttk.Frame(t2)
    btn2.grid(row=6, column=0, columnspan=3, sticky="w", **pad)
    start_btn = ttk.Button(btn2, text="Başlat", style="Accent.TButton")
    start_btn.pack(side="left", padx=(0, 8))
    cancel_btn = ttk.Button(btn2, text="İptal", state="disabled")
    cancel_btn.pack(side="left", padx=(0, 8))
    open2_btn = ttk.Button(btn2, text="Klasörü aç", state="disabled")
    open2_btn.pack(side="left")

    # ---------------- Sekme 3: Ayarlar ----------------
    t3 = ttk.Frame(nb)
    nb.add(t3, text="  Ayarlar  ")
    t3.columnconfigure(1, weight=1)

    ttk.Label(t3, text="Kayıt klasörü", style="H.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", **pad)
    root_var = tk.StringVar(value=ayar["cikti_klasoru"] or str(ayarlar.cikti_koku()))
    ttk.Entry(t3, textvariable=root_var).grid(row=1, column=0, columnspan=2, sticky="ew", **pad)

    def pick_root():
        p = filedialog.askdirectory(title="Kayıt klasörü seç")
        if p:
            root_var.set(p)

    ttk.Button(t3, text="Gözat", command=pick_root).grid(row=1, column=2, **pad)
    ttk.Label(t3, text="İndirilen videolar (videolar/) ve analiz çıktıları bu klasörün içine yazılır. "
                       "Yapay zekâ (MCP) de aynı klasörü kullanır; değiştirince yapay zekâ uygulamasını yeniden başlat.",
              style="Muted.TLabel", wraplength=800, justify="left").grid(row=2, column=0, columnspan=3, sticky="w", **pad)

    ttk.Label(t3, text="Başlık görseli (isteğe bağlı)", style="H.TLabel").grid(row=3, column=0, columnspan=3, sticky="w", **pad)
    bg_var = tk.StringVar(value=ayar["arka_plan"])
    ttk.Entry(t3, textvariable=bg_var).grid(row=4, column=0, columnspan=2, sticky="ew", **pad)

    def pick_bg():
        p = filedialog.askopenfilename(
            title="Görsel seç", filetypes=[("Görsel", "*.png *.jpg *.jpeg *.webp *.bmp"), ("Tüm dosyalar", "*.*")])
        if p:
            bg_var.set(p)

    ttk.Button(t3, text="Seç", command=pick_bg).grid(row=4, column=2, **pad)
    ttk.Label(t3, text="Boş bırakırsan renk geçişi kullanılır. Uygulamanın geri kalanı beyaz kalır.",
              style="Muted.TLabel").grid(row=5, column=0, columnspan=3, sticky="w", **pad)

    def save_settings():
        folder = root_var.get().strip()
        if folder:
            try:
                Path(folder).expanduser().mkdir(parents=True, exist_ok=True)
            except Exception as exc:
                messagebox.showerror(vs.APP_NAME, "Klasör açılamadı: %s" % exc)
                return
        bg = bg_var.get().strip()
        if bg and not os.path.isfile(bg):
            messagebox.showerror(vs.APP_NAME, "Görsel dosyası bulunamadı.")
            return
        ayar.update(ayarlar.kaydet(cikti_klasoru=folder, arka_plan=bg))
        draw_banner()
        load_list()
        log("Ayarlar kaydedildi. Kayıt klasörü: %s" % ayarlar.cikti_koku())

    def clear_bg():
        bg_var.set("")
        save_settings()

    brow = ttk.Frame(t3)
    brow.grid(row=6, column=0, columnspan=3, sticky="w", **pad)
    ttk.Button(brow, text="Ayarları kaydet", style="Accent.TButton", command=save_settings).pack(side="left", padx=(0, 8))
    ttk.Button(brow, text="Görseli kaldır", command=clear_bg).pack(side="left", padx=(0, 8))
    ttk.Button(brow, text="Kayıt klasörünü aç", command=lambda: open_dir(str(ayarlar.cikti_koku()))).pack(side="left")

    # ---------------- Sekme 4: Yapay Zekaya Bagla ----------------
    t4 = ttk.Frame(nb)
    nb.add(t4, text="  Yapay Zekaya Bağla  ")
    t4.columnconfigure(0, weight=1)
    ttk.Label(t4, text="Hangi yapay zekâya bağlayacaksın?", style="H.TLabel").grid(row=0, column=0, sticky="w", **pad)
    hedefler = ["Claude Desktop", "Claude Code", "Gemini CLI", "ChatGPT / Codex", "Abacus Desktop"]
    hedef_var = tk.StringVar(value=hedefler[0])
    hedef_box = ttk.Combobox(t4, textvariable=hedef_var, state="readonly", values=hedefler)
    hedef_box.grid(row=1, column=0, sticky="ew", **pad)
    snippet = tk.Text(t4, height=9, wrap="word", font=("Consolas", 9), bg=SOFT, fg=TEXT, relief="flat", bd=0,
                      padx=8, pady=6)
    snippet.grid(row=2, column=0, sticky="ew", padx=8, pady=5)

    def fill_snippet(*_):
        snippet.configure(state="normal")
        snippet.delete("1.0", "end")
        snippet.insert("end", baglanti_metni(hedef_var.get()))
        snippet.configure(state="disabled")

    hedef_box.bind("<<ComboboxSelected>>", fill_snippet)

    def copy_snippet():
        root.clipboard_clear()
        root.clipboard_append(snippet.get("1.0", "end").strip())
        status_var.set("Panoya kopyalandı.")

    def register_claude():
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        r = subprocess.run([sys.executable, str(HERE / "mcp_kaydet.py"), "--hedef", "claude"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           cwd=str(HERE), creationflags=flags)
        log((r.stdout + r.stderr).strip())
        status_var.set("Claude kaydı yazıldı. Claude Desktop'u yeniden başlat."
                       if r.returncode == 0 else "Kayıt başarısız, günlüğe bak.")

    b4 = ttk.Frame(t4)
    b4.grid(row=3, column=0, sticky="w", **pad)
    ttk.Button(b4, text="Metni kopyala", command=copy_snippet).pack(side="left", padx=(0, 8))
    ttk.Button(b4, text="Claude Desktop'a otomatik kaydet", style="Accent.TButton",
               command=register_claude).pack(side="left")

    # ---------------- Ortak alt kisim ----------------
    bottom = ttk.Frame(outer)
    bottom.pack(fill="both", expand=True, pady=(8, 0))
    bottom.columnconfigure(0, weight=1)
    bottom.rowconfigure(2, weight=1)
    progress = ttk.Progressbar(bottom, mode="determinate", maximum=100.0)
    progress.grid(row=0, column=0, sticky="ew")
    status_var = tk.StringVar(value="Hazır.")
    ttk.Label(bottom, textvariable=status_var, style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=3)
    log_box = tk.Text(bottom, height=8, wrap="word", font=("Consolas", 9), bg=SOFT, fg=TEXT, relief="flat", bd=0,
                      padx=8, pady=6)
    log_box.grid(row=2, column=0, sticky="nsew")
    log_box.configure(state="disabled")

    def append_log(msg):
        log_box.configure(state="normal")
        log_box.insert("end", msg + "\n")
        log_box.see("end")
        log_box.configure(state="disabled")

    def set_busy(busy, indeterminate=False):
        state["running"] = busy
        for b in (inc_btn, start_btn):
            b.configure(state="disabled" if busy else "normal")
        cancel_btn.configure(state="normal" if (busy and not indeterminate) else "disabled")
        if busy and indeterminate:
            progress.configure(mode="indeterminate")
            progress.start(12)
        else:
            progress.stop()
            progress.configure(mode="determinate")

    def poll():
        try:
            while True:
                kind, payload = msg_queue.get_nowait()
                if kind == "log":
                    append_log(payload)
                elif kind == "progress":
                    d, t = payload
                    if t > 0:
                        progress.configure(value=min(100.0, d * 100.0 / t))
                elif kind == "status":
                    status_var.set(payload)
                elif kind == "incele_done":
                    finish_incele(payload)
                elif kind == "lisans_bitti":
                    set_busy(False)
                    status_var.set("Deneme süresi doldu.")
                    messagebox.showerror(vs.APP_NAME, payload)
                elif kind == "kare_done":
                    finish_kare(payload)
        except queue.Empty:
            pass
        root.after(150, poll)

    # ---- Incele akisi ----
    def last_log_line(path):
        try:
            with open(path, "rb") as f:
                f.seek(0, os.SEEK_END)
                f.seek(max(0, f.tell() - 600))
                lines = f.read().decode("utf-8", "replace").strip().splitlines()
            return lines[-1][:120] if lines else ""
        except Exception:
            return ""

    def incele_worker(source):
        import incele
        try:
            msg_queue.put(("status", "Video hazırlanıyor (indirme gerekebilir)..."))
            res = incele.prepare(source, log=log)
            log("Klasör: %s (%s)%s" % (res["klasor"], res["tur"], " [önceden vardı]" if res["yeniden_kullanildi"] else ""))
            if res["analiz_durumu"] == "done":
                log("Analiz zaten var, yeniden çalıştırılmadı.")
                msg_queue.put(("incele_done", res))
                return
            msg_queue.put(("status", "Analiz çalışıyor..."))
            logfile = os.path.join(res["analiz_klasoru"], "analiz_log.txt")
            p = incele.start_analysis(res["video_path"], res["analiz_klasoru"], wait=False)

            def watch():
                while p.poll() is None:
                    line = last_log_line(logfile)
                    if line:
                        msg_queue.put(("status", "Analiz: " + line))
                    threading.Event().wait(2.0)

            w = threading.Thread(target=watch, daemon=True)
            w.start()
            p.wait()
            msg_queue.put(("incele_done", res if p.returncode == 0 else None))
        except Exception as exc:
            log("HATA: %s" % exc)
            if type(exc).__name__ == "DenemeBitti":
                msg_queue.put(("lisans_bitti", str(exc)))
            else:
                msg_queue.put(("incele_done", None))

    def finish_incele(res):
        set_busy(False)
        load_list()
        if res is None:
            status_var.set("İnceleme başarısız. Günlüğe bak.")
            return
        state["open_target"] = res["analiz_klasoru"]
        open1_btn.configure(state="normal")
        status_var.set("Bitti: %s" % res["analiz_klasoru"])
        log("Sonuç: %s  (olaylar.md, sheets/, yakin_cekim/)" % res["analiz_klasoru"])

    def start_incele():
        src = src_var.get().strip().strip('"')
        if not src:
            messagebox.showinfo(vs.APP_NAME, "Bir link yaz ya da video dosyası seç.")
            return
        set_busy(True, indeterminate=True)
        open1_btn.configure(state="disabled")
        threading.Thread(target=incele_worker, args=(src,), daemon=True).start()

    inc_btn.configure(command=start_incele)
    open1_btn.configure(command=lambda: open_dir(state["open_target"]))

    # ---- Kare cikar akisi ----
    def kare_worker(video, out_dir, kwargs):
        try:
            s = vs.process_video(video, out_dir, log=log,
                                 progress=lambda d, t: msg_queue.put(("progress", (d, t))),
                                 cancel=state["cancel"], **kwargs)
            msg_queue.put(("kare_done", s))
        except Exception as exc:
            log("HATA: %s" % exc)
            msg_queue.put(("kare_done", None))

    def finish_kare(s):
        set_busy(False)
        progress.configure(value=100.0)
        if s is None:
            status_var.set("İptal edildi veya hata oluştu.")
            return
        state["open_target"] = s["out_dir"]
        open2_btn.configure(state="normal")
        status_var.set("Tamamlandı: %d kare, %d sayfa" % (s["frames_kept"], len(s["sheets"])))
        log("Çıktı: %s" % s["out_dir"])

    def start_kare():
        video = video_var.get().strip()
        if not video or not os.path.exists(video):
            messagebox.showerror(vs.APP_NAME, "Geçerli bir video dosyası seç.")
            return
        out_dir = out_var.get().strip() or str(ayarlar.cikti_koku() / "calisma" / vs.safe_name(Path(video).stem))
        out_var.set(out_dir)
        try:
            kw = {"mode": mode_key(), "cols": max(1, int(cols_var.get())), "rows": max(1, int(rows_var.get())),
                  "thumb_w": max(48, int(thumb_var.get())), "quality": min(100, max(40, int(quality_var.get()))),
                  "save_frames": save_frames_var.get(), "sharpen": sharpen_var.get()}
            val = float(value_var.get().replace(",", "."))
        except Exception:
            messagebox.showerror(vs.APP_NAME, "Sayısal alanları kontrol et.")
            return
        k = kw["mode"]
        if k == "every_n":
            kw["n"] = max(1, int(val))
        elif k == "fps":
            kw["target_fps"] = max(0.01, val)
        elif k == "scene":
            kw["scene_thresh"] = min(0.95, max(0.02, val))
        state["cancel"].clear()
        set_busy(False)
        set_busy(True)
        progress.configure(value=0.0)
        open2_btn.configure(state="disabled")
        threading.Thread(target=kare_worker, args=(video, out_dir, kw), daemon=True).start()

    def do_cancel():
        if state["running"]:
            state["cancel"].set()
            status_var.set("İptal ediliyor...")

    start_btn.configure(command=start_kare)
    cancel_btn.configure(command=do_cancel)
    open2_btn.configure(command=lambda: open_dir(state["open_target"]))

    sync_mode()
    fill_snippet()
    load_list()
    log("Kayıt klasörü: %s" % ayarlar.cikti_koku())
    root.after(150, poll)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
