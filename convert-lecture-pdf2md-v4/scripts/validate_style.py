"""validate_style.py <raw.md> <styled.md> <n_slides>
Checks a merc-styled lecture md against the raw conversion. Problems are prefixed
[part-N] (or [doc]) so failing PARTs can be re-styled individually.
Checks: slide heading count, one H1, ToC links, per-slide word coverage (<0.9),
AI Key Idea callouts, figure blocks (format + count vs raw), no <details>,
balanced <table>, math ($ balance, $$ placement, | in table math), pipe-table
cell counts + trailing footnote rows, mermaid safe subset + mmdc compile.
Prints a summary line, problems, then `FAILING_PARTS: part-2,part-5` (or none).
Exit code 1 if any problem, else 0.
"""
import re, sys, subprocess, tempfile, os, collections, shutil

raw_p, sty_p, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
raw = open(raw_p, encoding="utf-8").read()
sty = open(sty_p, encoding="utf-8").read()
lines = sty.split("\n")

problems = []  # (part or None, msg)


def flag(part, msg):
    problems.append((part, msg))


def words(t):
    t = re.sub(r"<!--.*?-->", " ", t, flags=re.S)
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", t)          # image links
    return re.findall(r"[a-z0-9]{3,}", t.lower())


# ---------- line scan: fences, part/slide anchors ----------
in_fence = [False] * len(lines)   # True for fence lines and their content
fence_lang = {}                   # start line idx -> (lang, end idx)
fence = None                      # (marker, start idx, lang)
for i, l in enumerate(lines):
    m = re.match(r"^\s*(`{3,}|~{3,})\s*([\w+-]*)", l)
    if fence is None:
        if m:
            fence = (m.group(1), i, m.group(2).lower())
            in_fence[i] = True
    else:
        in_fence[i] = True
        if m and m.group(1)[0] == fence[0][0] and len(m.group(1)) >= len(fence[0]) and not m.group(2):
            fence_lang[fence[1]] = (fence[2], i)
            fence = None
if fence is not None:
    fence_lang[fence[1]] = (fence[2], len(lines))
    flag(None, "unclosed code fence")

part_of_line = [None] * len(lines)
slide_part = {}
part_anchor_line = {}
part_first_slide_line = {}
cur = None
for i, l in enumerate(lines):
    if not in_fence[i]:
        m = re.match(r'^\s*<a id="part-(\d+)"></a>', l)
        if m:
            cur = int(m.group(1))
            part_anchor_line[cur] = i
        m = re.match(r'^\s*<a id="s(\d+)"></a>', l)
        if m and cur is not None:
            slide_part[int(m.group(1))] = cur
            part_first_slide_line.setdefault(cur, i)
    part_of_line[i] = cur


def P(i):
    return part_of_line[i] if i is not None and i < len(part_of_line) else None


# ---------- slide split (raw vs styled) ----------
raw_sl = {int(m.group(1)): m.group(2) for m in
          re.finditer(r"^## Slide (\d+):(.*?)(?=^## Slide \d+:|\Z)", raw, flags=re.M | re.S)}
sty_sl = {int(m.group(1)): m.group(2) for m in
          re.finditer(r'<a id="s(\d+)"></a>(.*?)(?=<a id="s\d+"></a>|<a id="part-\d+"></a>|\Z)', sty, flags=re.S)}

# ---------- doc-level ----------
heads = len(re.findall(r"^### \d+ · ", sty, flags=re.M))
if heads != n:
    flag(None, f"slide headings {heads} != {n}")
h1 = [i for i, l in enumerate(lines) if not in_fence[i] and re.match(r"^# ", l)]
if len(h1) != 1:
    flag(None, f"H1 count {len(h1)} != 1")
anchors = set(re.findall(r'<a id="([^"]+)"></a>', sty))
bad = [l for l in re.findall(r"\]\(#([^)]+)\)", sty) if l not in anchors]
if bad:
    flag(None, f"broken ToC links: {bad[:10]}")
if len(re.findall(r"<table\b", sty)) != len(re.findall(r"</table>", sty)):
    flag(None, "unbalanced <table>/</table>")


# ---------- coverage + figure counts per slide ----------
def fig_expected(txt):
    c = 0
    for m in re.finditer(r"<!-- INJECT_START: ([^ ]+) -->(.*?)<!-- INJECT_END: \1 -->", txt, flags=re.S):
        body = m.group(2).strip()
        if body and body.lower() != "skip":
            c += 1
    return c


