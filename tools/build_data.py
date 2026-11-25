"""Rebuild data.json and syn.json for the Audio University video search.

Usage: python3 build_data.py index_all.json ["_Caption Glossary.md"]
index_all.json is either a list of row objects keyed by the sheet's header row,
or the raw Google Sheets get_values JSON ({"values": [[header...], [row...], ...]}).
Without a glossary path, syn.json is left as it is and only data.json is rebuilt.
"""
import json
import re
import sys

SKIP_SYNONYMS = {
    'door', 'army', 'persona', 'grass', 'nick', 'skew', 'copycat', 'master plan', 'music use', 'debel',
    'radio', 'sure', 'road', 'phantom', 'wedges', 'in-ears', 'gain stage', 'studio 1', 'midi', 'middy',
    'eq', 'eqs', 'daw', 'ox', 'ax', 'oux', 'oxm', 'im', 'ms', 'raa', 'lf', 'pity', 'tamper', 'adam', "adam's",
}


def to_seconds(stamp):
    total = 0
    for part in stamp.split(':'):
        total = total * 60 + int(part)
    return total


CIRCLE = {}


def build(rows_path, glossary_path=None):
    global CIRCLE
    import os
    if os.path.exists('circle-posts.json'):
        CIRCLE = json.load(open('circle-posts.json'))
    rows = json.load(open(rows_path))
    if isinstance(rows, dict) and 'values' in rows:
        hdr = rows['values'][0]
        rows = [dict(zip(hdr, r + [''] * (len(hdr) - len(r)))) for r in rows['values'][1:]]
    out = []
    for r in rows:
        if r.get('status') != 'done' or not r.get('summary'):
            continue
        moments = []
        for part in (r.get('key_moments') or '').split('|'):
            m = re.match(r'(\d+(?::\d{1,2}){1,2})\s+(.*)', part.strip())
            if m:
                moments.append([to_seconds(m.group(1)), m.group(2).strip()])
        out.append({
            'id': r['video_id'], 't': r['title'], 'd': r['published'], 'dur': r['duration'],
            'v': int(r.get('views') or 0), 's': r['summary'],
            'tp': [x.strip() for x in (r.get('topics') or '').split(';') if x.strip()],
            'g': [re.sub(r'\s*\(sponsor\)', '', x, flags=re.I).strip() for x in (r.get('gear_brands') or '').split(';') if x.strip()],
            'km': moments,
            'c': CIRCLE.get(r['video_id'], '').replace('https://community.audiouniversityonline.com/c/learn/', ''),
        })
    json.dump(out, open('data.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    if not glossary_path:
        print(f'{len(out)} videos, {sum(len(o["km"]) for o in out)} moments (syn.json unchanged)')
        return

    syn = {}
    for line in open(glossary_path):
        m = re.match(r'- \*\*(.+?)\*\* \| (.+)', line.strip())
        if not m:
            continue
        canon = m.group(1).split('(')[0].split('/')[0].strip().lower()
        for v in m.group(2).split(','):
            v = v.strip().lower()
            if v and v != canon and len(v) > 2 and '(' not in v and v not in SKIP_SYNONYMS:
                syn[v] = canon
    json.dump(syn, open('syn.json', 'w'), separators=(',', ':'))
    print(f'{len(out)} videos, {sum(len(o["km"]) for o in out)} moments, {len(syn)} synonyms')


if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
