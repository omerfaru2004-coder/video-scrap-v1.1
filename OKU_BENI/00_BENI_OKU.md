# 0. Buradan Başla

Bu klasörde bir video analiz aracı var. Adı **Video Scrap**.

## Ne işe yarar, tek cümleyle

Bir videoyu yapay zekâya izletmek yerine, aracın hazırladığı kısa metni ve birkaç resmi okutursun.
Böylece hem video bilgisayarından çıkmaz, hem de çok az kredi harcanır.

## Nasıl çalışır, üç cümleyle

1. Araç videoyu 40 karelik sayfalara dizer (buna "kontak sayfası" deniyor).
2. Kesmeleri ve kamera hareketlerini bulup `olaylar.md` adlı bir metne yazar: "12. saniyede kesme var, 3. sayfaya bak".
3. Yapay zekâ önce o metni okur, sadece gereken sayfayı açar.

## İki kullanım yolu var

| Yol | Kim kullanır | Nasıl açılır |
|---|---|---|
| Pencere (arayüz) | Sen, elle | `BASLAT.bat` dosyasına çift tıkla |
| MCP aracı | Yapay zekâ, sohbet içinden | Bir kez bağlarsın, sonra sohbette "bu linki incele" dersin |

## Hangi dosyayı okuyacağım

Sırayla oku. Hepsi sade dille yazıldı, teknik bilgi gerekmez.

| Dosya | Ne zaman okunur |
|---|---|
| `01_KURULUM.md` | **İlk iş.** Programı bilgisayara kurmak için |
| `02_KULLANIM_KILAVUZU.md` | Kurulum bittikten sonra. Hangi düğme ne yapar, dosyalar nereye gider |
| `03_YAPAY_ZEKAYA_BAGLAMA.md` | Yapay zekâya bağlamak istersen |
| `04_GITHUB_YAYIN.md` | Projeyi GitHub'a yüklemek istersen |
| `05_TEKNIK_DETAYLAR.md` | Merak edersen. Analizin nasıl çalıştığı, sınırlar, komut satırı |

Yapay zekâ ajanı kullanıyorsan (Claude Code, Codex, Gemini CLI) ek olarak şu dosyalar var:
`../CLAUDE.md`, `../AGENTS.md`, `../GEMINI.md`. Bunlar ajanın projeyi tanıması için; senin okumana gerek yok.

## En kısa yol (acele edenler için)

1. `01_KURULUM.md` içindeki 3 adımı yap.
2. `BASLAT.bat` dosyasına çift tıkla.
3. Linki kutuya yapıştır, **İncele**'ye bas.
4. **Sonuç klasörünü aç** düğmesine bas, `olaylar.md` dosyasını oku.

Bir şey ters giderse: `01_KURULUM.md` dosyasının en altındaki **Sorun giderme** tablosuna bak.