for k in sorted(raw_sl):
    pk = slide_part.get(k)
    rw = collections.Counter(words(raw_sl[k]))
    sw = collections.Counter(words(sty_sl.get(k, "")))
    tot = sum(rw.values())
    if tot:
        cov = sum(min(c, sw[w]) for w, c in rw.items()) / tot
        if cov < 0.9:
            miss = [w for w in rw if sw[w] < rw[w]][:12]
            flag(pk, f"slide {k}: coverage {cov:.2f} missing {miss}")
    exp = fig_expected(raw_sl[k])
    got = len(re.findall(r"\*\*Figure — AI transcription\*\*", sty_sl.get(k, "")))
    if got < exp:
        flag(pk, f"slide {k}: figure blocks {got} < expected {exp}")

raw_markers = len(re.findall(r"<!-- INJECT_START", raw))
exp_total = fig_expected(raw)
fig_styled = len(re.findall(r"^> \*\*Figure — AI transcription\*\* \(slide \d{2}\)$", sty, flags=re.M))
if fig_styled < exp_total and not any("figure blocks" in m for _, m in problems):
    flag(None, f"figure blocks {fig_styled} < expected {exp_total}")

# ---------- AI callouts + figure block format ----------
tip_per_part = collections.Counter()
KI = "> **Key Idea (AI-added):**"
for i, l in enumerate(lines):
    if in_fence[i]:
        continue
    s = l.rstrip()
    pi = P(i)
    if s.strip() == "> [!TIP]":
        nxt = lines[i + 1].rstrip() if i + 1 < len(lines) else ""
        if not nxt.startswith(KI):
            flag(pi, f"line {i+1}: [!TIP] not followed by '{KI}'")
            continue
        tip_per_part[pi] += 1
        if pi is None:
            flag(None, f"line {i+1}: Key Idea callout outside any PART")
        else:
            a, f1 = part_anchor_line.get(pi), part_first_slide_line.get(pi)
            if not (i > a and (f1 is None or i < f1)):
                flag(pi, f"line {i+1}: Key Idea must sit between PART heading and its first slide anchor")
        txt = [nxt[len(KI):]]
        j = i + 2
        while j < len(lines) and lines[j].startswith(">"):
            txt.append(lines[j].lstrip("> ").rstrip())
            j += 1
        wc = len(" ".join(txt).split())
        if wc > 60:
            flag(pi, f"line {i+1}: Key Idea {wc} words > 60")
    elif "Key Idea" in s and not (s.startswith(KI) and i > 0 and lines[i - 1].strip() == "> [!TIP]"):
        flag(pi, f"line {i+1}: 'Key Idea' text not in the required callout form")
    if s.strip() == "> [!NOTE]":
        nxt = lines[i + 1].rstrip() if i + 1 < len(lines) else ""
        if "**Figure" in nxt:
            if not re.match(r"^> \*\*Figure — AI transcription\*\* \(slide \d{2}\)$", nxt):
                flag(pi, f"line {i+2}: figure header malformed: {nxt[:70]}")
    elif "**Figure" in s and (i == 0 or lines[i - 1].strip() != "> [!NOTE]"):
        flag(pi, f"line {i+1}: figure marker without preceding '> [!NOTE]'")
for p, c in tip_per_part.items():
    if c > 1:
        flag(p, f"{c} Key Idea callouts (max 1 per PART)")

# ---------- <details> ----------
for i, l in enumerate(lines):
    if not in_fence[i] and re.search(r"<details\b", l):
        flag(P(i), f"line {i+1}: <details> not allowed in lectures")

# ---------- math ----------
in_dd = False
for i, l in enumerate(lines):
    if in_fence[i]:
        continue
    s = l.strip()
    if s == "$$":
        in_dd = not in_dd
        continue
    if in_dd:
        continue
    t = re.sub(r"`[^`]*`", "", l)
    t = t.replace("\\$", "")
    if "$$" in t and re.match(r"^\s*(>|[-*+]\s|\d+\.\s)", l):
        flag(P(i), f"line {i+1}: $$ inside blockquote/list, use a ```math fence")
    t2 = t.replace("$$", "")
    if re.sub(r"^[\s>*+\d.-]+", "", t).strip() == "$$":
        continue
    if t2.count("$") % 2 == 1 or t.count("$$") % 2 == 1:
        flag(P(i), f"line {i+1}: unescaped $ or unbalanced math")
    if l.lstrip().startswith("|"):
        for m in re.finditer(r"(?<!\\)\$(.+?)(?<!\\)\$", t):
            if re.search(r"(?<!\\)\|", m.group(1)):
                flag(P(i), f"line {i+1}: bare | inside math in table row")
                break
