# Video Scrap v1.1 - Teknik Detaylar

> Günlük kullanım için `02_KULLANIM_KILAVUZU.md` yeterlidir. Bu dosya analizin iç işleyişini ve komut satırını anlatır.

Bir videonun **her karesini** (veya istediğin sıklıkta karelerini) çıkarır ve
**40 kareyi tek bir fotoğrafta** birleştirir. Böylece yapay zekâya videoyu
saniyede 1 kare olarak gondermek yerine, 3-5 tane yogun kontak sayfası
gönderirsin. Aynı bilgi, çok daha az token.

Her karenin altında **zaman damgası** (`00:00:01.233`) ve **kare numarası** (`#37`)
yazdığı için yapay zekâ "hangi saniyede ne olduğunu" doğrudan okuyabilir.

Tamamen **yerel** çalışır: internet yok, kredi harcamaz, video bilgisayarından çıkmaz.

---

## 1. Çalıştırma

`BASLAT.bat` dosyasına çift tıkla. Arayüz konsol penceresi olmadan açılır
(hata olursa uygulama mesaj kutusu gösterir).

Komut satırından:

```bash
python video_scrap.py
```

Başka bir bilgisayarda ilk kez çalıştıracaksan:

```bash
pip install -r requirements.txt
```

(Gerekli: Python 3.9+, `opencv-python`, `pillow`, `numpy`, `mcp`, `yt-dlp`, `scenedetect`)

