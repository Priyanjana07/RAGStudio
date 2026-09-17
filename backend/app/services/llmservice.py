import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

def get_client() -> Groq:
    """Create the Groq client only when an LLM operation is requested."""
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("groq_api_key")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. Add it to the environment or .env file."
        )
    return Groq(api_key=api_key)


def generate_answer(
    question: str,
    context: str
):
    prompt = f"""
You are an AI assistant answering questions about a document.

Use ONLY the information provided in the context below.

If the answer cannot be found in the context, say:
"I couldn't find the answer in the document."

Context:
{context}

Question:
{question}

Answer:
"""

    response = get_client().chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content or ""
