def clean_text(text):
    """
    Clean extracted PDF text.
    """
    text = " ".join(text.split())
    return text


def create_chunks(text, page_number, chunk_size=500, overlap=100):
    """
    Split page text into smaller overlapping chunks
    while keeping the page number.
    """

    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size

        chunk_text = " ".join(words[start:end])

        chunks.append({
            "text": chunk_text,
            "page": page_number
        })

        start += chunk_size - overlap

    return chunks