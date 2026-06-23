# Lofi YouTube Pipeline

Otomatik lofi müzik video üretim pipeline'ı. YouTube için 1 saatlik lofi playlist videoları üretir.

## Özellikler

- 🎵 **Müzik Üretimi**: Suno.com ile otomatik veya manuel müzik üretimi
- 🖼️ **Görsel Üretimi**: MiniMax Image-01 ile thumbnail ve arka plan görselleri
- 🎬 **Video Klipler**: MiniMax Hailuo 02 ile video segment üretimi
- ✂️ **Montaj**: FFmpeg ile ses/video birleştirme
- 📤 **YouTube Upload**: YouTube Data API v3 ile otomatik yükleme

## Kurulum

### Gereksinimler

- Python 3.11+
- FFmpeg 6.0+
- API hesapları (Suno, MiniMax, Google Cloud)

### Adımlar

```bash
# 1. Repository'yi klonla
cd /workspace/lofi-pipeline

# 2. Virtual environment oluştur
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# veya: venv\Scripts\activate  # Windows

# 3. Bağımlılıkları yükle
pip install -r requirements.txt

# 4. FFmpeg'i yükle (sistem bağımlılığı)
# Ubuntu/Debian:
sudo apt install ffmpeg

# macOS:
brew install ffmpeg

# Windows:
# https://ffmpeg.org/download.html adresinden indir ve PATH'e ekle
```

### Environment Değişkenleri

`.env` dosyası oluştur:

```bash
# Suno.com
SUNO_COOKIE="your_suno_session_cookie"
SUNO_EMAIL="your_email@example.com"
SUNO_PASSWORD="your_password"
TWOCAPTCHA_KEY="your_2captcha_api_key"

# MiniMax
MINIMAX_API_KEY="your_minimax_api_key"
MINIMAX_GROUP_ID="your_minimax_group_id"

# YouTube
YOUTUBE_CLIENT_SECRETS_FILE="client_secrets.json"
YOUTUBE_REFRESH_TOKEN="your_refresh_token"
```

> ⚠️ **Güvenlik**: `.env` dosyasını asla Git'e commit etmeyin!

## Kullanım

### Tam Pipeline Çalıştır

```bash
python main.py --full
```

### Belirli Aşamaları Çalıştır

```bash
# Sadece müzik üretimi
python main.py --music

# Sadece görsel üretimi
python main.py --visual

# Sadece video klipler
python main.py --clips

# Sadece playlist oluşturma
python main.py --playlist

# Sadece video montaj
python main.py --assemble

# Final video composition
python main.py --compose
```

### Durum Kontrolü

```bash
# Pipeline durumunu göster
python main.py --status

# Pipeline state'i resetle
python main.py --reset
```

## Pipeline Aşamaları

```
┌─────────────────────────────────────────────────────────────┐
│                    TAM PIPELINE (~6-9 saat)                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [0:00-0:30]  Konfigürasyon ve planlama                     │
│                                                              │
│  [0:30-4:00]  Müzik üretimi (Suno, 50 track)               │
│               ↓                                             │
│  [4:00-4:45]  Playlist oluşturma (FFmpeg, crossfade)        │
│                                                              │
│  [0:30-1:00]  Görsel üretimi (MiniMax Image-01, paralel)   │
│               ↓                                             │
│  [1:00-4:00]  Video klipler (MiniMax Hailuo 02, paralel)   │
│               ↓                                             │
│  [4:45-5:15]  Video montaj (FFmpeg, concat+loop)           │
│               ↓                                             │
│  [5:15-5:30]  Final assembly (ses+görsel birleştirme)      │
│               ↓                                             │
│  [5:30-5:50]  YouTube upload                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Dizin Yapısı

```
lofi-pipeline/
├── config.py              # Konfigürasyon yönetimi
├── main.py                # Ana orchestration script
├── suno_client.py         # Suno API entegrasyonu
├── minimax_client.py      # MiniMax API entegrasyonu
├── playlist_builder.py     # Playlist ve montaj mantığı
├── requirements.txt       # Python bağımlılıkları
├── README.md              # Bu dosya
│
├── config/                # Prompt ve metadata dosyaları
│   ├── prompts_music.json
│   ├── prompts_visual.json
│   └── youtube_metadata.json
│
├── music/
│   ├── raw/               # Suno'dan gelen ham dosyalar
│   ├── processed/         # İşlenmiş dosyalar
│   └── final/             # Final playlist
│
├── visual/
│   ├── thumbnails/        # YouTube thumbnail görselleri
│   ├── backgrounds/       # Arka plan görselleri
│   ├── video_clips/       # Hailuo video klipleri
│   └── final/             # Montajlanmış video
│
├── upload/
│   └── ready/             # YouTube'a yüklenecek dosyalar
│
└── logs/                  # Log dosyaları
```

## Konfigürasyon

`config.py` dosyasını düzenleyerek pipeline parametrelerini ayarlayabilirsiniz:

```python
# Pipeline ayarları
PIPELINE.target_duration_minutes = 60
PIPELINE.target_video_fps = 25

