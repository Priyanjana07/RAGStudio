import numpy as np
import umap
from backend.app.services.embedding_service import generate_embedding
from backend.app.services.retrieval_service import search_chunks
from backend.app.services.vector_store import get_embedding_collection

from sklearn.decomposition import PCA

def reduce_embeddings(
    embeddings: list[list[float]],
    n_components: int = 3
):
    if len(embeddings) < 3:
        raise ValueError(
            "At least 3 embeddings are required for dimensionality reduction"
        )

    embedding_array = np.array(embeddings)

    reducer = umap.UMAP(
        n_components=n_components,
        random_state=42
    )

    reduced = reducer.fit_transform(embedding_array)

    return reduced.tolist()


def get_document_embeddings(
    document_id: int,
    model_name: str = "minilm"
):
    from backend.app.services.vector_store import get_embedding_collection

    collection = get_embedding_collection(model_name)

    # Get all IDs belonging to this document/model
    results = collection.get(
        where={
            "document_id": document_id
        },
        include=[
            "embeddings",
            "documents",
            "metadatas"
        ]
    )

    # Keep only records created by the current embedding experiment
    prefix = f"experiment_{document_id}_{model_name}_"

    filtered = []

    for i, record_id in enumerate(results["ids"]):
        if record_id.startswith(prefix):
            filtered.append(i)

    return {
        "embeddings": [
            results["embeddings"][i]
            for i in filtered
        ],
        "documents": [
            results["documents"][i]
            for i in filtered
        ],
        "metadatas": [
            results["metadatas"][i]
            for i in filtered
        ]
    }

def generate_visualization(
    document_id: int,
    model_name: str = "minilm",
    method: str = "umap",
    dimensions: int = 3,
    query: str | None = None
):
    data = get_document_embeddings(
        document_id=document_id,
        model_name=model_name
    )

    embeddings = data["embeddings"]
    metadatas = data["metadatas"]
    documents = data["documents"]

    if len(embeddings) < dimensions:
        raise ValueError(
            f"At least {dimensions} embeddings are required "
            "for dimensionality reduction"
        )

    query_embedding = None
    retrieved_texts = set()

    # Embed and retrieve query
    if query:
        query_embedding = generate_embedding(
            query,
            model_name=model_name
        )

        results = get_embedding_collection(
            model_name
        ).query(
            query_embeddings=[query_embedding],
            n_results=3,
            where={
                "document_id": document_id
            }
        )

        retrieved_texts = set(
            results["documents"][0]
        )

    # Dimensionality reduction
    if query:
        reduced_embeddings, reduced_query = reduce_embeddings_with_query(
            embeddings=embeddings,
            query_embedding=query_embedding,
            method=method,
            n_components=dimensions
        )

    else:
        if method == "umap":
            reduced_embeddings = reduce_embeddings(
                embeddings=embeddings,
                n_components=dimensions
            )

        elif method == "pca":
            reduced_embeddings = reduce_embeddings_pca(
                embeddings=embeddings,
                n_components=dimensions
            )

        else:
            raise ValueError(
                "Unsupported dimensionality reduction method. "
                "Use 'umap' or 'pca'."
            )

        reduced_query = None

    # Create chunk points
    points = []

    for i, coordinates in enumerate(reduced_embeddings):

        metadata = metadatas[i]

        point = {
            "type": "chunk",
            "chunk_number": metadata.get("chunk_index",i),
            "page_number": metadata.get("page_number"),
            "text": documents[i],
            "retrieved": documents[i] in retrieved_texts,
            "x": round(coordinates[0], 4),
            "y": round(coordinates[1], 4)
        }

        if dimensions == 3:
            point["z"] = round(coordinates[2], 4)

        points.append(point)

    # Add query point
    if reduced_query is not None:

        query_point = {
            "type": "query",
            "x": round(reduced_query[0], 4),
            "y": round(reduced_query[1], 4)
        }

        if dimensions == 3:
            query_point["z"] = round(reduced_query[2], 4)

        points.append(query_point)

    return points
def reduce_embeddings_pca(
    embeddings: list[list[float]],
    n_components: int = 3
):
    if len(embeddings) < n_components:
        raise ValueError(
            f"At least {n_components} embeddings are required "
            "for dimensionality reduction"
        )

    embedding_array = np.array(embeddings)

    reducer = PCA(
        n_components=n_components
    )

    reduced = reducer.fit_transform(embedding_array)

    return reduced.tolist()

def reduce_embeddings_with_query(
    embeddings: list[list[float]],
    query_embedding: list[float],
    method: str = "umap",
    n_components: int = 3
):
    if len(embeddings) < 3:
        raise ValueError(
            "At least 3 document embeddings are required"
        )

    embedding_array = np.array(embeddings)
    query_array = np.array(query_embedding).reshape(1, -1)

    if method == "umap":
        reducer = umap.UMAP(
            n_components=n_components,
            random_state=42
        )

    elif method == "pca":
        reducer = PCA(
            n_components=n_components
        )

    else:
        raise ValueError(
            "Unsupported dimensionality reduction method. "
            "Use 'umap' or 'pca'."
        )

    combined = np.vstack([
        embedding_array,
        query_array
    ])

    reduced = reducer.fit_transform(combined)

    document_points = reduced[:-1]
    query_point = reduced[-1]

    return (
        document_points.tolist(),
        query_point.tolist()
    )