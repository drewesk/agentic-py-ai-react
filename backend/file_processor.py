import os

def extract_text(file_path, file_type):
    if file_type.lower() == "txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    # extend with pdf, docx as needed
    return ""