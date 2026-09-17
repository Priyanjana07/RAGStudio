from backend.app.services.embedding_service import generate_embedding
from backend.app.services.vector_store import get_embedding_collection


def search_chunks(
    query: str,
    document_id: int,
    top_k: int = 3,
    model_name: str = "minilm"
):
    # 1. Convert query into the same embedding model
    query_embedding = generate_embedding(
        query,
        model_name=model_name
    )

    # 2. Search the same model-specific collection
    collection = get_embedding_collection(
        model_name
    )

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={
            "document_id": document_id
        }
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    relevant_results = []

    for i in range(len(documents)):
        metadata = metadatas[i]

        relevant_results.append({
            "text": documents[i],
            "chunk_index": metadata.get(
                "chunk_index"
            ),
            "chunk_number": metadata.get(
                "chunk_number"
            ),
            "page_number": metadata.get(
                "page_number"
            ),
            "distance": float(
                distances[i]
            )
        })

    return relevant_results