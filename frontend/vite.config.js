import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Replace with your actual local IP address (e.g., 192.168.1.42)

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,    // or use '0.0.0.0' to bind to all interfaces
    port: 5173,
  }
})