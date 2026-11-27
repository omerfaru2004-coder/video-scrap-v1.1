# Video Scrap v1.1 — Gemini Bağlamı

Tam bağlam `CLAUDE.md` dosyasındadır; **önce onu oku**. Bu dosya yalnızca kısa özettir,
çelişki olursa `CLAUDE.md` geçerlidir.

## Özet

Yerel video analiz aracı: kareleri kontak sayfalarına dizer, kesme/geçiş/kamera hareketini ölçer,
zaman damgalı `olaylar.md` üretir. Video dışarı çıkmaz, analiz kredi harcamaz.

- Giriş noktaları: `video_scrap.py`, `arayuz.py`, `incele.py`, `analiz.py`, `mcp_server.py`
- Çıktı: `videolar/<klasör>/analiz/` (`olaylar.md`, `olaylar.json`, `sheets/`, `yakin_cekim/`)
- MCP: 14 araç; kayıt `mcp_kaydet.py --hedef claude`
- Git dışı: `videolar/`, `calisma/`, `libs/`, `.venv/`, `ayarlar.json`, `__pycache__/`

## Kurulum

Kullanıcı "kur" derse: `python kur.py` çalıştır. `.venv`, paketler ve ffmpeg (`imageio-ffmpeg`)
kendiliğinden kurulur; elle kopyalama veya ayrı ffmpeg kurulumu gerekmez. Durum: `python kur.py --kontrol`.
Çift tıklama için `KUR.bat` aynı işi yapar.

## Kurallar

- Arayüz metinleri ve belgeler Türkçe.
- `videolar/` ve `calisma/` altındaki kullanıcı verileri silinmez.
- Bağımlılıklar proje içi `.venv` ve `libs/` altına kurulur.
- Bağlam denetimi: `python dogrula_baglam.py`

Ayrıntı ve bilinen sınırlar: `CLAUDE.md`.
