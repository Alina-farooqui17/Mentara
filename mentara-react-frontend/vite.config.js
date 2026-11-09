import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/upload-pdf":"http://127.0.0.1:8000", "/ask":"http://127.0.0.1:8000", "/generate-notes":"http://127.0.0.1:8000", "/generate-mcqs":"http://127.0.0.1:8000", "/submit-quiz":"http://127.0.0.1:8000" }
  }
});
