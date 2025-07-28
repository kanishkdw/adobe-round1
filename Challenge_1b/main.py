# File: Challenge_1b/main.py

import os
import json
from datetime import datetime
from parser import extract_outline
from ranker import rank_sections
from summarizer import extract_subsections

COLLECTION_PATH = "Collection 1"
  # <- Change to Collection 2 / 3 to test others
PDF_DIR = os.path.join(COLLECTION_PATH, "PDFs")
INPUT_JSON = os.path.join(COLLECTION_PATH, "challenge1b_input.json")
OUTPUT_JSON = os.path.join(COLLECTION_PATH, "generated_output.json")

def load_input():
    with open(INPUT_JSON) as f:
        data = json.load(f)
    persona = data["persona"]["role"]
    job = data["job_to_be_done"]["task"]
    documents = data["documents"]
    filenames = [d["filename"] for d in documents]
    return persona, job, filenames

def parse_pdfs(filenames):
    outlines = {}
    for filename in filenames:
        path = os.path.join(PDF_DIR, filename)
        outlines[filename] = extract_outline(path)
    return outlines

def generate_output(persona, job, input_docs, top_sections, subsections):
    return {
        "metadata": {
            "input_documents": input_docs,
            "persona": persona,
            "job_to_be_done": job,
            "processing_timestamp": datetime.utcnow().isoformat()
        },
        "extracted_sections": top_sections,
        "subsection_analysis": subsections
    }

if __name__ == "__main__":
    persona, job, input_files = load_input()
    outlines = parse_pdfs(input_files)
    


    top_sections = rank_sections(outlines, persona, job)
    subsections = extract_subsections(PDF_DIR, top_sections)  # Uses heading page number

    result = generate_output(persona, job, input_files, top_sections, subsections)

    with open(OUTPUT_JSON, "w") as f:
        json.dump(result, f, indent=2)

    print(f" Output written to {OUTPUT_JSON}")
