import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    open: true,
    proxy: {
      // REST API calls — forwarded to Priyanshu's backend on Codespace
      '/api': {
        target: 'https://depin-backend.loca.lt',
        changeOrigin: true,
        secure: false,
        headers: {
          'bypass-tunnel-reminder': 'true',
          'User-Agent': 'depin-guard-bot',
        },
      },
      // WebSocket for live sensor stream
      '/ws': {
        target: 'wss://depin-backend.loca.lt',
        ws: true,
        changeOrigin: true,
        headers: {
          'bypass-tunnel-reminder': 'true',
          'User-Agent': 'depin-guard-bot',
        },
      },
    },
  },
});