# 🌿 Mentara

### Your AI-Powered Smart Study Companion

**Learn Smarter. Understand Better. Study with AI.**

Mentara transforms static PDF documents into interactive learning experiences using Generative AI, semantic search, and modern web technologies.

Upload your study material, ask questions, generate notes, create MCQs, and test your knowledge — all in one place.

---

## ✨ Features

- 📄 **Smart PDF Processing** – Upload PDFs and extract study content.
- 💬 **AI-Powered Q&A** – Get context-aware answers from your documents.
- 🧠 **Semantic Search** – Find relevant information using vector embeddings.
- 📝 **AI Notes Generation** – Turn lengthy study materials into structured notes.
- ❓ **MCQ Generation** – Automatically create practice questions.
- 🎯 **Interactive Quizzes** – Test your understanding and view results.
- 📚 **Learning History** – Access saved notes and previous learning activities.

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| Frontend | React.js, JavaScript, HTML, CSS, Vite |
| Backend | Python, FastAPI, Uvicorn |
| AI | Groq API, GPT-OSS 120B |
| Embeddings | Sentence Transformers, all-MiniLM-L6-v2 |
| Vector Database | ChromaDB |
| Database | Supabase PostgreSQL, SQLAlchemy |
| PDF Processing | PyPDF |

## ⚙️ How It Works

```text
PDF Upload
    ↓
Text Extraction & Chunking
    ↓
Embedding Generation
    ↓
ChromaDB Semantic Search
    ↓
Groq AI Processing
    ↓
Answers | Notes | MCQs | Quizzes
```

## 📂 Project Structure

```text
Mentara/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── text_processor.py
│   └── vector_store.py
│
├── mentara-react-frontend/
│   ├── src/
│   ├── public/
│   ├── api.js
│   └── package.json
│
├── requirements.txt
└── README.md
```


## 🔮 Future Enhancements

- Flashcard generation
- Cloud-based vector storage
- Personalized learning spaces
- Learning progress analytics
- Support for additional document formats

## 💡 What Makes Mentara Special?

Mentara brings together full-stack development, Generative AI, document processing, and semantic search to create a practical AI-powered learning experience.

Building this project provided hands-on experience with **LLM integration, REST APIs, vector databases, embeddings, React, FastAPI, and PostgreSQL.**

