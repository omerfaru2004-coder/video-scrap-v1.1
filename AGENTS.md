# Video Scrap v1.1 — Ajan Bağlamı

Bu projenin tam bağlamı `CLAUDE.md` dosyasındadır. **Önce onu oku**, sonra işe başla.
Burada yalnızca kısa özet ve o dosyaya yönlendirme vardır; iki dosya çelişirse `CLAUDE.md` geçerlidir.

## Özet

Video Scrap, bir videoyu yapay zekâya az token harcayarak analiz ettiren yerel bir araçtır.
Kareleri 40'lık kontak sayfalarına dizer; sert kesmeleri, yumuşak geçişleri ve kamera hareketlerini
(zoom, kaydırma, dönme) ölçüp zaman damgalı `olaylar.md` üretir. Tamamen yerelde çalışır.

- Giriş noktaları: `video_scrap.py`, `arayuz.py`, `incele.py`, `analiz.py`, `mcp_server.py`
- Çıktı: `videolar/<klasör>/analiz/` (`olaylar.md`, `olaylar.json`, `sheets/`, `yakin_cekim/`, `durum.json`)
- MCP: 14 araç, `mcp_server.py`; kayıt `mcp_kaydet.py --hedef claude`
- Git dışı: `videolar/`, `calisma/`, `libs/`, `.venv/`, `ayarlar.json`, `__pycache__/`

## Kurulum (ajan icin)

Kullanici "kur" derse başka bir şey sorma, şunu çalıştır:

```bat
python kur.py
```

`kur.py` proje içindeki `.venv`'i açar, `requirements.txt` paketlerini ve ffmpeg'i
(`imageio-ffmpeg`) kendi kurar; sistem Python'una dokunmaz, elle kopyalama gerektirmez.
Tekrar çalıştırmak zararsızdır. Sadece durum bakmak için: `python kur.py --kontrol`.
Sonra `python dogrula_baglam.py` ile bağlamı doğrula. Kullanıcı çift tıklamayı seviyorsa
`KUR.bat` aynı işi yapar (Python yoksa winget ile kurmayı dener).

## Kurallar

- Arayüz metinleri ve belgeler Türkçe.
- `videolar/` ve `calisma/` altındaki kullanıcı verileri silinmez, taşınmaz.
- Bağımlılıklar sistem Python'una değil, proje içi `.venv` ve `libs/` altına kurulur.
- Değişiklik sonrası aynı kullanım yolundan yeniden denenir; görsel doğrulama yapılmadıysa
  "gözle kontrol edildi" denmez.
- Bağlam dosyası depoyla tutarlı mı: `python dogrula_baglam.py`

Ayrıntı, tablolar ve bilinen sınırlar: `CLAUDE.md`.
