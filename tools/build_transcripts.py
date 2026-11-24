"""Build transcripts.json for Video Finder's moment search.

Usage: python3 tools/build_transcripts.py TRANSCRIPT_DIR [data.json] [syn.json]

TRANSCRIPT_DIR holds the library's .md files (one per video, with a
video_id line in the front matter and "[m:ss] text" caption lines).
Only videos listed in data.json are included. Each caption line becomes
[seconds, "token token ..."] with stopwords and filler removed and caption
misspellings mapped to their canonical spelling (from syn.json), so the
page can point a search at the exact line where a term comes up.
"""
import glob
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
basically maybe probably definitely literally going'''.split())

STAMP = re.compile(r'\[(\d+(?::\d{1,2}){1,2})\]')
TOKEN = re.compile(r"[a-z0-9][a-z0-9'.+\-/]*[a-z0-9+]|[a-z0-9]")


def to_seconds(stamp):
    total = 0
    for part in stamp.split(':'):
        total = total * 60 + int(part)
    return total


def build(src, data_path='data.json', syn_path='syn.json'):
    keep = {v['id'] for v in json.load(open(data_path))}
    syn = json.load(open(syn_path)) if os.path.exists(syn_path) else {}
    syn_res = [(re.compile(r'(^|[^a-z0-9])' + re.escape(k) + r'(?=$|[^a-z0-9])'), v)
               for k, v in sorted(syn.items(), key=lambda kv: -len(kv[0]))]
    out = {}
    for path in glob.glob(os.path.join(src, '*.md')):
        text = open(path, encoding='utf-8', errors='replace').read()
        m = re.search(r'video_id:\s*(\S+)', text)
        if not m or m.group(1) not in keep:
            continue
        vid = m.group(1)
        body = text.split('---', 2)[-1]
        parts = STAMP.split(body)
        lines = []
        for i in range(1, len(parts) - 1, 2):
            sec = to_seconds(parts[i])
            s = parts[i + 1].lower().replace('\n', ' ')
            s = re.sub(r'\[(music|applause|laughter|__)\]', ' ', s)
            for r, canon in syn_res:
                if canon in s:
                    continue
                s = r.sub(lambda mm: mm.group(1) + canon, s)
            toks = [t.strip(".'") for t in TOKEN.findall(s)]
            toks = [t for t in toks if t and t not in STOP and not t.isdigit() or (t.isdigit() and len(t) >= 2)]
            toks = [t for t in toks if t not in STOP]
            if toks:
                lines.append([sec, ' '.join(toks)])
        if lines:
            out[vid] = lines
    json.dump(out, open('transcripts.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    n = sum(len(v) for v in out.values())
    print(f'{len(out)} videos, {n} caption lines, {os.path.getsize("transcripts.json")//1024} KB')


if __name__ == '__main__':
    build(*sys.argv[1:])
