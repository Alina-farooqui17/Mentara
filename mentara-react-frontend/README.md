# Mentara React Frontend

This is the redesigned React/Vite frontend for Mentara. It keeps the existing FastAPI RAG backend unchanged.

## Run

1. Keep your FastAPI backend running on `http://127.0.0.1:8000`.
2. Open a terminal in this folder.
3. Run:

```bash
npm install
npm run dev
```

4. Open `http://localhost:5173`.

The Vite proxy sends Mentara API requests to the existing FastAPI server.

## Personalization

The name entered on the welcome screen is stored only in the browser's `localStorage`. There is no hard-coded personal name in the app.
