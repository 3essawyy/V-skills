#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert-lecture-pdf2md-v2: lecture-slide PDF -> token-lean Markdown that keeps figure meaning.

Stages (0 LLM tokens except Stage 2):
  1. extract : text in reading order + figure crops + images_manifest.json (batches for vision)
  2. (agent) : vision model writes media/<stem>/<asset_id>.md per figure (see SKILL.md)
  3. --inject: merge those companion files into the markdown, validate, print fidelity report
  --report   : fidelity report only (no changes)

No install-path dependencies: everything resolves from CLI args.
Requires: pip install pymupdf pillow
"""

import os
import re
import sys
import json
import hashlib
import argparse
import unicodedata
from collections import Counter
from typing import List, Dict, Any, Tuple, Optional

try:
    import pymupdf
    from PIL import Image
except ImportError as e:
    print(f"Error: missing dependency ({e}). Run: pip install pymupdf pillow")
    sys.exit(1)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------
MIN_FIG_AREA_FRAC = 0.01     # figures smaller than this share of the page are decorative
BG_AREA_FRAC = 0.90          # raster covering this much of the page = background, ignored
REPEAT_FRAC = 0.25           # same figure signature on >= this share of pages (min 3) = template decor
LOWTEXT_CHARS = 30           # page with less text and no figure -> whole page goes to vision
ANNOT_MAX_CHARS = 80         # non-bullet text blocks up to this long are treated as figure annotations
MAX_PX = 1000               # long edge of figure crops sent to vision
BATCH_SIZE = 8
CTX_CHARS = 160

BULLET_L1 = "•▪●■◦○"
BULLET_L2 = "–—-"
MATH_CHARS = set("∑∫∂∇√∞≈≠≤≥±×÷∈∉⊂⊆∪∩αβγδεθλμσφωΣΩΔΠ")


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------
def clean(text: str) -> str:
    """Light normalisation only: keep math glyphs, dashes and minus signs intact."""
    text = unicodedata.normalize("NFC", text)
    for a, b in (("ﬁ", "fi"), ("ﬂ", "fl"), (" ", " "),
                 ("“", '"'), ("”", '"'), ("‘", "'"), ("’", "'")):
        text = text.replace(a, b)
    return re.sub(r"[ \t]+", " ", text).strip()


def block_to_lines(raw: str, is_bullet_block: bool) -> List[str]:
    """Turn one text block into markdown list/plain lines; wrapped lines are rejoined."""
    out: List[str] = []
    for line in raw.split("\n"):
        t = clean(line)
        if not t:
            continue
        first = t[0]
        if first in BULLET_L1 and (len(t) == 1 or t[1] in " \t" or first in BULLET_L1):
            out.append("- " + t[1:].strip())
        elif first in BULLET_L2 and len(t) > 1 and t[1] == " " and is_bullet_block:
            out.append("  - " + t[2:].strip())
        elif is_bullet_block and out:
            out[-1] += " " + t          # wrapped continuation of previous bullet
        else:
            out.append(t)
    return [l for l in out if l.strip(" -")]


# ---------------------------------------------------------------------------
# Figure detection (vector clusters: kept from v1)
# ---------------------------------------------------------------------------
def find_vector_drawing_clusters(page: "pymupdf.Page", min_drawings: int = 3,
                                 margin_x: float = 45.0, margin_y: float = 25.0):
    """Cluster vector drawing paths into figure bounding boxes. Returns [(rect, n_draw)]."""
    page_w, page_h = page.rect.width, page.rect.height
    drawings = page.get_drawings()
    if not drawings:
        return []

    cand = []
    for d in drawings:
        r = pymupdf.Rect(d["rect"])
        if r.width <= 0 and r.height <= 0:
            continue
        if r.width >= page_w * 0.90 and r.height >= page_h * 0.90:
            continue                       # slide background
        if r.width >= page_w * 0.85 and r.height <= 3:
            continue                       # full-width rule
        cand.append(r)
    if len(cand) < min_drawings:
        return []

    def grow(c):
        return pymupdf.Rect(c.x0 - margin_x, c.y0 - margin_y, c.x1 + margin_x, c.y1 + margin_y)

    clusters: List[pymupdf.Rect] = []
    for r in cand:
        for i, c in enumerate(clusters):
            if grow(c).intersects(r):
                clusters[i] = c | r
                break
        else:
            clusters.append(pymupdf.Rect(r))

    changed = True
    while changed:
        changed = False
        merged, skip = [], set()
        for i, c in enumerate(clusters):
            if i in skip:
                continue
            for j in range(i + 1, len(clusters)):
                if j not in skip and grow(c).intersects(clusters[j]):
                    c = c | clusters[j]
                    skip.add(j)
                    changed = True
            merged.append(c)
        clusters = merged

    # pull in short neighbouring labels (axis labels, node labels)
    for b in page.get_text("blocks"):
        br, bt = pymupdf.Rect(b[:4]), b[4].strip()
        if not bt or any(ch in bt for ch in BULLET_L1) or len(bt.split("\n")) > 3:
            continue
        for i, c in enumerate(clusters):
            if pymupdf.Rect(c.x0 - 15, c.y0 - 15, c.x1 + 15, c.y1 + 15).intersects(br):
                clusters[i] = c | br
                break

    out = []
    for c in clusters:
        if c.width >= 50 and c.height >= 35:
            pad = pymupdf.Rect(max(0, c.x0 - 6), max(0, c.y0 - 6),
                               min(page_w, c.x1 + 6), min(page_h, c.y1 + 6))
            n = sum(1 for r in cand if pad.contains(r) or (pad & r).get_area() > 0.5 * r.get_area())
            out.append((pad, n))
    out.sort(key=lambda t: (t[0].y0, t[0].x0))
    return out


# ---------------------------------------------------------------------------
# Per-page analysis (no files written here)
# ---------------------------------------------------------------------------
def analyse_page(page: "pymupdf.Page", slide_num: int) -> Dict[str, Any]:
    pw, ph = page.rect.width, page.rect.height
    page_area = pw * ph
    blocks, title, title_font, number = [], "", 0.0, str(slide_num)

    for b in page.get_text("dict").get("blocks", []):
        if "lines" not in b:
            continue
        lines, max_font = [], 0.0
        for ln in b["lines"]:
            lines.append("".join(s["text"] for s in ln["spans"]))
            for s in ln["spans"]:
                max_font = max(max_font, s["size"])
        raw = "\n".join(lines).strip()
        if not raw:
            continue
        x0, y0, x1, y1 = b["bbox"]
        if raw.isdigit() and len(raw) <= 3 and (y0 > ph * 0.80 or (y0 < ph * 0.15 and x0 > pw * 0.75)):
            number = raw
            continue
        is_bullet = any(l.lstrip()[:1] in BULLET_L1 for l in lines)
        if y0 < ph * 0.30 and max_font > title_font and len(lines) <= 3 and not is_bullet:
            title_font, title = max_font, clean(raw.replace("\n", " "))
        blocks.append({"bbox": (x0, y0, x1, y1), "raw": raw, "font": max_font,
                       "bullet": is_bullet, "y0": y0, "x0": x0})

    # figure candidates
    figs: List[Dict[str, Any]] = []
    for info in page.get_images(full=True):
        xref = info[0]
        try:
            rects = page.get_image_rects(xref)
        except Exception:
            rects = []
        for r in rects[:1]:
            if r.get_area() >= BG_AREA_FRAC * page_area:
                continue                   # full-page background picture
            try:
                nbytes = len(page.parent.extract_image(xref)["image"])
                ext = page.parent.extract_image(xref)["ext"].lower()
            except Exception:
                nbytes, ext = 0, "png"
            figs.append({"kind": "raster", "rect": r, "n_draw": 0, "xref": xref,
                         "jpeg": ext in ("jpg", "jpeg"), "bytes": nbytes})
    for rect, n in find_vector_drawing_clusters(page):
        if any(f["kind"] == "raster" and (rect & f["rect"]).get_area() > 0.5 * min(rect.get_area(), f["rect"].get_area())
               for f in figs):
            continue                       # raster already covers it
        figs.append({"kind": "vector", "rect": rect, "n_draw": n, "xref": 0, "jpeg": False, "bytes": 0})

    for f in figs:
        r = f["rect"]
        f["sig"] = (f["kind"], f["xref"] or f["n_draw"], round(r.x0 / 6), round(r.y0 / 6),
                    round(r.width / 6), round(r.height / 6))
        f["frac"] = r.get_area() / page_area

    chars = sum(len(b["raw"]) for b in blocks)
    return {"num": slide_num, "number": number, "title": title or f"Slide {slide_num}", "has_title": bool(title),
            "title_font": title_font, "blocks": blocks, "figs": figs, "chars": chars,
            "w": pw, "h": ph}


# ---------------------------------------------------------------------------
# Rendering figure crops (downscaled to cut vision tokens)
# ---------------------------------------------------------------------------
def render_crop(page: "pymupdf.Page", rect: "pymupdf.Rect", out_path: str) -> int:
    zoom = max(1.0, min(2.0, MAX_PX / max(rect.width, rect.height)))
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=rect)
    pix.save(out_path)
    try:
        with Image.open(out_path) as im:
            im = im.convert("RGB")
            if max(im.size) > MAX_PX:
                im.thumbnail((MAX_PX, MAX_PX))
            im.save(out_path, optimize=True)
            return im.size[0] * im.size[1]
    except Exception:
        return 0


def hint_for(fig: Dict[str, Any], labels: List[str]) -> Tuple[str, bool]:
    r = fig["rect"]
    if fig["kind"] == "raster" and (fig["jpeg"] or fig["bytes"] > 120000):
        return "photo-or-screenshot", False
    if r.height < 60 and r.width > 100:
        return "equation", True
    hard = fig["n_draw"] > 250 or sum(ch in MATH_CHARS for l in labels for ch in l) >= 6
    return "diagram-or-plot", hard


# ---------------------------------------------------------------------------
# Stage 1: extract
# ---------------------------------------------------------------------------
def extract(pdf: str, out_md: str, media_dir: str, stem: str) -> None:
    doc = pymupdf.open(pdf)
    n_pages = len(doc)
    print(f"PDF: {os.path.basename(pdf)}  pages={n_pages}")
    pages = [analyse_page(doc[i], i + 1) for i in range(n_pages)]

    # repeated figures (logos / template art) are decorative
    sig_count = Counter(f["sig"] for p in pages for f in p["figs"])
    repeat_min = max(3, int(REPEAT_FRAC * n_pages))

    os.makedirs(media_dir, exist_ok=True)
    rel_media = os.path.basename(os.path.dirname(media_dir)) + "/" + stem   # "media/<stem>"
    assets, md = [], [f"Source: {os.path.basename(pdf)} ({n_pages} slides)", "", f"# {stem}", ""]
    dropped = {"small": 0, "repeated": 0}
    fig_no = 0

    for p in pages:
        page = doc[p["num"] - 1]
        keep = []
        for f in p["figs"]:
            if f["frac"] < MIN_FIG_AREA_FRAC:
                dropped["small"] += 1
            elif sig_count[f["sig"]] >= repeat_min:
                dropped["repeated"] += 1
            else:
                keep.append(f)

        # several fragments on one slide (matrices, multi-panel plots) -> one composite figure,
        # so vision sees the whole structure once instead of N disconnected crops
        if len(keep) >= 2:
            u = pymupdf.Rect(keep[0]["rect"])
            for f in keep[1:]:
                u |= f["rect"]
            keep = [{"kind": "vector", "rect": u, "n_draw": sum(f["n_draw"] for f in keep), "xref": 0,
                     "jpeg": any(f["jpeg"] for f in keep), "bytes": max(f["bytes"] for f in keep),
                     "frac": u.get_area() / (p["w"] * p["h"]), "sig": None, "composite": True}]

        # text-free page without any detected figure: send the whole page to vision
        if p["chars"] < LOWTEXT_CHARS and not keep:
            keep.append({"kind": "page", "rect": page.rect, "n_draw": 0, "xref": 0,
                         "jpeg": False, "bytes": 0, "frac": 1.0, "sig": None})

        # absorb every short non-bullet text block on a figure slide (axis ticks, legends, matrix digits,
        # formula pieces next to a plot) so the crop shows the figure WITH its annotations;
        # bullets and long prose stay in the body as text
        for f in keep:
            if f["kind"] == "page":
                continue
            for b in p["blocks"]:
                txt = clean(b["raw"].replace("\n", " "))
                if b["bullet"] or txt == p["title"] or len(txt) > ANNOT_MAX_CHARS or b["raw"].count("\n") >= 6:
                    continue
                f["rect"] = f["rect"] | pymupdf.Rect(b["bbox"])

        # text inside kept figures becomes labels (carried to vision + fallback), not body text
        body, labels_by_fig = [], {id(f): [] for f in keep}
        for b in p["blocks"]:
            if b["raw"].strip() == p["title"] or clean(b["raw"].replace("\n", " ")) == p["title"] and b["font"] >= p["title_font"]:
                continue
            br = pymupdf.Rect(b["bbox"])
            owner = None
            if not b["bullet"]:
                for f in keep:
                    if f["kind"] != "page" and (f["rect"].contains(br) or (f["rect"] & br).get_area() > 0.65 * br.get_area()):
                        owner = f
                        break
            if owner:
                labels_by_fig[id(owner)].extend(l for l in (clean(x) for x in b["raw"].split("\n")) if l)
            else:
                body.append(b)

        elements = [("text", b["y0"], b["x0"], b) for b in body]
        for k, f in enumerate(keep):
            elements.append(("fig", f["rect"].y0, f["rect"].x0, (k, f)))
        elements.sort(key=lambda e: (e[1], e[2]))

        md.append(f"## Slide {p['num']}: {p['title']}" if p["has_title"] else f"## Slide {p['num']}:")
        for idx, (kind, _, _, data) in enumerate(elements):
            if kind == "text":
                md.extend(block_to_lines(data["raw"], data["bullet"]))
                continue
            k, f = data
            fig_no += 1
            aid = f"slide_{p['num']:02d}_fig_{k + 1:02d}"
            fpath = os.path.join(media_dir, aid + ".png")
            render_crop(page, f["rect"], fpath)
            labels = labels_by_fig[id(f)]
            hint, hard = ("page-image", True) if f["kind"] == "page" else hint_for(f, labels)
            if f.get("composite") and hint == "diagram-or-plot":
                hint = "composite (matrix / multi-panel / plot)"
            before = [clean(e[3]["raw"].replace("\n", " "))[:CTX_CHARS] for e in elements[max(0, idx - 2):idx] if e[0] == "text"]
            after = [clean(e[3]["raw"].replace("\n", " "))[:CTX_CHARS] for e in elements[idx + 1:idx + 3] if e[0] == "text"]
            assets.append({"id": aid, "slide": p["num"], "slide_title": p["title"], "image": f"{rel_media}/{aid}.png",
                           "companion": f"{rel_media}/{aid}.md", "hint": hint, "hard": hard,
                           "labels": labels[:40], "context_before": before, "context_after": after})
            md.append(f"<!-- INJECT_START: {aid} -->")
            md.append(f"![Figure {fig_no}, slide {p['num']}]({rel_media}/{aid}.png)")
            if labels:
                md.append("Labels in figure: " + " | ".join(labels[:40]))
            md.append(f"<!-- INJECT_END: {aid} -->")
        md.append("")

    with open(out_md, "w", encoding="utf-8") as fh:
        fh.write("\n".join(md))

    batches = {f"batch_{i // BATCH_SIZE + 1}": assets[i:i + BATCH_SIZE] for i in range(0, len(assets), BATCH_SIZE)}
    manifest = os.path.join(os.path.dirname(media_dir), f"{stem}.manifest.json")
    with open(manifest, "w", encoding="utf-8") as fh:
        json.dump({"pdf": os.path.basename(pdf), "markdown": os.path.basename(out_md), "slides": n_pages,
                   "total_assets": len(assets), "hard_assets": sum(a["hard"] for a in assets),
                   "dropped_decorative": dropped, "batches": batches}, fh, indent=1, ensure_ascii=False)
    print(f"Markdown : {out_md}")
    print(f"Manifest : {manifest}  ({len(assets)} figures for vision, {sum(a['hard'] for a in assets)} flagged hard, "
          f"{len(batches)} batches, dropped decorative {dropped})")


# ---------------------------------------------------------------------------
# Stage 3: inject + validate + fidelity report
# ---------------------------------------------------------------------------
def validate(content: str) -> Tuple[bool, str]:
    if not content.strip():
        return False, "empty companion file"
    if content.count("```") % 2:
        return False, "unbalanced code fence"
    if "```mermaid" in content and not re.search(
            r"```mermaid\s*\n\s*(flowchart|graph|sequenceDiagram|classDiagram|stateDiagram|erDiagram|gantt|pie|mindmap|timeline|xychart)",
            content):
        return False, "mermaid block missing diagram header"
    if content.count("$$") % 2:
        return False, "unbalanced $$"
    return True, "ok"


PATTERN = re.compile(r"<!-- INJECT_START:\s*([\w\-]+)\s*-->\s*(.*?)\s*<!-- INJECT_END:\s*\1\s*-->", re.DOTALL)


def inject(md_path: str, media_dir: str, rel_media: str) -> None:
    with open(md_path, "r", encoding="utf-8") as fh:
        content = fh.read()
    stats = Counter()
    problems: List[str] = []

    def repl(m):
        aid = m.group(1)
        comp = os.path.join(media_dir, aid + ".md")
        if not os.path.exists(comp):
            stats["pending"] += 1
            return m.group(0)
        with open(comp, "r", encoding="utf-8") as fh:
            text = fh.read().strip()
        if text.lower() == "skip":
            stats["skipped_decorative"] += 1
            return f"<!-- skipped decorative: {aid} -->"
        ok, why = validate(text)
        if not ok:
            problems.append(f"{aid}: {why}")
            stats["invalid"] += 1
            return m.group(0)
        stats["injected"] += 1
        return (f"<!-- INJECT_START: {aid} -->\n**[Figure {aid} - AI transcription]**\n{text}\n\n"
                f"![{aid}]({rel_media}/{aid}.png)\n<!-- INJECT_END: {aid} -->")

    content = PATTERN.sub(repl, content)
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(content)
    print(f"Inject: {dict(stats)}")
    for p in problems:
        print("  invalid:", p)


def report(pdf: str, md_path: str) -> None:
    with open(md_path, "r", encoding="utf-8") as fh:
        content = fh.read()
    n_pages = len(pymupdf.open(pdf))
    n_sections = len(re.findall(r"^## Slide \d+:", content, re.M))
    pending = [m.group(1) for m in PATTERN.finditer(content) if "AI transcription" not in m.group(2)]
    empty = [m.group(1) for m in re.finditer(r"^## Slide (\d+):[^\n]*\n(?=(?:\s*\n)*(?:## Slide|\Z))", content, re.M)]
    print("--- fidelity report ---")
    print(f"slides in PDF: {n_pages} | sections in md: {n_sections} -> {'OK' if n_pages == n_sections else 'MISMATCH'}")
    print(f"figures awaiting transcription: {len(pending)} {pending[:12]}{'...' if len(pending) > 12 else ''}")
    print(f"empty slide sections: {empty or 'none'}")
    print(f"markdown size: {len(content)} chars (~{len(content) // 4} tokens)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description="Lecture slide PDF -> lean Markdown (+ figure manifest for vision)")
    ap.add_argument("input_pdf")
    ap.add_argument("--out-dir", default=None,
                    help="default: sibling 'converted' dir if PDF sits in 'original', else <pdf dir>/converted")
    ap.add_argument("--inject", action="store_true", help="merge media/<stem>/<id>.md companions, then report")
    ap.add_argument("--report", action="store_true", help="fidelity report only")
    args = ap.parse_args()

    pdf = os.path.abspath(args.input_pdf)
    if not os.path.isfile(pdf):
        sys.exit(f"Error: not found: {pdf}")
    stem = os.path.splitext(os.path.basename(pdf))[0]
    src_dir = os.path.dirname(pdf)
    if args.out_dir:
        out_dir = os.path.abspath(args.out_dir)
    elif os.path.basename(src_dir).lower() == "original":
        out_dir = os.path.join(os.path.dirname(src_dir), "converted")
    else:
        out_dir = os.path.join(src_dir, "converted")
    media_dir = os.path.join(out_dir, "media", stem)
    out_md = os.path.join(out_dir, stem + ".md")
    os.makedirs(out_dir, exist_ok=True)

    if args.report:
        report(pdf, out_md)
    elif args.inject:
        inject(out_md, media_dir, "media/" + stem)
        report(pdf, out_md)
    else:
        extract(pdf, out_md, media_dir, stem)
        report(pdf, out_md)


if __name__ == "__main__":
    main()
