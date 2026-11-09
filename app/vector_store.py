
import uuid

import chromadb
from sentence_transformers import SentenceTransformer


# ============================================================
# CHROMADB
# ============================================================

chroma_client = chromadb.PersistentClient(
    path="data/vector_db"
)

collection = chroma_client.get_or_create_collection(
    name="mentara_documents"
)


# ============================================================
# EMBEDDING MODEL
# ============================================================

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# ============================================================
# ADD PDF CHUNKS
# ============================================================

def add_chunks(chunks, filename, document_id):
    """
    Generate embeddings and store all PDF chunks.

    Every chunk stores:
    - Unique ID
    - Document ID
    - Filename
    - Page number
    - Chunk index
    """

    if not chunks:
        return 0

    documents = []
    metadatas = []
    ids = []

    upload_id = str(uuid.uuid4())

    for index, chunk in enumerate(chunks):

        documents.append(chunk["text"])

        metadatas.append({
            "filename": filename,
            "document_id": int(document_id),
            "page": int(chunk["page"]),
            "chunk_index": index
        })

        ids.append(
            f"{upload_id}_chunk_{index}"
        )

    embeddings = embedding_model.encode(
        documents,
        show_progress_bar=False
    ).tolist()

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    return len(documents)


# ============================================================
# SEARCH RELEVANT CHUNKS
# ============================================================

def search_chunks(
    query,
    top_k=3,
    filename=None,
    document_id=None
):
    """
    Retrieve the most relevant chunks.

    Optional filters ensure that results
    belong to the selected PDF.
    """

    if not query or not query.strip():
        return []

    where = None

    if document_id is not None:
        where = {
            "document_id": int(document_id)
        }

    elif filename:
        where = {
            "filename": filename
        }

    query_embedding = embedding_model.encode(
        [query]
    ).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"]
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    sources = []

    for document, metadata in zip(documents, metadatas):

        sources.append({
            "text": document,
            "filename": metadata["filename"],
            "page": metadata["page"],
            "document_id": metadata.get("document_id")
        })

    return sources


# ============================================================
# GET ALL CHUNKS FROM ONE PDF
# ============================================================

def get_document_chunks(document_id):
    """
    Retrieve every stored chunk belonging
    to one uploaded PDF.

    Unlike semantic search, this function
    does not select only the top relevant chunks.
    """

    results = collection.get(
        where={
            "document_id": int(document_id)
        },
        include=["documents", "metadatas"]
    )

    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])

    chunks = []

    for document, metadata in zip(documents, metadatas):

        chunks.append({
            "text": document,
            "filename": metadata["filename"],
            "page": metadata["page"],
            "chunk_index": metadata.get("chunk_index", 0)
        })

    # Preserve original PDF order.
    chunks.sort(
        key=lambda item: (
            item["page"],
            item["chunk_index"]
        )
    )

    return chunks
