#!/usr/bin/env python3
"""
Upload with YouTube's built-in multi-language localizations.
YouTube auto-selects the right language for each viewer based on their location/settings.
"""
import os, sys, json, urllib.request, urllib.parse
import urllib.error
import random

def get_access_token(refresh_token, client_id, client_secret):
    data = urllib.parse.urlencode({
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token',
    }).encode()
    req = urllib.request.Request(
        'https://oauth2.googleapis.com/token',
        data=data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)['access_token']

# Pre-translated titles and descriptions for each channel
# Format: language_code -> {"title": "...", "description": "..."}
# We use YouTube's localization keys: es, zh-Hans, hi, ar, fr (top 5 most spoken besides English)

TRANSLATIONS = {
    'thelofi': {
        'en': {
            'title': '1 Hour Lofi Beats to Study, Sleep & Relax | Cozy Rain Night Vibes',
            'description': '🌧️ Cozy Lofi Hip Hop for studying, sleeping, and unwinding\n\n1 hour of warm, melancholic lofi beats featuring rain on windows, soft piano, vinyl crackle, and the quiet intimacy of a late-night study session.\n\n🌙 What\'s inside:\n• Rain ambience\n• Warm lamp lighting\n• Soft piano & jazzy chords\n• Cozy room atmosphere\n• Vinyl crackle texture\n\n☕ Best for:\n• Deep work & studying\n• Late-night relaxation\n• Sleep & meditation\n• Reading & writing\n• Quiet coffee shop vibes\n\n🎧 Headphones recommended.\n\n#Lofi #StudyMusic #ChillBeats #RainSounds #1HourLofi'
        },
        'es': {
            'title': '1 Hora de Lofi Beats para Estudiar, Dormir y Relajarse | Vibras de Lluvia',
            'description': '🌧️ Lofi Hip Hop acogedor para estudiar, dormir y desconectar\n\n1 hora de ritmos lofi cálidos y melancólicos con lluvia en ventanas, piano suave, crujido de vinilo y la íntima tranquilidad de una sesión de estudio nocturna.\n\n🌙 Qué encontrarás:\n• Ambiente de lluvia\n• Luz cálida de lámpara\n• Piano suave y acordes de jazz\n• Atmósfera acogedora\n• Textura de vinilo\n\n☕ Ideal para:\n• Trabajo profundo y estudio\n• Relajación nocturna\n• Sueño y meditación\n• Lectura y escritura\n\n🎧 Se recomiendan auriculares.\n\n#Lofi #MusicaParaEstudiar #ChillBeats #Lluvia #1HoraLofi'
        },
        'zh-Hans': {
            'title': '1小时 Lofi 音乐 学习 睡眠 放松 | 舒适雨夜氛围',
            'description': '🌧️ 舒适的 Lofi Hip Hop,适合学习、睡眠和放松\n\n1小时温暖、忧郁的 lofi 节拍,雨声、柔和的钢琴、黑胶唱片的噼啪声,以及深夜学习的宁静亲密感。\n\n🌙 内容:\n• 雨声环境\n• 温暖的灯光\n• 柔和的钢琴和爵士和弦\n• 舒适的房间氛围\n• 黑胶质感\n\n☕ 适合:\n• 深度工作和学习\n• 深夜放松\n• 睡眠和冥想\n• 阅读和写作\n\n🎧 推荐使用耳机。\n\n#Lofi #学习音乐 #ChillBeats #雨声 #1小时Lofi'
        },
        'hi': {
            'title': '1 घंटे Lofi बीट्स - पढ़ाई, नींद और आराम | आरामदायक बारिश की रात',
            'description': '🌧️ पढ़ाई, सोने और आराम के लिए आरामदायक Lofi Hip Hop\n\n1 घंटे के गर्म, उदास lofi बीट्स - खिड़की पर बारिश, मुलायम पियानो, विनाइल की आवाज़, और देर रात की पढ़ाई का शांत माहौल।\n\n🌙 इसमें क्या है:\n• बारिश का माहौल\n• गर्म लैंप की रोशनी\n• मुलायम पियानो और जैज़ chords\n• आरामदायक कमरे का माहौल\n\n☕ इसके लिए बेहतर:\n• गहरा काम और पढ़ाई\n• देर रात आराम\n• नींद और ध्यान\n• पढ़ने और लिखने\n\n🎧 हेडफ़ोन की सिफारिश।\n\n#Lofi #स्टडीम्यूज़िक #चिलबीट्स #बारिश'
        },
        'ar': {
            'title': 'ساعة من موسيقى Lofi للدراسة والنوم والاسترخاء | أجواء مريحة تحت المطر',
            'description': '🌧️ موسيقى Lofi Hip Hop مريحة للدراسة والنوم والاسترخاء\n\nساعة من إيقاعات lofi الدافئة والحزينة مع المطر على النوافذ والبيانو الناعم وصوت الفينيل والأجواء الهادئة لجلسات الدراسة الليلية.\n\n🌧️ يتضمن:\n• أجواء المطر\n• إضاءة المصباح الدافئة\n• بيانو ناعم وألحان الجاز\n• أجواء الغرفة المريحة\n\n☕ مناسب لـ:\n• العمل العميق والدراسة\n• الاسترخاء الليلي\n• النوم والتأمل\n• القراءة والكتابة\n\n🎧 يفضل استخدام سماعات الأذن.\n\n#Lofi #موسيقى_الدراسة #تشيل_بيتس #مطر'
        },
        'fr': {
            'title': '1 Heure de Beats Lofi pour Étudier, Dormir & Se Détendre | Nuit Pluvieuse Cosy',
            'description': '🌧️ Lofi Hip Hop cosy pour étudier, dormir et se détendre\n\n1 heure de beats lofi chaleureux et mélancoliques avec pluie sur les fenêtres, piano doux, crépitement du vinyle et l\'intimité tranquille d\'une session d\'étude tardive.\n\n🌙 Au programme:\n• Ambiance pluvieuse\n• Éclairage chaud de lampe\n• Piano doux et accords jazzy\n• Atmosphère cosy\n• Texture vinyle\n\n☕ Parfait pour:\n• Travail profond et études\n• Détente nocturne\n• Sommeil et méditation\n• Lecture et écriture\n\n🎧 Casque recommandé.\n\n#Lofi #MusiqueÉtude #ChillBeats #Pluie #1HeureLofi'
        },
    },
    'lofinippon': {
        'en': {
            'title': '1 Hour Lofi Beats to Study, Sleep & Relax | Japanese Sakura Night',
            'description': '🌸 Japanese Lofi Hip Hop for studying, sleeping, and unwinding\n\n1 hour of serene, traditional Japanese-inspired lofi beats. Lantern light, sakura petals, tatami rooms, and the peaceful sound of bamboo rain.\n\n🌙 What\'s inside:\n• Sakura petals ambience\n• Paper lantern glow\n• Koto & traditional Japanese instruments\n• Bamboo rain texture\n• Tatami room atmosphere\n\n☕ Best for:\n• Meditation & zen\n• Studying & focus\n• Sleep & relaxation\n• Tea ceremony ambience\n• Anime watching\n\n🎧 Headphones recommended.\n\n#Lofi #JapaneseLofi #Sakura #StudyMusic #ChillBeats'
        },
        'es': {
            'title': '1 Hora de Lofi Beats para Estudiar, Dormir y Relajarse | Noche de Cerezos',
            'description': '🌸 Lofi Hip Hop japonés para estudiar, dormir y desconectar\n\n1 hora de serenos beats lofi inspirados en Japón tradicional. Luz de linternas, pétalos de sakura, habitaciones de tatami y el sonido pacífico de la lluvia de bambú.\n\n🌙 Qué encontrarás:\n• Ambiente de pétalos de sakura\n• Brillo de linterna de papel\n• Koto e instrumentos japoneses\n• Textura de lluvia de bambú\n• Atmósfera de tatami\n\n☕ Ideal para:\n• Meditación y zen\n• Estudio y concentración\n• Sueño y relajación\n\n🎧 Se recomiendan auriculares.\n\n#Lofi #LofiJapones #Sakura #MusicaParaEstudiar'
        },
        'zh-Hans': {
            'title': '1小时 Lofi 音乐 学习 睡眠 放松 | 日式樱花之夜',
            'description': '🌸 日式 Lofi Hip Hop,适合学习、睡眠和放松\n\n1小时宁静、传统的日式 lofi 节拍。灯笼光、樱花瓣、榻榻米房间,以及竹林雨的宁静之声。\n\n🌙 内容:\n• 樱花瓣环境\n• 纸灯笼光\n• 古筝和传统日本乐器\n• 竹林雨声\n• 榻榻米房间氛围\n\n☕ 适合:\n• 冥想和禅修\n• 学习专注\n• 睡眠和放松\n• 茶道氛围\n• 看动漫\n\n🎧 推荐使用耳机。\n\n#Lofi #日式Lofi #樱花 #学习音乐'
        },
        'hi': {
            'title': '1 घंटे Lofi बीट्स - पढ़ाई, नींद और आराम | जापानी साकुरा रात',
            'description': '🌸 पढ़ाई, सोने और आराम के लिए जापानी Lofi Hip Hop\n\n1 घंटे के शांत, पारंपरिक जापानी-प्रेरित lofi बीट्स। लालटेन की रोशनी, साकुरा की पंखुड़ियाँ, तातामी कमरे, और बांस की बारिश की शांत आवाज़।\n\n🌙 इसमें क्या है:\n• साकुरा पंखुड़ियों का माहौल\n• कागज़ की लालटेन की चमक\n• कोतो और पारंपरिक जापानी वाद्ययंत्र\n• बांस की बारिश\n\n☕ इसके लिए बेहतर:\n• ध्यान और ज़ेन\n• पढ़ाई और एकाग्रता\n• नींद और आराम\n\n🎧 हेडफ़ोन की सिफारिश।\n\n#Lofi #जापानी_लोफी #साकुरा #स्टडीम्यूज़िक'
        },
        'ar': {
            'title': 'ساعة من موسيقى Lofi للدراسة والنوم | ليلة يابانية بالكرز',
            'description': '🌸 موسيقى Lofi Hip Hop يابانية للدراسة والنوم والاسترخاء\n\nساعة من إيقاعات lofi الهادئة المستوحاة من اليابان التقليدية. ضوء الفوانيس وبتلات الساكورا وغرف التاتامي وصوت هطول الأمطار على الخيزران.\n\n🌙 يتضمن:\n• أجواء بتلات الساكورا\n• توهج الفوانيس الورقية\n• آلات يابانية تقليدية\n• صوت أمطار الخيزران\n• أجواء غرف التاتامي\n\n☕ مناسب لـ:\n• التأمل والزن\n• الدراسة والتركيز\n• النوم والاسترخاء\n\n🎧 يفضل استخدام سماعات الأذن.\n\n#Lofi #لوفي_ياباني #ساكورا #موسيقى_الدراسة'
        },
        'fr': {
            'title': '1 Heure de Beats Lofi pour Étudier, Dormir & Se Détendre | Nuit Japonaise Sakura',
            'description': '🌸 Lofi Hip Hop japonais pour étudier, dormir et se détendre\n\n1 heure de beats lofi sereins inspirés du Japon traditionnel. Lumière des lanternes, pétales de sakura, pièces en tatami et le son paisible de la pluie sur le bambou.\n\n🌙 Au programme:\n• Ambiance pétales de sakura\n• Lueur de lanterne en papier\n• Koto et instruments japonais traditionnels\n• Pluie sur le bambou\n• Atmosphère tatami\n\n☕ Parfait pour:\n• Méditation et zen\n• Études et concentration\n• Sommeil et détente\n\n🎧 Casque recommandé.\n\n#Lofi #LofiJaponais #Sakura #MusiqueÉtude'
        },
    },
    'flychill': {
        'en': {
            'title': '1 Hour Lofi Beats to Study, Sleep & Relax | Rainy Window Night',
            'description': '🌃 Chill Lofi Hip Hop for studying, sleeping, and unwinding\n\n1 hour of urban, melancholic lofi beats. Rain-streaked windows, city bokeh lights, soft piano, and the contemplative mood of late-night cityscape views.\n\n🌙 What\'s inside:\n• Rain on glass texture\n• City lights bokeh\n• Soft piano & ambient pads\n• Late-night urban atmosphere\n• Contemplative mood\n\n☕ Best for:\n• Late-night focus\n• Studying & deep work\n• Sleep & relaxation\n• Reading & writing\n• Coding sessions\n\n🎧 Headphones recommended.\n\n#Lofi #ChillBeats #StudyMusic #SleepMusic #CityLofi'
        },
        'es': {
            'title': '1 Hora de Lofi Beats para Estudiar, Dormir y Relajarse | Noche de Ventana Lluviosa',
            'description': '🌃 Lofi Hip Hop chill para estudiar, dormir y desconectar\n\n1 hora de beats lofi urbanos y melancólicos. Ventanas empañadas de lluvia, luces bokeh de la ciudad, piano suave y el ambiente contemplativo de las vistas nocturnas urbanas.\n\n🌙 Qué encontrarás:\n• Sonido de lluvia en cristal\n• Luces de ciudad bokeh\n• Piano suave y pads ambientales\n• Atmósfera urbana nocturna\n• Estado de ánimo contemplativo\n\n☕ Ideal para:\n• Concentración nocturna\n• Estudiar y trabajo profundo\n• Sueño y relajación\n\n🎧 Se recomiendan auriculares.\n\n#Lofi #ChillBeats #MusicaParaEstudiar #LofiUrbano'
        },
        'zh-Hans': {
            'title': '1小时 Lofi 音乐 学习 睡眠 放松 | 雨夜窗景',
            'description': '🌃 适合学习、睡眠和放松的 Chill Lofi Hip Hop\n\n1小时都市、忧郁的 lofi 节拍。雨痕斑驳的窗户、城市散景灯光、柔和的钢琴,以及深夜城市景观的沉思氛围。\n\n🌙 内容:\n• 玻璃上的雨声质感\n• 城市灯光散景\n• 柔和的钢琴和环境音垫\n• 深夜都市氛围\n• 沉思的情绪\n\n☕ 适合:\n• 深夜专注\n• 学习和深度工作\n• 睡眠和放松\n• 阅读和写作\n• 编程\n\n🎧 推荐使用耳机。\n\n#Lofi #ChillBeats #学习音乐 #城市Lofi'
        },
        'hi': {
            'title': '1 घंटे Lofi बीट्स - पढ़ाई, नींद और आराम | बारिश की रात, खिड़की का दृश्य',
            'description': '🌃 पढ़ाई, सोने और आराम के लिए चिल Lofi Hip Hop\n\n1 घंटे के शहरी, उदास lofi बीट्स। बारिश से भीगी खिड़कियाँ, शहर की bokeh lights, मुलायम पियानो, और देर रात के शहर के विचारशील माहौल।\n\n🌙 इसमें क्या है:\n• काँच पर बारिश की आवाज़\n• शहर की रोशनी का bokeh\n• मुलायम पियानो और ambient pads\n• देर रात का शहरी माहौल\n\n☕ इसके लिए बेहतर:\n• देर रात एकाग्रता\n• पढ़ाई और गहरा काम\n• नींद और आराम\n\n🎧 हेडफ़ोन की सिफारिश।\n\n#Lofi #चिल_बीट्स #स्टडीम्यूज़िक #शहरी_लोफी'
        },
        'ar': {
            'title': 'ساعة من موسيقى Lofi للدراسة والنوم | نافذة ممطرة ليلية',
            'description': '🌃 موسيقى Chill Lofi Hip Hop للدراسة والنوم والاسترخاء\n\nساعة من إيقاعات lofi الحضرية والحزينة. نوافذ مبللة بالمطر وأضواء bokeh للمدينة وبيانو ناعم وأجواء التأمل في مناظر المدينة الليلية.\n\n🌙 يتضمن:\n• صوت المطر على الزجاج\n• أضواء المدينة bokeh\n• بيانو ناعم وأصوات محيطة\n• أجواء حضرية ليلية\n\n☕ مناسب لـ:\n• التركيز في وقت متأخر من الليل\n• الدراسة والعمل العميق\n• النوم والاسترخاء\n\n🎧 يفضل استخدام سماعات الأذن.\n\n#Lofi #تشيل_بيتس #موسيقى_الدراسة #لوفي_حضري'
        },
        'fr': {
            'title': '1 Heure de Beats Lofi pour Étudier, Dormir & Se Détendre | Nuit Pluvieuse Fenêtre',
            'description': '🌃 Chill Lofi Hip Hop pour étudier, dormir et se détendre\n\n1 heure de beats lofi urbains et mélancoliques. Fenêtres striées de pluie, lumières bokeh de la ville, piano doux et ambiance contemplative des vues nocturnes de la ville.\n\n🌙 Au programme:\n• Son de pluie sur verre\n• Lumières de ville bokeh\n• Piano doux et pads ambiants\n• Atmosphère urbaine nocturne\n• Humeur contemplative\n\n☕ Parfait pour:\n• Concentration tardive\n• Études et travail profond\n• Sommeil et détente\n\n🎧 Casque recommandé.\n\n#Lofi #ChillBeats #MusiqueÉtude #LofiUrbain'
        },
    },
}

