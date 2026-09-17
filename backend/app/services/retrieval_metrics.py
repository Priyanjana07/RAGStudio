def precision_at_k(
    retrieved_chunks: list[int],
    relevant_chunks: set[int],
    k: int
):
    retrieved = retrieved_chunks[:k]

    if not retrieved:
        return 0.0

    relevant_retrieved = sum(
        1 for chunk in retrieved
        if chunk in relevant_chunks
    )

    return relevant_retrieved / len(retrieved)


def recall_at_k(
    retrieved_chunks: list[int],
    relevant_chunks: set[int],
    k: int
):
    if not relevant_chunks:
        return 0.0

    retrieved = retrieved_chunks[:k]

    relevant_retrieved = sum(
        1 for chunk in retrieved
        if chunk in relevant_chunks
    )

    return relevant_retrieved / len(relevant_chunks)


def reciprocal_rank(
    retrieved_chunks: list[int],
    relevant_chunks: set[int]
):
    for rank, chunk in enumerate(retrieved_chunks, start=1):
        if chunk in relevant_chunks:
            return 1 / rank

    return 0.0


def mean_reciprocal_rank(
    retrieved_lists: list[list[int]],
    relevant_chunks_list: list[set[int]]
):
    if not retrieved_lists:
        return 0.0

    reciprocal_ranks = []

    for retrieved, relevant in zip(
        retrieved_lists,
        relevant_chunks_list
    ):
        reciprocal_ranks.append(
            reciprocal_rank(
                retrieved,
                relevant
            )
        )

    return sum(reciprocal_ranks) / len(reciprocal_ranks)