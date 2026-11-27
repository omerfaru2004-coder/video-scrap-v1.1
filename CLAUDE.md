# Video Scrap v1.1 — Proje Bağlamı

Bu dosya, projede çalışacak yapay zekâ ajanı için kısa bağlam notudur. Kod, komutlar ve
dosya adları Türkçedir; arayüz dili Türkçedir.

## Proje nedir

Video Scrap, bir videoyu yapay zekâya **az token** harcayarak analiz ettiren yerel bir araçtır.
Videonun karelerini 40'lık kontak sayfalarına dizer; sert kesmeleri, yumuşak geçişleri ve kamera
hareketlerini (zoom, kaydırma, dönme) ölçüp zaman damgalı bir `olaylar.md` listesi üretir.
Yapay zekâ önce bu metni okur, yalnızca gereken sayfaları açar.

- Tamamen yerel çalışır: video dışarı çıkmaz, analiz kredi harcamaz.
- Link verilir; araç indirir, `videolar/shortsN` veya `videolar/videoN` klasörüne koyar, analiz eder.
- Aynı link ikinci kez verilirse yeniden indirilmez, mevcut analiz kullanılır.
- İki kullanım yolu vardır: masaüstü penceresi ve yerel MCP sunucusu.

## Giriş noktaları

| Dosya | Görev |
|---|---|
| `video_scrap.py` | Uygulama başlatıcı (pencereyi açar) |
| `arayuz.py` | Tkinter arayüzü: Video İncele, Kare Çıkar, Ayarlar, Yapay Zekâya Bağla |
| `incele.py` | Link/dosya → indir → analiz hattı (komut satırı: `python incele.py <link>`) |
| `analiz.py` | Asıl analiz: kesme, geçiş, kamera hareketi, kontak sayfaları |
| `ses.py` | Transkript (ffmpeg + Whisper) |
| `mcp_server.py` | Yerel MCP sunucusu (14 araç) |
| `mcp_kaydet.py` | MCP kaydını yazar: `--hedef claude`, `--goster`, `--kaldir` |
| `ayarlar.py` | `ayarlar.json` okuma/yazma (kayıt klasörü, başlık görseli) |
| `kur.py` | Kurulum: `.venv` + paketler + ffmpeg; `--kontrol`, `--yenile` |
| `dogrula_baglam.py` | Bu dosyayı depoyla karşılaştıran ücretsiz denetleyici (model çağırmaz) |
| `tests/` | `pytest` testleri: kilit, atomik yazım, yol güvenliği, link doğrulama, pid izleme |
| `AGENTS.md`, `GEMINI.md` | Aynı bağlamın Codex ve Gemini CLI için kısa sürümü; `CLAUDE.md`'ye yönlendirir |
| `KUR.bat` / `BASLAT.bat` | Kurulum ve tek başlatıcı (konsol penceresi açılmaz) |

## Kurulum

Tek komut, tekrar çalıştırılabilir, sistem Python'una dokunmaz:

```bat
python kur.py            :: eksikleri kurar (kuruluysa indirme yapmaz)
python kur.py --kontrol  :: sadece durum
python kur.py --yenile   :: paketleri bastan kur
```

`kur.py` `.venv`'i açar, `requirements.txt` paketlerini kurar ve ffmpeg'i `imageio-ffmpeg`
paketiyle `.venv` içine getirir; `incele.py` bu yolu yt-dlp'ye `--ffmpeg-location` ile verir.
Bu yüzden kullanıcı ffmpeg kurmaz, dosya kopyalamaz. `KUR.bat` aynı betiği çağırır ve Python
yoksa winget ile kurmayı dener. Ajan "kur" dendiğinde doğrudan `python kur.py` çalıştırmalıdır.

## Veri nerede durur

