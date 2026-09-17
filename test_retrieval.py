from backend.app.services.retrieval_service import search_chunks


def main() -> None:
    results = search_chunks(
        query="What is this document about?",
        document_id=1,
        top_k=3,
    )

    print("Results:")
    for result in results:
        print(result)


if __name__ == "__main__":
    main()
