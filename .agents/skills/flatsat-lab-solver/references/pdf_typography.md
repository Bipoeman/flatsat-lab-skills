# Thai Typography & PDF Layout Optimization

## 1. Complex Thai Text Shaping with HarfBuzz
Direct text insertion via PDF libraries (such as `page.insert_text()` with system TTF/TTC fonts) often lacks HarfBuzz complex text shaping on macOS/Linux. This causes Thai vowels (เช่น สระอุ, สระอู, สระอิ, สระอี) and tone marks (ไม้เอก, ไม้โท, ไม้ตรี, ไม้จัตวา, การันต์) to render detached or improperly stacked.

### The Pillow + HarfBuzz Engine:
Using Pillow (which bundles native libraqm and HarfBuzz):
1. Render text to a 300 DPI transparent RGBA PNG:
   ```python
   scale = 3  # 300 DPI (72 pt * 3)
   img = Image.new("RGBA", (int(w * scale), int(h * scale)), (0, 0, 0, 0))
   draw = ImageDraw.Draw(img)
   font = ImageFont.truetype("fonts/THSarabunNew.ttf", int(font_size_pt * scale))
   draw.text((x, y), text, font=font, fill=(10, 40, 180, 255))
   ```
2. Insert the transparent high-res overlay onto the PDF:
   ```python
   page.insert_image(rect, filename=tmp_path, keep_proportion=False)
   ```
This guarantees pristine, grammatically correct Thai tone mark placement and crisp typography.

## 2. Standard Font & Color Specifications
- **Font**: `TH Sarabun New` (`fonts/THSarabunNew.ttf`)
- **Answer Text Color**: Royal Navy Blue `RGB(10, 40, 180)`
- **Data/Metric Numbers**: Dark Slate Gray `RGB(30, 30, 30)`

## 3. Recommended Font Sizes for FlatSat Lab Sheets
- **Header blanks (File size, CRC32, Chunk count)**: 12.0 pt
- **Table Data Cells**: 10.5 – 11.0 pt
- **Table Observation Narrative (Table 2)**: 9.0 pt, line spacing 1.38
- **Questions 1–6 Answers**: 9.5 pt, line spacing 1.35
- **Conclusion & Discussion (Section 7)**: 8.0 – 8.2 pt, line spacing 1.35

## 4. Layout & Collision Avoidance
- In many FlatSat lab sheets, Section 7 lists 3 bullet points as prompts with very narrow gaps between them.
- **Rule**: Do not inject text directly between prompt bullets if vertical space is less than 20 pt. Place the comprehensive conclusion answer (points 1, 2, 3) into the dedicated open whitespace below the prompts (typically y = 660 to 770).

