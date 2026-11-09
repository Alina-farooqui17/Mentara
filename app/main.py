import os
import json
import uuid
import time
from pathlib import Path
from typing import Optional
from groq import Groq

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pypdf import PdfReader
from google import genai
from sqlalchemy.orm import Session

from app.text_processor import clean_text, create_chunks
from app.vector_store import (
    add_chunks,
    search_chunks,
    get_document_chunks
)
from app.database import SessionLocal
from app import models


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
UPLOAD_DIR = BASE_DIR / "data" / "uploads"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv(BASE_DIR / ".env")

api_key = os.getenv("GEMINI_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    raise RuntimeError(
        "GROQ_API_KEY was not found in the .env file."
    )

groq_client = Groq(
    api_key=groq_api_key,
    timeout=45.0,
    max_retries=0
)

GROQ_MODEL = "openai/gpt-oss-120b"


# ============================================================
# GEMINI CONFIGURATION
# ============================================================

client = genai.Client(api_key=api_key)

GEMINI_MODEL = "gemini-3.6-flash"
GEMINI_TIMEOUT = 120


def get_gemini_text(response):

    output_text = getattr(response, "output_text", None)

    if output_text and output_text.strip():
        return output_text.strip()

    outputs = getattr(response, "outputs", None)

    if outputs:
        texts = []

        for output in outputs:
            text = getattr(output, "text", None)

            if text:
                texts.append(text)

        if texts:
            return "\n".join(texts).strip()

    raise RuntimeError("Gemini returned no readable text.")


def ask_gemini(prompt):

    try:
        print("\n[Mentara] Sending request to Groq...")

        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Mentara, an academic study assistant. "
                        "Give accurate, clear, well-organized explanations."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_completion_tokens=4096
        )

        answer = completion.choices[0].message.content

        if not answer or not answer.strip():
            raise RuntimeError("Groq returned an empty response.")

        print("[Mentara] Groq response received successfully.")

        return answer.strip()

    except Exception as e:

        error_message = f"{type(e).__name__}: {str(e)}"

        print(f"\n[Mentara Groq ERROR] {error_message}")

        raise RuntimeError(
            f"AI request failed: {error_message}"
        ) from e


# ============================================================
# DATABASE HELPERS
# ============================================================

def get_document_id(db: Session, filename: Optional[str]):

    if not filename:
        return None

    document = (
        db.query(models.Document)
        .filter(models.Document.filename == filename)
        .order_by(models.Document.id.desc())
        .first()
    )

    return document.id if document else None


def get_document_by_id(db: Session, document_id: int):

    return (
        db.query(models.Document)
        .filter(models.Document.id == document_id)
        .first()
    )


def resolve_document(filename=None, document_id=None):

    db = SessionLocal()

    try:

        if document_id is not None:

            document = get_document_by_id(db, document_id)

        elif filename:

            selected_id = get_document_id(db, filename)

            document = (
                get_document_by_id(db, selected_id)
                if selected_id is not None
                else None
            )

        else:

            document = (
                db.query(models.Document)
                .order_by(models.Document.id.desc())
                .first()
            )

        if not document:
            return None

        return {
            "id": document.id,
            "filename": document.filename
        }

    finally:
        db.close()


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Mentara API",
    description="AI Learning Assistant using RAG, Gemini and Supabase",
    version="2.2.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============================================================
# BASIC API
# ============================================================

@app.get("/api/status")
def api_status():

    return {
        "status": "online",
        "message": "Mentara API is running"
    }


# ============================================================
# ACTIVITY HISTORY
# ============================================================

