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