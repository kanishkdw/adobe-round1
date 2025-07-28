# main.py
import os
import json
from parser import extract_outline

INPUT_DIR = "/app/input"
OUTPUT_DIR = "/app/output"

if _name_ == "_main_":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Starting processing of PDFs from {INPUT_DIR}...")

    for filename in os.listdir(INPUT_DIR):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(INPUT_DIR, filename)
            print(f"Processing: {pdf_path}")
            result = extract_outline(pdf_path)

            json_path = os.path.join(OUTPUT_DIR, filename.replace(".pdf", ".json"))
            with open(json_path, "w") as f:
                json.dump(result, f, indent=4)
            
            print(f"Saved output to {json_path}")

    print("Processing complete.")