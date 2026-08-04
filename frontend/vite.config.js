import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 80,
    // Proxy /api/* to Flask backend — mirrors the nginx rule used in production
    proxy: {
      '/api': {
        target: 'http://192.168.0.137:5000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
