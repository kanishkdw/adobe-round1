# File: Challenge_1b/summarizer.py

import fitz  # PyMuPDF

def extract_text_from_page(pdf_path, page_number):
    try:
        doc = fitz.open(pdf_path)
        page = doc[page_number - 1]
        return page.get_text().strip()
    except Exception as e:
        print(f"Error reading {pdf_path} page {page_number}: {e}")
        return ""

def extract_subsections(pdf_dir, sections):
    results = []
    for sec in sections:
        pdf_path = f"{pdf_dir}/{sec['document']}"
        text = extract_text_from_page(pdf_path, sec["page_number"])
        if text:
            results.append({
                "document": sec["document"],
                "refined_text": text[:2000],  # Truncate for submission limits
                "page_number": sec["page_number"]
            })
    return results