# Müzik ayarları
MUSIC.tracks_count = 50
MUSIC.bpm_range = (65, 85)
MUSIC.crossfade_seconds = 3.0

# Video ayarları
VIDEO.unique_clips = 15
VIDEO.loops_per_clip = 4
VIDEO.resolution = "768p"
```

## Maliyet Tahmini

| Kalem | Miktar | Tahmini Maliyet |
|-------|--------|-----------------|
| Suno müzik (50 track) | ~1000 kredi | $3-8 |
| MiniMax görseller | 6 adet | $0.18 |
| MiniMax videolar (15 clip) | 15 adet | $5.25 |
| **Toplam** | | **~$8-14** |

## Risk Yönetimi

### API Erişimi Yoksa

Suno API erişiminiz yoksa, `main.py` otomatik olarak manuel moda geçer:

1. Prompt dosyası oluşturulur (`config/prompts_manual.txt`)
2. Suno Web UI'de manual olarak track üretin
3. MP3 dosyalarını `music/raw/` klasörüne koyun
4. Pipeline'a devam edin

### Retry Mekanizması

Her API çağrısı `config.py` içindeki `max_retries` ile belirlenen sayıda tekrar eder. Ayrıca checkpoint mekanizması sayesinde yarıda kalan pipeline'lar kaldığı yerden devam edebilir.

## Troubleshooting

### FFmpeg Hataları

```bash
# FFmpeg'in kurulu olduğunu doğrula
ffmpeg -version

# Eksikse yükle
sudo apt install ffmpeg  # Ubuntu
brew install ffmpeg      # macOS
```

### API Bağlantı Hataları

```bash
# MiniMax quota kontrolü
python -c "from minimax_client import create_minimax_client; c = create_minimax_client(); print(c.check_quota())"

# Suno credential kontrolü
python -c "from suno_client import validate_suno_credentials; print(validate_suno_credentials())"
```

### Disk Alanı

```bash
# Pipeline çalıştırmadan önce yeterli alan kontrolü
df -h /workspace

# Ara dosyaları temizle
rm -rf /workspace/lofi-pipeline/music/processed/*
rm -rf /workspace/lofi-pipeline/visual/video_clips/*
```

## Geliştirme

```bash
# Kod formatlamak
black .

# Lint kontrolü
flake8 .

# Tip kontrolü
mypy .

# Testler
pytest
```

## Lisans

MIT License

## Katkıda Bulunma

1. Fork yap
2. Feature branch oluştur (`git checkout -b feature/yeni-ozellik`)
3. Commit (`git commit -am 'Yeni özellik eklendi'`)
4. Push (`git push origin feature/yeni-ozellik`)
5. Pull Request aç

---

*Bu pipeline, architecture.md dokümanına referans alınarak oluşturulmuştur.*