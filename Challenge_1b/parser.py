import fitz  
import collections
import re
import unicodedata


def normalize(text):
    text = unicodedata.normalize("NFKC", text)  # Normalize multilingual characters
    return re.sub(r"\s+", " ", text.strip())


def is_heading_candidate(text, size, font, bold, y_position):
    if not text or len(text) > 120 or len(text.split()) > 20:
        return False
    if len(text) < 3:
        return False
    if any(text.endswith(c) for c in [".", ":", ";"]):
        return False
    if text.lower() in {"page", "figure", "table"}:
        return False
    if not bold and sum(c.islower() for c in text) > len(text) * 0.7:
        return False
    if y_position > 700:  # Avoid footer/footer-like lines
        return False
    return True


def group_styles(text_blocks):
    style_counter = collections.Counter((b["size"], b["bold"]) for b in text_blocks)
    common_style = style_counter.most_common(1)[0][0]
    heading_styles = [
        style for style in style_counter
        if style[0] > common_style[0] or (style[1] and style[0] >= common_style[0])
    ]
    heading_styles = sorted(heading_styles, key=lambda x: (-x[0], not x[1]))[:5]
    return {style: f"H{i+1}" for i, style in enumerate(heading_styles)}


def extract_title(first_page_blocks):
    large_blocks = sorted(
        [b for b in first_page_blocks if len(b["text"]) > 5],
        key=lambda b: (-b["size"], b["y"])
    )
    top_texts = []
    for b in large_blocks:
        if not any(b["text"] in t["text"] for t in top_texts):
            top_texts.append(b)
        if len(top_texts) == 2:
            break
    return normalize(" ".join(b["text"] for b in top_texts))


def extract_outline(pdf_path):
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        return {"title": f"Error opening file: {e}", "outline": []}

    text_blocks = []
    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if "lines" not in b:
                continue
            for l in b["lines"]:
                for s in l["spans"]:
                    text = normalize(s["text"])
                    if not text:
                        continue
                    text_blocks.append({
                        "text": text,
                        "size": round(s["size"], 1),
                        "font": s["font"],
                        "bold": "bold" in s["font"].lower(),
                        "page": page_num + 1,
                        "y": s["bbox"][1]
                    })

    if not text_blocks:
        return {"title": "No text found", "outline": []}

    first_page_blocks = [b for b in text_blocks if b["page"] == 1]
    title = extract_title(first_page_blocks)

    style_to_level = group_styles(text_blocks)

    outline = []
    seen = set()
    for b in text_blocks:
        style = (b["size"], b["bold"])
        if style not in style_to_level:
            continue
        if not is_heading_candidate(b["text"], b["size"], b["font"], b["bold"], b["y"]):
            continue
        text = normalize(b["text"])
        if text in seen:
            continue
        seen.add(text)
        outline.append({
            "level": style_to_level[style],
            "text": text,
            "page": b["page"] - 1  # match schema
        })

    return {
        "title": title,
        "outline": outline
    }