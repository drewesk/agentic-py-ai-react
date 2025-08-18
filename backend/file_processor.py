import os

def extract_text(file_path, file_type):
    ft = (file_type or "").lower()

    if ft == "txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    if ft == "pdf":
        try:
            from pypdf import PdfReader  # pip install pypdf
        except ImportError:
            return ""
        text = []
        with open(file_path, "rb") as f:
            reader = PdfReader(f)
            for page in reader.pages:
                text.append(page.extract_text() or "")
        return "\n".join(text).strip()

    if ft in ("docx",):
        try:
            import docx2txt  # pip install docx2txt
        except ImportError:
            return ""
        return (docx2txt.process(file_path) or "").strip()

    # TODO: add OCR for scanned PDFs (pytesseract) if needed
    return ""