# Video Scrap — Değişiklik Günlüğü

Biçim: [Keep a Changelog](https://keepachangelog.com/tr/1.1.0/). Sürümleme: [SemVer](https://semver.org/lang/tr/).

## [1.1] — 2026-11-27

### Eklendi
- Tkinter pencere arayüzü: kahverengi/mor banner, beyaz gövde, sürükle-bırak, canlı log.
- Yerel MCP sunucusu (stdio, 14 araç): `download_video`, `incele_video`, `videolari_listele`,
  `video_info`, `scrap_video`, `analyze_video`, `zoom_range`, `transcribe_video`,
  `read_transcript`, `job_status`, `list_outputs`, `view_sheet`, `read_prompt`, `read_manifest`.
- İki aşamalı analiz: genel tarama (40'lık kontak sayfaları) + geçiş anlarının yakın çekimi.
- Kesme, yumuşak geçiş ve kamera hareketi (zoom / kaydırma / dönme) tespiti; `olaylar.md` çıktısı.
- `incele.py`: link ver → indir → `videolar/videoN` veya `videolar/shortsN` → analiz.
- `dogrula_baglam.py`: 18 kontrolle bağlam dosyalarının depoyla tutarlılığını denetler (model çağırmaz).
- `tests/`: 25 `pytest` testi (kilit, atomik yazım, yol güvenliği, link doğrulama, pid izleme).
- `mcp_kaydet.py`: Abacus / Claude Desktop / Claude Code kaydını tek komutla yazar.
- `OKU_BENI/`: kurulum, kullanım kılavuzu, yapay zekâya bağlama, GitHub yayını, teknik detay.

### Düzeltildi
- MCP kaydında `args` eksikliği: Python REPL açılıyor, istemci 30 sn sonra zaman aşımına düşüyordu.
- Sabit kullanıcı yolları (`C:/Users/<ad>/...`) kaldırıldı; konum `VIDEO_SCRAP_HOME` ve dosya
  konumundan türetiliyor.
- Kilit aynı süreçte ikinci kez alınınca `EDEADLK` veriyordu: `threading.RLock` + iç içe sayaç.
- `kayit.json`, `durum.json`, `ses_durum.json`, `ayarlar.json` yarım yazılabiliyordu: geçici dosya +
  `os.replace()` ile atomik yazım.
- `start_analysis` ve `transcribe_video` içinde `logf` tanıtıcısı sızıyordu.
- yt-dlp'ye doğrulamasız link geçiliyordu (`--exec=...` seçenek olarak yorumlanabilir): `url_dogrula()`
  ve `--` ayracı eklendi.
- `pid` yazılmadan ölen iş sonsuza kadar "running" görünüyordu: pid `Popen` sonrası yazılıyor,
  pid yoksa 120 sn sonra bayat sayılıyor.
- Aynı link eşzamanlı verilince kayıt eziliyordu; çalışan analizin üstüne ikincisi başlatılabiliyordu.
- `mcp_kaydet.py` `sys.executable` yazıyordu: artık önce `.venv\Scripts\python.exe`.
- `download_video` konsol penceresi açıyordu ve zaman aşımı yoktu.

### Bilinen sınırlar
- Kamera tespiti kusurlu: yumuşak sahne geçişleri bazen `zoom-out` etiketleniyor, ölçekler yaklaşık.
- Yalnızca Windows (`KUR.bat`, `BASLAT.bat`, `os.startfile`, `CREATE_NO_WINDOW`).
- MCP yalnızca yerel `stdio`; ağ üzerinden bağlanan bir sunucu yok.
- `whisper` ve `torch` isteğe bağlı (`requirements.txt` dışında).
