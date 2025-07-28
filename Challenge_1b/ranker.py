# File: Challenge_1b/ranker.py

from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("all-MiniLM-L6-v2")

def rank_sections(outlines, persona, job):
    context = persona + ". " + job
    context_embedding = model.encode(context, convert_to_tensor=True)

    candidates = []

    for doc_name, parsed in outlines.items():
        for section in parsed["outline"]:
            section_text = section["text"]
            section_embedding = model.encode(section_text, convert_to_tensor=True)
            score = util.cos_sim(section_embedding, context_embedding).item()

            candidates.append({
                "document": doc_name,
                "section_title": section_text,
                "page_number": section["page"],
                "score": score
            })

    candidates.sort(key=lambda x: x["score"], reverse=True)
    for i, item in enumerate(candidates[:5]):
        item["importance_rank"] = i + 1
        del item["score"]

    return candidates[:5]