@app.get("/api/history")
def get_activity_history():

    db = SessionLocal()

    try:

        documents = (
            db.query(models.Document)
            .order_by(models.Document.uploaded_at.desc())
            .all()
        )

        notes = (
            db.query(models.Note)
            .order_by(models.Note.created_at.desc())
            .all()
        )

        attempts = (
            db.query(models.QuizAttempt)
            .order_by(models.QuizAttempt.attempted_at.desc())
            .all()
        )

        return {
            "documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "pages": doc.pages,
                    "total_chunks": doc.total_chunks,
                    "uploaded_at": (
                        doc.uploaded_at.isoformat()
                        if doc.uploaded_at else None
                    )
                }
                for doc in documents
            ],

            "notes": [
                {
                    "id": note.id,
                    "document_id": note.document_id,
                    "content": note.content,
                    "created_at": (
                        note.created_at.isoformat()
                        if note.created_at else None
                    )
                }
                for note in notes
            ],

            "quiz_attempts": [
                {
                    "id": attempt.id,
                    "document_id": attempt.document_id,
                    "score": attempt.score,
                    "total_questions": attempt.total_questions,
                    "percentage": attempt.percentage,
                    "attempted_at": (
                        attempt.attempted_at.isoformat()
                        if attempt.attempted_at else None
                    )
                }
                for attempt in attempts
            ]
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Could not retrieve activity history: {str(e)}"
        )

    finally:
        db.close()


# ============================================================
# UPLOAD PDF
# ============================================================

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file was selected."
        )

    filename = Path(file.filename).name

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    contents = await file.read()

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="The uploaded PDF is empty."
        )

    unique_filename = f"{uuid.uuid4()}_{filename}"
    file_path = UPLOAD_DIR / unique_filename

    with open(file_path, "wb") as f:
        f.write(contents)

    try:
        reader = PdfReader(str(file_path))

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read PDF: {str(e)}"
        )

    all_chunks = []
    readable_pages = 0

    for page_number, page in enumerate(reader.pages, start=1):

        try:
            page_text = page.extract_text()
        except Exception:
            page_text = None

        if not page_text:
            continue

        cleaned_page_text = clean_text(page_text)

        if not cleaned_page_text.strip():
            continue

        readable_pages += 1

        page_chunks = create_chunks(
            cleaned_page_text,
            page_number=page_number,
            chunk_size=500,
            overlap=100
        )

        all_chunks.extend(page_chunks)

    if not all_chunks:
        raise HTTPException(
            status_code=400,
            detail="No readable text was found in this PDF."
        )

    db = SessionLocal()
    document_id = None

    try:

        document = models.Document(
            filename=filename,
            pages=len(reader.pages),
            total_chunks=len(all_chunks)
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        document_id = document.id

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Could not save PDF information: {str(e)}"
        )

    finally:
        db.close()

    try:

        stored_count = add_chunks(
            all_chunks,
            filename,
            document_id
        )

    except Exception as e:

        db = SessionLocal()

        try:

            failed_document = get_document_by_id(db, document_id)

            if failed_document:
                db.delete(failed_document)
                db.commit()

        except Exception:
            db.rollback()

        finally:
            db.close()

        raise HTTPException(
            status_code=500,
            detail=f"Could not store PDF in ChromaDB: {str(e)}"
        )

    return {
        "success": True,
        "filename": filename,
        "pages": len(reader.pages),
        "readable_pages": readable_pages,
        "total_chunks": len(all_chunks),
        "stored_in_chromadb": stored_count,
        "document_id": document_id,
        "stored_in_database": True
    }


# ============================================================
# SEARCH
# ============================================================

@app.get("/search")
def search(question: str):

    if not question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    results = search_chunks(
        question,
        top_k=5
    )

    return {
        "question": question,
        "results": results
    }


# ============================================================
# FORMAT CHUNKS
# ============================================================

def format_chunks(chunks):

    context_parts = []

    for chunk in chunks:

        context_parts.append(
            f"\nPAGE {chunk['page']}\n\n{chunk['text']}"
        )

    return "\n".join(context_parts)


# ============================================================
# DETECT DOCUMENT-WIDE QUESTIONS
# ============================================================

def is_document_wide_question(question):

    question = question.lower()

    document_wide_phrases = [
        "complete story",
        "whole story",
        "entire story",
        "full story",
        "complete summary",
        "full summary",
        "summarize",
        "summary of the pdf",
        "summary of this pdf",
        "entire pdf",
        "whole pdf",
        "complete pdf",
        "whole document",
        "entire document",
        "complete document",
        "all chapters",
        "every chapter",
        "beginning, middle and end",
        "beginning middle and end",
        "chronological order",
        "from beginning to end",
        "from the beginning",
        "overall explanation",
        "all important events",
        "all topics in the document"
    ]

    return any(
        phrase in question
        for phrase in document_wide_phrases
    )


