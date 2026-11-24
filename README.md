# Audio University Video Finder

A static search page for Audio University's YouTube library. Members type a question and get the videos that cover it, with links that jump to the exact moment.

Live: https://audiouniversityonline-sketch.github.io/video-search/ (GitHub Pages, branch `main`, root folder)
Embedded in Circle with `circle-embed-snippet.html` (Custom HTML block).

## Files
- `index.html`: the page. Search runs in the browser; no server and no API calls.
- `data.json`: one record per video: id, title, date, duration, views, summary, topic tags, gear/brands, key moments `[seconds, description]`.
- `syn.json`: caption misspelling map (variant to canonical) so "Newman" finds Neumann.
- `build_data.py`: rebuilds `data.json` and `syn.json` from the index sheet export and the caption glossary.

## Where the data comes from
- Index sheet "Transcript Library Index" (Google Sheet `1O_fFGkIZ4Tq1rdqueI1K6m6BNC0X1frTMsEDV5yzLcE`): one row per video, columns video_id through caption_misspellings. Key moments (column M) are checked against the timestamped transcripts in Drive (Production > YouTube Transcript Library).
- Caption glossary: `_Caption Glossary.md` in the same Drive folder.

## Updating
1. Export the sheet's values (A1:O) to `index_all.json` as a list of row objects keyed by the header row.
2. `python3 build_data.py index_all.json "_Caption Glossary.md"`
3. Commit and push `data.json` and `syn.json`. GitHub Pages redeploys in about a minute.

Links back up 2 seconds from each caption line so a clip starts cleanly. Caption lines are about 15 seconds apart, so a link can land a few seconds before the exact sentence.

## Updating the data

`data.json` is built from the Transcript Library Index sheet. From the repo root:

    python3 tools/build_data.py sheet.json

where `sheet.json` is the sheet's values (A1:O, header row first). `syn.json` only changes when the caption glossary is passed as a second argument.
