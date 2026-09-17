import chromadb

client = chromadb.PersistentClient(
    path="chroma_db"
)

collection = client.get_or_create_collection(
    name="ragviz_chunks"
)

result = collection.get(
    limit=1,
    include=[
        "documents",
        "embeddings",
        "metadatas"
    ]
)

print("ID:")
print(result["ids"][0])

print("\nDocument:")
print(result["documents"][0])

print("\nMetadata:")
print(result["metadatas"][0])

print("\nEmbedding dimension:")
print(len(result["embeddings"][0]))