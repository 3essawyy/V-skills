"""coverage.py <pdf> <md> [threshold]
Per slide: share of the PDF page's words (>=3 letters) that appear in that slide's md section.
Raw md sections are '## Slide N:'; styled md sections are '<a id="sNN">'. Prints slides below threshold
with the missing PDF lines (lines of the page with <50% of their words present)."""
import re, sys, collections, fitz
sys.stdout.reconfigure(encoding="utf-8")
pdf, md_p = sys.argv[1], sys.argv[2]
th = float(sys.argv[3]) if len(sys.argv) > 3 else 0.9
md = open(md_p, encoding="utf-8").read()
W = lambda t: re.findall(r"[a-z0-9]{3,}", t.lower())
secs = {int(m.group(1)): m.group(2) for m in re.finditer(r"^## Slide (\d+):(.*?)(?=^## Slide \d+:|\Z)", md, re.M | re.S)}
if not secs:
    secs = {int(m.group(1)): m.group(2) for m in re.finditer(
        r'<a id="s(\d+)"></a>(.*?)(?=<a id="s\d+"></a>|<a id="part-\d+"></a>|\Z)', md, re.S)}
d = fitz.open(pdf); bad = 0
for i, page in enumerate(d, 1):
    txt = page.get_text()
    pw = collections.Counter(W(txt)); tot = sum(pw.values())
    if not tot: continue
    mw = collections.Counter(W(secs.get(i, "")))
    cov = sum(min(c, mw[w]) for w, c in pw.items()) / tot
    if cov < th:
        bad += 1
        lines = [l.strip() for l in txt.splitlines() if len(W(l)) >= 2
                 and sum(1 for w in W(l) if mw[w]) / len(W(l)) < 0.5]
        print(f"slide {i}: {cov:.2f} missing lines: {lines[:8]}")
print(f"{pdf}: {bad} slides below {th}")
