from backend.app.services.embedding_service import generate_embedding


embedding = generate_embedding(
    "Object oriented programming uses classes and objects.",
    model_name="minilm"
)

print("Embedding dimension:", len(embedding))
print("First 5 values:", embedding[:5])