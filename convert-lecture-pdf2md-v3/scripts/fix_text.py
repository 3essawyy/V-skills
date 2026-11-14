"""fix_text.py <pdf> <raw.md> <slide,slide,...>
For the given slides, rebuild the slide's text body from the PDF text layer (reading order),
keep its figure blocks (INJECT_START..END) and skipped-decor comments, drop the old text lines.
Drops: title line, footer, scrambled equation blocks (one word per line)."""
import re, sys, fitz
sys.stdout.reconfigure(encoding="utf-8")
pdf, md_p, slides = sys.argv[1], sys.argv[2], [int(x) for x in sys.argv[3].split(",")]
FOOTER = re.compile(r"^(Computer Engineering(,| Department)?( Cairo University)?|Cairo University|\d+)$")
md = open(md_p, encoding="utf-8").read()
d = fitz.open(pdf)

def body(page, title):
    out = []
    for b in sorted(page.get_text("blocks"), key=lambda b: (round(b[1]), b[0])):
        lines = [l.strip() for l in b[4].splitlines() if l.strip()]
        if not lines: continue
        words = sum(len(l.split()) for l in lines)
        if len(lines) >= 3 and words / len(lines) < 1.6: continue      # scrambled equation object
        for l in lines:
            if FOOTER.match(l) or l == title.strip(): continue
            l = l.replace("", "×").replace("", "≈").replace("", "=")
            if l.startswith(chr(0x2022)): out.append("- " + l[1:].strip())
            elif l.startswith((chr(0x2013), "- ")): out.append("  - " + l[1:].strip())
            elif out and out[-1].startswith(("- ", "  - ")) and l[:1].islower():
                out[-1] += " " + l                                           # wrapped bullet line
            else: out.append(l)
    return out

for n in slides:
    m = re.search(rf"^## Slide {n}:(.*?)$(.*?)(?=^## Slide \d+:|\Z)", md, re.M | re.S)
    title, sec = m.group(1), m.group(2)
    keep = re.findall(r"<!-- INJECT_START:.*?<!-- INJECT_END:[^>]*-->|<!-- skipped decorative:[^>]*-->", sec, re.S)
    new = f"## Slide {n}:{title}\n" + "\n".join(body(d[n - 1], title)) + "\n" + "\n".join(keep) + "\n\n"
    md = md[:m.start()] + new + md[m.end():]
open(md_p, "w", encoding="utf-8").write(md)
print("rebuilt slides:", slides)
