"""Build members.json: a privacy-preserving index of members-only course lessons.

Usage: python3 tools/build_members.py COURSES_JSON MAP_JSON VTT_DIR [syn.json]

The public page must never contain course text, so each lesson is stored as
30-second windows of hashed words (and hashed word pairs). The page hashes the
visitor's search the same way and can tell which lesson, and roughly where in
it, a topic comes up, without the lesson's words being readable in the file.
"""
import json
import os
import re
import sys

STOP = set('''a about above after again against all also am an and any are as at be because been before being
below between both but by can could did do does doing don't down during each even every few for from further get
gets getting go goes going gonna got had has have having he her here hers herself him himself his how i i'd i'll
i'm i've if in into is it it's its itself just kind let let's like little lot make makes making me might more most
much my myself need no nor not now of off oh ok okay on once one only or other our ours ourselves out over own
pretty really right said same say says see she should so some something sort still such sure take than that that's
the their theirs them themselves then there there's these they they're thing things think this those through to
too um uh up us use used using very want was way we we'll we're we've well were what what's when where which while
who whom why will with would yeah yes you you'd you'll you're you've your yours yourself yourselves actually
basically maybe probably definitely literally'''.split())
TOKEN = re.compile(r"[a-z0-9][a-z0-9'+\-]*[a-z0-9+]|[a-z0-9]")
WINDOW = 30


def stem(t):
    t = re.sub(r"'s$", '', t)
    if len(t) > 5 and t.endswith('ing'):
        return t[:-3]
    if len(t) > 4 and t.endswith('ed'):
        return t[:-2]
    if len(t) > 3 and t.endswith('s') and not t.endswith('ss'):
        return t[:-1]
    return t


def fnv(s):
    h = 0x811c9dc5
    for b in s.encode('utf-8'):
        h ^= b
        h = (h * 0x01000193) & 0xffffffff
    return format(h >> 8, 'x')


def tokens(text, syn_res):
    s = ' ' + text.lower() + ' '
    for r, canon in syn_res:
        s = r.sub(lambda m: m.group(1) + canon, s)
    out = []
    for t in TOKEN.findall(s):
        t = t.strip(".'-")
        if not t or t in STOP:
            continue
        out.append(stem(t))
    return out


def parse_vtt(text):
    cues = []
    blocks = re.split(r'\n\s*\n', text.replace('\r', ''))
    for b in blocks:
        m = re.search(r'(\d+):(\d+):(\d+)[.,]\d+\s*-->', b) or re.search(r'(\d+):(\d+)[.,]\d+\s*-->', b)
        if not m:
            continue
        g = [int(x) for x in m.groups()]
        sec = g[0] * 3600 + g[1] * 60 + g[2] if len(g) == 3 else g[0] * 60 + g[1]
        body = b[m.end():].split('\n', 1)[1] if '\n' in b[m.end():] else ''
        body = re.sub(r'<[^>]+>', ' ', body)
        cues.append((sec, body))
    return cues


def build(courses_path, map_path, vtt_dir, syn_path='syn.json'):
    courses = json.load(open(courses_path))
    lmap = json.load(open(map_path))
    syn = json.load(open(syn_path)) if os.path.exists(syn_path) else {}
    syn_res = [(re.compile(r'(^|[^a-z0-9])' + re.escape(k) + r'(?=$|[^a-z0-9])'), v)
               for k, v in sorted(syn.items(), key=lambda kv: -len(kv[0]))]
    course_keys = list(courses.keys())
    lessons = []
    for o in lmap:
        path = os.path.join(vtt_dir, f"{o['lesson']}.vtt")
        if not os.path.exists(path):
            continue
        cues = parse_vtt(open(path, encoding='utf-8', errors='replace').read())
        if not cues:
            continue
        wins = {}
        for sec, body in cues:
            wins.setdefault(sec // WINDOW * WINDOW, []).append(body)
        hw = []
        for start in sorted(wins):
            toks = tokens(' '.join(wins[start]), syn_res)
            hs = {fnv(t) for t in toks}
            hs |= {fnv(a + ' ' + b) for a, b in zip(toks, toks[1:])}
            if hs:
                hw.append([start, ' '.join(sorted(hs))])
        c = courses[o['course']]
        sec_name = c['section_names'].get(str(o['section']), '')
        pos = [x[0] for x in c['sections'][str(o['section'])]].index(o['lesson'])
        lessons.append({
            'c': course_keys.index(o['course']), 'id': o['lesson'], 's': int(o['section']),
            'n': o['name'], 'sn': sec_name, 'o': pos, 'dur': cues[-1][0],
            'nt': ' '.join(sorted({fnv(t) for t in tokens(o['name'] + ' ' + sec_name, syn_res)})),
            'w': hw,
        })
    out = {'courses': [{'slug': courses[k]['slug'], 't': courses[k]['title']} for k in course_keys],
           'lessons': lessons}
    json.dump(out, open('members.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print(f"{len(lessons)} lessons, {os.path.getsize('members.json') // 1024} KB")


if __name__ == '__main__':
    build(*sys.argv[1:])
