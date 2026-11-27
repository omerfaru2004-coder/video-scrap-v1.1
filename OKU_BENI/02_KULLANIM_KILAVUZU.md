# 2. Kullanım Kılavuzu

Kurulum bitti varsayıyorum. Bu sayfa "hangi düğmeye basacağım, dosyalar nereye gidiyor" sorusunu yanıtlar.

---

## A. Pencere (BASLAT.bat)

Pencerenin üstünde renkli banner, altında 4 sekme var. En altta ilerleme çubuğu ve günlük kutusu bulunur.

### Sekme 1: Video İncele — en çok bunu kullanacaksın

1. Kutunun içine **YouTube linkini yapıştır**. (Veya **Dosya seç** ile bilgisayarındaki videoyu seç.)
2. **İncele** düğmesine bas.
3. Araç sırayla şunu yapar: videoyu indirir → `videolar/` içinde kendi klasörüne koyar → analiz eder.
4. Bitince **Sonuç klasörünü aç** düğmesine bas, çıktıyı gör.

Klasör adını araç kendisi verir:

- 180 saniye ve kısa videolar (veya `/shorts/` linkleri) → `shorts1`, `shorts2`, ...
- Diğerleri → `video1`, `video2`, ...

Aynı linki ikinci kez verirsen **yeniden indirmez**, hazır analizi açar. Alttaki
"Önceki videolar" listesinde bir satıra çift tıklarsan o videonun klasörü açılır.

### Sekme 2: Kare Çıkar

Analiz yapmadan sadece kontak sayfası üretir. Video seç, kare seçim modunu seç
(her kare / her N. kare / saniyede N kare / sahne değişimi), **Başlat**'a bas.
Çıktı `calisma/<video adı>/` içine yazılır.

### Sekme 3: Ayarlar

| Ayar | Ne yapar |
|---|---|
| **Kayıt klasörü** | `videolar/` ve `calisma/` hangi klasörün içinde açılsın. Boşsa program klasörü kullanılır. Başka diske almak için ör. `D:\VideoScrap` seç, **Ayarları kaydet**'e bas |
| **Başlık görseli** | Üst banner için kendi resmini seç. Boşsa renk geçişi kullanılır. Gövde her zaman beyazdır |

Kayıt klasörünü değiştirdiysen yapay zekâ uygulamasını (Abacus, Claude vb.) kapat-aç;
MCP sunucusu ayarı açılışta okur.

### Sekme 4: Yapay Zekaya Bağla

Listeden yapay zekâyı seç, çıkan metni **Kopyala**, ilgili dosyaya yapıştır.
Claude Desktop için **Claude Desktop'a otomatik kaydet** düğmesi dosyayı kendisi yazar.
Ayrıntı: `03_YAPAY_ZEKAYA_BAGLAMA.md`.

---

## B. Yapay zekâ ile kullanırken

Bağlantıyı bir kez kurduktan sonra sohbete normal cümle yazarsın; hangi aracı çağıracağını
yapay zekâ kendisi seçer.

### Hangi cümleye hangi araç

| Sen ne yazarsın | Araç | Ne olur |
|---|---|---|
| "Bu linki incele" | `incele_video` | İndirir, klasöre koyar, analizi arka planda başlatır |
| "Analiz bitti mi?" | `job_status` | Durumu söyler, bitince `olaylar.md` listesini verir |
| "Daha önce neleri inceledik?" | `videolari_listele` | `videolar/` içindekileri ve durumlarını listeler |
| "Şu sayfayı göster" | `view_sheet` | Bir kontak sayfasını resim olarak getirir (kredi harcayan tek adım) |
| "12. ile 18. saniye arasına yakından bak" | `zoom_range` | O aralığı sık karelerle yeni sayfalara döker |
| "Videoda ne konuşuluyor?" | `transcribe_video`, `read_transcript` | Sesi yazıya döker (Whisper kurulu olmalı) |
| "Dosyalar nerede?" | `list_outputs` | Klasördeki sayfaları ve dosyaları listeler |
| "Süresi, çözünürlüğü ne?" | `video_info` | Süre, fps, çözünürlük, kare sayısı |
| Sadece kare çıkarma | `scrap_video` | Kareleri çıkarıp kontak sayfası üretir |
| Sadece indir | `download_video` | Videoyu indirir, analiz etmez |
| Analizi elle başlat | `analyze_video` | İki aşamalı analizi belirli dosya için çalıştırır |
| Hazır metinler | `read_prompt`, `read_manifest` | `prompt.txt` ve `manifest.csv` içeriğini getirir |

