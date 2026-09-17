from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


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

    return response.choices[0].message.content