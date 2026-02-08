import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  // NC Framework module path: /m/demo/agent-ui/
  base: '/m/demo/agent-ui/',
  server: {
    allowedHosts: true,
    proxy: {
      '/agent-api': { 
        target: process.env.VITE_API_TARGET || 'http://127.0.0.1:8000', 
        changeOrigin: true 
      }
    }
  }
})