# ============================================================
# ASK AI - OPTIMIZED SINGLE REQUEST
# ============================================================

@app.get("/ask")
def ask_ai(
    question: str,
    filename: Optional[str] = None,
    document_id: Optional[int] = None
):

    if not question or not question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    document = resolve_document(filename, document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Selected PDF was not found."
        )

    selected_document_id = document["id"]
    selected_filename = document["filename"]

    # Broad questions use every stored chunk.
    # Specific questions use semantic retrieval.

    try:

        if is_document_wide_question(question):

            print(
                "[Mentara Ask AI] Document-wide question detected. "
                "Loading all PDF chunks..."
            )

            selected_chunks = get_document_chunks(
                selected_document_id
            )

        else:

            print(
                "[Mentara Ask AI] Specific question detected. "
                "Retrieving relevant chunks..."
            )

            selected_chunks = search_chunks(
                question,
                top_k=8,
                document_id=selected_document_id
            )

        if not selected_chunks:
            raise HTTPException(
                status_code=404,
                detail="No relevant PDF content was found."
            )

        context = format_chunks(selected_chunks)

        print(
            f"[Mentara Ask AI] Sending {len(selected_chunks)} chunks "
            "in one request."
        )

        prompt = f"""
You are Mentara, an expert AI learning assistant.

Answer the student's question using the supplied PDF content.

STUDENT QUESTION:
{question}

DOCUMENT:
{selected_filename}

INSTRUCTIONS:

1. Read all supplied content carefully.
2. Answer the exact question.
3. Do not invent information or introduce unsupported facts.
4. Preserve important names, dates, places, definitions and events.
5. For stories, explain events in chronological order.
6. For complete-story questions, cover the beginning, middle,
   climax and ending wherever the supplied content contains them.
7. For academic questions, explain concepts clearly with examples
   when they are present in the PDF.
8. Use headings and bullet points where useful.
9. Include page references for important information.
10. Avoid unnecessary repetition.
11. If the supplied content does not contain enough information,
    clearly say what is missing instead of guessing.

PDF CONTENT:

{context}

Now provide a clear, comprehensive answer.
"""

        answer = ask_gemini(prompt)

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=502,
            detail=f"Ask AI failed: {str(e)}"
        )

    source_pages = sorted({
        chunk["page"]
        for chunk in selected_chunks
    })

    return {
        "answer": answer,
        "filename": selected_filename,
        "document_id": selected_document_id,
        "total_chunks_processed": len(selected_chunks),
        "total_batches": 1,
        "complete_pdf_processed": (
            len(selected_chunks) == len(
                get_document_chunks(selected_document_id)
            )
        ),
        "sources": [
            {
                "filename": selected_filename,
                "page": page
            }
            for page in source_pages
        ]
    }


# ============================================================
# NOTES REQUEST
# ============================================================

class NotesRequest(BaseModel):

    filename: Optional[str] = None
    document_id: Optional[int] = None


# ============================================================
# GENERATE COMPLETE PDF NOTES - BATCH PROCESSING
# ============================================================

