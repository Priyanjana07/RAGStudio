from backend.app.services.retrieval_metrics import (
    precision_at_k,
    recall_at_k,
    reciprocal_rank
)


retrieved = [7, 3, 10]
relevant = {3, 7}


print(
    "Precision@3:",
    precision_at_k(
        retrieved,
        relevant,
        3
    )
)

print(
    "Recall@3:",
    recall_at_k(
        retrieved,
        relevant,
        3
    )
)

print(
    "Reciprocal Rank:",
    reciprocal_rank(
        retrieved,
        relevant
    )
)