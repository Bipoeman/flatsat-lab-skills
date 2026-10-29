#!/usr/bin/env python3
"""
Terminal Capture Utility using Charmbracelet freeze with Text-to-Path Vector SVG conversion.
Eliminates font dependencies and PDF font fallback issues (e.g. Times-Roman) by converting
all glyphs into 100% pure vector SVG <path> elements.
"""

import os
import sys
import subprocess
import base64
import io
import re
import html
import xml.etree.ElementTree as ET
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

def colorize_ansi(line):
    """Adds standard ANSI escape sequences for terminal syntax styling."""
    if line.startswith("==="):
        return f"\033[1;36m{line}\033[0m"
    if "[SYSTEM]" in line:
        line = line.replace("[SYSTEM]", "\033[1;32m[SYSTEM]\033[0m")
    if "[START]" in line:
        line = line.replace("[START]", "\033[1;34m[START]\033[0m")
    if "[RECOVERY]" in line:
        line = line.replace("[RECOVERY]", "\033[1;35m[RECOVERY]\033[0m")
    if "[WARNING]" in line:
        line = line.replace("[WARNING]", "\033[1;33m[WARNING]\033[0m")
    if "[TX]" in line:
        line = line.replace("[TX]", "\033[1;33m[TX]\033[0m")
    if "[RELAY]" in line:
        line = line.replace("[RELAY]", "\033[1;33m[RELAY]\033[0m")
    if "OK!" in line:
        line = line.replace("OK!", "\033[1;32mOK!\033[0m")
    if "TIMEOUT!" in line:
        line = line.replace("TIMEOUT!", "\033[1;31mTIMEOUT!\033[0m")
    if "RF Timeout / Drop." in line:
        line = line.replace("RF Timeout / Drop.", "\033[1;31mRF Timeout / Drop.\033[0m")
    if "RADIATION SPIKE" in line:
        line = f"\033[1;31m{line}\033[0m"
    if "Got RF ACK" in line:
        line = line.replace("Got RF ACK from Ground Station!", "\033[1;32mGot RF ACK from Ground Station!\033[0m")
    if "CHUNK_DATA:" in line:
        line = line.replace("CHUNK_DATA:", "\033[1;35mCHUNK_DATA:\033[0m\033[36m") + "\033[0m"
    return line

def convert_svg_text_to_paths(svg_path, out_path=None):
    """
    Parses a freeze-generated SVG, extracts the embedded JetBrains Mono WOFF2 font,
    and converts all <text> and <tspan> elements into SVG <path> elements.
    Uses xml.etree.ElementTree for robust DOM parsing (ignoring empty self-closing tags).
    """
    if out_path is None:
        out_path = svg_path
        
    with open(svg_path, "r", encoding="utf-8") as f:
        svg_raw = f.read()

    b64_match = re.search(r"base64,([A-Za-z0-9+/=]+)", svg_raw)
    if not b64_match:
        return

    # Load embedded font
    font = TTFont(io.BytesIO(base64.b64decode(b64_match.group(1))))
    glyphSet = font.getGlyphSet()
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    upem = font["head"].unitsPerEm

    # Cache vector glyph paths
    glyph_paths = {}
    for char_code, glyph_name in cmap.items():
        pen = SVGPathPen(glyphSet)
        try:
            glyphSet[glyph_name].draw(pen)
            glyph_paths[chr(char_code)] = pen.getCommands()
        except Exception:
            pass

    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    root = ET.fromstring(svg_raw)

    font_g = None
    for g in root.iter('{http://www.w3.org/2000/svg}g'):
        if 'font-family' in g.attrib:
            font_g = g
            break

    if font_g is None:
        return

    font_size_str = font_g.attrib.get('font-size', '13.00px').replace('px', '')
    font_size = float(font_size_str)
    default_fill = font_g.attrib.get('fill', '#f8f8f2')
    scale = font_size / upem

    # Remove style elements containing woff2 font
    for style in list(root.iter('{http://www.w3.org/2000/svg}style')):
        for parent in root.iter():
            if style in list(parent):
                parent.remove(style)

    paths_g = ET.Element('{http://www.w3.org/2000/svg}g')
    if 'clip-path' in font_g.attrib:
        paths_g.attrib['clip-path'] = font_g.attrib['clip-path']

    for text_elem in font_g.findall('{http://www.w3.org/2000/svg}text'):
        x_val = float(text_elem.attrib.get('x', '0px').replace('px', ''))
        y_val = float(text_elem.attrib.get('y', '0px').replace('px', ''))
        cur_x = x_val

        def render_span(txt, fill_col):
            nonlocal cur_x
            if not txt:
                return
            txt = txt.replace('\xa0', ' ')
            for char in txt:
                adv = 600 * scale
                if char in cmap and cmap[ord(char)] in hmtx:
                    adv = hmtx[cmap[ord(char)]][0] * scale
                if char in glyph_paths and glyph_paths[char]:
                    d = glyph_paths[char]
                    p = ET.SubElement(paths_g, '{http://www.w3.org/2000/svg}path')
                    p.attrib['d'] = d
                    p.attrib['transform'] = f'translate({cur_x:.2f},{y_val:.2f}) scale({scale:.6f},{-scale:.6f})'
                    p.attrib['fill'] = fill_col
                cur_x += adv

        if text_elem.text:
            render_span(text_elem.text, default_fill)

        for child in text_elem:
            child_fill = child.attrib.get('fill', default_fill)
            if child.text:
                render_span(child.text, child_fill)
            if child.tail:
                render_span(child.tail, default_fill)

    for parent in root.iter():
        children = list(parent)
        if font_g in children:
            idx = children.index(font_g)
            parent.remove(font_g)
            parent.insert(idx, paths_g)
            break

    out_bytes = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    with open(out_path, 'wb') as f:
        f.write(out_bytes)

def capture_terminal_output(lines, output_svg_path, width=888, height=450, font_size=13, theme="dracula"):
    """
    Runs charmbracelet freeze and generates a pure vector SVG with text converted to paths.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_svg_path)), exist_ok=True)
    ansi_lines = [colorize_ansi(l) for l in lines]
    tmp_txt = output_svg_path + ".tmp.txt"
    with open(tmp_txt, "w") as f:
        f.write("\n".join(ansi_lines))
        
    cmd = [
        "freeze", tmp_txt,
        "-l", "ansi",
        "--window",
        "--theme", theme,
        "--width", str(width),
        "--height", str(height),
        "--font.size", str(font_size),
        "--line-height", "1.3",
        "-o", output_svg_path
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        if output_svg_path.endswith(".svg"):
            convert_svg_text_to_paths(output_svg_path)
            print(f"[FREEZE] Vector SVG (text outlines as paths): {output_svg_path} ({width}x{height})")
    finally:
        if os.path.exists(tmp_txt):
            os.remove(tmp_txt)

if __name__ == "__main__":
    test_lines = [
        "=== FlatSat Node: Serial Terminal ===",
        "[SYSTEM] Booting subsystem... OK!",
        "[START] Mission test sequence running...",
        "[TX] Transmitting telemetry packets to ground... OK!"
    ]
    capture_terminal_output(test_lines, "artifact/test_skill_capture.svg", width=888, height=350)

