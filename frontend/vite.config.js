import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');

  const BACKEND_URL  = env.VITE_API_URL   || 'http://localhost:8000';
  const AUTH_URL     = env.VITE_AUTH_URL  || 'http://localhost:8001';
  const WS_BACKEND   = BACKEND_URL.replace(/^http/, 'ws');

  return {
    plugins: [react()],
    server: {
      port: 3000,
      open: true,
      proxy: {
        '/api': {
          target: BACKEND_URL,
          changeOrigin: true,
          secure: false,
          headers: {
            'bypass-tunnel-reminder': 'true',
            'User-Agent': 'depin-guard-bot',
          },
        },
        '/fraud-alerts': {
          target: BACKEND_URL,
          changeOrigin: true,
          secure: false,
          headers: {
            'bypass-tunnel-reminder': 'true',
            'User-Agent': 'depin-guard-bot',
          },
        },
        '/report-fraud': {
          target: BACKEND_URL,
          changeOrigin: true,
          secure: false,
          headers: {
            'bypass-tunnel-reminder': 'true',
            'User-Agent': 'depin-guard-bot',
          },
        },
        '/login': {
          target: AUTH_URL,
          changeOrigin: true,
          secure: false,
          headers: {
            'bypass-tunnel-reminder': 'true',
            'User-Agent': 'depin-guard-bot',
          },
        },
        '/verify': {
          target: AUTH_URL,
          changeOrigin: true,
          secure: false,
          headers: {
            'bypass-tunnel-reminder': 'true',
            'User-Agent': 'depin-guard-bot',
          },
        },
        '/ws': {
          target: WS_BACKEND,
          ws: true,
          changeOrigin: true,
          headers: {
            'bypass-tunnel-reminder': 'true',
            'User-Agent': 'depin-guard-bot',
          },
        },
      },
    },
  };
});