@app.post("/generate-notes")
def generate_notes(request: NotesRequest):

    document = resolve_document(
        request.filename,
        request.document_id
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="The selected PDF was not found."
        )

    selected_document_id = document["id"]
    selected_filename = document["filename"]

    all_chunks = get_document_chunks(selected_document_id)

    if not all_chunks:
        raise HTTPException(
            status_code=404,
            detail="No stored PDF content was found."
        )

    # Small batches keep each Groq request much smaller.
    BATCH_SIZE = 2

    batches = [
        all_chunks[i:i + BATCH_SIZE]
        for i in range(0, len(all_chunks), BATCH_SIZE)
    ]

    total_batches = len(batches)
    notes_parts = []

    print(
        f"[Mentara Notes] Processing {len(all_chunks)} chunks "
        f"in {total_batches} small batches."
    )

    for batch_index, batch_chunks in enumerate(batches, start=1):

        batch_context = format_chunks(batch_chunks)

        prompt = f"""
You are Mentara, an expert academic study assistant.

Create detailed, exam-oriented study notes from ONLY the supplied
section of the PDF. This is section {batch_index} of {total_batches}.

DOCUMENT:
{selected_filename}

INSTRUCTIONS:
1. Cover every important topic and subtopic in this section.
2. Preserve definitions and key terminology.
3. Explain concepts in simple, student-friendly language.
4. Include classifications, lists and important points.
5. Include examples, formulas, rules and steps wherever present.
6. Preserve important names, dates and facts.
7. Do not invent information or omit meaningful content.
8. Retain page references from the supplied text.
9. Use clear headings, subheadings and bullet points.
10. Avoid unnecessary repetition.

Return well-structured Markdown notes for this section only.

PDF SECTION CONTENT:
{batch_context}
"""

        print(
            f"[Mentara Notes] Starting batch {batch_index}/{total_batches}."
        )

        batch_notes = None

        # Retry rate-limit responses. Other errors are reported immediately.
        for attempt in range(3):

            try:
                completion = groq_client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are Mentara, an academic study assistant. "
                                "Create accurate, clear and detailed study notes."
                            )
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_completion_tokens=1600
                )

                batch_notes = completion.choices[0].message.content

                if not batch_notes or not batch_notes.strip():
                    raise RuntimeError("Groq returned empty notes.")

                batch_notes = batch_notes.strip()
                break

            except Exception as e:

                status_code = getattr(e, "status_code", None)

                if status_code == 429 and attempt < 2:

                    retry_after = None
                    response = getattr(e, "response", None)

                    if response is not None:
                        try:
                            retry_after = response.headers.get("retry-after")
                        except Exception:
                            retry_after = None

                    try:
                        wait_seconds = float(retry_after)
                    except (TypeError, ValueError):
                        wait_seconds = 20 * (attempt + 1)

                    wait_seconds = max(5, min(wait_seconds, 90))

                    print(
                        f"[Mentara Notes] Groq rate limit reached. "
                        f"Retrying batch {batch_index} in {wait_seconds} seconds."
                    )

                    time.sleep(wait_seconds)
                    continue

                raise HTTPException(
                    status_code=502,
                    detail=(
                        f"Notes generation failed at batch {batch_index} "
                        f"of {total_batches}: {str(e)}"
                    )
                )

        if not batch_notes:
            raise HTTPException(
                status_code=502,
                detail=f"No notes were returned for batch {batch_index}."
            )

        notes_parts.append(
            f"## Section {batch_index}\n\n{batch_notes}"
        )

        print(
            f"[Mentara Notes] Finished batch {batch_index}/{total_batches}."
        )

        # Leave a gap between requests to reduce per-minute rate limiting.
        if batch_index < total_batches:
            time.sleep(5)

    final_notes = (
        f"# Complete Study Notes: {selected_filename}\n\n"
        + "\n\n---\n\n".join(notes_parts)
    )

    db = SessionLocal()

    try:

        note = models.Note(
            document_id=selected_document_id,
            content=final_notes
        )

        db.add(note)
        db.commit()

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Notes generated, but saving failed: {str(e)}"
        )

    finally:
        db.close()

    print(
        "[Mentara Notes] All PDF sections generated and saved successfully."
    )

    return {
        "notes": final_notes,
        "filename": selected_filename,
        "document_id": selected_document_id,
        "total_chunks_processed": len(all_chunks),
        "total_batches": total_batches,
        "complete_pdf_processed": True
    }


# ============================================================
# MCQ VALIDATION
# ============================================================

def validate_mcqs(mcqs):

    if not isinstance(mcqs, list):
        return False

    for mcq in mcqs:

        if not isinstance(mcq, dict):
            return False

        if "question" not in mcq:
            return False

        if "options" not in mcq:
            return False

        if "answer" not in mcq:
            return False

        if not isinstance(mcq["options"], list):
            return False

        if len(mcq["options"]) != 4:
            return False

        if mcq["answer"] not in ["A", "B", "C", "D"]:
            return False

    return True


