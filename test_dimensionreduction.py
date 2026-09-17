from backend.app.services.dimensionality_service import get_document_embeddings

data = get_document_embeddings(
    document_id=1,
    model_name="minilm"
)

print("Number of embeddings:", len(data["embeddings"]))
print("Embedding dimensions:", len(data["embeddings"][0]))
print("First metadata:", data["metadatas"][0])

from backend.app.services.dimensionality_service import (
    get_document_embeddings,
    reduce_embeddings_pca
)

data = get_document_embeddings(
    document_id=1,
    model_name="minilm"
)

pca_points = reduce_embeddings_pca(
    data["embeddings"],
    n_components=3
)

print("Number of points:", len(pca_points))
print("First PCA point:", pca_points[0])
print("PCA dimensions:", len(pca_points[0]))