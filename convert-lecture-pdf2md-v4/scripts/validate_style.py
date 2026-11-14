"""validate_style.py <raw.md> <styled.md> <n_slides>
Checks a merc-styled lecture md (v4.1: PARTs + topic subsections) against the raw
conversion. Problems are prefixed [part-N] (or [doc]) so failing PARTs can be
re-styled individually.
Checks: one H1 + H3 subtitle + Source/Scope lines, ToC links, kept/dropped slide
accounting (hidden <a id="sNN"> anchors + `*Dropped slides:*` footer, must cover
1..N), dropped-slide content guard (>40 words), subsection headings/anchors/ranges,
per-subsection word coverage (<0.9, set-presence), figure links (<id>.png) + figure
block format, no `Slide use:` filler, Key Idea placement/form (<=60 words, <=1 per
PART), Roadmap (<=1, exact heading, placement), no <details>, balanced <table>,
math ($ balance, $$ placement, | in table math), pipe-table cell counts + trailing
footnote rows, mermaid safe subset + mmdc compile.
INJECT blocks with content `skip`, empty, or starting `drop:` need no image link.
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


INJ = re.compile(r"<!-- INJECT_START: ([^ ]+) -->(.*?)<!-- INJECT_END: \1 -->", re.S)


def is_dead(body):
    b = body.strip().lower()
    return (not b) or b == "skip" or b.startswith("drop:")


def strip_skip(t):
    """Drop INJECT blocks whose content is skip/empty/drop: (not figures to link)."""
    return INJ.sub(lambda m: " " if is_dead(m.group(2)) else m.group(0), t)


def drop_text(t):
    """Replace `drop: <label> — <names>` blocks by the names only (for the dropped-slide guard)."""
    def rep(m):
        b = m.group(2).strip()
        if b.lower().startswith("drop:"):
            b = b[5:].strip()
            b = re.split(r"\s+[—–-]\s+|—", b, maxsplit=1)[-1]
            return " " + b + " "
        return m.group(0)
    return INJ.sub(rep, t)


def words(t):
    t = strip_skip(t)
    t = re.sub(r"(?mi)^\s*(slide use|use|purpose):.*$", " ", t)   # AI filler lines the style step deletes on purpose
    t = re.sub(r"<!--.*?-->", " ", t, flags=re.S)
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", t)          # image links
    t = re.sub(r"\\(begin|end)\{[^}]*\}", " ", t)        # LaTeX environments
    t = re.sub(r"\\[A-Za-z]+", " ", t)                   # LaTeX macros (\rightarrow): lost legitimately when grammar moves from LaTeX to code
    t = re.sub(r"slide_\d+_fig_\d+|\bfig\b", " ", t)     # "fig" from figure ids / marker lines
    return re.findall(r"[a-z0-9]{3,}", t.lower())


# ---------- line scan: fences ----------
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

# ---------- structure scan: parts, subsections, slide anchors ----------
part_of_line = [None] * len(lines)
part_anchor_line = {}            # part -> line of <a id="part-N">
part_first_sub_line = {}         # part -> first <a id="part-N-M"> line
sub_anchor_line = {}             # (N, M) -> line
sub_heads = []                   # (line, N, M, a, b, title)
slide_anchor = []                # (slide number, line)
footer_line = len(lines)
cur = None
SUB_RE = re.compile(r"^### (\d+)\.(\d+)\s+(.*?)\s*\(slides?\s+(\d+)(?:\s*[–-]\s*(\d+))?\)\s*$")
for i, l in enumerate(lines):
    if not in_fence[i]:
        m = re.match(r'^\s*<a id="part-(\d+)"></a>', l)
        if m:
            cur = int(m.group(1))
            part_anchor_line[cur] = i
        m = re.match(r'^\s*<a id="part-(\d+)-(\d+)"></a>', l)
        if m:
            sub_anchor_line[(int(m.group(1)), int(m.group(2)))] = i
            part_first_sub_line.setdefault(int(m.group(1)), i)
        m = re.match(r'^\s*<a id="s(\d+)"></a>\s*$', l)
        if m:
            slide_anchor.append((int(m.group(1)), i))
        m = SUB_RE.match(l)
        if m:
            a = int(m.group(4))
            b = int(m.group(5)) if m.group(5) else a
            sub_heads.append((i, int(m.group(1)), int(m.group(2)), a, b, m.group(3)))
        if re.match(r"^\*Scope:", l) and footer_line == len(lines):
            footer_line = i
    part_of_line[i] = cur


def P(i):
    return part_of_line[i] if i is not None and i < len(part_of_line) else None


# sub text spans: heading line -> next sub heading / part anchor / footer
bounds = sorted(set([h[0] for h in sub_heads] + list(part_anchor_line.values()) + [footer_line]))
sub_span = {}
for h in sub_heads:
    nxt = min([b for b in bounds if b > h[0]] or [len(lines)])
    sub_span[h[0]] = (h[0], nxt)


def sub_of_line(i):
    """Subsection head containing line i (no PART boundary between), else None."""
    best = None
    for h in sub_heads:
        if h[0] < i:
            best = h
    if best is None:
        return None
    pa = [v for v in part_anchor_line.values() if best[0] < v < i]
    return None if pa or i >= footer_line else best


# ---------- raw sections ----------
raw_sl = {int(m.group(1)): m.group(2) for m in
          re.finditer(r"^## Slide (\d+):(.*?)(?=^## Slide \d+:|\Z)", raw, flags=re.M | re.S)}

# ---------- header / footer ----------
h1 = [i for i, l in enumerate(lines) if not in_fence[i] and re.match(r"^# ", l)]
if len(h1) != 1:
    flag(None, f"H1 count {len(h1)} != 1")
if h1:
    nxt = next((l for l in lines[h1[0] + 1:] if l.strip()), "")
    if not re.match(r"^### \S", nxt):
        flag(None, "line after H1 must be an H3 subtitle ('### ...')")
if not re.search(r"^> \*\*Source:\*\*", sty, flags=re.M):
    flag(None, "missing '> **Source:**' line")
if not re.search(r"^\*Scope:", sty, flags=re.M):
    flag(None, "missing '*Scope: ...*' footer line")

anchors = set(re.findall(r'<a id="([^"]+)"></a>', sty))
bad = [l for l in re.findall(r"\]\(#([^)]+)\)", sty) if l not in anchors]
if bad:
    flag(None, f"broken ToC links: {bad[:10]}")
if len(re.findall(r"<table\b", sty)) != len(re.findall(r"</table>", sty)):
    flag(None, "unbalanced <table>/</table>")

# ---------- kept / dropped accounting ----------
kept = [s for s, _ in slide_anchor]
kept_set = set(kept)
if len(kept) != len(kept_set):
    flag(None, f"duplicate slide anchors: {sorted(s for s, c in collections.Counter(kept).items() if c > 1)}")
if kept != sorted(kept):
    flag(None, "slide anchors not in ascending order")

dropped = set()
dm = re.search(r"^\*Dropped slides:\s*(.*?)\*?\s*$", sty, flags=re.M)
if not dm:
    flag(None, "missing '*Dropped slides: ...*' footer line")
else:
    body = dm.group(1).strip().rstrip("*").strip()
    if body.lower() != "none":
        body = re.sub(r"\([^)]*\)", "", body)
        for part in body.split(","):
            r = re.match(r"\s*(\d+)(?:\s*[–-]\s*(\d+))?", part)
            if r:
                a = int(r.group(1))
                b = int(r.group(2)) if r.group(2) else a
                dropped.update(range(a, b + 1))
        if not dropped:
            flag(None, "Dropped slides line has no slide numbers (use 'none')")
allset = set(range(1, n + 1))
if dropped & kept_set:
    flag(None, f"slides both kept and dropped: {sorted(dropped & kept_set)}")
miss = sorted(allset - kept_set - dropped)
extra = sorted((kept_set | dropped) - allset)
if miss:
    flag(None, f"slides neither kept nor dropped: {miss}")
if extra:
    flag(None, f"slide numbers outside 1..{n}: {extra}")

for k in sorted(dropped & set(raw_sl)):
    txt = re.sub(r"<!--.*?-->", " ", strip_skip(drop_text(raw_sl[k])), flags=re.S)
    wc = len(txt.split())
    if wc > 40:
        flag(None, f"dropped slide {k:02d} has {wc} words of content")

# ---------- subsections ----------
for (i, N, M, a, b, title) in sub_heads:
    pk = N
    if b < a:
        flag(pk, f"line {i+1}: subsection {N}.{M} has reversed range {a}-{b}")
    if P(i) != N:
        flag(pk, f"line {i+1}: subsection {N}.{M} sits under PART {P(i)}")
    prev = next((lines[j] for j in range(i - 1, -1, -1) if lines[j].strip()), "")
    if prev.strip() != f'<a id="part-{N}-{M}"></a>':
        flag(pk, f"line {i+1}: subsection {N}.{M} needs '<a id=\"part-{N}-{M}\"></a>' right before its heading")
for (N, M), li in sub_anchor_line.items():
    nxt = next((lines[j] for j in range(li + 1, len(lines)) if lines[j].strip()), "")
    if not SUB_RE.match(nxt):
        flag(N, f"line {li+1}: anchor part-{N}-{M} not followed by a '### {N}.{M} ... (slides a-b)' heading")

sub_of_slide = {}
for s, li in slide_anchor:
    h = sub_of_line(li)
    if h is None:
        flag(P(li), f"slide {s:02d}: not inside any subsection")
        continue
    sub_of_slide[s] = h
    if not (h[3] <= s <= h[4]):
        flag(h[1], f"slide {s:02d} anchor outside range ({h[3]}-{h[4]}) of subsection {h[1]}.{h[2]}")

# ---------- coverage (set-presence per subsection) ----------
sub_words = {}
for h in sub_heads:
    a, b = sub_span[h[0]]
    sub_words[h[0]] = set(words("\n".join(lines[a:b])))
all_words = set(words(sty))
for s in sorted(kept_set):
    if s not in raw_sl:
        flag(None, f"slide {s:02d}: not found in raw")
        continue
    rw = words(raw_sl[s].split("\n", 1)[1] if "\n" in raw_sl[s] else "")   # skip the "## Slide N: title" line: titles become subsection headings, reworded
    if not rw:
        continue
    h = sub_of_slide.get(s)
    sw = sub_words[h[0]] if h else all_words
    pk = h[1] if h else None
    cov = sum(1 for w in rw if w in sw) / len(rw)
    if cov < 0.9:
        missing = list(dict.fromkeys(w for w in rw if w not in sw))[:12]
        flag(pk, f"slide {s:02d}: coverage {cov:.2f} missing {missing}")

# ---------- figures ----------
exp_ids = [m.group(1) for m in INJ.finditer(raw) if not is_dead(m.group(2))
           and not (re.match(r"slide_(\d+)_", m.group(1)) and int(re.match(r"slide_(\d+)_", m.group(1)).group(1)) in dropped)]  # dropped slides need no image (content guard covers them)
linked = 0
for fid in exp_ids:
    if re.search(re.escape(fid) + r"\.png", sty):
        linked += 1
    else:
        sm = re.match(r"slide_(\d+)_", fid)
        pk = sub_of_slide[int(sm.group(1))][1] if sm and int(sm.group(1)) in sub_of_slide else None
        flag(pk, f"figure {fid}: no link to {fid}.png in styled md")

# ---------- AI callouts, figure block format, filler ----------
tip_per_part = collections.Counter()
KI = "> **Key Idea (AI-added):**"
for i, l in enumerate(lines):
    s = l.rstrip()
    pi = P(i)
    if re.match(r"^[>\s]*Slide use:", s):
        flag(pi, f"line {i+1}: filler line 'Slide use:'")
    if in_fence[i]:
        continue
    if s.strip() == "> [!TIP]":
        nxt = lines[i + 1].rstrip() if i + 1 < len(lines) else ""
        if not nxt.startswith(KI):
            flag(pi, f"line {i+1}: [!TIP] not followed by '{KI}'")
            continue
        tip_per_part[pi] += 1
        if pi is None:
            flag(None, f"line {i+1}: Key Idea callout outside any PART")
        else:
            a, f1 = part_anchor_line.get(pi), part_first_sub_line.get(pi)
            if not (i > a and (f1 is None or i < f1)):
                flag(pi, f"line {i+1}: Key Idea must sit between PART heading and its first subsection anchor")
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

# ---------- roadmap ----------
road = [i for i, l in enumerate(lines) if not in_fence[i] and re.match(r"^#+\s.*Roadmap", l)]
if len(road) > 1:
    flag(None, f"{len(road)} Roadmap headings (max 1)")
for i in road:
    if lines[i].rstrip() != "### Roadmap (AI-added)":
        flag(None, f"line {i+1}: Roadmap heading must be exactly '### Roadmap (AI-added)'")
    toc = next((j for j, l in enumerate(lines) if re.match(r"^## Table of Contents", l)), None)
    p1 = part_anchor_line.get(1)
    if toc is None or i < toc or (p1 is not None and i > p1):
        flag(None, f"line {i+1}: Roadmap must sit after the ToC and before <a id=\"part-1\">")
    nxt = next((lines[j] for j in range(i + 1, len(lines)) if lines[j].strip()), "")
    if not re.match(r"^\s*(`{3,}|~{3,})\s*mermaid\b", nxt):
        flag(None, f"line {i+1}: Roadmap must be followed by a mermaid block")

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

print(f"kept={len(kept_set)} dropped={len(dropped)}/{n} subsections={len(sub_heads)} "
      f"parts={len(part_anchor_line)} mermaid={len(blocks)} invalid={mm_bad} "
      f"figures_linked={linked}/{len(exp_ids)} "
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
