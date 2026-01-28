/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    // Note: aws-config.js injection removed - using aws-config.json fetch in index.html instead
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
          
          // CloudScape Design System
          'vendor-cloudscape': ['@cloudscape-design/components', '@cloudscape-design/collection-hooks'],
          
          // AWS Amplify
          'vendor-aws': ['aws-amplify', '@aws-amplify/ui-react'],
          
          // HTTP client and utilities
          'vendor-http': ['axios', 'react-hot-toast', 'date-fns'],
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

  // Vitest configuration
  test: {
    globals: true,
    environment: 'jsdom',
    include: ['src/**/*.{test,tests}.{js,ts,tsx}'],
    setupFiles: ['./src/test/setup.ts'],
  },
})
