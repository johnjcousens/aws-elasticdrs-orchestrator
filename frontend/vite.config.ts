import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { injectConfigScript } from './vite-plugin-inject-config'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    injectConfigScript(), // Inject aws-config.js script tag into index.html
  ],
  
  // Build optimization configuration
  build: {
    // Minification settings
    minify: 'esbuild',
    
    // Code splitting configuration
    rollupOptions: {
      output: {
        // Manual chunks for better caching
        manualChunks: {
          // Core vendor libraries
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          
          // Material-UI core
          'vendor-mui-core': ['@mui/material', '@emotion/react', '@emotion/styled'],
          
          // Material-UI icons and data grid (loaded on demand)
          'vendor-mui-extended': ['@mui/icons-material', '@mui/x-data-grid'],
          
          // AWS Amplify
          'vendor-aws': ['aws-amplify', '@aws-amplify/ui-react'],
          
          // HTTP client
          'vendor-http': ['axios'],
        },
      },
    },
    
    // Chunk size warning limit (500KB)
    chunkSizeWarningLimit: 500,
    
    // Source maps for production debugging (optional)
    // Set to false to disable, 'hidden' to generate but not expose in browser
    sourcemap: false,
    
    // Target modern browsers for smaller bundle size
    target: 'es2015',
    
    // Asset inline limit (4KB)
    assetsInlineLimit: 4096,
    
    // CSS code splitting
    cssCodeSplit: true,
  },
  
  // Development server configuration
  server: {
    port: 3000,
    open: true,
    cors: true,
  },
  
  // Preview server configuration (for testing production build locally)
  preview: {
    port: 3000,
    open: true,
  },
})
