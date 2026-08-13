import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({
  root: 'apps/web',
  plugins: [react()],
  server: {
    proxy: {
      '/auth': 'http://127.0.0.1:8000',
      '/slots': 'http://127.0.0.1:8000',
      '/appointment-confirmations': 'http://127.0.0.1:8000',
      '/appointments': 'http://127.0.0.1:8000',
      '/pages': 'http://127.0.0.1:8000',
      '/answers': 'http://127.0.0.1:8000',
      '/conversations': 'http://127.0.0.1:8000',
      '/admin': 'http://127.0.0.1:8000',
    },
  },
  build: { outDir: '../../dist', emptyOutDir: true },
});
