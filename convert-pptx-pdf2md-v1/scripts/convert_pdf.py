#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ptcm-pdf-v1: Presentation PDF to Complete Markdown Converter (DTCM-v3 Aesthetic Edition)
----------------------------------------------------------------------------------------
Specialized slide deck ingestion and conversion engine for Gemini CLI.
Features:
- Full DTCM-v3 Executive Styling: Metadata banner, Table of Contents, List of Figures
- 2D Spatial Canvas Reconstruction: Title isolation, corner slide numbers, nested bullets
- Auto-Bolding Lead-in Keyphrases: Formats colon-delimited terms into * **Term:** Detail
- Universal Visual Asset Evaluation: Universal classification (Mermaid vs Pure Image vs Math)
- Dual Visual Co-existence: Stacked Mermaid diagram + visible PNG with formal sequential Figure captions
- Hybrid Visual Extraction: Intercepts raster bitmaps + clusters vector drawing paths
- Partitioned Manifest: images_manifest.json chunked into <= 30 item batches with bullet context
- 3-Stage DTCM-v3 Lifecycle: Extract -> Agent Vision Transcription -> Syntax-Guarded Dual Injection
"""

import os
import sys
import re
import json
import argparse
import unicodedata
from typing import List, Dict, Any, Tuple, Optional

try:
    import pymupdf  # PyMuPDF
    from PIL import Image
    import io
except ImportError as e:
    print(f"Error: Required dependency missing ({e}). Run: pip install pymupdf pillow")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Formatting & Text Enhancement Helpers
# ---------------------------------------------------------------------------

def normalize_text_and_math(text: str) -> str:
    """Normalize mathematical unicode characters and symbols while preserving formatting."""
    norm = unicodedata.normalize('NFKC', text)
    norm = norm.replace('\u2022', '').replace('\u2013', '').replace('\u2014', '')
    norm = norm.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    return norm.strip()


def github_slugify(text: str) -> str:
    """Generate clean GitHub-Flavored Markdown (GFM) anchor slug."""
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    text = re.sub(r'<.*?>', '', text)
    text = text.lower()
    cleaned = []
    for ch in text:
        if ch.isalnum() or ch in [' ', '-', '_']:
            cleaned.append(ch)
        elif ch == '—':
            cleaned.append('-')
    res = "".join(cleaned)
    res = re.sub(r'\s+', '-', res)
    res = re.sub(r'-+', '-', res)
    return res.strip('-')


def format_bullet_line(raw_line: str, is_level_2: bool = False) -> str:
    """
    Format a raw bullet line with DTCM-v3 bold lead-in keyphrases.
    e.g. 'Grading Policy: Midterm 20%' -> '* **Grading Policy:** Midterm 20%'
    """
    clean = normalize_text_and_math(raw_line)
    if not clean:
        return ""

    indent = "  * " if is_level_2 else "* "

    # Check for colon delimiter for lead-in bolding
    if ":" in clean and not clean.startswith("http"):
        parts = clean.split(":", 1)
        lead_in = parts[0].strip()
        rest = parts[1].strip()
        # Only bold if lead-in is concise (1-5 words)
        if 0 < len(lead_in.split()) <= 6:
            if rest:
                return f"{indent}**{lead_in}:** {rest}"
            else:
                return f"{indent}**{lead_in}:**"

    # Check for dash delimiter (e.g. 'Midterm - 20%')
    if " - " in clean:
        parts = clean.split(" - ", 1)
        lead_in = parts[0].strip()
        rest = parts[1].strip()
        if 0 < len(lead_in.split()) <= 5:
            return f"{indent}**{lead_in}:** {rest}"

    return f"{indent}{clean}"


# ---------------------------------------------------------------------------
# Visual Asset Model & Universal Evaluator
# ---------------------------------------------------------------------------

class SlideAsset:
    def __init__(self, asset_id: str, slide_num: int, asset_type: str, bbox: Tuple[float, float, float, float],
                 file_path: str, title: str = "", byte_size: int = 0, is_jpeg: bool = False):
        self.asset_id = asset_id
        self.slide_num = slide_num
        self.asset_type = asset_type          # 'raster_image' | 'vector_crop'
        self.bbox = bbox                      # (x0, y0, x1, y1)
        self.file_path = file_path
        self.title = title
        self.byte_size = byte_size
        self.is_jpeg = is_jpeg
        self.figure_number = 0
        self.figure_description = ""
        self.transcription_target = "mermaid" # 'mermaid' | 'latex' | 'table' | 'image'
        self.skip_diagram_synthesis = False
        self.preceding_text: List[str] = []
        self.following_text: List[str] = []

    def evaluate_and_classify(self):
        """
        Universal Visual Asset Evaluator:
        Classifies asset into appropriate transcription target vs pure image link.
        """
        width = self.bbox[2] - self.bbox[0]
        height = self.bbox[3] - self.bbox[1]

        # 1. Raster Images
        if self.asset_type == "raster_image":
            # Real-world photos, web screenshots, or large JPEG collages (like Slide 42)
            if self.is_jpeg or self.byte_size > 120000 or (width > 400 and height > 250):
                self.transcription_target = "image"
                self.skip_diagram_synthesis = True
                self.figure_description = "Visual Illustration & Context Reference"
            else:
                # Smaller PNG bitmaps (icons, simple charts)
                self.transcription_target = "mermaid"
                self.skip_diagram_synthesis = False
                self.figure_description = "Architectural Diagram / Flowchart"

        # 2. Vector Drawing Crops
        else:
            # Check aspect ratio & dimensions
            if height < 60 and width > 100:
                self.transcription_target = "latex"
                self.skip_diagram_synthesis = False
                self.figure_description = "Mathematical Derivation & Formulas"
            elif width > 180 and height > 100:
                # Flowcharts, reinforcement learning feedback loops (Slide 62, 63)
                self.transcription_target = "mermaid"
                self.skip_diagram_synthesis = False
                self.figure_description = "System Flowchart & Process Architecture"
            else:
                self.transcription_target = "mermaid"
                self.skip_diagram_synthesis = False
                self.figure_description = "Conceptual Diagram & State Representation"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.asset_id,
            "figure_number": self.figure_number,
            "slide_number": self.slide_num,
            "slide_title": self.title,
            "asset_type": self.asset_type,
            "file_path": self.file_path,
            "bbox": [round(coord, 1) for coord in self.bbox],
            "transcription_target": self.transcription_target,
            "skip_diagram_synthesis": self.skip_diagram_synthesis,
            "figure_description": self.figure_description,
            "context": {
                "preceding_bullets": self.preceding_text,
                "following_bullets": self.following_text
            }
        }


# ---------------------------------------------------------------------------
# Vector Drawing & Visual Clustering Engine
# ---------------------------------------------------------------------------

def find_vector_drawing_clusters(page: pymupdf.Page, min_drawings: int = 3,
                                 margin_x: float = 45.0, margin_y: float = 25.0) -> List[pymupdf.Rect]:
    """Cluster vector drawing paths into unified diagram bounding boxes."""
    page_w, page_h = page.rect.width, page.rect.height
    drawings = page.get_drawings()
    if not drawings:
        return []

    candidate_rects = []
    for d in drawings:
        r = pymupdf.Rect(d['rect'])
        if r.width >= page_w * 0.90 and r.height >= page_h * 0.90:
            continue
        if r.width <= 0 or r.height <= 0:
            continue
        if r.width >= page_w * 0.85 and r.height <= 3:
            continue
        candidate_rects.append(r)

    if len(candidate_rects) < min_drawings:
        return []

    clusters: List[pymupdf.Rect] = []
    for r in candidate_rects:
        merged = False
        for i, c in enumerate(clusters):
            expanded = pymupdf.Rect(c.x0 - margin_x, c.y0 - margin_y, c.x1 + margin_x, c.y1 + margin_y)
            if expanded.intersects(r):
                clusters[i] = c | r
                merged = True
                break
        if not merged:
            clusters.append(pymupdf.Rect(r))

    changed = True
    while changed:
        changed = False
        new_clusters = []
        skip_indices = set()
        for i in range(len(clusters)):
            if i in skip_indices:
                continue
            curr = clusters[i]
            for j in range(i + 1, len(clusters)):
                if j in skip_indices:
                    continue
                expanded = pymupdf.Rect(curr.x0 - margin_x, curr.y0 - margin_y, curr.x1 + margin_x, curr.y1 + margin_y)
                if expanded.intersects(clusters[j]):
                    curr = curr | clusters[j]
                    skip_indices.add(j)
                    changed = True
            new_clusters.append(curr)
        clusters = new_clusters

    # Merge neighboring non-bullet text labels (axis labels, diagram node labels)
    raw_blocks = page.get_text("blocks")
    for b in raw_blocks:
        b_rect = pymupdf.Rect(b[:4])
        b_txt = b[4].strip()
        if not b_txt or '•' in b_txt or len(b_txt.split('\n')) > 3:
            continue
        for i, c in enumerate(clusters):
            expanded = pymupdf.Rect(c.x0 - 15, c.y0 - 15, c.x1 + 15, c.y1 + 15)
            if expanded.intersects(b_rect):
                clusters[i] = c | b_rect
                break

    significant_clusters = []
    for c in clusters:
        if c.width >= 50 and c.height >= 35:
            padded = pymupdf.Rect(
                max(0, c.x0 - 6),
                max(0, c.y0 - 6),
                min(page_w, c.x1 + 6),
                min(page_h, c.y1 + 6)
            )
            significant_clusters.append(padded)

    significant_clusters.sort(key=lambda r: (r.y0, r.x0))
    return significant_clusters


# ---------------------------------------------------------------------------
# Slide Parsing & Metadata Extraction Engine
# ---------------------------------------------------------------------------

class SlideContent:
    def __init__(self, slide_num: int, width: float, height: float):
        self.slide_num = slide_num
        self.width = width
        self.height = height
        self.title = f"Slide {slide_num}"
        self.slide_number_raw = str(slide_num)
        self.blocks: List[Dict[str, Any]] = []
        self.assets: List[SlideAsset] = []


def extract_deck_metadata(doc: pymupdf.Document, default_stem: str) -> Dict[str, str]:
    """Parse Slide 1 to extract course title, lecturer, term, and presentation subject."""
    meta = {
        "title": default_stem,
        "course": "Computer Science & Engineering",
        "term": "Academic Lecture Series",
        "lecturer": "Course Instructor",
        "source": "Official Lecture Presentation Slides"
    }

    if len(doc) == 0:
        return meta

    p1 = doc[0]
    p1_dict = p1.get_text("dict")
    spans = []
    for b in p1_dict.get("blocks", []):
        if "lines" in b:
            for l in b["lines"]:
                for s in l["spans"]:
                    txt = s["text"].strip()
                    if txt:
                        spans.append((s["size"], txt))

    # Sort spans by font size descending
    spans_by_size = sorted(spans, key=lambda x: x[0], reverse=True)

    # Detect largest text as main title
    if spans_by_size:
        main_titles = [txt for sz, txt in spans_by_size if sz >= spans_by_size[0][0] - 4]
        if main_titles:
            meta["title"] = " — ".join(main_titles[:2])

    for sz, txt in spans:
        if "PhD" in txt or "Prof" in txt or "Dr" in txt or "Bayoumi" in txt:
            meta["lecturer"] = txt
        elif "Spring" in txt or "Fall" in txt or "Summer" in txt or "202" in txt:
            meta["term"] = txt
        elif "Classification" in txt or "Intelligence" in txt or "Learning" in txt or "Networks" in txt:
            meta["course"] = txt

    return meta


def parse_slide(page: pymupdf.Page, slide_num: int, asset_dir: str, zoom: float = 2.0) -> SlideContent:
    """Parse a single slide, extracting titles, bullets, and assets in spatial order."""
    page_w, page_h = page.rect.width, page.rect.height
    slide = SlideContent(slide_num, page_w, page_h)

    page_dict = page.get_text("dict")
    raw_blocks = page_dict.get("blocks", [])

    detected_title = ""
    max_title_font_size = 0.0
    text_items = []

    for b in raw_blocks:
        if "lines" not in b:
            continue
        b_bbox = b["bbox"]
        b_x0, b_y0, b_x1, b_y1 = b_bbox

        block_text_parts = []
        block_max_font = 0.0
        is_bullet_level_1 = False
        is_bullet_level_2 = False

        for line in b["lines"]:
            line_parts = []
            for s in line["spans"]:
                txt = s["text"]
                sz = s["size"]
                if sz > block_max_font:
                    block_max_font = sz
                if '•' in txt:
                    is_bullet_level_1 = True
                elif '–' in txt or '—' in txt:
                    is_bullet_level_2 = True
                line_parts.append(txt)
            block_text_parts.append("".join(line_parts))

        full_raw_text = "\n".join(block_text_parts).strip()
        if not full_raw_text:
            continue

        # Corner slide number detection
        norm_digits = full_raw_text.strip()
        if norm_digits.isdigit() and len(norm_digits) <= 3:
            if (b_y0 > page_h * 0.80) or (b_y0 < page_h * 0.15 and b_x0 > page_w * 0.75):
                slide.slide_number_raw = norm_digits
                continue

        # Title detection
        if b_y0 < page_h * 0.30 and block_max_font > max_title_font_size and len(full_raw_text.split('\n')) <= 3:
            if not is_bullet_level_1 and not is_bullet_level_2:
                max_title_font_size = block_max_font
                detected_title = normalize_text_and_math(full_raw_text.replace('\n', ' '))

        text_items.append({
            "type": "text",
            "bbox": b_bbox,
            "raw_text": full_raw_text,
            "max_font": block_max_font,
            "is_l1": is_bullet_level_1,
            "is_l2": is_bullet_level_2,
            "y0": b_y0,
            "x0": b_x0
        })

    slide.title = detected_title if detected_title else f"Slide {slide_num}"

    # Extract Raster Images
    raster_assets = []
    image_list = page.get_images(full=True)
    os.makedirs(asset_dir, exist_ok=True)

    for img_idx, img_info in enumerate(image_list):
        xref = img_info[0]
        base_image = page.parent.extract_image(xref)
        image_bytes = base_image["image"]
        image_ext = base_image["ext"]

        if len(image_bytes) < 1500:
            continue

        rects = page.get_image_rects(xref)
        img_bbox = rects[0] if rects else pymupdf.Rect(page_w * 0.2, page_h * 0.3, page_w * 0.8, page_h * 0.7)

        asset_id = f"slide_{slide_num:02d}_img_{img_idx+1:02d}"
        file_name = f"{asset_id}.{image_ext}"
        rel_path = os.path.join(os.path.basename(asset_dir), file_name).replace("\\", "/")
        full_path = os.path.join(asset_dir, file_name)

        with open(full_path, "wb") as f_img:
            f_img.write(image_bytes)

        asset = SlideAsset(
            asset_id=asset_id,
            slide_num=slide_num,
            asset_type="raster_image",
            bbox=(img_bbox.x0, img_bbox.y0, img_bbox.x1, img_bbox.y1),
            file_path=rel_path,
            title=slide.title,
            byte_size=len(image_bytes),
            is_jpeg=(image_ext.lower() in ['jpg', 'jpeg'])
        )
        asset.evaluate_and_classify()
        raster_assets.append(asset)

    # Extract Vector Drawing Clusters
    vector_assets = []
    vector_clusters = find_vector_drawing_clusters(page, min_drawings=3, margin_x=45.0, margin_y=25.0)

    for v_idx, v_rect in enumerate(vector_clusters):
        overlaps_raster = False
        for r_asset in raster_assets:
            r_rect = pymupdf.Rect(r_asset.bbox)
            if v_rect.intersects(r_rect) and (v_rect & r_rect).get_area() > 0.5 * min(v_rect.get_area(), r_rect.get_area()):
                overlaps_raster = True
                break
        if overlaps_raster:
            continue

        asset_id = f"slide_{slide_num:02d}_fig_{v_idx+1:02d}"
        file_name = f"{asset_id}.png"
        rel_path = os.path.join(os.path.basename(asset_dir), file_name).replace("\\", "/")
        full_path = os.path.join(asset_dir, file_name)

        mat = pymupdf.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, clip=v_rect)
        pix.save(full_path)

        asset = SlideAsset(
            asset_id=asset_id,
            slide_num=slide_num,
            asset_type="vector_crop",
            bbox=(v_rect.x0, v_rect.y0, v_rect.x1, v_rect.y1),
            file_path=rel_path,
            title=slide.title,
            byte_size=len(pix.tobytes()),
            is_jpeg=False
        )
        asset.evaluate_and_classify()
        vector_assets.append(asset)

    all_assets = raster_assets + vector_assets
    slide.assets = all_assets

    # Integrate Content Elements
    content_elements = []
    filtered_text_items = []

    for item in text_items:
        clean = normalize_text_and_math(item["raw_text"])
        if clean == slide.title and item["max_font"] >= max_title_font_size:
            continue

        is_internal_label = False
        item_rect = pymupdf.Rect(item["bbox"])
        for asset in all_assets:
            a_rect = pymupdf.Rect(asset.bbox)
            if a_rect.contains(item_rect) or ((a_rect & item_rect).get_area() > 0.65 * item_rect.get_area()):
                if not item["is_l1"]:
                    is_internal_label = True
                    break
        if is_internal_label:
            continue
        filtered_text_items.append(item)

    for item in filtered_text_items:
        content_elements.append({
            "kind": "text",
            "y0": item["y0"],
            "x0": item["x0"],
            "data": item
        })

    for asset in all_assets:
        content_elements.append({
            "kind": "asset",
            "y0": asset.bbox[1],
            "x0": asset.bbox[0],
            "data": asset
        })

    content_elements.sort(key=lambda el: (el["y0"], el["x0"]))
    slide.blocks = content_elements

    # Populate surrounding bullet context
    for idx, el in enumerate(content_elements):
        if el["kind"] == "asset":
            asset_obj: SlideAsset = el["data"]
            preceding = []
            for prev_idx in range(idx - 1, -1, -1):
                prev_el = content_elements[prev_idx]
                if prev_el["kind"] == "text":
                    txt = normalize_text_and_math(prev_el["data"]["raw_text"])
                    if txt:
                        preceding.insert(0, txt)
                if len(preceding) >= 3:
                    break

            following = []
            for next_idx in range(idx + 1, len(content_elements)):
                next_el = content_elements[next_idx]
                if next_el["kind"] == "text":
                    txt = normalize_text_and_math(next_el["data"]["raw_text"])
                    if txt:
                        following.append(txt)
                if len(following) >= 3:
                    break

            asset_obj.preceding_text = preceding
            asset_obj.following_text = following

    return slide


# ---------------------------------------------------------------------------
# DTCM-v3 Markdown Document Synthesis
# ---------------------------------------------------------------------------

def render_slide_to_markdown(slide: SlideContent) -> str:
    """Render a single slide with DTCM-v3 typography, bold lead-ins, and figure captions."""
    md_lines = []
    slug = github_slugify(f"slide-{slide.slide_num}-{slide.title}")
    
    md_lines.append(f"<a id=\"{slug}\"></a>")
    md_lines.append(f"### Slide {slide.slide_num}: {slide.title}\n")

    for el in slide.blocks:
        if el["kind"] == "text":
            item = el["data"]
            raw = item["raw_text"]
            lines = raw.split("\n")
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    continue
                formatted_bullet = format_bullet_line(stripped, is_level_2=item["is_l2"])
                if formatted_bullet:
                    md_lines.append(formatted_bullet)

        elif el["kind"] == "asset":
            asset: SlideAsset = el["data"]
            md_lines.append(f"\n<!-- INJECT_START: {asset.asset_id} -->")
            md_lines.append(f"![{slide.title} ({asset.asset_id})]({asset.file_path})")
            md_lines.append(f"\n**Figure {asset.figure_number}:** [Slide {slide.slide_num}] {slide.title} — {asset.figure_description}")
            md_lines.append(f"<!-- INJECT_END: {asset.asset_id} -->\n")

    md_lines.append("\n---\n")
    return "\n".join(md_lines)


def generate_full_document(all_slides: List[SlideContent], all_assets: List[SlideAsset],
                           meta: Dict[str, str], pdf_stem: str) -> str:
    """Generate the full executive DTCM-v3 Markdown document."""
    doc_lines = []

    # 1. Executive Metadata Banner
    doc_lines.append(f"# {meta['title']}\n")
    doc_lines.append("### Comprehensive Technical Presentation & Study Guide\n")
    doc_lines.append(f"> **Course / Domain:** {meta['course']} · **Academic Term:** {meta['term']}")
    doc_lines.append(f"> **Lecturer / Author:** {meta['lecturer']} · **Source:** {meta['source']}")
    doc_lines.append("> **Documentation Standard:** DTCM-v3 High-Fidelity Architecture (`ptcm-pdf-v1`)\n")
    doc_lines.append("---\n")

    # 2. Table of Contents
    doc_lines.append("## Table of Contents\n")
    for s in all_slides:
        slug = github_slugify(f"slide-{s.slide_num}-{s.title}")
        doc_lines.append(f"* [Slide {s.slide_num}: {s.title}](#{slug})")
    doc_lines.append("\n---\n")

    # 3. List of Figures
    if all_assets:
        doc_lines.append("## List of Figures\n")
        for asset in all_assets:
            target_badge = "📊 Flowchart" if asset.transcription_target == "mermaid" else ("📐 Formula" if asset.transcription_target == "latex" else "🖼️ Visual")
            doc_lines.append(f"* **Figure {asset.figure_number}:** [Slide {asset.slide_num}] {asset.title} — *{asset.figure_description}* (`{target_badge}`)")
        doc_lines.append("\n---\n")

    # 4. Slide Content Body
    for s in all_slides:
        doc_lines.append(render_slide_to_markdown(s))

    return "\n".join(doc_lines)


# ---------------------------------------------------------------------------
# Manifest Generation & Partitioning
# ---------------------------------------------------------------------------

def generate_partitioned_manifest(all_assets: List[SlideAsset], output_dir: str, batch_size: int = 30) -> str:
    """Generate auto-chunked images_manifest.json with universal classification."""
    manifest_data: Dict[str, Any] = {
        "generator": "ptcm-pdf-v1 (DTCM-v3 Edition)",
        "total_assets": len(all_assets),
        "batch_size": batch_size,
        "batches": {}
    }

    current_batch_idx = 1
    current_batch_list = []

    for idx, asset in enumerate(all_assets):
        current_batch_list.append(asset.to_dict())
        if len(current_batch_list) >= batch_size or idx == len(all_assets) - 1:
            batch_key = f"batch_{current_batch_idx}"
            manifest_data["batches"][batch_key] = current_batch_list
            current_batch_list = []
            current_batch_idx += 1

    manifest_path = os.path.join(output_dir, "images_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)

    return manifest_path


# ---------------------------------------------------------------------------
# Stage 3: Syntax Guard & Dual Stacked Injection Engine
# ---------------------------------------------------------------------------

def validate_mermaid_or_math(content: str) -> Tuple[bool, str]:
    """Validate Mermaid code blocks or LaTeX display math delimiters."""
    if "```mermaid" in content:
        if content.count("```") % 2 != 0:
            return False, "Unbalanced code fence backticks."
        valid_headers = [
            "flowchart", "graph", "sequenceDiagram", "classDiagram",
            "stateDiagram", "stateDiagram-v2", "erDiagram", "gantt",
            "pie", "quadrantChart", "mindmap", "timeline", "xychart-beta"
        ]
        if not any(h in content for h in valid_headers):
            return False, "Missing valid Mermaid diagram declaration header."

    if "$$" in content:
        if content.count("$$") % 2 != 0:
            return False, "Unbalanced $$ LaTeX display math delimiters."

    return True, "Valid"


def inject_transcriptions(markdown_path: str, media_dir: str) -> Tuple[int, int]:
    """
    Inject transcribed companion files (media/image_X.md) using the DTCM-v3 Dual Stacked layout:
    Transcribed Mermaid / LaTeX block directly followed by the visible PNG image & formal caption.
    """
    if not os.path.exists(markdown_path):
        raise FileNotFoundError(f"Markdown file not found: {markdown_path}")

    with open(markdown_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(
        r'<!-- INJECT_START:\s*([a-zA-Z0-9_\-]+)\s*-->\s*(.*?)\s*<!-- INJECT_END:\s*\1\s*-->',
        re.DOTALL
    )

    injected_count = 0
    skipped_count = 0

    def replacer(match):
        nonlocal injected_count, skipped_count
        asset_id = match.group(1)
        original_block = match.group(2).strip()

        companion_path = os.path.join(media_dir, f"{asset_id}.md")
        if not os.path.exists(companion_path):
            skipped_count += 1
            return match.group(0)

        with open(companion_path, "r", encoding="utf-8") as cf:
            transcription = cf.read().strip()

        is_valid, reason = validate_mermaid_or_math(transcription)
        if not is_valid:
            print(f"Warning: Syntax validation failed for {asset_id} ({reason}). Preserving original fallback.")
            skipped_count += 1
            return match.group(0)

        injected_count += 1

        # Dual Stacked Layout: Transcribed diagram directly followed by visible PNG and caption
        replacement = (
            f"<!-- INJECT_START: {asset_id} -->\n"
            f"{transcription}\n\n"
            f"{original_block}\n"
            f"<!-- INJECT_END: {asset_id} -->"
        )
        return replacement

    updated_content = pattern.sub(replacer, content)

    with open(markdown_path, "w", encoding="utf-8") as f:
        f.write(updated_content)

    return injected_count, skipped_count


# ---------------------------------------------------------------------------
# CLI Orchestrator & Multi-Mode Driver
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="ptcm-pdf-v1: Presentation PDF to Complete Markdown Converter (DTCM-v3 Aesthetic Edition)"
    )
    parser.add_argument("input_pdf", help="Path to input presentation PDF file")
    parser.add_argument("output_path", nargs="?", default=None, help="Output Markdown path or structured directory")
    parser.add_argument("--asset-dir", default=None, help="Custom asset directory for media/visuals")
    parser.add_argument("--manifest", action="store_true", help="Generate partitioned images_manifest.json")
    parser.add_argument("--inject", action="store_true", help="Inject transcribed media/image_X.md files into Markdown")
    parser.add_argument("--structured", action="store_true", help="Generate modular multi-chapter slide files with index")
    parser.add_argument("--zoom", type=float, default=2.0, help="Rendering scale for vector diagram crops (default 2.0 = 144 DPI)")

    args = parser.parse_args()

    input_pdf = os.path.abspath(args.input_pdf)
    if not os.path.exists(input_pdf):
        print(f"Error: Input PDF file not found: {input_pdf}")
        sys.exit(1)

    pdf_stem = os.path.splitext(os.path.basename(input_pdf))[0]
    workspace_dir = os.path.dirname(input_pdf)

    # Every PDF gets its own dedicated folder to prevent cross-document collision
    if args.output_path:
        raw_target = os.path.abspath(args.output_path)
        if raw_target.endswith(".md"):
            out_target = raw_target
            pdf_folder = os.path.dirname(out_target)
        else:
            if os.path.basename(raw_target).lower() == pdf_stem.lower():
                pdf_folder = raw_target
            else:
                pdf_folder = os.path.join(raw_target, pdf_stem)
            out_target = os.path.join(pdf_folder, f"{pdf_stem}.md")
    else:
        if os.path.basename(workspace_dir).lower() == pdf_stem.lower():
            pdf_folder = workspace_dir
        else:
            pdf_folder = os.path.join(workspace_dir, pdf_stem)
        out_target = os.path.join(pdf_folder, f"{pdf_stem}.md")

    if args.asset_dir:
        asset_dir = os.path.abspath(args.asset_dir)
    else:
        asset_dir = os.path.join(pdf_folder, "media")

    os.makedirs(pdf_folder, exist_ok=True)
    os.makedirs(asset_dir, exist_ok=True)

    if args.inject:
        md_file = out_target if os.path.isfile(out_target) else os.path.join(pdf_folder, f"{pdf_stem}.md")
        print(f"Injecting transcribed visual companion files into: {md_file}")
        injected, skipped = inject_transcriptions(md_file, asset_dir)
        print(f"Injection complete: {injected} assets injected, {skipped} skipped.")
        return

    # Stage 1: Extraction & Conversion
    print(f"Opening presentation PDF: {input_pdf}")
    doc = pymupdf.open(input_pdf)
    total_pages = len(doc)
    print(f"Total Slides: {total_pages}")
    print(f"Output Asset Directory: {asset_dir}")

    meta = extract_deck_metadata(doc, pdf_stem)
    all_slides: List[SlideContent] = []
    all_assets: List[SlideAsset] = []

    global_fig_counter = 1
    for page_idx in range(total_pages):
        page = doc[page_idx]
        slide = parse_slide(page, slide_num=page_idx + 1, asset_dir=asset_dir, zoom=args.zoom)
        for asset in slide.assets:
            asset.figure_number = global_fig_counter
            global_fig_counter += 1
        all_slides.append(slide)
        all_assets.extend(slide.assets)

    print(f"Extraction complete: {len(all_assets)} visual assets harvested (raster + vector crops).")

    if args.manifest or len(all_assets) > 0:
        manifest_dir = pdf_folder
        manifest_file = generate_partitioned_manifest(all_assets, manifest_dir, batch_size=30)
        print(f"Generated partitioned manifest: {manifest_file}")

    full_md = generate_full_document(all_slides, all_assets, meta, pdf_stem)
    full_md_path = out_target if out_target.endswith(".md") else os.path.join(out_target, f"{pdf_stem}.md")

    os.makedirs(os.path.dirname(full_md_path), exist_ok=True)
    with open(full_md_path, "w", encoding="utf-8") as f_out:
        f_out.write(full_md)

    print(f"Successfully generated DTCM-v3 styled Markdown: {full_md_path}")


if __name__ == "__main__":
    main()
