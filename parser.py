#!/usr/bin/env python3
import re, sys, pathlib, yaml

# --- Inputs/outputs ---
md_path = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "reading_list.md")
out_path = pathlib.Path("_data/reading.yml")
out_path.parent.mkdir(parents=True, exist_ok=True)

text = md_path.read_text(encoding="utf-8", errors="ignore")
lines = text.splitlines()

# --- Regexes ---
def clean_header(s: str) -> str:
    # remove leading enumeration like "7.", "12)", "1 .", etc.
    s = re.sub(r"^\s*\d+\s*[\.\)]\s*", "", s)
    return re.sub(r"\s+", " ", s).strip()

h2_re = re.compile(r"^##\s+(.+?)\s*$")
h3_re = re.compile(r"^###\s+(.+?)\s*$")

bullet_re = re.compile(r"^\s*[-*]\s+(.+)$")
year_start_re = re.compile(r"^\s*(?:\*\*)?(\d{4})(?:\*\*)?\s*:?\s*", re.UNICODE)
link_re = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

topic = None      # from ## headers (your high-level topics)
subtopic = None   # from ### headers (optional)
items = []
seen = set()

for raw in lines:
    # Track topics/subtopics
    m2 = h2_re.match(raw)
    if m2:
        topic = clean_header(m2.group(1))
        subtopic = None
        continue
    m3 = h3_re.match(raw)
    if m3:
        subtopic = clean_header(m3.group(1))
        continue

    # Only parse bullet lines
    mb = bullet_re.match(raw)
    if not mb:
        continue
    content = mb.group(1).strip()

    # Try to read a leading year (supports **YYYY** or plain YYYY, optional colon)
    year = None
    my = year_start_re.match(content)
    if my:
        year = int(my.group(1))
        content = content[my.end():].strip()  # strip the leading year bit

    # Grab the first [Title](URL) on the line
    ml = link_re.search(content)
    if not ml:
        # Nothing to extract (e.g., a plain text bullet) -> skip
        continue
    title = ml.group(1).strip()
    url = ml.group(2).strip()

    # Heuristic "venue" from trailing text after the link (short, no http)
    tail = content[ml.end():].strip()
    tail = tail.strip(" .–—-:()[]")
    venue = None
    if tail and "http" not in tail and len(tail) <= 120:
        venue = tail

    # Topics list: always include the H2; include H3 if present
    topics = []
    if topic:
        topics.append(topic)
    if subtopic:
        topics.append(subtopic)

    key = (year, title, url, tuple(topics))
    if key in seen:
        continue
    seen.add(key)

    item = {"year": year, "title": title, "url": url}
    if venue:
        item["venue"] = venue
    if topics:
        item["topics"] = topics
    items.append(item)

# Sort: newest year first; items without year at the end
def sort_key(it):
    y = it.get("year")
    ykey = -(y) if isinstance(y, int) else 10**9
    return (ykey, it["title"].lower())

items.sort(key=sort_key)

yaml.safe_dump(items, out_path.open("w", encoding="utf-8"), sort_keys=False, allow_unicode=True)

print(f"Wrote {len(items)} entries to {out_path}")
# Optional: preview first few
for it in items[:5]:
    print(f"- {it.get('year')} | {it['title']} ({it.get('venue','')})")
