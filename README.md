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

## 🚀 Getting Started

**1. Clone the repository**

```bash
git clone https://github.com/Alina-farooqui17/Mentara.git
cd Mentara
```

**2. Set up the backend**

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**3. Configure environment variables**

Create a `.env` file in the root directory:

```env
GROQ_API_KEY=your_groq_api_key
DATABASE_URL=your_supabase_database_url
```

**4. Run the backend**

```bash
uvicorn app.main:app --reload
```

**5. Run the frontend**

Open another terminal:

```bash
cd mentara-react-frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

## 🔮 Future Enhancements

- Flashcard generation
- Cloud-based vector storage
- Personalized learning spaces
- Learning progress analytics
- Support for additional document formats

## 💡 What Makes Mentara Special?

Mentara brings together full-stack development, Generative AI, document processing, and semantic search to create a practical AI-powered learning experience.

Building this project provided hands-on experience with **LLM integration, REST APIs, vector databases, embeddings, React, FastAPI, and PostgreSQL.**

