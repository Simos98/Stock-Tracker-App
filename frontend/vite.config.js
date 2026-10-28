import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Where `npm run dev` forwards /api calls; override if Flask runs on another port
const apiProxyTarget = process.env.API_PROXY_TARGET || 'http://127.0.0.1:5000';

export default defineConfig({
  plugins: [react()],
  server: {
    // Forward API calls to Flask so the browser sees a single origin in dev
    proxy: {
      '/api': apiProxyTarget,
    },
  },
  build: {
    // Flask serves the built SPA from backend/src/static
    outDir: '../backend/src/static',
    emptyOutDir: true,
  },
});
