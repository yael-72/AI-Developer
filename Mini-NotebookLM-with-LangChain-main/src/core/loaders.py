from pathlib import Path
from io import BytesIO

import fitz  # PyMuPDF
from docx import Document


def load_file(filename: str, data: bytes) -> str:
    """
    Load uploaded file content and convert it into plain text.

    Supported formats:
    - .txt
    - .md
    - .pdf
    - .docx
    """

    suffix = Path(filename).suffix.lower()

    # Text files
    if suffix in [".txt", ".md"]:
        return data.decode("utf-8")

    # PDF files
    if suffix == ".pdf":
        text_parts = []

        pdf = fitz.open(stream=data, filetype="pdf")

        for page in pdf:
            text = page.get_text("text")

            if text.strip():
                text_parts.append(text)

        pdf.close()

        return "\n\n".join(text_parts)

    # Word documents
    if suffix == ".docx":
        doc = Document(BytesIO(data))

        paragraphs = [
            paragraph.text.strip()
            for paragraph in doc.paragraphs
            if paragraph.text.strip()
        ]

        return "\n".join(paragraphs)

    raise ValueError(
        f"Unsupported file type: {suffix}. "
        "Supported types: txt, md, pdf, docx"
    )