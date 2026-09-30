import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Dev: same-origin /api → FastAPI (no CORS needed). Prod: set VITE_API_URL or
// serve behind a reverse proxy that forwards /api to the backend.
// Tailwind runs via postcss.config.js (tailwindcss v3).
export default defineConfig({
  plugins: [react()],
  // Default `npm run build` → frontend/dist. `npm run build:backend` writes
  // into ../backend/public (outside this project root), so emptyOutDir must
  // be allowed or Vite will refuse to wipe that folder.
  build: {
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
