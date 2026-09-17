def build_context(results: list[dict]) -> str:
    """
    Convert retrieved chunks into a formatted context
    that can be provided to the LLM.
    """

    context_parts = []

    for i, result in enumerate(results, start=1):

        text = result["text"]
        page_number = result.get("page_number")
        chunk_index = result.get("chunk_index")

        context_parts.append(
            f"[Source {i} | Page {page_number} | Chunk {chunk_index}]\n"
            f"{text}"
        )

    return "\n\n".join(context_parts)