from rank_bm25 import BM25Okapi


def tokenize(text: str):
    return text.lower().split()


def bm25_search(
    query: str,
    documents: list[dict],
    top_k: int = 3
):
    if not documents:
        return []

    tokenized_documents = [
        tokenize(document["text"])
        for document in documents
    ]

    bm25 = BM25Okapi(tokenized_documents)

    query_tokens = tokenize(query)

    scores = bm25.get_scores(query_tokens)

    ranked_indices = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )

    results = []

    for index in ranked_indices[:top_k]:
        document = documents[index]

        results.append({
            "text": document["text"],
            "chunk_number": document.get("chunk_number"),
            "page_number": document.get("page_number"),
            "score": float(scores[index])
        })

    return results

def hybrid_search(
    bm25_results: list[dict],
    vector_results: list[dict],
    top_k: int = 3
):
    combined = []

    combined.extend(bm25_results)
    combined.extend(vector_results)

    # Remove duplicate chunks
    seen = set()
    unique_results = []

    for result in combined:
        chunk_number = result.get("chunk_number")

        if chunk_number in seen:
            continue

        seen.add(chunk_number)
        unique_results.append(result)

    return unique_results[:top_k]

def reciprocal_rank_fusion(
    result_lists: list[list[dict]],
    top_k: int = 3,
    k: int = 60
):
    scores = {}
    result_map = {}

    for results in result_lists:
        for rank, result in enumerate(results, start=1):
            chunk_number = result.get("chunk_number")

            if chunk_number is None:
                continue

            rrf_score = 1 / (k + rank)

            scores[chunk_number] = (
                scores.get(chunk_number, 0) + rrf_score
            )

            result_map[chunk_number] = result

    ranked_chunks = sorted(
        scores.keys(),
        key=lambda chunk: scores[chunk],
        reverse=True
    )

    fused_results = []

    for chunk_number in ranked_chunks[:top_k]:
        result = result_map[chunk_number].copy()

        result["rrf_score"] = round(
            scores[chunk_number],
            6
        )

        fused_results.append(result)

    return fused_results