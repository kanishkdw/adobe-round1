import fitz  # PyMuPDF
import collections
import re


def normalize(text):
    return re.sub(r"\s+", " ", text.strip())


def is_heading_candidate(text, size, font, bold, y_position, is_uppercase_ratio):
    if not text or len(text) > 120 or len(text.split()) > 20:
        return False
    if len(text) < 3:
        return False
    if any(text.endswith(c) for c in [":", ".", ";"]):
        return False
    if text.lower() in {"page", "figure", "table"}:
        return False
    if not bold and sum(c.islower() for c in text) > len(text) * 0.7:
        return False
    if y_position > 700:  # avoid footers
        return False
    if is_uppercase_ratio > 0.7 and len(text.split()) == 1:
        return False  # Likely not a meaningful heading
    return True


def group_styles(text_blocks):
    style_counter = collections.Counter(
        (b["size"], b["bold"]) for b in text_blocks
    )
    common_style = style_counter.most_common(1)[0][0]

    heading_styles = [
        style for style in style_counter
        if style[0] > common_style[0] or (style[1] and style[0] >= common_style[0])
    ]
    heading_styles = sorted(set(heading_styles), key=lambda x: -x[0])[:4]
    return {style: f"H{i+1}" for i, style in enumerate(heading_styles)}


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
                    uppercase_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
                    text_blocks.append({
                        "text": text,
                        "size": round(s["size"], 1),
                        "font": s["font"],
                        "bold": "bold" in s["font"].lower(),
                        "page": page_num + 1,
                        "y": s["bbox"][1],
                        "uppercase_ratio": uppercase_ratio
                    })

    if not text_blocks:
        return {"title": "No text found", "outline": []}

    first_page_blocks = [b for b in text_blocks if b["page"] == 1]
    first_page_blocks.sort(key=lambda b: (-b["size"], b["y"]))
    title_texts = []
    seen_titles = set()
    for b in first_page_blocks:
        if b["text"] not in seen_titles and len(b["text"]) > 5:
            title_texts.append(b["text"])
            seen_titles.add(b["text"])
            if len(title_texts) >= 2:
                break
    title = normalize(" ".join(title_texts))

    style_to_level = group_styles(text_blocks)
    outline = []
    seen_texts = set()
    for b in text_blocks:
        style = (b["size"], b["bold"])
        if style not in style_to_level:
            continue
        if not is_heading_candidate(b["text"], b["size"], b["font"], b["bold"], b["y"], b["uppercase_ratio"]):
            continue

        heading_text = normalize(b["text"])
        if heading_text in seen_texts:
            continue
        seen_texts.add(heading_text)

        outline.append({
            "level": style_to_level[style],
            "text": heading_text,
            "page": b["page"]
        })

    return {
        "title": title,
        "outline": outline
    }
