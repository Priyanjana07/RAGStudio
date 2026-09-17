import fitz # type: ignore


def extract_text(pdf_path):

    document = fitz.open(pdf_path)

    pages = []

    for page_number, page in enumerate(document):

        text = page.get_text()

        pages.append({
            "page": page_number + 1,
            "text": text,
            "character_count": len(text),
            "word_count": len(text.split()),
            "has_text": bool(text.strip())
        })

    document.close()

    return pages