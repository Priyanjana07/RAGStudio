from backend.app.services.retrieval_service import search_chunks


results = search_chunks(
    query="What is this document about?",
    document_id=1,
    top_k=3
)

print("Documents:")
print(results["documents"])

print("\nDistances:")
print(results["distances"])

print("\nMetadata:")
print(results["metadatas"])