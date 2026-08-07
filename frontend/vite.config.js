import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd())
  const backendHost = env.VITE_BACKEND_HOST || 'localhost:5000'

  return {
    plugins: [react()],
    server: {
      host: true,
      port: 80,
      // Proxy /api/* to Flask backend — mirrors the nginx rule used in production
      proxy: {
        '/api': {
          target: `http://${backendHost}`,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },
  }
})
