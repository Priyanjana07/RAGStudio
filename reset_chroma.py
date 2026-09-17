import chromadb


client = chromadb.PersistentClient(
    path="chroma_db"
)

client.delete_collection(
    name="ragviz_chunks"
)

print("ChromaDB collection deleted.")