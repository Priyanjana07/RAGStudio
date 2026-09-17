import chromadb


# Create a persistent ChromaDB database
client = chromadb.PersistentClient(
    path="chroma_db"
)


# Create/get our collection
collection = client.get_or_create_collection(
    name="ragviz_chunks"
)

def get_embedding_collection(model_name: str):
    """
    Get a separate ChromaDB collection for each
    embedding model.
    """

    collection_name = f"ragviz_{model_name}"

    return client.get_or_create_collection(
        name=collection_name
    )

def store_chunks(
    document_id: int,
    chunks: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict]
):
    """
    Store chunks, embeddings, and metadata in ChromaDB.
    """

    ids = [
        f"{document_id}_{i}"
        for i in range(len(chunks))
    ]

    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas
    )

    return len(chunks)

def get_experiment_collection(name: str):
    return client.get_or_create_collection(name=name)

def delete_document_embeddings(document_id: int):
    deleted_count = 0

    # 1. Delete from the generic collection
    results = collection.get(
        where={
            "document_id": document_id
        }
    )

    ids = results.get("ids", [])

    if ids:
        collection.delete(ids=ids)
        deleted_count += len(ids)

    # 2. Delete from all model-specific collections
    model_names = [
        "minilm",
        "mpnet",
        "distilroberta",
    ]

    for model_name in model_names:
        model_collection = get_embedding_collection(
            model_name
        )

        results = model_collection.get(
            where={
                "document_id": document_id
            }
        )

        ids = results.get("ids", [])

        if ids:
            model_collection.delete(ids=ids)
            deleted_count += len(ids)

    return deleted_count