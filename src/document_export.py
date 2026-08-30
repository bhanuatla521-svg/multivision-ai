import os
import json
from typing import List, Dict
from pathlib import Path
import pdfkit
from docx import Document
from openpyxl import Workbook
from .media_helpers import save_media

# Optional: configure pdfkit wkhtmltopdf path if needed
# pdfkit_config = pdfkit.configuration(wkhtmltopdf=os.getenv('WKHTMLTOPDF_PATH', '/usr/local/bin/wkhtmltopdf'))


def create_pdf(html_content: str) -> str:
    """Generate a PDF from HTML string and store it, returning the filename."""
    # pdfkit.from_string returns the PDF as bytes when output_path is None
    pdf_bytes = pdfkit.from_string(html_content, False)  # type: ignore[arg-type]
    filename = save_media(pdf_bytes, ext=".pdf", prefix="doc_")
    return filename


def create_word(html_content: str) -> str:
    """Generate a .docx file from simple HTML (limited to paragraphs and headings)."""
    doc = Document()
    # Very naive conversion – split on newlines, treat lines starting with '# ' as heading
    for line in html_content.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("# "):
            doc.add_heading(line[2:], level=1)
        elif line.startswith("## "):
            doc.add_heading(line[3:], level=2)
        else:
            doc.add_paragraph(line)
    # Save to bytes
    tmp_path = Path(os.getenv('TMP', '/tmp')) / f"tmp_{os.urandom(4).hex()}.docx"
    doc.save(tmp_path)
    with open(tmp_path, "rb") as f:
        data = f.read()
    os.remove(tmp_path)
    filename = save_media(data, ext=".docx", prefix="doc_")
    return filename


def create_excel(table: List[Dict[str, str]]) -> str:
    """Create an Excel workbook from a list of dictionaries (rows)."""
    wb = Workbook()
    ws = wb.active
    if not table:
        # Empty workbook
        pass
    else:
        # Write header
        headers = list(table[0].keys())
        ws.append(headers)
        for row in table:
            ws.append([row.get(h, "") for h in headers])
    tmp_path = Path(os.getenv('TMP', '/tmp')) / f"tmp_{os.urandom(4).hex()}.xlsx"
    wb.save(tmp_path)
    with open(tmp_path, "rb") as f:
        data = f.read()
    os.remove(tmp_path)
    filename = save_media(data, ext=".xlsx", prefix="doc_")
    return filename
