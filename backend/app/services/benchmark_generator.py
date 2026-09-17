import json

from backend.app.services.llmservice import client


def generate_benchmark_questions(
    document_chunks: list[dict],
    num_questions: int = 5
):
    if not document_chunks:
        return []

    chunk_text = "\n\n".join(
        f"CHUNK_ID: {chunk['chunk_number']}\n"
        f"TEXT: {chunk['text']}"
        for chunk in document_chunks
    )

    prompt = f"""
You are generating an evaluation benchmark for a document retrieval system.

The document can be ANY type of PDF:
- research paper
- textbook
- legal document
- annual report
- technical documentation
- university document
- business report
- manual
- etc.

Based ONLY on the document chunks below, generate exactly
{num_questions} diverse questions that can be answered from the document.

For every question provide:

1. question
2. expected_answer
3. relevant_chunks

The relevant_chunks field MUST contain the chunk_number values
of the chunks that contain information needed to answer the question.

Requirements:
- Do not invent information.
- Every question must be answerable from the provided chunks.
- Questions should cover different parts/topics of the document.
- Avoid questions whose answer is simply yes/no.
- Use the exact chunk_number values provided.
- relevant_chunks must contain at least one chunk.
- Return ONLY valid JSON.
- Do not include markdown.

Output format:

[
    {{
        "question": "...",
        "expected_answer": "...",
        "relevant_chunks": [1, 2]
    }}
]

DOCUMENT CHUNKS:

{chunk_text}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    content = response.choices[0].message.content

    try:
        benchmark_questions = json.loads(content)
    except json.JSONDecodeError:
        raise ValueError(
            "LLM returned invalid JSON while generating benchmark questions"
        )

    return benchmark_questions