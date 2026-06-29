#!/usr/bin/env python3
"""
Seasonal content detection - returns overrides for current date/season.
Used by upload-smart.py to inject seasonal themes.
"""
import datetime
from typing import Optional

# Date-based seasonal definitions
# Format: (start_date, end_date, season_id, prompt_modifier, title_prefix, tag_additions, color_palette)
SEASONS = [
    # (month, day) ranges
    ((1, 1), (1, 15), 'new_year', 'cozy winter wonderland, fresh start energy, gentle hope',
        'New Year Lofi', ['new year', 'january lofi', 'fresh start', 'cozy winter'], 
        {'accent': 'gold', 'mood': 'hopeful'}),
    ((1, 16), (2, 14), 'winter_study', 'snow falling outside, fireplace warmth, focused study',
        'Winter Lofi', ['winter lofi', 'snow', 'fireplace', 'cozy winter study'],
        {'accent': 'cool blue', 'mood': 'cozy'}),
    ((2, 15), (3, 15), 'exam_prep', 'intense study focus, library quiet, exam season energy',
        'Exam Lofi', ['exam music', 'study focus', 'library', 'concentration'],
        {'accent': 'purple', 'mood': 'focused'}),
    ((3, 16), (4, 30), 'spring', 'cherry blossom, spring rain, renewal',
        'Spring Lofi', ['spring lofi', 'cherry blossom', 'sakura', 'rain'],
        {'accent': 'pink', 'mood': 'fresh'}),
    ((5, 1), (6, 15), 'spring_exam', 'finals crunch, intense focus, all-nighter energy',
        'Finals Lofi', ['finals week', 'all nighter', 'study hard', 'cramming'],
        {'accent': 'red', 'mood': 'urgent'}),
    ((6, 16), (8, 31), 'summer_chill', 'summer night, warm breeze, vacation vibes',
        'Summer Lofi', ['summer lofi', 'beach', 'warm night', 'vacation'],
        {'accent': 'orange', 'mood': 'chill'}),
    ((9, 1), (9, 30), 'back_to_school', 'new semester, fresh notebooks, library return',
        'Back to School Lofi', ['back to school', 'study music', 'new semester', 'library'],
        {'accent': 'warm amber', 'mood': 'productive'}),
    ((10, 1), (10, 31), 'halloween', 'spooky cozy, autumn leaves, halloween night',
        'Halloween Lofi', ['halloween lofi', 'spooky', 'autumn', 'pumpkin'],
        {'accent': 'orange', 'mood': 'spooky'}),
    ((11, 1), (12, 15), 'winter_exam', 'Turkey exam season (YKS/LGS/KPSS), intense focus',
        'Exam Lofi', ['turkish exam', 'yks', 'lgs', 'kpss', 'study hard', 'cramming'],
        {'accent': 'deep blue', 'mood': 'focused'}),
    ((12, 16), (12, 31), 'christmas', 'cozy christmas, snow, fireplace, holiday warmth',
        'Christmas Lofi', ['christmas lofi', 'holiday', 'cozy christmas', 'snow'],
        {'accent': 'red + green', 'mood': 'cozy'}),
]

# Channel-specific seasonal priorities
CHANNEL_SEASON_FOCUS = {
    'thelofi': ['christmas', 'halloween', 'summer_chill', 'back_to_school', 'exam_prep', 'winter_exam'],
    'lofinippon': ['spring', 'winter_study', 'summer_chill', 'new_year', 'winter_exam', 'exam_prep'],
    'flychill': ['exam_prep', 'spring_exam', 'winter_exam', 'back_to_school', 'summer_chill', 'halloween'],
}

def get_current_season(date=None):
    if date is None:
        date = datetime.datetime.utcnow()
    month, day = date.month, date.day
    for (sm, sd), (em, ed), sid, modifier, prefix, tags, palette in SEASONS:
        if (month, day) >= (sm, sd) and (month, day) <= (em, ed):
            return {
                'id': sid,
                'modifier': modifier,
                'title_prefix': prefix,
                'tags': tags,
                'palette': palette,
                'date': date.strftime('%Y-%m-%d'),
            }
    return None

def get_seasonal_titles(channel, season):
    if not season:
        return []
    prefix = season['title_prefix']
    base = [
        f"1 Hour {prefix} Beats to Study, Sleep & Relax | Cozy Vibes",
        f"Late Night {prefix} | Cozy Room & Melancholic Beats",
        f"{prefix} Mix | Soft Piano & Rain Ambience",
        f"{prefix} Hip Hop Radio | Slow Beats for Focus",
        f"Chill {prefix} | Warm Light & Quiet Night",
        f"{prefix} Sleep Music | Window Rain & Cozy Mood",
        f"Cozy {prefix} Beats | Coffee, Books & Slow Evening",
        f"{prefix} Chillhop | Late Hours & Soft Piano",
    ]
    return base

def get_seasonal_tags(channel, season):
    if not season:
        return []
    base_tags = list(season['tags'])
    return base_tags

def get_seasonal_thumbnail_modifier(season):
    """Add seasonal elements to thumbnail prompt"""
    if not season:
        return ''
    modifiers = {
        'new_year': ' with subtle golden fireworks in distant background',
        'winter_study': ' with soft snow falling outside window, warm fireplace glow',
        'exam_prep': ' with stacks of books on desk, intense focused lighting',
        'spring': ' with cherry blossom petals drifting past window, fresh green tones',
        'spring_exam': ' with stressed study mood, notes scattered on desk',
        'summer_chill': ' with warm sunset orange light, summer evening mood',
        'back_to_school': ' with fresh notebooks and new textbooks, motivated energy',
        'halloween': ' with subtle pumpkin glow, autumn leaves, cozy spooky mood',
        'winter_exam': ' with deep snow outside, intense study lamp, all-nighter feel',
        'christmas': ' with subtle Christmas tree lights, snow falling, warm holiday glow',
    }
    return modifiers.get(season['id'], '')

def main():
    """Test seasonal detection"""
    import sys
    test_date = sys.argv[1] if len(sys.argv) > 1 else None
    if test_date:
        date = datetime.datetime.strptime(test_date, '%Y-%m-%d')
    else:
        date = None
    season = get_current_season(date)
    print(f'Current date: {date or datetime.datetime.utcnow().strftime("%Y-%m-%d")}')
    print(f'Season: {season}')
    print()
    for ch in ['thelofi', 'lofinippon', 'flychill']:
        titles = get_seasonal_titles(ch, season)
        tags = get_seasonal_tags(ch, season)
        print(f'--- {ch} ---')
        print(f'  Sample titles: {titles[:2]}')
        print(f'  Tags: {tags[:3]}')

if __name__ == '__main__':
    main()
