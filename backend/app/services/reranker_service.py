from sentence_transformers import CrossEncoder


RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_reranker = None


def get_reranker():
    global _reranker

    if _reranker is None:
        _reranker = CrossEncoder(RERANKER_MODEL)

    return _reranker


def rerank(
    query: str,
    documents: list[dict],
    top_k: int = 3
):
    if not documents:
        return []

    reranker = get_reranker()

    pairs = [
        [query, document["text"]]
        for document in documents
    ]

    scores = reranker.predict(pairs)

    ranked_indices = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )

    results = []

    for index in ranked_indices[:top_k]:
        result = documents[index].copy()

        result["rerank_score"] = float(
            scores[index]
        )

        results.append(result)

    return results