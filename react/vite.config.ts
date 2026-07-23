import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    proxy: {
      '/api': 'http://localhost:8080'
      // NO rewrite — PHP index.php strips /api prefix itself via preg_replace('#^/api#', '', $uri)
      // Adding rewrite here would double-strip and cause 404 from PHP
    }
  }
})
