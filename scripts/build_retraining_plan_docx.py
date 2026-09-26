from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "plan_reentrenamiento_ml_cerespinn.md"
OUTPUT = ROOT / "docs" / "Plan_de_implementacion_reentrenamiento_ML_CeresPinn.docx"

NAVY = "17365D"
PALE_BLUE = "EDF3F9"
LIGHT_GRAY = "D9D9D9"
TEXT = RGBColor(31, 41, 55)
MUTED = RGBColor(75, 85, 99)


def set_font(run, name: str, size: float | None = None, bold: bool | None = None):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), name)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold


def set_cell_shading(cell, fill: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=90, start=110, bottom=90, end=110):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_table_borders(table):
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.find(qn("w:tblBorders"))
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = f"w:{edge}"
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "5")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), LIGHT_GRAY)


def repeat_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def add_page_field(paragraph):
    run = paragraph.add_run()
    fld_char = OxmlElement("w:fldChar")
    fld_char.set(qn("w:fldCharType"), "begin")
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = " PAGE "
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char)
    run._r.append(instr_text)
    run._r.append(fld_end)


def add_inline_runs(paragraph, text: str, base_size=10.5):
    # Supports Markdown bold and inline code without treating source paths as citations.
    pieces = re.split(r"(`[^`]+`|\*\*[^*]+\*\*)", text)
    for piece in pieces:
        if not piece:
            continue
        if piece.startswith("`") and piece.endswith("`"):
            run = paragraph.add_run(piece[1:-1])
            set_font(run, "Consolas", min(9.0, max(7.5, base_size - 0.3)))
            run.font.color.rgb = RGBColor(31, 78, 121)
        elif piece.startswith("**") and piece.endswith("**"):
            run = paragraph.add_run(piece[2:-2])
            set_font(run, "Aptos", base_size, True)
            run.font.color.rgb = TEXT
        else:
            run = paragraph.add_run(piece)
            set_font(run, "Aptos", base_size)
            run.font.color.rgb = TEXT


def add_table(doc: Document, rows: list[list[str]]):
    if not rows:
        return
    columns = len(rows[0])
    table = doc.add_table(rows=len(rows), cols=columns)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_table_borders(table)
    usable_width = 6.75
    lengths = [max(len(row[i]) if i < len(row) else 0 for row in rows) for i in range(columns)]
    total = max(sum(max(8, length) for length in lengths), 1)
    widths = [usable_width * max(8, length) / total for length in lengths]
    # Protect short status/index columns and keep narrative columns readable.
    if columns == 3:
        widths = [usable_width * 0.25, usable_width * 0.35, usable_width * 0.40]
    elif columns == 4:
        widths = [usable_width * 0.12, usable_width * 0.38, usable_width * 0.20, usable_width * 0.30]
    for r_idx, values in enumerate(rows):
        row = table.rows[r_idx]
        for c_idx, value in enumerate(values):
            cell = row.cells[c_idx]
            cell.width = Inches(widths[c_idx])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cell, top=65, start=100, bottom=65, end=100)
            if r_idx == 0:
                set_cell_shading(cell, NAVY)
            elif r_idx % 2 == 0:
                set_cell_shading(cell, PALE_BLUE)
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.paragraph_format.line_spacing = 1.05
            if r_idx == 0:
                paragraph.paragraph_format.keep_with_next = True
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx == 0 and columns >= 3 else WD_ALIGN_PARAGRAPH.LEFT
            cell_size = 8.2 if columns >= 4 else 8.3
            if r_idx == 0:
                run = paragraph.add_run(value)
                set_font(run, "Aptos", cell_size, True)
                run.font.color.rgb = RGBColor(255, 255, 255)
            else:
                add_inline_runs(paragraph, value, cell_size)
    repeat_header(table.rows[0])


