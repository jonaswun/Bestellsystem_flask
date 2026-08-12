import fs from 'fs'
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd())
  const backendHost = env.VITE_BACKEND_HOST || 'localhost:5000'

  return {
    plugins: [
      react(),

      VitePWA({
        registerType: 'autoUpdate',
        injectRegister: 'auto',

        includeAssets: [
          'vite.svg',
          'Logos_Rucksackberger_klein.jpg',
        ],

        manifest: {
          name: 'Bestellsystem',
          short_name: 'BestellApp',
          description: 'Bestellsystem Web App',

          theme_color: '#1f2937',
          background_color: '#ffffff',

          display: 'standalone',
          orientation: 'portrait',

          start_url: '/',
          scope: '/',

          icons: [
            {
              src: 'Logos_Rucksackberger_klein.jpg',
              sizes: '512x512',
              type: 'image/jpeg',
            },
            {
              src: 'vite.svg',
              sizes: '192x192',
              type: 'image/svg+xml',
            },
          ],
        },

        workbox: {
          cleanupOutdatedCaches: true,
          clientsClaim: true,
          skipWaiting: true,
        },
      }),
    ],

    server: {
      host: true,
      port: 443,
      https: {
        key: fs.readFileSync('./certs/bestellsystem.service-key.pem'),
        cert: fs.readFileSync('./certs/bestellsystem.service.pem'),
      },
      proxy: {
        '/api': {
          target: `http://${backendHost}`,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },

    preview: {
      host: true,
      port: 443,
      https: {
        key: fs.readFileSync('./certs/bestellsystem.service-key.pem'),
        cert: fs.readFileSync('./certs/bestellsystem.service.pem'),
      },
    },
  }
})