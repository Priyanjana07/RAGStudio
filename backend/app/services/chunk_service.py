from langchain_text_splitters import RecursiveCharacterTextSplitter
import tiktoken
def fixed_chunking(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50
) -> list[str]:
    """
    Split text into fixed-size character chunks
    with overlapping characters between chunks.
    """

    if not text:
        return []

    if overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller than chunk_size"
        )

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:

        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        # Move forward while keeping overlap
        start += chunk_size - overlap

    return chunks



def recursive_chunking(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50
) -> list[str]:
    """
    Split text recursively while trying to preserve
    paragraphs, sentences, and words.
    """

    if not text:
        return []

    if overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller than chunk_size"
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            ""
        ]
    )

    return splitter.split_text(text)




def token_chunking(
    text: str,
    chunk_size: int = 200,
    overlap: int = 20
) -> list[str]:
    """
    Split text based on number of tokens rather than characters.
    """

    if not text:
        return []

    if overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller than chunk_size"
        )

    # GPT-style tokenizer
    encoding = tiktoken.get_encoding("cl100k_base")

    tokens = encoding.encode(text)

    chunks = []

    start = 0

    while start < len(tokens):

        end = start + chunk_size

        chunk_tokens = tokens[start:end]

        chunk_text = encoding.decode(chunk_tokens).strip()

        if chunk_text:
            chunks.append(chunk_text)

        start += chunk_size - overlap

    return chunks