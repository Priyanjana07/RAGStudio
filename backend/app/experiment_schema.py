from typing import Literal

from pydantic import BaseModel, Field, model_validator


# -------------------------
# Chunking configuration
# -------------------------

class ChunkingConfig(BaseModel):
    strategy: Literal[
        "fixed",
        "recursive",
        "sentence",
        "token"
    ]

    chunk_size: int = Field(
        gt=0,
        description="Maximum size of each chunk"
    )

    overlap: int = Field(
        ge=0,
        description="Number of characters/tokens overlapping between chunks"
    )

    @model_validator(mode="after")
    def validate_overlap(self):
        if self.overlap >= self.chunk_size:
            raise ValueError(
                "overlap must be smaller than chunk_size"
            )

        return self


# -------------------------
# Embedding configuration
# -------------------------

class EmbeddingConfig(BaseModel):
    model: Literal[
        "minilm",
        "mpnet",
        "distilroberta"
    ]


# -------------------------
# Retrieval configuration
# -------------------------

class RetrievalConfig(BaseModel):
    method: Literal[
        "vector",
        "bm25",
        "hybrid",
        "hybrid_reranker",
        "rrf"
    ]

    top_k: int = Field(
        gt=0,
        description="Number of results returned by retrieval"
    )

    similarity: Literal[
        "cosine"
    ]

    threshold: float | None = Field(
        default=None,
        ge=0,
        description="Optional similarity threshold"
    )


# -------------------------
# Generation configuration
# -------------------------

class GenerationConfig(BaseModel):
    llm: str

    temperature: float = Field(
        ge=0,
        le=2
    )

    top_p: float = Field(
        gt=0,
        le=1
    )

    max_tokens: int = Field(
        gt=0
    )


# -------------------------
# Complete configuration
# -------------------------

class ExperimentConfig(BaseModel):
    chunking: ChunkingConfig
    embedding: EmbeddingConfig
    retrieval: RetrievalConfig
    generation: GenerationConfig


# -------------------------
# Experiment request
# -------------------------

class ExperimentRunRequest(BaseModel):
    document_id: int

    evaluation_set_id: int

    config_a: ExperimentConfig
    config_b: ExperimentConfig