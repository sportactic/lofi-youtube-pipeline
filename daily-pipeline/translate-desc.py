#!/usr/bin/env python3
"""Translate descriptions to top 5 most-spoken languages using Gemini Flash"""
import os, sys, json
import urllib.request
import urllib.error

GEMINI_KEY = 'AIzaSyDAWUrkq5q1emAOM5EOa1WTNnkd8IplV8o'

# Top 5 most spoken languages (besides English) for global reach
# Sources: Ethnologue 2025 + YouTube regional penetration
LANGS = {
    'es': 'Spanish (Español)',
    'zh': 'Mandarin Chinese (中文)',
    'hi': 'Hindi (हिन्दी)',
    'ar': 'Arabic (العربية)',
    'fr': 'French (Français)',
}

def translate(text, target_lang):
    """Translate text using Gemini Flash"""
    prompt = f"""Translate the following YouTube video description into {LANGS[target_lang]}. Keep it natural and engaging. Preserve all emojis, hashtags, and line breaks. Do NOT add explanations - return ONLY the translated text.

Text to translate:
{text}"""
    
    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}'
    body = {
        'contents': [{
            'parts': [{'text': prompt}]
        }]
    }
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.load(r)
            return data['candidates'][0]['content']['parts'][0]['text'].strip()
    except urllib.error.HTTPError as e:
        print(f'  {target_lang} HTTP {e.code}: {e.read().decode()[:200]}')
        return None
    except Exception as e:
        print(f'  {target_lang} error: {e}')
        return None

def main():
    channel = sys.argv[1] if len(sys.argv) > 1 else 'thelofi'
    en_file = f'/workspace/daily-pipeline/desc-{channel}-en.txt'
    if not os.path.exists(en_file):
        print(f'No English description at {en_file}')
        sys.exit(1)
    en_text = open(en_file).read()
    
    print(f'Translating {channel} description to {len(LANGS)} languages...')
    translations = {'en': en_text}
    for code in LANGS:
        print(f'  {code} ({LANGS[code]})...', end=' ', flush=True)
        t = translate(en_text, code)
        if t:
            translations[code] = t
            print(f'OK ({len(t)} chars)')
        else:
            print('FAILED')
    
    # Output combined description
    # YouTube allows multi-language descriptions via "Description (English): ... Description (Spanish): ..." or via tags
    # Best practice: combine all in one description with clear language separators
    combined = en_text + '\n\n---\n\n'
    for code, txt in translations.items():
        if code == 'en':
            continue
        combined += f'\n[{code.upper()}]\n{txt}\n\n'
    
    out_path = f'/workspace/daily-pipeline/desc-{channel}-multilang.txt'
    with open(out_path, 'w') as f:
        f.write(combined)
    print(f'Combined description saved: {out_path} ({len(combined)} chars)')
    
    # Save individual translations too
    for code, txt in translations.items():
        with open(f'/workspace/daily-pipeline/desc-{channel}-{code}.txt', 'w') as f:
            f.write(txt)

if __name__ == '__main__':
    main()
