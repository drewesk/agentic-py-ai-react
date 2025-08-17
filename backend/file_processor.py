import os

def extract_text(file_path, file_type):
    ft = (file_type or "").lower()
    if ft == "txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    # TODO: pdf/docx support; for now, explicit empty return to avoid surprises
    return ""
