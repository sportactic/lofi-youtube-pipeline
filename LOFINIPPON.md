# LoFi Nippon Channel Pipeline

**Channel:** [@lofinippon](https://www.youtube.com/@lofinippon) (LoFi Nippon)
**Channel ID:** `UCEXLQ3tlpMu4TWnHojfEP7g`
**Style:** Japanese traditional lo-fi (koto, shamisen, shakuhachi)
**Visual style:** Anime girl in kimono + tanuki mascot
**Color palette:** Sakura pink + indigo + gold leaf

## Setup
1. OAuth client saved to mavis secret: `YOUTUBE_NIPPON_CLIENT_SECRETS_JSON`
2. Channel handle saved: `YOUTUBE_NIPPON_CHANNEL_HANDLE`
3. Channel ID saved: `YOUTUBE_NIPPON_CHANNEL_ID`
4. Refresh token placeholder: `YOUTUBE_NIPPON_REFRESH_TOKEN` (PENDING_OAUTH_FLOW)

## Files
- `lofinippon/CONFIG.md` — full channel plan and separation rules
- `lofinippon/oauth-nippon.py` — OAuth flow for @lofinippon (separate from TheLoFi)
- `lofinippon/upload-nippon.py` — upload script (uses YOUTUBE_NIPPON_* secrets)
- `lofinippon/visual-style-nippon.md` — visual prompt templates
- `lofinippon/suno-prompts-nippon.md` — Suno prompt templates

## Separation Rules (DO NOT MIX)
| Aspect | @The-Lo-Fi | @lofinippon |
|---|---|---|
| Channel ID | `UCpdnbfS3UL-_bKr_8uJGYxQ` | `UCEXLQ3tlpMu4TWnHojfEP7g` |
| Mascot | Green chameleon | Tanuki (raccoon dog) |
| Outfit | Hoodie/sweater | Kimono/yukata |
| Color | Warm amber + teal | Sakura pink + indigo |
| Secrets prefix | `YOUTUBE_*` | `YOUTUBE_NIPPON_*` |

## Next Steps
1. Run `oauth-nippon.py` on a machine with browser access to get refresh token
2. Save refresh token to mavis secret `YOUTUBE_NIPPON_REFRESH_TOKEN`
3. Generate Japanese-themed tracks in Suno (user manual)
4. Generate Japanese-themed visuals
5. Build and upload first video
