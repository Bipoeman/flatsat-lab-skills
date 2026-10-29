# Terminal Capture with Charmbracelet Freeze & Vector Path Conversion

## 1. The Challenge with Freeze SVGs in PDFs
Charmbracelet `freeze` generates high-quality terminal mockups with macOS window controls and syntax highlighting. However, when freeze outputs SVG:
- Freeze embeds `JetBrains Mono` as base64-encoded **WOFF2** inside `<style>@font-face</style>`.
- PDF conversion engines (like PyMuPDF `fitz.open().convert_to_pdf()`) and many standard PDF tools **do not support WOFF2 fonts inside SVGs**.
- As a consequence, the PDF converter discards the font and silently falls back to **Times-Roman (Serif)**, corrupting the code terminal appearance.

## 2. The Solution: Text-to-Path Conversion
Convert all glyphs in the SVG into raw vector `<path d="...">` outlines:
1. Extract the base64 WOFF2 font from the freeze SVG `<style>`.
2. Load the font using Python `fontTools.ttLib.TTFont` (supported by `brotli`).
3. For each character, extract its exact Bezier vector curves using `fontTools.pens.svgPathPen.SVGPathPen`.
4. Parse the SVG DOM using `xml.etree.ElementTree` (robust XML parser that cleanly ignores self-closing empty tags like `<tspan xml:space="preserve"/>`).
5. Replace `<text>` and `<tspan>` elements with `<path d="..." transform="translate(x, y) scale(s, -s)" fill="...">`.
6. Remove the `<style>` tag.

## 3. Benefits
- **Zero Font Substitution**: In PDF, PyMuPDF translates SVG paths into native PDF vector operators (`m`, `l`, `c`, `f`). It will never fall back to Times-Roman.
- **Infinite Resolution**: Mathematically sharp vector graphics at any zoom level.
- **Self-Contained**: The SVG file has no external font dependencies and renders identically in browsers, Illustrator, Figma, and PDF viewers.

## 4. Freeze CLI Parameters
Recommended parameters for FlatSat terminal captures:
```bash
freeze <input.txt> \
  -l ansi \
  --window \
  --theme dracula \
  --width 888 \
  --height <height> \
  --font.size 13 \
  --line-height 1.3 \
  -o <output.svg>
```
Followed immediately by `convert_svg_text_to_paths(<output.svg>)`.

