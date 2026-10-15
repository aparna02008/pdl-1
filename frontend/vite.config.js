import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'CiviAI',
        short_name: 'CiviAI',
        description: 'Report civic issues in your city',
        start_url: '/',
        display: 'standalone',
        background_color: '#ffffff',
        theme_color: '#3b5b8c',
        icons: [
          { src: '/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icon-512.png', sizes: '512x512', type: 'image/png' }
        ]
      }
    })
  ],
  server: { port: 5173, allowedHosts: true },
  preview: { allowedHosts: true }
})