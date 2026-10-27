import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
  server: {
    proxy: {
      // FastAPI backend (backend/app); uvicorn's default port
      '/api': 'http://localhost:8000',
    },
  },
});
