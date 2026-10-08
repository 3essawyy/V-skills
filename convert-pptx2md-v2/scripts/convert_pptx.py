#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PTCM-v2: Advanced PowerPoint (PPTX) to Complete Markdown Converter
------------------------------------------------------------------
Extracts slides, shapes, tables, speaker notes, and embedded images,
synthesizing high-fidelity Markdown adhering to DTCM-v2 visual standards.
"""

import os
import sys
import re
import argparse
from typing import List, Dict, Any, Tuple

try:
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE
    from PIL import Image
    import io
except ImportError as e:
    print(f"Error: Required dependency missing ({e}). Run: pip install python-pptx pillow")
    sys.exit(1)


def github_slugify(text: str) -> str:
    """Generate GitHub-Flavored Markdown (GFM) anchor slug."""
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


def extract_table(table_shape) -> str:
    """Convert native PowerPoint table to clean Markdown table."""
    table = table_shape.table
    rows = []
    for row in table.rows:
        row_vals = [cell.text.strip().replace('\n', ' ') for cell in row.cells]
        rows.append(row_vals)

    if not rows:
        return ""

    headers = rows[0]
    separator = ["---"] * len(headers)
    data_rows = rows[1:]

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(separator) + " |"
    ]
    for r in data_rows:
        lines.append("| " + " | ".join(r) + " |")

    return "\n".join(lines)


def convert_pptx(pptx_path: str, output_md_path: str = None, asset_dir: str = None) -> str:
    if not os.path.exists(pptx_path):
        raise FileNotFoundError(f"File not found: {pptx_path}")

    base_name = os.path.splitext(os.path.basename(pptx_path))[0]
    clean_base = re.sub(r'[^\w\-]', '_', base_name).strip('_')

    if not output_md_path:
        output_md_path = f"{clean_base}.md"

    if not asset_dir:
        asset_dir = os.path.join("assets", clean_base.lower().replace('_', '-'))

    os.makedirs(asset_dir, exist_ok=True)
    prs = Presentation(pptx_path)

    slides_data = []
    all_images_count = 0

    for s_idx, slide in enumerate(prs.slides, 1):
        slide_info = {
            "slide_num": s_idx,
            "title": f"Slide {s_idx:02d}",
            "text_blocks": [],
            "tables": [],
            "hero_images": [],
            "notes": ""
        }

        # 1. Extract speaker notes
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            notes = slide.notes_slide.notes_text_frame.text.strip()
            if notes:
                slide_info["notes"] = notes

        # 2. Extract and classify images
        img_idx = 0
        for shape in slide.shapes:
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                img_idx += 1
                all_images_count += 1
                blob = shape.image.blob
                ext = shape.image.ext
                img_filename = f"slide_{s_idx:02d}_img_{img_idx:02d}.{ext}"
                img_path = os.path.join(asset_dir, img_filename).replace("\\", "/")

                with open(img_path, "wb") as f:
                    f.write(blob)

                # Differentiate hero graphics (> 5KB or > 150x150) vs small icons
                is_hero = False
                try:
                    im = Image.open(io.BytesIO(blob))
                    w, h = im.size
                    if len(blob) > 5120 or (w >= 150 and h >= 150):
                        is_hero = True
                except Exception:
                    if len(blob) > 5120:
                        is_hero = True

                if is_hero:
                    slide_info["hero_images"].append({
                        "path": img_path,
                        "filename": img_filename,
                        "size": len(blob)
                    })

        # 3. Spatially sort text shapes and tables (top, then left)
        shapes_to_sort = []
        for s in slide.shapes:
            if s.has_text_frame or s.has_table:
                shapes_to_sort.append(s)

        shapes_to_sort.sort(key=lambda x: (x.top, x.left))

        # Check for title
        detected_title = None
        for s in shapes_to_sort:
            if s.has_text_frame:
                txt = s.text_frame.text.strip()
                # Skip slide numbering artifact
                if txt in ['‹#›', '#']:
                    continue
                first_line = txt.split('\n')[0].strip()
                if first_line and len(first_line) < 100:
                    detected_title = first_line
                    break

        if detected_title:
            slide_info["title"] = f"Slide {s_idx:02d}: {detected_title}"

        # Collect sorted content
        for s in shapes_to_sort:
            if s.has_table:
                table_md = extract_table(s)
                if table_md:
                    slide_info["tables"].append(table_md)
            elif s.has_text_frame:
                txt = s.text_frame.text.strip()
                if txt and txt not in ['‹#›', '#']:
                    slide_info["text_blocks"].append(txt)

        slides_data.append(slide_info)

    # 4. Generate Master Markdown Document
    md = []
    md.append(f"# {base_name.strip()}\n")
    md.append("> Converted via **PTCM-v2** (PowerPoint to Complete Markdown Standard)\n")
    md.append("---\n")
    md.append("## 📑 Table of Contents\n")

    for s in slides_data:
        slug = github_slugify(s["title"])
        md.append(f"- [{s['title']}](#{slug})")

    md.append("\n---\n")

    for s in slides_data:
        md.append(f"## {s['title']}\n")

        # Attach hero images
        for hero in s["hero_images"]:
            md.append(f"![{s['title']}]({hero['path']})\n")

        # Add text blocks
        for block in s["text_blocks"]:
            # If block looks like Check your understanding or note
            if "check your understanding" in block.lower():
                md.append(f"> ### ✋ Check Your Understanding\n> {block}\n")
            elif len(block.split('\n')) > 1:
                # Multi-line block
                for line in block.split('\n'):
                    line_clean = line.strip()
                    if line_clean:
                        if line_clean.startswith(('•', '-', '*', '–')):
                            md.append(f"* {line_clean.lstrip('•-*– ')}")
                        else:
                            md.append(f"{line_clean}\n")
                md.append("")
            else:
                md.append(f"{block}\n")

        # Add tables
        for t in s["tables"]:
            md.append(t + "\n")

        # Add speaker notes if any
        if s["notes"]:
            md.append(f"> 💡 **Speaker Notes & Facilitator Guidance:**\n> {s['notes']}\n")

        md.append("---\n")

    final_content = "\n".join(md).strip() + "\n"
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write(final_content)

    print(f"✅ Conversion complete: {output_md_path}")
    print(f"   • Slides processed: {len(slides_data)}")
    print(f"   • Images extracted: {all_images_count} (saved to '{asset_dir}')")
    return output_md_path


def main():
    parser = argparse.ArgumentParser(description="Convert PPTX to Complete Markdown (PTCM-v2)")
    parser.add_argument("input_pptx", help="Path to input .pptx file")
    parser.add_argument("output_md", nargs="?", default=None, help="Path to output .md file (optional)")
    parser.add_argument("--asset-dir", default=None, help="Directory to save extracted media (optional)")

    args = parser.parse_args()
    convert_pptx(args.input_pptx, args.output_md, args.asset_dir)


if __name__ == "__main__":
    main()
