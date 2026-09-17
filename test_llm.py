from backend.app.services.retrieval_service import search_chunks
from backend.app.services.llmservice import generate_answer


query = "What is this document about?"

results = search_chunks(
    query=query,
    document_id=1,
    top_k=3
)

chunks = results["documents"][0]

context = "\n\n---\n\n".join(chunks)

answer = generate_answer(
    question=query,
    context=context
)

print("\nQUESTION:")
print(query)

print("\nANSWER:")
print(answer)

print("\nSOURCES:")
for i, metadata in enumerate(results["metadatas"][0]):
    print(
        f"Chunk {metadata['chunk_index']} "
        f"(distance: {results['distances'][0][i]})"
    )

@app.post("/documents/{document_id}/ask")
def ask_document(
    document_id: int,
    query: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Check that the document belongs to this user
    document = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # 2. Retrieve relevant chunks
    results = search_chunks(
        query=query,
        document_id=document_id,
        top_k=3
    )

    chunks = results["documents"][0]

    # 3. Combine chunks into context
    context = "\n\n---\n\n".join(chunks)

    # 4. Ask the LLM
    answer = generate_answer(
        question=query,
        context=context
    )

    # 5. Return answer + sources
    return {
        "question": query,
        "answer": answer,
        "sources": [
            {
                "chunk_index": results["metadatas"][0][i]["chunk_index"],
                "distance": results["distances"][0][i]
            }
            for i in range(len(chunks))
        ]
    }