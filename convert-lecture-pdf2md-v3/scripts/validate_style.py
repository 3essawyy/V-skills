"""validate_style.py <raw.md> <styled.md> <n_slides>
Checks a merc-styled lecture md against the raw conversion:
 - slide headings == n, ToC links all resolve, exactly one H1
 - per-slide word coverage (raw words found in styled slide) -> flags < 0.9
 - every mermaid block compiles with mmdc
"""
import re, sys, subprocess, tempfile, os, collections

raw_p, sty_p, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
raw = open(raw_p, encoding="utf-8").read()
sty = open(sty_p, encoding="utf-8").read()

def words(t):
    t = re.sub(r"<!--.*?-->", " ", t, flags=re.S)
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", t)          # image links
    return re.findall(r"[a-z0-9]{3,}", t.lower())

# split raw by "## Slide N:" and styled by anchors sNN
raw_sl = {int(m.group(1)): m.group(2) for m in
          re.finditer(r"^## Slide (\d+):(.*?)(?=^## Slide \d+:|\Z)", raw, flags=re.M | re.S)}
sty_sl = {int(m.group(1)): m.group(2) for m in
          re.finditer(r'<a id="s(\d+)"></a>(.*?)(?=<a id="s\d+"></a>|<a id="part-\d+"></a>|\Z)', sty, flags=re.S)}

problems = []
heads = len(re.findall(r"^### \d+ · ", sty, flags=re.M))
if heads != n: problems.append(f"slide headings {heads} != {n}")
if len(re.findall(r"^# ", sty, flags=re.M)) != 1: problems.append("H1 count != 1")
anchors = set(re.findall(r'<a id="([^"]+)"></a>', sty))
bad = [l for l in re.findall(r"\]\(#([^)]+)\)", sty) if l not in anchors]
if bad: problems.append(f"broken ToC links: {bad[:10]}")

for k in sorted(raw_sl):
    rw = collections.Counter(words(raw_sl[k]))
    sw = collections.Counter(words(sty_sl.get(k, "")))
    tot = sum(rw.values())
    if not tot: continue
    cov = sum(min(c, sw[w]) for w, c in rw.items()) / tot
    if cov < 0.9:
        miss = [w for w in rw if sw[w] < rw[w]][:12]
        problems.append(f"slide {k}: coverage {cov:.2f} missing {miss}")

blocks = re.findall(r"```mermaid\n(.*?)```", sty, flags=re.S)
tmp = tempfile.mkdtemp()
mm_bad = 0
for i, b in enumerate(blocks):
    f = os.path.join(tmp, f"b{i}.mmd")
    open(f, "w", encoding="utf-8").write(b)
    r = subprocess.run(f'mmdc -q -i "{f}" -o "{f}.svg"', shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        mm_bad += 1
        err = (r.stderr or r.stdout).strip().splitlines()
        problems.append(f"mermaid block {i} invalid: {err[-1][:150] if err else '?'}")

print(f"slides={heads}/{n} anchors={len(anchors)} mermaid={len(blocks)} invalid={mm_bad} "
      f"size={len(sty)} chars (~{len(sty)//4} tok) vs raw {len(raw)}")
print("\n".join(problems) if problems else "ALL CHECKS PASS")
