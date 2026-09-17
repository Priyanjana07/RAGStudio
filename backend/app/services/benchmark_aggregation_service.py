def aggregate_benchmark_results(
    benchmark_results: list[dict]
):
    strategies = [
        "vector",
        "bm25",
        "rrf",
        "rrf_reranker"
    ]

    summary = {}

    for strategy in strategies:

        precision_values = []
        recall_values = []
        mrr_values = []
        latency_values = []

        for question_result in benchmark_results:

            result = question_result["results"][strategy]

            precision_values.append(
                result["precision_at_k"]
            )

            recall_values.append(
                result["recall_at_k"]
            )

            mrr_values.append(
                result["reciprocal_rank"]
            )

            latency_values.append(
                result["latency_ms"]
            )

        if not precision_values:
            continue

        summary[strategy] = {
            "average_precision_at_k": round(
                sum(precision_values) /
                len(precision_values),
                4
            ),

            "average_recall_at_k": round(
                sum(recall_values) /
                len(recall_values),
                4
            ),

            "mrr": round(
                sum(mrr_values) /
                len(mrr_values),
                4
            ),

            "average_latency_ms": round(
                sum(latency_values) /
                len(latency_values),
                3
            )
        }

    return summary