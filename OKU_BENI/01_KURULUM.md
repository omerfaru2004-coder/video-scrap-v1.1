# 1. Kurulum (adım adım)

Bu sayfayı baştan sona sırayla yap. Atlama yapma. Her adımda ne göreceğini yazdım.

Kurulum **proje klasörünün içine** yapılır. Sistemindeki Python'a hiçbir şey eklenmez.
Elle dosya kopyalaman, ayrıca ffmpeg kurman gerekmez: kurulum onu da kendi getirir.

---

## Adım 1: Python kur

Python, programın çalışması için gereken motor. Tek seferlik.

1. Tarayıcıda şu adresi aç: https://www.python.org/downloads/
2. Büyük sarı **Download Python** düğmesine bas.
3. İndirilen dosyaya çift tıkla.
4. **ÇOK ÖNEMLİ:** Açılan ilk ekranın en altında **"Add python.exe to PATH"** yazan bir kutu var.
   Bu kutuyu **mutlaka işaretle**. İşaretlemezsen program "python bulunamadı" der.
5. **Install Now** düğmesine bas, bitmesini bekle, **Close**'a bas.

**Kontrol:** Başlat menüsüne `cmd` yaz, açılan siyah pencerede şunu yaz ve Enter'a bas:

```bat
python --version
```

`Python 3.11.9` gibi bir yazı görmelisin. "tanınmıyor" diyorsa kutuyu işaretlemeyi unutmuşsun:
Python'u kaldır, baştan kur, kutuyu işaretle.

> Python hiç kurmak istemiyorsan: `KUR.bat` bunu senin yerine denemeye çalışır (winget ile).
> Yine de en sağlamı bu adımı elle yapmaktır.

---

## Adım 2: Projeyi bilgisayara al

İki yol var, birini seç.

**Yol A — ZIP ile (git bilmiyorsan bunu seç):**
Proje klasörünü ZIP olarak indir, sağ tık → **Tümünü ayıkla**. Çıkan klasörün içine gir.

**Yol B — git ile:**

```bat
git clone https://github.com/<kullanici-adin>/video-scrap.git
cd video-scrap
```

---

## Adım 3: Kur (tek çift tık)

Proje klasörünün içindeki **`KUR.bat`** dosyasına çift tıkla.

Ne oluyor: `.venv` adında bir klasör açılır, gerekli paketler **ve ffmpeg** oraya kurulur.
İnternetten indirme yapıldığı için 1-3 dakika sürebilir. Siyah pencerede satırlar akar, bu normaldir.

**Bittiğinde** şu yazıyı görürsün:

```
Hazir. ffmpeg: ...\.venv\...\ffmpeg.exe
BASLAT.bat ile uygulamayi acabilirsin.
```

Pencere "Devam etmek için bir tuşa basın" derse bir tuşa bas, kapanır.

İkinci kez çift tıklarsan hiçbir şey indirmez, sadece "Paketler zaten kurulu" der. Zararsızdır.

---

## Adım 4: Programı aç

**`BASLAT.bat`** dosyasına çift tıkla.

- Siyah konsol penceresi **açılmaz**, doğrudan uygulama penceresi gelir. Bu normal.
- Pencerenin üstünde renkli bir banner, altında sekmeler görürsün.
- Bir hata olursa uygulama sana mesaj kutusu gösterir, sessizce kapanmaz.

Açıldıysa kurulum bitti. Şimdi `02_KULLANIM_KILAVUZU.md` dosyasına geç.

---

## Yapay zekâya kurdur (üşenenler için)

Bilgisayarında Claude Code, Codex, Gemini CLI gibi bir yapay zekâ ajanı varsa kurulumu o yapar.
Proje klasörünü aç ve ajana tek cümle yaz:

```
kur
```

Ajan `AGENTS.md` / `CLAUDE.md` dosyasındaki talimatı okur ve `python kur.py` çalıştırır.
Senin yapman gereken tek şey sonunda `BASLAT.bat` dosyasına çift tıklamak olur.

Elle çalıştırmak istersen:

```bat
python kur.py
```

Sadece "kurulu mu?" diye bakmak için:

```bat
python kur.py --kontrol
```

---

## İsteğe bağlı: konuşmayı yazıya dökme

`transcribe_video` aracı videodaki konuşmayı yazıya çevirir. Bunun için ayrı ve ağır bir paket gerekir.
Sadece ihtiyacın varsa kur:

```bat
.venv\Scripts\python -m pip install openai-whisper
```

GPU yoksa `small` modeli kullanılır, ilk çalıştırmada model indirilir. Kurmazsan diğer her şey çalışır.

---

## Sorun giderme

| Ne görüyorsun | Ne yapacaksın |
|---|---|
| `python` tanınmıyor | Python'u kaldır, baştan kur, "Add python.exe to PATH" kutusunu işaretle, siyah pencereyi kapat-aç |
| `ModuleNotFoundError: No module named ...` | `KUR.bat` çalıştır, sonra `BASLAT.bat` ile aç |
| `KUR.bat` "Python kurulamadi" diyor | Python'u https://www.python.org/downloads/ adresinden elle kur, kutuyu işaretle, `KUR.bat`'a tekrar çift tıkla |
| `KUR.bat` paket indirirken hata verdi | İnterneti kontrol et, `KUR.bat`'a tekrar çift tıkla; sorun sürerse `python kur.py --yenile` çalıştır |
| ffmpeg hatası | `KUR.bat`'a tekrar çift tıkla; ffmpeg `.venv` içine yeniden kurulur |
| YouTube linki okunamadı | `.venv\Scripts\python -m pip install -U yt-dlp` |
| Pencere hiç açılmıyor | Proje klasöründe siyah pencerede `python video_scrap.py` çalıştır, hata yazısını oku |
| `KUR.bat` hata verdi | Siyah penceredeki son 10 satırı oku; genelde internet veya PATH sorunudur |

Hâlâ olmuyorsa: `05_TEKNIK_DETAYLAR.md` dosyasına bak veya proje sahibine siyah penceredeki
hata metnini gönder.
