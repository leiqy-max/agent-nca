import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  // Use relative asset URLs so the same build works under /m/demo/agent-ui/
  // and other intranet sub-path deployments.
  base: process.env.VITE_BASE || './',
  server: {
    host: '0.0.0.0',
    allowedHosts: true,
    cors: true,
    proxy: {
      '/agent-api': { 
        target: process.env.VITE_API_TARGET || 'http://127.0.0.1:8000', 
        changeOrigin: true 
      }
    }
  }
})
