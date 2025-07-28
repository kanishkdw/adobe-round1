from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def rank_sections(outlines, persona, job):
    sections = []

    # Flatten all outlines into (document, page, section_title, dummy_content)
    for doc, content in outlines.items():
        for item in content.get("outline", []):
            page = item.get("page", 0)
            text = item.get("text", "")
            sections.append((doc, page, text, text))  # using text as dummy content

    # print("DEBUG: Sections format =", sections)

    if not sections:
        print("No sections found.")
        return []

    # Construct query from persona and job
    query = f"{persona} {job}"

    # Corpus: section content + query
    corpus = [s[3] for s in sections] + [query]

    # Vectorize using TF-IDF
    vectorizer = TfidfVectorizer().fit(corpus)
    vectors = vectorizer.transform(corpus)

    query_vec = vectors[-1]          # Last vector is the query
    section_vecs = vectors[:-1]      # All others are section vectors

    # Compute cosine similarity
    scores = cosine_similarity(query_vec, section_vecs).flatten()

    # Rank sections by score
    ranked = sorted(zip(sections, scores), key=lambda x: x[1], reverse=True)

    top_k = 5  # Change this if needed
    top_sections = []
    for rank, ((doc, page, title, _), score) in enumerate(ranked[:top_k], 1):
        top_sections.append({
            "document": doc,
            "page_number": page,
            "section_title": title,
            "importance_rank": rank
        })

    return top_sections
