# YouTube Manual Localization Helper

The YouTube Data API v3 does NOT support adding localizations to existing (already-uploaded) videos via PUT update. This is a known API limitation.

## For videos that need multi-language via YouTube Studio:

1. Go to https://studio.youtube.com/
2. Click on a video → "Details" (left sidebar)
3. Click "Add Language" button (top right, in description section)
4. Select each language:
   - Spanish (Español)
   - Chinese (中文)
   - Hindi (हिन्दी)
   - Arabic (العربية)
   - French (Français)
5. Enter translated title + description for each
6. Save

## Languages to add (5 most spoken besides English):
- Spanish: code `es`
- Mandarin: code `zh-Hans`
- Hindi: code `hi`
- Arabic: code `ar`
- French: code `fr`

## Videos that need manual localization:
TheLoFi channel (UCpdnbfS3UL-_bKr_8uJGYxQ):
- HuaUcIvsBzU (1 Hour+ Cozy Lofi Vibes)
- dWKkNIjl0ZQ (1 Hour+ Cozy Lofi Vibes Beats)
- b-KqcNGuW3E (1 Hour Smooth Rainy Lo-Fi)
- SEF4f2SNgNI (1 Hour+ Japanese Lo-Fi)
- 7IhGTiy19T8 (Midnight Waves Koto)
- ebUnCJwxBBY (African Lo-Fi)
- And older videos

LoFiNippon channel (UCEXLQ3tlpMu4TWnHojfEP7g):
- KTAC886oDWg (1 Hour+ Japanese Lo-Fi Beats)
- mNgeBtWHgtA (1 Hour+ Japanese Lo-Fi Beats Sakura)
- WhhStj51U74 (1 Hour Japanese Lo-Fi Mix)
- WNk1mx0AU2U (1 Hour+ Japanese Lo-Fi Beats)
- IppKTe-eQB4 (Japanese Lofi Hip Hop Mix)
- Older videos

## For NEW videos uploaded via upload-localized.py:
Localizations are automatically added during initial upload.
