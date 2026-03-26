import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    open: true,
    // THE REVERSE PROXY CONFIGURATION
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000', // Forward to Python Backend
        changeOrigin: true,
        secure: false,
      },
      '/ws/live': {
        target: 'ws://depin-backend.loca.lt',
        ws: true,
        changeOrigin: true,
        headers: {
          'bypass-tunnel-reminder': 'true',
          'User-Agent': 'depin-guard-bot'
        }
      }
    }
  }
});