**Normal akış:** `incele_video` → `job_status` (bitene kadar) → `olaylar.md` oku → gerekirse
`view_sheet` veya `zoom_range`.

**Tasarrufun sırrı:** yapay zekâ önce `olaylar.md` metnini okur, sadece gereken sayfayı açar.
Sen "önce metni oku, sadece 12-18. saniye sayfalarını aç" dersen kredi neredeyse sıfır kalır.

### Nerede neyi kaydeder

Kayıt kökü = Ayarlar'daki "Kayıt klasörü" (boşsa program klasörü). Aşağıdaki yollar bu kökün içindedir.

| Yol | İçinde ne var |
|---|---|
| `videolar/kayit.json` | Hangi link hangi klasöre indi (aynı link tekrar inmesin diye) |
| `videolar/<klasör>/video.mp4` | İndirilen veya kopyalanan video |
| `videolar/<klasör>/info.json` | Kaynak link, başlık, süre, indirme zamanı |
| `videolar/<klasör>/analiz/olaylar.md` | **Okunacak ana dosya:** hangi saniyede ne var, hangi sayfada |
| `videolar/<klasör>/analiz/olaylar.json` | Aynı bilgi, makine okur biçimde |
| `videolar/<klasör>/analiz/sheets/` | Genel sayfalar (her saniyeden 1 kare) |
| `videolar/<klasör>/analiz/yakin_cekim/` | Geçiş ve hareket anlarının sık kareli sayfaları |
| `videolar/<klasör>/analiz/durum.json`, `analiz_log.txt` | Analiz durumu ve günlüğü |
| `videolar/<klasör>/analiz/transcript.md` | Konuşma dökümü (sadece `transcribe_video` çalıştıysa) |
| `calisma/<ad>/` | "Kare Çıkar" ve `scrap_video` çıktıları (`sheets/`, `prompt.txt`, `rapor.md`, `manifest.csv`) |

Program klasöründeki ayar dosyaları:

| Dosya | Ne tutar |
|---|---|
| `ayarlar.json` | Kayıt klasörü ve başlık görseli (arayüzden yazılır) |
| `libs/` ve `.venv/` | Kurulu paketler (proje içinde kalır) |

Kullanıcı klasöründe (`C:\Users\<sen>\`) sadece bağlantı kayıtları bulunur:

| Dosya | Ne için |
|---|---|
| `.abacusai\mcp.json` | Abacus Desktop MCP listesi (`python mcp_kaydet.py` yazar, yedeğini alır) |
| `%APPDATA%\Claude\claude_desktop_config.json` | Claude Desktop (arayüzdeki düğme veya `python mcp_kaydet.py --hedef claude`) |
| `.gemini\settings.json` | Gemini CLI (elle eklersin) |
| `.codex\config.toml` | ChatGPT masaüstü / Codex (elle eklersin) |

**Güvenlik kuralı:** MCP aracı yalnızca kayıt klasörünün **içine** yazar; dışarısı için gelen
yazma isteğini reddeder. Videoyu okumak için bilgisayarın herhangi bir yerindeki dosyayı gösterebilirsin.

### Kredi / token

- İndirme, analiz, kontak sayfası üretimi: **tamamen yerel, 0 kredi.**
- Kredi sadece yapay zekâ bir sayfayı **gördüğünde** (`view_sheet`) veya metin okuduğunda harcanır.
- Tasarruf için: "önce `olaylar.md`'yi oku, sadece şu saniyeler arasındaki sayfaları aç" de.

---

## C. Komut satırı (isteğe bağlı)

Pencereyi hiç açmadan kullanmak istersen:

```bat
python incele.py "https://www.youtube.com/watch?v=..."      # indir + analiz
python incele.py "C:\video.mp4"                              # yerel dosya
python video_scrap.py --video "C:\video.mp4" --mode fps --fps 2
python mcp_kaydet.py --goster                                # Abacus kaydını göster
```

Daha fazlası: `05_TEKNIK_DETAYLAR.md`.