def add_manual_list_paragraph(doc: Document, marker: str, text: str):
    """Render a stable list item without Word carrying numbering across sections."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.26)
    p.paragraph_format.first_line_indent = Inches(-0.20)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.08
    prefix = p.add_run(f"{marker}  ")
    set_font(prefix, "Aptos", 10.25)
    prefix.font.color.rgb = TEXT
    add_inline_runs(p, text, 10.25)
    return p


def configure_styles(doc: Document):
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Aptos"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = TEXT
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.12

    title = styles["Title"]
    title.font.name = "Aptos Display"
    title._element.rPr.rFonts.set(qn("w:ascii"), "Aptos Display")
    title._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos Display")
    title.font.size = Pt(25)
    title.font.bold = True
    title.font.color.rgb = RGBColor(0, 0, 0)
    title.paragraph_format.space_after = Pt(18)

    for style_name, size, before, after in (
        ("Heading 1", 16, 18, 8),
        ("Heading 2", 12.5, 13, 5),
        ("Heading 3", 11, 10, 4),
    ):
        style = styles[style_name]
        style.font.name = "Aptos Display"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Aptos Display")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos Display")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True

    for style_name in ("List Bullet", "List Number"):
        style = styles[style_name]
        style.font.name = "Aptos"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
        style.font.size = Pt(10.25)
        style.paragraph_format.space_after = Pt(3)
        style.paragraph_format.line_spacing = 1.08


def build_document():
    text = SOURCE.read_text(encoding="utf-8")
    lines = text.splitlines()
    doc = Document()
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.72)
    section.left_margin = Inches(0.85)
    section.right_margin = Inches(0.85)
    configure_styles(doc)

    doc.core_properties.title = "Plan de implementación para reentrenamiento y consumo de predicciones en CeresPinn"
    doc.core_properties.subject = "Plan técnico para datos entrenamiento validación integración y despliegue"
    doc.core_properties.author = "Proyecto CeresPinn"

    footer = section.footer
    footer_p = footer.paragraphs[0]
    footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_p.paragraph_format.space_before = Pt(3)
    r = footer_p.add_run("CeresPinn  Plan de implementación  ")
    set_font(r, "Aptos", 8)
    r.font.color.rgb = MUTED
    add_page_field(footer_p)

    first_heading = True
    table_rows: list[list[str]] = []
    in_code = False
    code_lines: list[str] = []

    def flush_table():
        nonlocal table_rows
        if table_rows:
            add_table(doc, table_rows)
            table_rows = []

    def flush_code():
        nonlocal code_lines
        if code_lines:
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.25)
            p.paragraph_format.right_indent = Inches(0.15)
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(8)
            p.paragraph_format.line_spacing = 1.0
            run = p.add_run("\n".join(code_lines))
            set_font(run, "Consolas", 8.3)
            run.font.color.rgb = RGBColor(17, 24, 39)
            code_lines = []

    force_body_break = False
    for raw in lines:
        line = raw.rstrip()
        if line.strip() == "```json":
            flush_table()
            in_code = True
            force_body_break = False
            continue
        if line.strip() == "```" and in_code:
            in_code = False
            flush_code()
            continue
        if in_code:
            code_lines.append(line)
            continue
        if line.strip() == "<!-- PAGEBREAK -->":
            flush_table()
            doc.add_page_break()
            force_body_break = False
            continue
        if line.startswith("|") and line.endswith("|"):
            force_body_break = False
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if all(re.fullmatch(r"[-: ]+", cell or "-") for cell in cells):
                continue
            table_rows.append(cells)
            continue
        flush_table()
        if not line.strip():
            continue
        if line.startswith("# "):
            heading = line[2:].strip()
            if first_heading:
                p = doc.add_paragraph(style="Title")
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_before = Pt(96)
                p.paragraph_format.space_after = Pt(22)
                add_inline_runs(p, heading, 25)
                first_heading = False
            else:
                doc.add_paragraph("\u200b\u200b" + heading, style="Heading 1")
            force_body_break = False
            continue
        if line.startswith("## "):
            heading = line[3:].strip()
            if len(doc.paragraphs) <= 2:
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_after = Pt(26)
                run = p.add_run(heading)
                set_font(run, "Aptos", 14, True)
                run.font.color.rgb = RGBColor(0, 0, 0)
            else:
                doc.add_paragraph("\u200b\u200b" + heading, style="Heading 2")
                force_body_break = True
            continue
        if line.startswith("### "):
            doc.add_paragraph("\u200b\u200b" + line[4:].strip(), style="Heading 3")
            force_body_break = True
            continue
        numbered = re.match(r"^(\d+)\.\s+(.*)$", line)
        if numbered:
            force_body_break = False
            add_manual_list_paragraph(doc, f"{numbered.group(1)}.", numbered.group(2))
            continue
        if line.startswith("- "):
            force_body_break = False
            add_manual_list_paragraph(doc, "•", line[2:].strip())
            continue
        p = doc.add_paragraph()
        if len(doc.paragraphs) <= 8:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(5)
            add_inline_runs(p, line.strip(), 10)
            for run in p.runs:
                run.font.color.rgb = MUTED
        else:
            p.paragraph_format.keep_together = False
            if force_body_break:
                p.paragraph_format.keep_together = True
                p.add_run().add_break()
                force_body_break = False
            add_inline_runs(p, line.strip(), 10.5)

    flush_table()
    flush_code()

    # Keep table headings with their tables and avoid orphaned short paragraphs.
    for paragraph in doc.paragraphs:
        if paragraph.style.name.startswith("Heading"):
            paragraph.paragraph_format.keep_with_next = True
        if paragraph.text.startswith("Versión ") or paragraph.text.startswith("Fecha "):
            paragraph.paragraph_format.space_after = Pt(2)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    build_document()