def upload_localized_youtube(cfg, video_path, channel, thumbnail_path=None):
    """Upload with full multi-language localizations"""
    token = get_access_token(cfg['refresh_token'], cfg['client_id'], cfg['client_secret'])
    
    translations = TRANSLATIONS[channel]
    en = translations['en']
    
    # Pick title from one of the 10 variations (use English as base)
    titles_en = [
        "1 Hour Lofi Beats to Study, Sleep & Relax | Cozy Rain Night Vibes",
        "Late Night Lofi Hip Hop | Cozy Room, Rain Window & Coffee",
        "Chill Lofi Mix | Rain on Glass, Warm Lamp & Reading Vibes",
        "Lofi Hip Hop Radio | Soft Piano, Melancholy Night & Coffee Steam",
        "Rainy Night Lofi | Cozy Study Beats to Focus & Unwind",
        "Slow Lofi Beats | Melancholic Evenings, Vinyl Crackle & Rain",
        "Lofi Sleep Music | Late Night Window Rain & Quiet Room",
        "Cozy Lofi Hip Hop | Warm Lamp, Books & Midnight Rain",
        "Calm Lofi Mix | Late Hours, Tea Steam & Soft Piano",
        "Lofi Chill Beats | Rainy Window, Coffee & Quiet Study Night",
    ]
    if channel == 'lofinippon':
        titles_en = [
            "1 Hour Lofi Beats to Study, Sleep & Relax | Japanese Sakura Night",
            "和風ローファイ | 桜の夜、提灯と静かな雨音",
            "Japanese Lofi Hip Hop | Lantern Night, Sakura & Bamboo Rain",
            "和ロフィー | 静寂の茶屋、雨音と竹林の夜",
            "Tokyo Lofi Beats | Tanuki Lanterns, Tatami & Night Rain",
            "禅ローファイ | 桜の夜、提灯と畳の静けさ",
            "Sakura Night Lofi | Japanese Garden, Lanterns & Soft Koto",
            "Lo-Fi Japonés | Flores de Cerezo, Linternas & Lluvia Suave",
            "Lo-Fi Japonais | Jardin Zen, Lanterne & Pluie Douce",
            "Yume Lofi | Japanese Night, Maple Leaves & Tea Ceremony",
        ]
    elif channel == 'flychill':
        titles_en = [
            "1 Hour Lofi Beats to Study, Sleep & Relax | Rainy Window Night",
            "Chill Lofi Mix | City Rain, Window Lights & Late Night",
            "Lofi Hip Hop Radio | Neon Streets, Rain Drops & Melancholy",
            "Late Night Lofi | Coffee Shop Rain, City Glow & Soft Piano",
            "Urban Lofi Chill | Rainy Window, Bokeh Lights & Quiet Hours",
            "Lofi Sleep Music | City Night, Distant Lights & Soft Beats",
            "Moody Lofi Mix | Window Rain, Lavender Light & Slow Piano",
            "Lofi Hip Hop Beats | City Window, Rain & Midnight Glow",
            "Chillhop Lofi | Neon Rain, Coffee Steam & Late Night Vibes",
            "Quiet Lofi | Cityscape Rain, Warm Light & Reflective Beats",
        ]
    
    # Pick random title and update EN translation
    chosen_title_en = random.choice(titles_en)
    translations['en']['title'] = chosen_title_en
    
    # Build localizations (excluding English which is the default)
    localizations = {}
    for lang_code, content in translations.items():
        if lang_code == 'en':
            continue
        localizations[lang_code] = {
            'title': content['title'],
            'description': content['description'],
        }
    
    # Default snippet (English)
    metadata = {
        'snippet': {
            'title': translations['en']['title'],
            'description': translations['en']['description'],
            'tags': _get_tags(channel),
            'categoryId': '10',
            'defaultLanguage': 'en',
            'defaultAudioLanguage': 'en',
            'localizations': localizations,  # YouTube picks based on user location!
        },
        'status': {
            'privacyStatus': 'private',
            'publishAt': cfg.get('publish_at'),
            'embeddable': True,
            'license': 'youtube',
            'selfDeclaredMadeForKids': False,
            'madeForKids': False,
            'publicStatsViewable': True,
        }
    }
    
    file_size = os.path.getsize(video_path)
    init_req = urllib.request.Request(
        f'https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status,localizations',
        data=json.dumps(metadata).encode(),
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json; charset=UTF-8',
            'X-Upload-Content-Type': 'video/mp4',
            'X-Upload-Content-Length': str(file_size),
        },
        method='POST'
    )
    with urllib.request.urlopen(init_req, timeout=30) as r:
        upload_url = r.headers.get('Location')
    
    print(f'  Uploading {file_size/1024/1024:.1f}MB with {len(localizations)} language localizations...')
    with open(video_path, 'rb') as f:
        upload_req = urllib.request.Request(
            upload_url,
            data=f.read(),
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'video/mp4'},
            method='PUT'
        )
    with urllib.request.urlopen(upload_req, timeout=1800) as r:
        result = json.load(r)
    
    video_id = result['id']
    print(f'  ✓ Uploaded: https://youtube.com/watch?v={video_id}')
    print(f'    Title: {translations["en"]["title"]}')
    print(f'    Languages: EN (default) + {", ".join(localizations.keys())}')
    
    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            _upload_thumbnail(token, video_id, thumbnail_path)
        except Exception as e:
            print(f'    Thumbnail: {e}')
    
    return result

