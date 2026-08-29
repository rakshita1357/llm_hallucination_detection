import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      // Proxy API calls to backend if it runs on a different port
      '/api': {
        target: 'http://localhost:8000', // change if your backend uses another port
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
