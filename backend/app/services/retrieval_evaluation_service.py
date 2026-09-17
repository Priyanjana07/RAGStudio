import time

from backend.app.services.embedding_service import generate_embedding

from backend.app.services.bm25_service import (
    bm25_search,
    reciprocal_rank_fusion
)

from backend.app.services.reranker_service import rerank

from backend.app.services.vector_store import (
    get_embedding_collection
)

from backend.app.services.retrieval_metrics import (
    precision_at_k, recall_at_k, reciprocal_rank
)

from backend.app.services.benchmark_generator import (
    generate_benchmark_questions
)



def get_document_chunks(
    document_id: int,
    model_name: str = "minilm"
):
    collection = get_embedding_collection(
        model_name
    )

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

    return documents

def vector_search(
    query: str,
    document_id: int,
    top_k: int = 3,
    model_name: str = "minilm"
):
    collection = get_embedding_collection(
        model_name
    )

    query_embedding = generate_embedding(
        query,
        model_name=model_name
    )

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={
            "document_id": document_id
        }
    )

    output = []

    for text, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        output.append({
            "text": text,

            "chunk_number": metadata.get(
                "chunk_number",
                metadata.get("chunk_index")
            ),

            "page_number": metadata.get(
                "page_number"
            ),

            "distance": float(distance)
        })

    return output

def evaluate_retrieval_strategies(
    query: str,
    document_id: int,
    relevant_chunks: set[int],
    top_k: int = 3,
    candidate_k: int = 10,
    model_name: str = "minilm"
):
    documents = get_document_chunks(
        document_id=document_id,
        model_name=model_name
    )

    results = {}

    # -----------------------------
    # 1. Vector
    # -----------------------------

    start = time.perf_counter()

    vector_results = vector_search(
        query=query,
        document_id=document_id,
        top_k=top_k,
        model_name=model_name
    )

    vector_time = (
        time.perf_counter() - start
    ) * 1000

    vector_chunk_numbers = [
        result["chunk_number"]
        for result in vector_results
        if result.get("chunk_number") is not None
    ]

    results["vector"] = {
        "results": vector_results,
        "latency_ms": round(vector_time, 3),
        "precision_at_k": round(
            precision_at_k(
                vector_chunk_numbers,
                relevant_chunks,
                top_k
            ),
            4
        ),
        "recall_at_k": round(
            recall_at_k(
                vector_chunk_numbers,
                relevant_chunks,
                top_k
            ),
            4
        ),
        "reciprocal_rank": round(
            reciprocal_rank(
                vector_chunk_numbers,
                relevant_chunks
            ),
            4
        )
    }

    # -----------------------------
    # 2. BM25
    # -----------------------------

    start = time.perf_counter()

    bm25_results = bm25_search(
        query=query,
        documents=documents,
        top_k=top_k
    )

    bm25_time = (
        time.perf_counter() - start
    ) * 1000

    bm25_chunk_numbers = [
        result["chunk_number"]
        for result in bm25_results
        if result.get("chunk_number") is not None
    ]

    results["bm25"] = {
        "results": bm25_results,
        "latency_ms": round(bm25_time, 3),
        "precision_at_k": round(
            precision_at_k(
                bm25_chunk_numbers,
                relevant_chunks,
                top_k
            ),
            4
        ),
        "recall_at_k": round(
            recall_at_k(
                bm25_chunk_numbers,
                relevant_chunks,
                top_k
            ),
            4
        ),
        "reciprocal_rank": round(
            reciprocal_rank(
                bm25_chunk_numbers,
                relevant_chunks
            ),
            4
        )
    }

    # -----------------------------
    # 3. RRF
    # -----------------------------

    start = time.perf_counter()

    bm25_candidates = bm25_search(
        query=query,
        documents=documents,
        top_k=candidate_k
    )

    vector_candidates = vector_search(
        query=query,
        document_id=document_id,
        top_k=candidate_k,
        model_name=model_name
    )

    rrf_results = reciprocal_rank_fusion(
        result_lists=[
            bm25_candidates,
            vector_candidates
        ],
        top_k=top_k
    )

    rrf_time = (
        time.perf_counter() - start
    ) * 1000

    rrf_chunk_numbers = [
        result["chunk_number"]
        for result in rrf_results
        if result.get("chunk_number") is not None
    ]

    results["rrf"] = {
        "results": rrf_results,
        "latency_ms": round(rrf_time, 3),
        "precision_at_k": round(
            precision_at_k(
                rrf_chunk_numbers,
                relevant_chunks,
                top_k
            ),
            4
        ),
        "recall_at_k": round(
            recall_at_k(
                rrf_chunk_numbers,
                relevant_chunks,
                top_k
            ),
            4
        ),
        "reciprocal_rank": round(
            reciprocal_rank(
                rrf_chunk_numbers,
                relevant_chunks
            ),
            4
        )
    }

    # -----------------------------
    # 4. RRF + Reranker
    # -----------------------------

    start = time.perf_counter()

    rrf_candidates = reciprocal_rank_fusion(
        result_lists=[
            bm25_candidates,
            vector_candidates
        ],
        top_k=candidate_k
    )

    reranked_results = rerank(
        query=query,
        documents=rrf_candidates,
        top_k=top_k
    )

    rerank_time = (
        time.perf_counter() - start
    ) * 1000

    reranked_chunk_numbers = [
        result["chunk_number"]
        for result in reranked_results
        if result.get("chunk_number") is not None
    ]

    results["rrf_reranker"] = {
        "results": reranked_results,
        "latency_ms": round(rerank_time, 3),
        "precision_at_k": round(
            precision_at_k(
                reranked_chunk_numbers,
                relevant_chunks,
                top_k
            ),
            4
        ),
        "recall_at_k": round(
            recall_at_k(
                reranked_chunk_numbers,
                relevant_chunks,
                top_k
            ),
            4
        ),
        "reciprocal_rank": round(
            reciprocal_rank(
                reranked_chunk_numbers,
                relevant_chunks
            ),
            4
        )
    }

    return results



def run_retrieval_benchmark(
    document_id: int,
    top_k: int = 3,
    candidate_k: int = 10,
    model_name: str = "minilm"
):
    # --------------------------------
    # Get document chunks
    # --------------------------------

    document_chunks = get_document_chunks(
        document_id=document_id,
        model_name=model_name
    )

    if not document_chunks:
        return []

    # --------------------------------
    # Generate document-specific
    # benchmark questions
    # --------------------------------

    benchmark_questions = generate_benchmark_questions(
        document_chunks=document_chunks,
        num_questions=5
    )

    benchmark_results = []

    # --------------------------------
    # Evaluate every question
    # --------------------------------

    for item in benchmark_questions:

        query = item["question"]

        relevant_chunks = set(
            item["relevant_chunks"]
        )

        comparison = evaluate_retrieval_strategies(
            query=query,
            document_id=document_id,
            relevant_chunks=relevant_chunks,
            top_k=top_k,
            candidate_k=candidate_k,
            model_name=model_name
        )

        benchmark_results.append({
            "question": query,
            "expected_answer": item["expected_answer"],
            "relevant_chunks": item["relevant_chunks"],
            "results": comparison
        })

    return benchmark_results