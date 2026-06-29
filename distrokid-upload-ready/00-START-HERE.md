# 🎵 DistroKid Yükleme Paketi — Başlangıç Rehberi

## Drive'da Her Şey Hazır

Tüm dosyalar şu adreste:
**🔗 https://drive.google.com/drive/folders/19IanQTdzZo5bRaLOJ49TenWGPP3zc7v5**

## DistroKid'e Yükleme (Manuel)

⚠️ **Önemli:** DistroKid'in otomatik yükleme API'si yok. Her şey distrokid.com üzerinden manuel yapılacak.

### Plan
1. **3 Ana Albüm** (her kanal için 1 master):
   - TheLoFi: "Cozy Hours"
   - LofiNippon: "Matsuri Dreams" 
   - FlyChill: "Late Hours"

2. **14 Video Albümü** (her video için 1):
   - YouTube video = ayrı albüm
   - Farklı DistroKid release'leri olarak

### Adım 1: DistroKid'e Kayıt

1. https://distrokid.com/signup
2. **$22.99/yıl unlimited plan** (sınırsız albüm/track)
3. Hesap aç → login

### Adım 2: Her Albüm İçin Yükle

Drive'dan aç:
```
📁 TheLoFi → {video_id klasörü} → cover.jpg + tracks/
```

Sonra distrokid.com'da:

1. **"Add new release"** tıkla
2. **Album type:** Album (not Single/EP)
3. **Album title:** ilgili klasörün `album.json` dosyasından kopyala
4. **Cover art:** Drive'dan `cover.jpg` indir → upload
5. **Tracks:** Drive'dan `tracks/` klasöründeki MP3'leri sırayla yükle
   - Her track için Title alanına sadece parça adını yaz
   - Part I/II ayrı track olarak yüklenir
6. **Genre:** `Lo-Fi Hip-Hop` (veya Japanese Lo-Fi)
7. **Stores:** Tümünü seç (Spotify, Apple Music, YouTube Music, vb.)
8. **Submit** — $0 ek (zaten üye oldun)

### Toplam Yükleme

| Tür | Sayı | Ücret |
|-----|------|-------|
| Video Albümleri | 14 | $0 (sınırsız) |
| Master Albümler | 3 | $0 (sınırsız) |
| **Toplam Release** | **17** | **$22.99/yıl** |

17 albüm × ~10-20 track = ~250 track toplam.

## Track İsimleri — Hızlı Bakış

### TheLoFi (Cozy Hours)
1. Lamplight Reverie
2. Patina Window
3. Skybound Pages
4. Cobblestone Hours
5. Skylight Pages
6. Dusty Margins
7. Golden Overlook
8. Lantern Drift
9. Paper Lanterns
10. Maple Confession
(Part I ve Part II ayrı = 20 track)

### LofiNippon (Matsuri Dreams)
1. Tanuki Steps
2. Matsuri Glow
3. Bamboo Rain
4. Lantern Alley
5. Tea Garden Hush
6. Tatami Window
(Part I/II/III = 18 track)

### FlyChill (Late Hours)
1. Lamp Glow
2. Skylight Café
3. Night Window
4. Paper Cups
5. Corner Table
(Part I/II = 10 track)

## Dosya Yapısı

Bu klasörde (`/workspace/distrokid-upload-ready/`):

```
├── 00-START-HERE.md (bu dosya)
├── thelofi_DISTROKID.csv / .tsv
├── lofinippon_DISTROKID.csv / .tsv
├── flychill_DISTROKID.csv / .tsv
└── {video_id}_GUIDE.md (her video için detaylı rehber)
```

CSV/TSV'ler Excel/Google Sheets'te açılabilir — oradan kopyala-yapıştır.

## Hızlı Başlangıç

**Sıra önerisi:**
1. **TheLoFi Cozy Hours** (en popüler kanal, en çok albüm potansiyeli)
2. **LofiNippon Matsuri Dreams**
3. **FlyChill Late Hours**
4. Sonra video albümleri (her biri tek başına release)

Her biri ~15-30 dakika sürer. 17 albüm = ~5-8 saat toplam.

