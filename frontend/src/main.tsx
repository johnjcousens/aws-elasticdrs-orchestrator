import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// CloudScape Design System
import '@cloudscape-design/global-styles/index.css'
import { initializeTheme } from './styles/cloudscape-theme'

// Initialize CloudScape theme
initializeTheme()

// Wait for AWS config to load before rendering React
async function init() {
  if (window.configReady) {
    await window.configReady;
  }
  
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
}

init();
