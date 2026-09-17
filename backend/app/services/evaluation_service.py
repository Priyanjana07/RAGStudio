from groq import Groq
from dotenv import load_dotenv
import os
import json
import re

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

import re


def calculate_answer_overlap(
    answer: str,
    context: str
):
    """
    Baseline lexical overlap score.
    """

    answer_words = set(
        re.findall(
            r"\b[a-zA-Z]{4,}\b",
            answer.lower()
        )
    )

    context_words = set(
        re.findall(
            r"\b[a-zA-Z]{4,}\b",
            context.lower()
        )
    )

    if not answer_words or not context_words:
        return 0.0

    common_words = answer_words.intersection(
        context_words
    )

    score = len(common_words) / len(answer_words)

    return round(score, 4)


def calculate_overall_score(
    relevance: float,
    faithfulness: float,
    completeness: float
):
    """
    Calculate the overall answer-quality score.

    Faithfulness receives the highest weight because
    a RAG system should avoid unsupported information.
    """

    score = (
        0.30 * relevance
        + 0.40 * faithfulness
        + 0.30 * completeness
    )

    return round(score, 4)


def evaluate_answer(
    question: str,
    context: str,
    answer: str
):
    """
    Evaluate a RAG answer using an LLM judge.
    """

    prompt = f"""
You are a strict evaluator for a Retrieval-Augmented Generation (RAG) system.

Your job is to evaluate the generated answer against the provided context.

DO NOT reward the answer simply because it sounds good.

Use ONLY the context to evaluate the answer.

--------------------------------
QUESTION
--------------------------------
{question}

--------------------------------
CONTEXT
--------------------------------
{context}

--------------------------------
GENERATED ANSWER
--------------------------------
{answer}

--------------------------------
SCORING RUBRIC
--------------------------------

Give each score between 0 and 1.

RELEVANCE:
1.0 = Directly and completely answers the question.
0.8 = Directly answers the question with only minor unnecessary information.
0.6 = Mostly answers the question but misses some relevant information.
0.4 = Partially answers the question.
0.2 = Barely addresses the question.
0.0 = Does not answer the question.

FAITHFULNESS:
1.0 = Every important claim in the answer is clearly supported by the context.
0.8 = Almost all claims are supported; very minor unsupported details.
0.6 = Mostly supported but contains some unsupported or inferred information.
0.4 = Several claims are unsupported.
0.2 = Much of the answer is unsupported.
0.0 = Answer contradicts the context or is completely unsupported.

COMPLETENESS:
1.0 = Covers essentially all important information needed to answer the question from the context.
0.8 = Covers most important information but misses a minor point.
0.6 = Covers the main answer but misses several useful details.
0.4 = Covers only part of the important information.
0.2 = Misses most important information.
0.0 = Does not provide the required information.

IMPORTANT:
- Do NOT automatically give 1.
- Give 1 ONLY when the answer completely satisfies the criterion.
- Compare the answer carefully against the context.
- Do not judge based on writing quality.
- Do not add information that is not present in the context.
- Scores should be different when the answers have meaningful differences.

Return ONLY valid JSON.

Use exactly this format:

{{
    "relevance": 0.0,
    "faithfulness": 0.0,
    "completeness": 0.0
}}
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

    content = response.choices[0].message.content.strip()

    try:

        scores = json.loads(content)

        relevance = float(scores["relevance"])
        faithfulness = float(scores["faithfulness"])
        completeness = float(scores["completeness"])

        # Keep scores within valid range
        relevance = max(0.0, min(1.0, relevance))
        faithfulness = max(0.0, min(1.0, faithfulness))
        completeness = max(0.0, min(1.0, completeness))

        return {
            "relevance": relevance,
            "faithfulness": faithfulness,
            "completeness": completeness
        }

    except (
        json.JSONDecodeError,
        KeyError,
        ValueError
    ):

        return {
            "relevance": 0.0,
            "faithfulness": 0.0,
            "completeness": 0.0
        }
def calculate_overall_score(
    answer_quality: float,
    best_distance: float,
    latency_ms: float,
    min_distance: float,
    max_distance: float,
    min_latency: float,
    max_latency: float
):
    """
    Calculate an overall RAG performance score.

    Higher is better for:
    - answer quality
    - retrieval quality
    - speed
    """

    # ------------------------------------------
    # Normalize retrieval distance
    # Lower distance = better retrieval
    # ------------------------------------------

    if max_distance == min_distance:
        retrieval_score = 1.0
    else:
        retrieval_score = (
            (max_distance - best_distance)
            / (max_distance - min_distance)
        )

    # ------------------------------------------
    # Normalize latency
    # Lower latency = better speed
    # ------------------------------------------

    if max_latency == min_latency:
        speed_score = 1.0
    else:
        speed_score = (
            (max_latency - latency_ms)
            / (max_latency - min_latency)
        )

    # ------------------------------------------
    # Keep values between 0 and 1
    # ------------------------------------------

    retrieval_score = max(
        0.0,
        min(1.0, retrieval_score)
    )

    speed_score = max(
        0.0,
        min(1.0, speed_score)
    )

    # ------------------------------------------
    # Final weighted score
    # ------------------------------------------

    overall_score = (
        0.50 * answer_quality
        + 0.30 * retrieval_score
        + 0.20 * speed_score
    )

    return {
        "overall_score": round(
            overall_score,
            4
        ),
        "retrieval_score": round(
            retrieval_score,
            4
        ),
        "speed_score": round(
            speed_score,
            4
        )
    }