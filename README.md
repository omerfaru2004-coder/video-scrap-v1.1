# Video Scrap v1.1

Videoyu yapay zekâya **az token** harcayarak analiz ettirir.

Nasıl? Video modele gitmez. Araç videoyu 40 karelik "kontak sayfalarına" dizer, kesmeleri ve kamera
hareketlerini zaman damgalı bir `olaylar.md` metnine yazar. Yapay zekâ önce o metni okur, sadece
gereken sayfayı görüntü olarak açar.

- Tamamen yerel: video bilgisayarından çıkmaz, analiz kredi harcamaz.
- Link ver, gerisini araç yapsın: indirir, `videolar/videoN` klasörüne koyar, analiz eder.
- Basit pencere (Windows) ve yerel **MCP sunucusu** (Abacus, Claude, Gemini CLI, ChatGPT/Codex).
- Aynı link ikinci kez verilirse yeniden indirilmez.

## 2 adımda kurulum

Gerekenler: Python 3.10+ ve internet. Başka bir şey kurmana, dosya kopyalamana gerek yok:
ffmpeg dahil bütün paketleri kurulum kendisi getirir.

1. **Python kur** — https://www.python.org/downloads/ adresinden indir. Kurulum ekranında
   **"Add python.exe to PATH"** kutusunu işaretle. Bu kutu işaretlenmezse hiçbir şey çalışmaz.
2. **Projeyi al ve kur** — Bu klasörü indir (veya `git clone`), sonra:

   ```bat
   KUR.bat
   BASLAT.bat
   ```

`KUR.bat` gerekli paketleri ve ffmpeg'i proje içindeki `.venv` klasörüne kurar; sistemine dokunmaz.
Python hiç yoksa `KUR.bat` winget ile kurmayı dener. `BASLAT.bat` pencereyi açar, konsol penceresi görünmez.

Yapay zekâ ajanına "kur" demen yeterli: ajan `python kur.py` çalıştırır, aynı kurulumu yapar.
Durum kontrolü: `python kur.py --kontrol`.

## Kullanım

1. `BASLAT.bat` dosyasına çift tıkla.
2. **Video İncele** sekmesindeki kutuya YouTube linkini yapıştır.
3. **İncele** düğmesine bas. İndirme + analiz kendiliğinden başlar.
4. Bitince **Sonuç klasörünü aç** ile çıktıya git.

Sonuç: `videolar/<klasör>/analiz/olaylar.md`, `sheets/`, `yakin_cekim/`.

Yapay zekâya bağlamak için arayüzdeki **Yapay Zekaya Bağla** sekmesini kullan veya
`OKU_BENI/03_YAPAY_ZEKAYA_BAGLAMA.md` dosyasına bak.

## Dokümantasyon

Hepsi [`OKU_BENI/`](OKU_BENI/00_BENI_OKU.md) klasöründe, sade dille yazıldı:

| Dosya | Konu |
|---|---|
| `00_BENI_OKU.md` | Nereden başlanır, hangi dosya ne işe yarar |
| `01_KURULUM.md` | Sıfırdan kurulum, adım adım |
| `02_KULLANIM_KILAVUZU.md` | Hangi düğme ne yapar, dosyalar nereye kaydedilir |
| `03_YAPAY_ZEKAYA_BAGLAMA.md` | Abacus, Claude, Gemini, ChatGPT/Codex bağlantısı |
| `04_GITHUB_YAYIN.md` | Projeyi GitHub'a yükleme |
| `05_TEKNIK_DETAYLAR.md` | Analiz yöntemi, sınırlar, komut satırı |

## Geliştirme

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests -q          # 26 test
python dogrula_baglam.py           # 19 kontrol, çıkış kodu 0 = geçti
python _verify_mcp.py              # MCP sunucusunu stdio üzerinden dener
```

Değişiklikler: [CHANGELOG.md](CHANGELOG.md).

## GitHub'a yükleme

Depo hazır. GitHub'da boş bir depo aç (README ekleme), sonra proje klasöründe:

```bat
git remote add origin https://github.com/<kullanici-adin>/video-scrap.git
git push -u origin main
```

İlk gönderimde tarayıcıdan GitHub girişi istenir; şifre veya token yazman gerekmez.
Ayrıntı: `OKU_BENI/04_GITHUB_YAYIN.md`.

## Bilinen sınırlar

- Kamera hareketi ölçümleri yaklaşık değerler içerebilir (`toplam(yaklasik)` etiketli olaylara güvenme, `zoom_range` ile kareye bak).
- Yumuşak geçişler bazen kamera olayı gibi görünebilir.
- Arayüz Windows için yazıldı ve test edildi.

## Lisans

MIT, bkz. [LICENSE](LICENSE).
