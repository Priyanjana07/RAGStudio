from backend.app.services.context_service import build_context


results = [
    {
        "text": "This document contains placement preparation resources.",
        "distance": 0.2,
        "chunk_index": 0,
        "page_number": 1
    },
    {
        "text": "Topics include aptitude and data structures.",
        "distance": 0.3,
        "chunk_index": 1,
        "page_number": 1
    }
]


context = build_context(results)

print(context)