def _upload_thumbnail(token, video_id, image_path):
    with open(image_path, 'rb') as f:
        req = urllib.request.Request(
            f'https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={video_id}',
            data=f.read(),
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'image/jpeg'},
            method='POST'
        )
    with urllib.request.urlopen(req, timeout=60) as r:
        json.load(r)
    print(f'    ✓ Thumbnail uploaded')

def _get_tags(channel):
    return {
        'thelofi': ['lofi', 'lo-fi', 'lofi hip hop', 'chill beats', 'study music', 'sleep music', 'rain sounds', 'cozy room', 'late night', 'relaxing music', 'chillhop', 'lofi mix', '1 hour lofi', 'study beats', 'focus music', 'calm music', 'melancholic', 'piano lofi', 'jazz lofi', 'vinyl crackle'],
        'lofinippon': ['lofi', 'lo-fi', 'japanese lofi', 'study music', 'sleep music', 'sakura', 'lantern', 'tatami', 'zen music', 'chill beats', 'relaxing music', 'bamboo rain', 'japanese aesthetic', 'anime lofi', 'koto', 'tea ceremony', 'meditation', 'calm music'],
        'flychill': ['lofi', 'lo-fi', 'chill beats', 'study music', 'sleep music', 'rain music', 'city lofi', 'urban chill', 'chillhop', 'late night', 'melancholic', 'city lights', 'bokeh', 'relaxing music', 'focus music', '1 hour lofi', 'deep focus', 'coding music', 'rainy window', 'contemplative'],
    }[channel]

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('channel', choices=['thelofi', 'lofinippon', 'flychill'])
    parser.add_argument('video', help='Path to video file')
    parser.add_argument('--publish-at', help='ISO 8601 UTC')
    parser.add_argument('--thumbnail', help='Path to thumbnail')
    args = parser.parse_args()
    
    if args.channel == 'thelofi':
        cs = json.loads(os.environ['YOUTUBE_CLIENT_SECRETS_JSON'])
        cfg = {
            'refresh_token': os.environ['YOUTUBE_REFRESH_TOKEN'],
            'client_id': cs['installed']['client_id'],
            'client_secret': cs['installed']['client_secret'],
            'publish_at': args.publish_at,
        }
    elif args.channel == 'lofinippon':
        cs = json.load(open('/workspace/attachments/e21e0110__33902dd3-6a6a-479e-bbc0-b0e01f6406e3.json'))
        cfg = {
            'refresh_token': os.environ['YOUTUBE_NIPPON_REFRESH_TOKEN'],
            'client_id': cs['installed']['client_id'],
            'client_secret': cs['installed']['client_secret'],
            'publish_at': args.publish_at,
        }
    else:
        print(f'Use upload-smart.py for FlyChill (Zernio)')
        sys.exit(1)
    
    print(f'=== Localized Upload to {args.channel} ===')
    upload_localized_youtube(cfg, args.video, args.channel, args.thumbnail)

if __name__ == '__main__':
    main()
