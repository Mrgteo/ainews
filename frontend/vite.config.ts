import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3015,
    proxy: {
      '/api': {
        target: 'http://localhost:8015',
        changeOrigin: true,
      },
    },
  },
})
