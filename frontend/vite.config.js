import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const backendProxy = {
  '/api': 'http://127.0.0.1:8000',
  '/health': 'http://127.0.0.1:8000',
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    proxy: backendProxy,
  },
  preview: {
    host: true,
    proxy: backendProxy,
  },
})
