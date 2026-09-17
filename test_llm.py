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

"""Small manual smoke test for the LLM service.

Run this file directly only after setting ``GROQ_API_KEY`` and preparing a
document.  Keeping it as a normal script prevents pytest and Pylance from
treating an orphaned API endpoint as test code.
"""

from backend.app.services.context_service import build_context
from backend.app.services.llmservice import generate_answer
from backend.app.services.retrieval_service import search_chunks


def main() -> None:
    query = "What is this document about?"
    results = search_chunks(query=query, document_id=1, top_k=3)

    if not results:
        print("No chunks were retrieved.")
        return

    context = build_context(results)
    answer = generate_answer(question=query, context=context)

    print("QUESTION:")
    print(query)
    print("\nANSWER:")
    print(answer)
    print("\nSOURCES:")
    for result in results:
        print(
            "Chunk "
            f"{result.get('chunk_number', result.get('chunk_index'))} "
            f"(distance: {result.get('distance')})"
        )


if __name__ == "__main__":
    main()
