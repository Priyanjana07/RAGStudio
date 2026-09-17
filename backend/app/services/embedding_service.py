from sentence_transformers import SentenceTransformer


# Available embedding models
SUPPORTED_MODELS = {
    "minilm": "all-MiniLM-L6-v2",
     "mpnet": "all-mpnet-base-v2",
     "distilroberta": "all-distilroberta-v1",
    
}


_models = {}


def get_model(model_name: str = "minilm"):
    """
    Load an embedding model once and reuse it.
    """

    if model_name not in SUPPORTED_MODELS:
        raise ValueError(
            f"Unsupported embedding model: {model_name}"
        )

    if model_name not in _models:
        _models[model_name] = SentenceTransformer(
            SUPPORTED_MODELS[model_name]
        )

    return _models[model_name]


def generate_embedding(
    text: str,
    model_name: str = "minilm"
):
    """
    Convert text into a numerical vector.
    """

    model = get_model(model_name)

    embedding = model.encode(text)

    return embedding.tolist()

def generate_embeddings(
    texts: list[str],
    model_name: str = "minilm"
):
    """
    Generate embeddings for multiple texts at once.
    Batch encoding is much faster than encoding one text at a time.
    """

    model = get_model(model_name)

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        show_progress_bar=False
    )

    return embeddings.tolist()