# 3. Yapay Zekaya Bağlama (yerel MCP)

Video Scrap, **yerel (stdio) MCP sunucusu** olarak çalışır: yapay zekâ uygulaması `mcp_server.py` dosyasını
bilgisayarında kendisi başlatır. İnternete açılan bir sunucu yoktur.

Her bağlantıda iki değer lazım. Arayüzde **Yapay Zekaya Bağla** sekmesi bunları senin yolunla doldurup hazır verir.

| Değer | Örnek |
|---|---|
| Python yolu (`command`) | `C:/Users/<sen>/.../video-scrap-v1.1/.venv/Scripts/python.exe` (`.venv` yoksa `python`) |
| Sunucu dosyası (`args`) | `C:/Users/<sen>/.../video-scrap-v1.1/mcp_server.py` |

Yollarda `\` yerine `/` kullan (JSON'da `\` hata verir). Bağlantıdan sonra uygulamayı **tamamen kapatıp** yeniden aç.

---

## 1) Abacus Desktop / Code

```bash
python mcp_kaydet.py
```

Kayıt `C:\Users\<sen>\.abacusai\mcp.json` dosyasına `video-scrap` adıyla yazılır, diğer sunucular korunur,
dosyanın yedeği alınır. Sonra Abacus'ta MCP ekranında **İçeri aktar**'a bas. Kontrol: `python mcp_kaydet.py --goster`.
Kaldırmak: `python mcp_kaydet.py --kaldir`.

## 2) Claude

**Claude Desktop:** En kolayı arayüzde **Yapay Zekaya Bağla > Claude Desktop > Claude Desktop'a otomatik kaydet**
düğmesi; dosyayı kendisi yazar (yedek alır, diğer sunucuları korur). Elle yapmak için
Settings > Developer > Edit Config. Açılan `claude_desktop_config.json` dosyasına ekle:

```json
{
  "mcpServers": {
    "video-scrap": {
      "command": "C:/YOL/video scrap/.venv/Scripts/python.exe",
      "args": ["C:/YOL/video scrap/mcp_server.py"]
    }
  }
}
```

Dosyada zaten `mcpServers` varsa sadece `"video-scrap": {...}` bloğunu içine ekle. Claude Desktop'u tamamen kapat, aç;
sohbet kutusundaki araç simgesinde `video-scrap` görünmeli.

**Claude Code (terminal):**

```bash
claude mcp add video-scrap -s user -e VIDEO_SCRAP_HOME="C:/YOL/video-scrap-v1.1" -- "C:/YOL/video-scrap-v1.1/.venv/Scripts/python.exe" "C:/YOL/video-scrap-v1.1/mcp_server.py"
claude mcp get video-scrap
claude mcp list
```

`-s user` kaydı tüm projelerde görünür yapar; `-e VIDEO_SCRAP_HOME` aracın hangi klasörü kök
alacağını belirler. Kaydı silmek için: `claude mcp remove video-scrap -s user`.

Kayıt eski bir klasörü gösteriyorsa `claude mcp get video-scrap` çıktısındaki yolu kontrol et;
yanlışsa silip yukarıdaki komutla yeniden ekle.

**Ücretsiz seçenekler:** Claude Code oturumu ücretli bir plan ister. Oturum açmadan bağlamı
sınamak için `python dogrula_baglam.py` kullan (aşağıdaki bölüm). Gemini CLI ücretsiz kotayla
çalışır ve proje kökündeki `GEMINI.md` dosyasını kendisi okur; Codex CLI `AGENTS.md` dosyasını okur.
Her iki dosya da `CLAUDE.md`'ye yönlendirir, ayrı bakım gerekmez.

## Ücretsiz bağlam doğrulaması (oturum gerekmez)

`CLAUDE.md` içindeki iddiaları gerçek depoyla karşılaştırır; model çağırmaz, kredi harcamaz.

```bash
python dogrula_baglam.py              # ozet
python dogrula_baglam.py --ayrintili  # her kontrolun ayrintisi
```

Kontroller: araç sayısı ve adları `mcp_server.py` ile aynı mı, giriş noktaları ve rehberler var mı,
`.gitignore` kullanıcı verisini dışlıyor mu, `git ls-files` temiz mi, `mcp_kaydet.py` ve `incele.py`
çalışıyor mu, MCP kaydı bu klasörü mü gösteriyor. Çıkış kodu 0 = tutarlı, 1 = uyuşmazlık.

## 3) Gemini (Gemini CLI)

`C:\Users\<sen>\.gemini\settings.json` dosyasını aç (yoksa oluştur) ve ekle:

```json
{
  "mcpServers": {
    "video-scrap": {
      "command": "C:/YOL/video scrap/.venv/Scripts/python.exe",
      "args": ["C:/YOL/video scrap/mcp_server.py"]
    }
  }
}
```

Gemini CLI'ı aç, `/mcp` yaz: `video-scrap` ve araçları listelenmeli. Gemini'nin tarayıcıdaki web sürümü yerel
MCP çalıştıramaz; bunun için Gemini CLI kullan.

## 4) ChatGPT / OpenAI Codex

ChatGPT **masaüstü uygulaması**, Codex CLI ve IDE eklentisi aynı dosyayı kullanır:
`C:\Users\<sen>\.codex\config.toml`. Dosyaya ekle:

```toml
[mcp_servers.video-scrap]
command = "C:/YOL/video scrap/.venv/Scripts/python.exe"
args = ["C:/YOL/video scrap/mcp_server.py"]
startup_timeout_sec = 30
```

Ya da terminalden: `codex mcp add video-scrap -- "C:/YOL/video scrap/.venv/Scripts/python.exe" "C:/YOL/video scrap/mcp_server.py"`.
Uygulamayı yeniden başlat. Not: tablo adı `mcp_servers` (alt çizgili) olmalı; `mcpServers` yazarsan yok sayılır.
**chatgpt.com (web)** yerel MCP'yi doğrudan çalıştıramaz; masaüstü uygulama veya Codex kullan.

> Bu bölümlerdeki yapılandırma biçimleri 27 Kasım 2026 tarihinde resmi/ikincil dokümanlara bakılarak yazıldı.
> Uygulamalar sık güncellenir; menü adları değişmişse ilgili uygulamanın MCP yardım sayfasına bak.

---

## Yapay zekâya ne yazmalıyım?

Bağlandıktan sonra sohbete doğal dille yaz. Örnekler:

**Link analizi**
> Bu videoyu incele: https://youtu.be/XXXX
> Analiz bitince olaylar.md'yi oku ve geçişleri, animasyonları ve kamera hareketlerini zaman damgasıyla listele.
> Sadece gerçekten gerektiğinde sayfa aç (kredi tutumlu ol).

**Belirli bir ana yakından bakma**
> 12. ile 18. saniye arasındaki zoom hareketine zoom_range ile yakından bak ve ölçeği/yönünü söyle.

**Aynı videoyu tekrar sorma**
> Daha önce incelediğimiz videoları listele, video2'nin olaylar.md dosyasını oku ve en uzun geçişi bul.

**Konuşma ile görüntüyü birleştirme**
> video3'ün konuşma dökümünü çıkar (transcribe_video) ve hangi cümlede hangi görsel değişiklik olduğunu eşleştir.

**Kısa kural (her sohbetin başına yapıştırabilirsin)**
> video-scrap MCP aracını kullan. Link verirsem incele_video çağır, job_status ile bitmesini bekle,
> önce olaylar.md metnini oku, görsel sayfaları (view_sheet) yalnızca gerekirse aç. Emin olmadığın yerde bunu belirt.

## Çalışmıyorsa

| Belirti | Çözüm |
|---|---|
| Araç listede yok | Uygulamayı tamamen kapat/aç; yolları `/` ile yazdığını ve `python.exe` yolunun doğru olduğunu kontrol et |
| `ModuleNotFoundError: mcp` | `.venv\Scripts\python -m pip install -r requirements.txt` |
| Zaman aşımı | İlk açılışta yavaş olabilir; Codex'te `startup_timeout_sec` değerini artır |
| "Yazma sadece kayıt klasörü içinde" hatası | Normal güvenlik kuralı; çıktıyı kayıt klasörü içinde iste (Ayarlar sekmesinden kökü değiştirebilirsin) |
