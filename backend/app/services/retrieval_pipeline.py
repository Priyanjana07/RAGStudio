from backend.app.services.bm25_service import (
    bm25_search,
    reciprocal_rank_fusion
)

from backend.app.services.embedding_service import generate_embedding

from backend.app.services.reranker_service import rerank

from backend.app.services.vector_store import (
    get_embedding_collection
)


def hybrid_rerank_search(
    query: str,
    document_id: int,
    top_k: int = 3,
    candidate_k: int = 10,
    model_name: str = "minilm"
):
    collection = get_embedding_collection(model_name)

    # --------------------------------
    # Get document chunks
    # --------------------------------
    

    results = collection.get(
        where={
            "document_id": document_id
        },
        include=[
            "documents",
            "metadatas"
        ]
    )

    documents = []

    for text, metadata in zip(
        results["documents"],
        results["metadatas"]
    ):
        
        documents.append({
    "text": text,

    "chunk_number": metadata.get(
        "chunk_number",
        metadata.get("chunk_index")
    ),

    "page_number": metadata.get(
        "page_number"
    )
})

    if not documents:
        return []

    # --------------------------------
    # BM25
    # --------------------------------

    bm25_results = bm25_search(
        query=query,
        documents=documents,
        top_k=candidate_k
    )

    # --------------------------------
    # Vector Search
    # --------------------------------

    query_embedding = generate_embedding(
        query,
        model_name=model_name
    )

    vector_results_raw = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(candidate_k, len(documents)),
        where={
            "document_id": document_id
        }
    )

    vector_results = []

    for text, metadata, distance in zip(
        vector_results_raw["documents"][0],
        vector_results_raw["metadatas"][0],
        vector_results_raw["distances"][0]
    ):
        vector_results.append({
            "text": text,
            "chunk_number": metadata.get("chunk_number"),
            "page_number": metadata.get("page_number"),
            "distance": float(distance)
        })

    # --------------------------------
    # RRF
    # --------------------------------

    rrf_results = reciprocal_rank_fusion(
        result_lists=[
            bm25_results,
            vector_results
        ],
        top_k=candidate_k
    )

    # --------------------------------
    # Reranking
    # --------------------------------

    reranked_results = rerank(
        query=query,
        documents=rrf_results,
        top_k=top_k
    )

    return reranked_results