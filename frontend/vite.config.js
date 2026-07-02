import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  define: {
    // react-draggable/react-resizable (react-grid-layout's deps) read
    // process.env.NODE_ENV directly; Vite doesn't polyfill `process` in the
    // browser bundle like webpack does, so without this they throw
    // "process is not defined" the moment a drag/resize starts.
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development'),
  },
})