if in_dd:
    flag(None, "unclosed $$ block")


# ---------- pipe tables ----------
def cells(row):
    r = re.sub(r"`[^`]*`", "x", row)
    r = re.sub(r"(?<!\\)\$.+?(?<!\\)\$", "x", r)
    r = r.strip()
    if r.startswith("|"):
        r = r[1:]
    if r.endswith("|") and not r.endswith("\\|"):
        r = r[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", r)]


i = 0
while i < len(lines):
    if not in_fence[i] and lines[i].lstrip().startswith("|"):
        j = i
        while j < len(lines) and not in_fence[j] and lines[j].lstrip().startswith("|"):
            j += 1
        tbl = lines[i:j]
        hn = len(cells(tbl[0]))
        for off, row in enumerate(tbl[1:], 1):
            cs = cells(row)
            if len(cs) != hn:
                flag(P(i + off), f"line {i+off+1}: table row has {len(cs)} cells, header {hn}")
            if re.match(r"^[\s|:-]+$", row):
                continue
            first = cs[0]
            if first in ("*", "†") or first.lower().startswith("note") or \
               (hn > 1 and first and not any(cs[1:])):
                flag(P(i + off), f"line {i+off+1}: footnote-like table row, move to '> **Notes & Footnotes**'")
        i = j
    else:
        i += 1

# ---------- mermaid ----------
mm_bin = shutil.which("mmdc") or shutil.which("mmdc.cmd")
tmp = tempfile.mkdtemp()
blocks = []
for start, (lang, end) in sorted(fence_lang.items()):
    if lang == "mermaid":
        blocks.append((start, "\n".join(lines[start + 1:end])))
mm_bad = 0
for bi, (start, b) in enumerate(blocks):
    pk = P(start)
    tag = f"mermaid block {bi} (line {start+1})"
    bl = b.split("\n")
    first = next((x for x in bl if x.strip()), "")
    if not first.strip().startswith("%%{init"):
        flag(pk, f"{tag}: first line must be %%{{init: ...}}%%")
    if re.search(r"--\s*\"[^\"]*\"\s*-[->]|--\s+[^\s>|-][^\n]*?\s+-->", b):
        flag(pk, f"{tag}: '-- x -->' edge label, use -->|x|")
    if "([" in b:
        flag(pk, f"{tag}: stadium shape ([ ]) not allowed")
    if any(ord(c) > 127 for c in b):
        flag(pk, f"{tag}: non-ASCII characters")
    depth, sg_ids = 0, set()
    for x in bl:
        m = re.match(r"^\s*subgraph\s+([\w-]+)", x)
        if m:
            depth += 1
            sg_ids.add(m.group(1))
            if depth > 1:
                flag(pk, f"{tag}: nested subgraph")
        elif re.match(r"^\s*end\s*$", x) and depth:
            depth -= 1
    for x in bl:
        m = re.match(r"^\s*style\s+([\w-]+)\b", x)
        if m and m.group(1) in sg_ids:
            flag(pk, f"{tag}: style on subgraph id {m.group(1)}")
    if mm_bin:
        f = os.path.join(tmp, f"b{bi}.mmd")
        open(f, "w", encoding="utf-8").write(b)
        try:
            r = subprocess.run([mm_bin, "-q", "-i", f, "-o", f + ".svg"],
                               capture_output=True, text=True, timeout=180)
            if r.returncode != 0:
                mm_bad += 1
                err = (r.stderr or r.stdout).strip().splitlines()
                flag(pk, f"{tag} invalid: {err[-1][:150] if err else '?'}")
        except Exception as e:
            flag(pk, f"{tag}: mmdc failed to run: {e}")

print(f"slides={heads}/{n} anchors={len(anchors)} mermaid={len(blocks)} invalid={mm_bad} "
      f"figures={fig_styled}/{exp_total} (raw markers {raw_markers}) "
      f"size={len(sty)} chars (~{len(sty)//4} tok) vs raw {len(raw)}")
if blocks and not mm_bin:
    print("WARNING: mermaid unvalidated (mmdc missing)")
for p, m in problems:
    print(f"[part-{p}] {m}" if p is not None else f"[doc] {m}")
if not problems:
    print("ALL CHECKS PASS")
fp = sorted({p for p, _ in problems if p is not None})
print("FAILING_PARTS: " + (",".join(f"part-{p}" for p in fp) if fp else "none"))
sys.exit(1 if problems else 0)
