#!/usr/bin/env python3
"""
Generic FlatSat Lab PDF Engine.
Fills arbitrary FlatSat Lab PDFs with:
1. High-resolution HarfBuzz-shaped Thai & English text using TH Sarabun New.
2. 100% Vector SVGs for terminal screenshots without font distortion.
3. Automated box discovery and placement.
"""

import os
import sys
import fitz
from PIL import Image, ImageDraw, ImageFont

DEFAULT_FONT = "fonts/THSarabunNew.ttf"
DEFAULT_COLOR = (10, 40, 180)  # Royal Navy Blue

class FlatSatPdfFiller:
    def __init__(self, input_pdf_path, font_path=DEFAULT_FONT):
        if not os.path.exists(input_pdf_path):
            raise FileNotFoundError(f"Input PDF '{input_pdf_path}' not found!")
        self.input_pdf_path = input_pdf_path
        self.font_path = font_path
        self.doc = fitz.open(input_pdf_path)

    def render_text_image(self, lines, width_pt, height_pt, font_size_pt=10.0, color=DEFAULT_COLOR, line_spacing_factor=1.35):
        """Renders text with HarfBuzz complex text shaping to RGBA image."""
        scale = 3  # 300 DPI
        w_px = max(1, int(width_pt * scale))
        h_px = max(1, int(height_pt * scale))
        img = Image.new("RGBA", (w_px, h_px), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        font = ImageFont.truetype(self.font_path, int(font_size_pt * scale))
        y = int(2 * scale)
        line_h = int(font_size_pt * scale * line_spacing_factor)
        for line in lines:
            draw.text((int(2 * scale), y), line, font=font, fill=(color[0], color[1], color[2], 255))
            y += line_h
        return img

    def add_text(self, page_index, lines, rect, font_size_pt=10.0, color=DEFAULT_COLOR, line_spacing_factor=1.35):
        """Inserts rendered text block into page at rect."""
        page = self.doc[page_index]
        w = rect.x1 - rect.x0
        h = rect.y1 - rect.y0
        img = self.render_text_image(lines, w, h, font_size_pt, color, line_spacing_factor)
        
        tmp_path = f"/tmp/flatsat_text_{page_index}_{int(rect.y0)}_{int(rect.x0)}.png"
        img.save(tmp_path)
        page.insert_image(rect, filename=tmp_path, keep_proportion=False)
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    def add_vector_svg(self, page_index, svg_path, rect):
        """Inserts pure vector SVG (with text outlines as paths) into page."""
        if not os.path.exists(svg_path):
            print(f"[WARN] SVG '{svg_path}' not found, skipping.")
            return
        page = self.doc[page_index]
        inner_rect = fitz.Rect(rect.x0 + 4, rect.y0 + 4, rect.x1 - 4, rect.y1 - 4)
        svg_doc = fitz.open(svg_path)
        svg_pdf_bytes = svg_doc.convert_to_pdf()
        svg_pdf = fitz.open("pdf", svg_pdf_bytes)
        page.show_pdf_page(inner_rect, svg_pdf, 0, keep_proportion=False)
        print(f"[PDF] Inserted vector SVG '{os.path.basename(svg_path)}' into Page {page_index + 1}")

    def find_terminal_boxes(self, page_index):
        """Scans page for terminal output placeholder rectangles."""
        page = self.doc[page_index]
        drawings = page.get_drawings()
        candidate_rects = []
        for d in drawings:
            r = d.get("rect")
            if r and r.width > 300 and r.height > 60:
                candidate_rects.append(r)
        return candidate_rects

    def save(self, output_pdf_path):
        self.doc.save(output_pdf_path)
        self.doc.close()
        print(f"[SUCCESS] Saved answered PDF to {output_pdf_path}")

if __name__ == "__main__":
    print("FlatSat PDF Engine Module Ready.")