Kurulumu sadece proje klasörüne yapmak istersen (sistem Python'una dokunmadan):

```bash
python -m pip install --target libs --no-deps scenedetect click platformdirs tqdm colorama
```

`analiz.py`, `libs/` klasörü varsa onu otomatik kullanır. `scenedetect` hiç yoksa sert kesme
doğrulaması uyarı verilerek atlanır; analiz yine çalışır.

---

## 2. Arayüzde 4 adım

1. **Video dosyası** → `Gözat` ile videoyu seç. Üstte süre, fps, çözünürlük görünür.
2. **Çıktı klasörü** → otomatik dolar (`videoadi_scrap`). İstersen değiştir.
3. **Kare seçimi** → aşağıdaki modlardan birini seç.
4. **Başlat** → bitince `Klasörü aç`.

### Kare seçimi modları

| Mod | Ne yapar | Ne zaman kullan |
|---|---|---|
| **Her kare (tam kayıt)** | Videodaki tüm kareleri alır (30 fps → saniyede 30 kare) | Kısa videolar, hiçbir şey kaçmasın |
| **Her N. kare** | N karede bir alır (örn. 5 → 30 fps'de saniyede 6 kare) | Genel amaçlı, hızlı |
| **Saniyede N kare** | Saniyede hedeflediğin kare sayısını alır (örn. 2) | Uzun videolar, özet |
| **Sahne değişimi** | Sadece görüntünün belirgin değiştiği kareleri alır | Uzun videolar, kesme/geçiş analizi |

> "Her kare" modu 1 saatlik bir videoda on binlerce kare üretir; kontak sayfası
> sayısı da ona göre artar. Uzun videolarda `Her N. kare` veya `Saniyede N kare`
> ile başla.

### Kontak sayfası ayarları

- **Sütun / Satır** → varsayılan 8 x 5 = **40 kare/foto**. 10 x 4, 6 x 6 gibi
  istediğin düzeni kurabilirsin.
- **Küçük resim genişliği** → varsayılan 256 px. **Daha net görüntü için 384 veya
  480** yap; dosya büyür ama detay artar.
- **JPEG kalite** → 85 iyi bir denge. 92-95 en net.
- **Keskinleştir** → hızlı hareketli sahnelerde kenarları belirginleştirir (varsayılan açık).
- **Tek tek kareleri de kaydet** → `frames/` klasörüne her kareyi ayrı JPG olarak yazar. Çok yer kaplar.

---

## 3. Çıktılar

```
video_scrap/
├── sheets/
│   ├── sheet_0001.jpg     <- 40 kare, 00:00:00.000 - 00:00:01.300
│   ├── sheet_0002.jpg     <- 40 kare, 00:00:01.333 - 00:00:02.633
│   └── ...
├── frames/                <- (opsiyonel) tek tek kareler
├── prompt.txt             <- yapay zekâya yapıştırılacak hazır metin
├── rapor.md               <- özet: süre, mod, sayfa listesi
└── manifest.csv           <- her karenin hangi sayfada, hangi satır/sütunda olduğu
```

Sayfa okuma sırası: **soldan sağa, yukarıdan aşağıya** = videonun kronolojik akışı.

---

## 4. Claude / ChatGPT / Gemini'ye nasıl verilir

1. `prompt.txt` dosyasını aç, **tamamını kopyala**.
2. Sohbete yapıştır.
3. `sheets/` içindeki JPG'leri sırayla (sheet_0001, sheet_0002, ...) ekle.
4. Gönder.

`prompt.txt` içinde video bilgisi, sayfa düzeni, zaman aralıkları ve istenen
çıktı başlıkları hazır yazılıdır; yapay zekâ kareleri doğru sırada okur.

İstersen sonuna kendi sorunu ekle: *"Sadece 00:00:12 ile 00:00:18 arasına odaklan."*

---

## 5. Token / kredi mantığı

- Kare çıkarma ve birleştirme **tamamen yerel** → **0 kredi**.
- Kredi sadece görselleri sohbete yükleyip yapay zekâya incelettiğinde harcanır.
- 40 kare tek fotoğrafta = 1 görsel. 10 dakikalık 30 fps video = 18.000 kare =
  450 kontak sayfası. Aynı videoyu saniyede 2 kare ile alırsan = 1.200 kare =
  30 sayfa. Aradaki fark doğrudan maliyet farkı.

---

## 6. MCP sunucusu olarak kullanma

`mcp_server.py`, aynı işlevleri bir MCP aracı olarak sunar. Böylece yapay zekâ
sohbet içinden videoyu kendisi işler, çıktıyı istediğin klasöre yazar ve üretilen
kontak sayfalarını kendisi görüntüler.

### Araçlar

| Araç | Ne yapar |
|---|---|
| `download_video` | YouTube linkinden videoyu indirir |
| `video_info` | Süre, fps, çözünürlük, kare sayısı |
| `scrap_video` | Kareleri çıkarır, kontak sayfalarını üretir (kısa videolar için) |
| `incele_video` | **Ilk tercih.** Link verilince `videolar/` klasorune indirir, analizi baslatir (asagida) |
| `videolari_listele` | Daha once indirilen/analiz edilen videolar |
| `analyze_video` | İki aşamalı analiz: genel tarama + geçiş anlarının yakın çekimi (arka planda) |
| `job_status` | `analyze_video` durumu; bitince `olaylar.md` listesini verir |
| `zoom_range` | Belirli bir saniye aralığını (`start`, `end`, `step`) sık karelerle sayfalara döker |
| `transcribe_video` | Videonun sesini Whisper ile zaman damgalı yazıya döker (arka planda; GPU varsa medium) |
| `read_transcript` | Dökümü getirir; `start`/`end` (sn) ile aralık |
| `list_outputs` | Klasördeki sayfaları ve dosyaları listeler |
| `view_sheet` | Sayfayı **görüntü olarak** döndürür (`folder`: `sheets` veya `yakin_cekim`) |
| `read_prompt` | `prompt.txt` metnini döndürür |
| `read_manifest` | `manifest.csv` içeriğini döndürür |

### Link ver, gerisini araç yapsın (`videolar/`)

Yapay zekâya sadece linki ver. `incele_video` şunları yapar:

1. `videolar/` klasörü yoksa açar (sadece ilk seferde).
2. Videoyu kendi klasörüne indirir: kısa videolar (180 sn ve altı veya `/shorts/` linki) `shorts1`, `shorts2`...;
   diğerleri `video1`, `video2`...
3. Analizi arka planda başlatır; çıktı `videolar/<klasör>/analiz/` içine yazılır
   (`sheets/`, `yakin_cekim/`, `olaylar.md`, `olaylar.json`).
4. Aynı link tekrar verilirse yeniden indirmez; bitmiş analizi kullanır (`kayit.json` eşleşmeyi tutar).

Komut satırından da aynı iş: `python incele.py "<link veya video dosyası>"`.

### Kayıt

```bash
python mcp_kaydet.py            # kaydeder
python mcp_kaydet.py --goster   # mevcut kaydı gösterir
python mcp_kaydet.py --kaldir   # kaydı siler
```

Kayıt `~/.abacusai/mcp.json` dosyasına `video-scrap` adıyla eklenir; var olan
sunucular korunur ve dosyanın yedeği alınır. Sonra MCP ekranında **"İçeri aktar"**
butonuna bas; `video-scrap` listede görünür.

### İki aşamalı analiz (`analyze_video`)

1. Video 3 dk'lık parçalara bölünüp paralel taranır (bölme hız içindir, kare sayısını azaltmaz).
2. Her saniyeden 1 kare `sheets/` sayfalarına konur.
3. Kareler arası piksel farkı ölçülür: ani yükselme = keskin geçiş, sürekli yüksek = yumuşak geçiş.
4. Bu anların çevresinde sık kare `yakin_cekim/` sayfalarına konur (en fazla 400 kare).
5. `olaylar.md`: hangi saniyede ne var, hangi sayfada. AI sadece bu sayfaları açar.

6. Kamera hareketi (zoom, kaydırma, dönme) ayrıca ölçülür ve `olaylar.md` içinde `kamera` türüyle listelenir.
   Sert kesmeler kamera hareketi sayılmaz; kesmeyi aşan hareketler bölünür.

Kamera olayları en fazla 2 sn'lik parçalara bölünür. Ölçek ve dönme değeri mümkünse olayın ilk ve son karesinden
doğrudan ölçülür (`olcek_kaynak: dogrudan`); yeterli eşleşme yoksa kare kare toplamdan gelen yaklaşık değer kalır
(`toplam(yaklasik)`), ki bu değer gerçeğin birkaç katı çıkabilir.

Sert kesmeler PySceneDetect ile doğrulanır (eşik 40; düşük eşik hızlı animasyonu da kesme sanıyordu).
Kamera olayı kesme içeriyorsa elenmez, kesme noktasında bölünür.

Bilinen sınırlar:

- Yumuşak geçişler (çapraz solma) ve hızlı sahne değişimleri bazen "zoom-out" gibi kamera olayı görünebilir.
- Yaklaşık değerli olaylar (`toplam(yaklasik)`) güvenilir sayılmamalı; kritik anlarda `zoom_range` ile kareye bakın.
- Doğrudan ölçüm analiz süresini uzatır (test videosunda 2-3 dk'dan 7 dk'ya çıktı).

- Kamera olayları gözle yalnızca örnek sayfalarda doğrulandı; tamamı denetlenmedi.
  Ekran kaydı gibi içeriklerde sayfa içi yakınlaştırma da `kamera` olarak görünebilir.
- `zoom_range` içindeki `step` kare cinsindendir (saniye değil): `step=3` her 3. kare.
- Hız, videoya ve makineye göre değişir (test videosunda yaklaşık 2 dk); kesin bir hız garantisi yoktur.

Tüm çıktılar yalnızca kayıt klasörünün içine (varsayılan: program klasörü; Ayarlar sekmesinden değişir) yazılır; dışına yazma reddedilir.

### Sunucuyu elle çalıştırma (test)

```bash
python mcp_server.py
```

stdio üzerinden konuşur; stdout protokole aittir, günlükler stderr'e gider.

---

## 7. Komut satırı

```bash
# her kare, 40'lık sayfalar
python video_scrap.py --video "C:\video.mp4"

# her 5. kare, daha büyük ve net küçük resimler
python video_scrap.py --video "C:\video.mp4" --mode every_n --n 5 --thumb 384 --sharpen

# saniyede 2 kare, 6x6 düzen
python video_scrap.py --video "C:\video.mp4" --mode fps --fps 2 --cols 6 --rows 6

# sadece sahne değişimleri
python video_scrap.py --video "C:\video.mp4" --mode scene --scene-thresh 0.30 --scene-gap 0.5
```

Tüm parametreler: `python video_scrap.py --help`

---

## 8. Sorun giderme

| Belirti | Çözüm |
|---|---|
| `Video acilamadi` | Dosya bozuk veya codec yok. ffmpeg ile mp4'e çevir: `ffmpeg -i girdi.mkv -c copy cikti.mp4` |
| Sayfalar çok büyük | `--thumb 192` veya `--quality 75` düşür |
| Kareler bulanık | `--thumb 384 --sharpen` ve `--quality 92` |
| Çok yavaş | `--mode every_n --n 5` kullan; "her kare" modu diski çok yorar |
| Türkçe karakterli yol | Sorun yok, destekleniyor |
| MCP aracı görünmüyor | `python mcp_kaydet.py --goster` ile kaydı kontrol et, Desktop'ı yeniden başlat |
| MCP `ModuleNotFoundError: mcp` | `python -m pip install "mcp>=2"` |
