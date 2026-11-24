"""Rebuild data.json and syn.json for the Audio University video search.

Usage: python3 build_data.py index_all.json "_Caption Glossary.md"
index_all.json is a list of row objects keyed by the sheet's header row.
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


def build(rows_path, glossary_path):
    rows = json.load(open(rows_path))
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
            'g': [x.strip() for x in (r.get('gear_brands') or '').split(';') if x.strip()],
            'km': moments,
        })
    json.dump(out, open('data.json', 'w'), ensure_ascii=False, separators=(',', ':'))

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
    build(sys.argv[1], sys.argv[2])
