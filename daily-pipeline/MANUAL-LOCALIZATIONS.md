# YouTube Manuel Localization Rehberi

## Neden Otomatik Yapamıyoruz?

YouTube Data API v3, **mevcut (yüklenmiş) bir videoya PUT ile localization eklemeye İZİN VERMİYOR**.

Test sonuçları (2026-06-29 12:14 UTC):
- `videos.update` API'sine `snippet.localizations` gönderildi
- Response 200 OK döndü
- Ama GET ile kontrol edildiğinde `localizations` field BOŞ kaldı
- Hatta title "placeholder" olarak değiştirildi (manuel düzeltildi)

**YouTube bu özelliği sadece initial POST upload'da destekliyor.**

## Manuel Ekleme Adımları (YouTube Studio)

Her video için ~2 dakika:

1. https://studio.youtube.com adresine git
2. Sol menüden **İçerik** (Content) → ilgili videoyu seç
3. Sol panelden **Translations** veya **Subtitles** sekmesi
4. **"Add Language"** butonuna tıkla
5. Aşağıdaki 5 dili sırayla ekle:

| Dil | Kod | Örnek Başlık |
|---|---|---|
| 🇪🇸 Spanish | `es` | "1 Hora de Lofi Beats para Estudiar, Dormir y Relajarse" |
| 🇨🇳 Mandarin | `zh-Hans` | "1小时 Lofi 音乐 学习 睡眠 放松" |
| 🇮🇳 Hindi | `hi` | "1 घंटे Lofi बीट्स - पढ़ाई, नींद और आराम" |
| 🇸🇦 Arabic | `ar` | "ساعة من موسيقى Lofi للدراسة والنوم" |
| 🇫🇷 French | `fr` | "1 Heure de Beats Lofi pour Étudier, Dormir & Se Détendre" |

6. Her dil için başlık + açıklama gir
7. **Save** veya **Publish** tıkla

## Videolar Listesi (Manuel Ekleme Gerekli)

### TheLoFi (@The-Lo-Fi)
- HuaUcIvsBzU - "1 Hour+ Cozy Lofi Vibes to Sleep Study Focus | Late Night Ra..." (yayında)
- dWKkNIjl0ZQ - "1 Hour+ Cozy Lofi Vibes Beats to Sleep Study Focus | Anime G..." (yayında)
- b-KqcNGuW3E - "1 Hour Smooth Rainy Lo-Fi 🌧️ Beats to Sleep, Study & Focus..." (yayında)
- SEF4f2SNgNI - "Lofi Hip Hop Beats to Study, Sleep & Relax | Rainy Window..." (scheduled)
- CX6rdBybflU - ✅ ZATEN VAR (5 dil API ile eklendi)

### LoFiNippon (@lofinippon)
- WhhStj51U74 - "1 Hour Japanese Lo-Fi Mix for Sleep and Study" (yayında)
- mNgeBtWHgtA - "1 Hour+ Japanese Lo-Fi Beats to Sleep Study Focus | Sakura, ..." (yayında)
- KTAC886oDWg - "1 Hour+ Japanese Lo-Fi Beats to Sleep Study Focus | Sakura, ..." (yayında)
- WNk1mx0AU2U - scheduled
- 4WIfrWLWlk0 - ✅ ZATEN VAR (5 dil API ile eklendi)

### FlyChill (@FlyChill)
Zernio üzerinden yüklendi - Zernio API multi-language desteklemiyor.
Manuel ekleme veya Zernio'nun kendi arayüzünden yapılabilir.

## Zaman Tahmini

| Kanal | Video Sayısı | Süre (2dk/video) |
|---|---|---|
| TheLoFi | 4 video | ~8 dakika |
| LoFiNippon | 4 video | ~8 dakika |
| FlyChill | ~5 video | ~10 dakika |
| **TOPLAM** | **~13 video** | **~26 dakika** |

## Alternatif: Re-upload

Eğer YouTube Studio çok uzun gelirse, videoları silip yeniden yükle:
- `upload-localized.py` ile yeni upload otomatik 5 dil ekler
- AMA: tüm view/like istatistikleri silinir
- Ve yeni video yeni ID alır (eski linkler kırılır)

**Önerim**: Manuel ekleme. 26 dakika ama kalıcı çözüm.