| Yol | İçerik |
|---|---|
| `videolar/kayit.json` | İndirilen videoların kaydı (link → klasör) |
| `videolar/<klasör>/video.mp4`, `info.json` | Video ve üst veri |
| `videolar/<klasör>/analiz/olaylar.md` | Olay listesi (insan/ajan için özet) |
| `videolar/<klasör>/analiz/olaylar.json` | Aynı listenin makine biçimi (`olcek_kaynak` alanı dahil) |
| `videolar/<klasör>/analiz/sheets/` | Genel kontak sayfaları |
| `videolar/<klasör>/analiz/yakin_cekim/` | Olay çevresinden yakın çekim sayfaları |
| `videolar/<klasör>/analiz/durum.json` | Canlı durum: aşama, ilerleme, süre, sayılar |
| `videolar/<klasör>/analiz/analiz_log.txt` | Çalışma günlüğü |
| `calisma/` | Geçici/deneme çıktıları (sürüm denetimi dışında) |
| `ayarlar.json` | Kullanıcı ayarları (sürüm denetimi dışında) |
| `libs/` | Proje içi bağımlılıklar (PySceneDetect); sürüm denetimi dışında |
| `.venv/` | Proje içi sanal ortam; sürüm denetimi dışında |

Sürüm denetimine girenler yalnızca kod, `OKU_BENI/`, `README.md`, `LICENSE`, `requirements.txt`
ve başlatma betikleridir. `videolar/`, `calisma/`, `libs/`, `.venv/`, `ayarlar.json`,
`__pycache__/` `.gitignore` ile dışarıdadır.

## MCP araçları

`download_video`, `incele_video`, `videolari_listele`, `video_info`, `scrap_video`,
`analyze_video`, `zoom_range`, `transcribe_video`, `read_transcript`, `job_status`,
`list_outputs`, `view_sheet`, `read_prompt`, `read_manifest`.

Tipik akış: `incele_video` → `read_manifest` / `job_status` → `read_prompt` (olaylar.md) →
gerekli sayfalar için `view_sheet` → belirli bir aralık için `zoom_range`.

## Komutlar

```bash
KUR.bat                                  # .venv içine paketleri kurar
BASLAT.bat                               # arayüz (konsol görünmez)
python incele.py <link>                  # indir + analiz
python mcp_server.py                     # MCP sunucusunu elle çalıştır
python mcp_kaydet.py --hedef claude      # Claude Desktop kaydı
python mcp_kaydet.py --goster            # mevcut kaydı göster
python -m pytest tests -q                # testler (pytest gerekir: requirements-dev.txt)
python dogrula_baglam.py                 # bağlam denetimi, çıkış kodu 0 = geçti
```

Analiz çıktısı üretmek için ağ gerekmez; indirme adımı için `yt-dlp` ve `ffmpeg` gerekir.

## Kurallar

- Arayüz metinleri, günlükler ve belgeler Türkçe yazılır; kod tanımlayıcıları İngilizce kalabilir.
- Windows'ta alt süreçler `CREATE_NO_WINDOW` ile başlatılır; konsol penceresi açılmamalı.
- Bağımlılıklar sistem Python'una değil, proje içindeki `.venv` ve `libs/` altına kurulur.
- `videolar/` ve `calisma/` altındaki kullanıcı verileri silinmez, taşınmaz; yalnızca okunur.
- Bir değişiklikten sonra aynı kullanım yolundan (arayüz veya MCP) yeniden denenir.
- Görsel doğrulama yapılmadıysa "gözle kontrol edildi" denmez.

## Bilinen sınırlar

- Kamera tespiti kusurludur: yumuşak sahne geçişleri bazen `zoom-out` olarak etiketlenir.
- Bazı olayların ölçeği yaklaşık değerdir; `olaylar.json` içindeki `olcek_kaynak` alanı bunu belirtir.
- PySceneDetect eşiği 40'tır; kesme içeren olay silinmez, kesme noktasında bölünür.
- Analiz süresi videoya göre değişir (1 dk video ≈ 2 dk, 11 dk video ≈ 7 dk).
- `zoom_range` adımı kare cinsindendir; video süresini aşan bitiş uyarı verir.
- Kısa videolarda yakın çekim sayfaları toplam sayfaya yaklaşabilir; bu bilinçli bir tercihtir.