# ============================================================
# GENERATE MCQs
# ============================================================

class MCQRequest(BaseModel):

    filename: Optional[str] = None
    document_id: Optional[int] = None
    number: int = 5


@app.post("/generate-mcqs")
def generate_mcqs(request: MCQRequest):

    number = max(1, min(request.number, 10))

    document_id = request.document_id

    if document_id is None and request.filename:

        db = SessionLocal()

        try:

            document_id = get_document_id(
                db,
                request.filename
            )

        finally:
            db.close()

    sources = search_chunks(
        "important concepts definitions examples",
        top_k=12,
        document_id=document_id,
        filename=(
            request.filename
            if document_id is None
            else None
        )
    )

    if not sources:
        raise HTTPException(
            status_code=404,
            detail="No study material found."
        )

    context = format_chunks(sources)

    prompt = f"""
You are Mentara, an AI learning assistant.

Create exactly {number} multiple-choice questions
from the provided study material.

Cover different concepts and topics.

Each question must have exactly four options.

Return ONLY valid JSON using this structure:

[
  {{
    "question": "Question text",
    "options": [
      "Option A",
      "Option B",
      "Option C",
      "Option D"
    ],
    "answer": "A"
  }}
]

The answer must be A, B, C or D.

Do not include markdown.
Do not include explanations outside the JSON.

STUDY MATERIAL:

{context}
"""

    try:

        raw_response = ask_gemini(prompt)

    except Exception as e:

        raise HTTPException(
            status_code=502,
            detail=f"Gemini MCQ generation failed: {str(e)}"
        )

    cleaned = raw_response.strip()

    if cleaned.startswith("```"):

        cleaned = cleaned.replace(
            "```json", ""
        ).replace(
            "```", ""
        ).strip()

    try:

        mcqs = json.loads(cleaned)

    except json.JSONDecodeError:

        raise HTTPException(
            status_code=502,
            detail="Gemini returned invalid MCQ JSON."
        )

    if not validate_mcqs(mcqs):
        raise HTTPException(
            status_code=502,
            detail="Generated MCQs have an invalid format."
        )

    return {
        "mcqs": mcqs
    }


# ============================================================
# QUIZ
# ============================================================

class QuizSubmission(BaseModel):

    correct_answers: list[str]
    user_answers: list[str]
    document_id: Optional[int] = None


@app.post("/submit-quiz")
def submit_quiz(submission: QuizSubmission):

    correct_answers = submission.correct_answers
    user_answers = submission.user_answers

    if len(correct_answers) != len(user_answers):
        raise HTTPException(
            status_code=400,
            detail="Answer lists must have the same length."
        )

    score = 0

    for correct, user in zip(
        correct_answers,
        user_answers
    ):

        if correct.strip().upper() == user.strip().upper():
            score += 1

    total = len(correct_answers)

    percentage = (
        (score / total) * 100
        if total > 0
        else 0
    )

    rounded_percentage = round(percentage, 2)

    db = SessionLocal()

    try:

        document_id = submission.document_id

        if document_id is not None:

            document = get_document_by_id(
                db,
                document_id
            )

            if not document:
                raise HTTPException(
                    status_code=404,
                    detail="Document not found."
                )

        attempt = models.QuizAttempt(
            document_id=document_id,
            score=score,
            total_questions=total,
            percentage=rounded_percentage
        )

        db.add(attempt)
        db.commit()

    except HTTPException:

        db.rollback()
        raise

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Quiz saving failed: {str(e)}"
        )

    finally:
        db.close()

    return {
        "score": score,
        "total_questions": total,
        "percentage": rounded_percentage
    }


# ============================================================
# SERVE FRONTEND
# ============================================================

if not FRONTEND_DIR.exists():
    raise RuntimeError(
        f"Frontend folder not found: {FRONTEND_DIR}"
    )

app.mount(
    "/",
    StaticFiles(
        directory=str(FRONTEND_DIR),
        html=True
    ),
    name="frontend"
)