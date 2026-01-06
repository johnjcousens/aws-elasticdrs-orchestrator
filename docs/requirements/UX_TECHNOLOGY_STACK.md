# Technology Stack Setup Guide

## AWS DRS Orchestration System

**Version**: 2.2  
**Date**: January 6, 2026  
**Status**: Production Ready - GitHub Actions CI/CD Migration Complete

---

## Frontend Technology Requirements

### Core Framework Setup
| Technology | Version | Installation | Purpose |
|------------|---------|-------------|---------|
| React | 19.1.1 | `npm install react@19.1.1` | UI framework with hooks and functional components |
| TypeScript | 5.9.3 | `npm install typescript@5.9.3` | Type-safe JavaScript development |
| Vite | 7.1.7 | `npm install vite@7.1.7` | Build tool and development server |

### AWS CloudScape Design System Setup
| Package | Version | Installation | Purpose |
|---------|---------|-------------|---------|
| @cloudscape-design/components | 3.0.1148 | `npm install @cloudscape-design/components@3.0.1148` | AWS-native UI component library |
| @cloudscape-design/collection-hooks | 1.0.78 | `npm install @cloudscape-design/collection-hooks@1.0.78` | Table state management |
| @cloudscape-design/board-components | 3.0.130 | `npm install @cloudscape-design/board-components@3.0.130` | Advanced UI components |
| @cloudscape-design/design-tokens | 3.0.64 | `npm install @cloudscape-design/design-tokens@3.0.64` | Design system tokens |
| @cloudscape-design/global-styles | 1.0.49 | `npm install @cloudscape-design/global-styles@1.0.49` | Global CSS styles |

### AWS Integration Setup
| Package | Version | Installation | Purpose |
|---------|---------|-------------|---------|
| aws-amplify | 6.15.8 | `npm install aws-amplify@6.15.8` | Authentication and AWS integration |
| @aws-amplify/ui-react | 6.13.1 | `npm install @aws-amplify/ui-react@6.13.1` | Pre-built UI components for Amplify |

### Utility Libraries Setup
| Package | Version | Installation | Purpose |
|---------|---------|-------------|---------|
| react-router-dom | 7.9.5 | `npm install react-router-dom@7.9.5` | Client-side routing |
| axios | 1.13.2 | `npm install axios@1.13.2` | HTTP client for API communication |
| react-hot-toast | 2.6.0 | `npm install react-hot-toast@2.6.0` | Toast notifications |
| date-fns | 4.1.0 | `npm install date-fns@4.1.0` | Date formatting and manipulation |

---

## Development Dependencies Setup

### TypeScript & Linting Setup
| Package | Version | Installation | Purpose |
|---------|---------|-------------|---------|
| typescript | 5.9.3 | `npm install -D typescript@5.9.3` | TypeScript compiler |
| @types/react | 19.0.1 | `npm install -D @types/react@19.0.1` | React type definitions |
| @types/react-dom | 19.0.1 | `npm install -D @types/react-dom@19.0.1` | React DOM type definitions |
| eslint | 9.36.0 | `npm install -D eslint@9.36.0` | Code linting |
| typescript-eslint | 8.45.0 | `npm install -D typescript-eslint@8.45.0` | TypeScript ESLint rules |

### Build & Testing Setup
| Package | Version | Installation | Purpose |
|---------|---------|-------------|---------|
| @vitejs/plugin-react | 5.0.4 | `npm install -D @vitejs/plugin-react@5.0.4` | Vite React plugin |
| vitest | 3.2.4 | `npm install -D vitest@3.2.4` | Unit testing framework |
| @vitest/coverage-v8 | 3.2.4 | `npm install -D @vitest/coverage-v8@3.2.4` | Test coverage reporting |
| jsdom | 27.3.0 | `npm install -D jsdom@27.3.0` | DOM testing environment |

---

## Project Setup Instructions

### 1. Initialize Project
```bash
# Create new Vite React TypeScript project
npm create vite@latest aws-drs-orchestration -- --template react-ts
cd aws-drs-orchestration

# Install all dependencies
npm install
```

### 2. Install Required Dependencies
```bash
# Core dependencies
npm install react@19.1.1 react-dom@19.1.1 typescript@5.9.3

# CloudScape Design System
npm install @cloudscape-design/components@3.0.1148 \
  @cloudscape-design/collection-hooks@1.0.78 \
  @cloudscape-design/board-components@3.0.130 \
  @cloudscape-design/design-tokens@3.0.64 \
  @cloudscape-design/global-styles@1.0.49

# AWS Integration
npm install aws-amplify@6.15.8 @aws-amplify/ui-react@6.13.1

# Utilities
npm install react-router-dom@7.9.5 axios@1.13.2 react-hot-toast@2.6.0 date-fns@4.1.0

# Development dependencies
npm install -D @vitejs/plugin-react@5.0.4 vitest@3.2.4 \
  @vitest/coverage-v8@3.2.4 jsdom@27.3.0 eslint@9.36.0 \
  typescript-eslint@8.45.0 @types/react@19.0.1 @types/react-dom@19.0.1
```

---

## Required Configuration Files

### Vite Configuration (`vite.config.ts`)
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    target: 'esnext',
    outDir: 'dist',
  },
  server: {
    port: 5173,
    host: true,
  },
})
```

### TypeScript Configuration (`tsconfig.json`)
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"]
}
```

### Package.json Scripts
```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "type-check": "tsc --noEmit",
    "lint": "eslint .",
    "test": "vitest run",
    "test:watch": "vitest"
  }
}
```

---

## Development Environment Setup

### Required Node.js Version
- **Node.js**: 18.0.0 or higher
- **npm**: 9.0.0 or higher

### Browser Support Requirements
- **Modern Browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **ES2020 Features**: Native support required
- **No IE Support**: Modern JavaScript features used throughout

### Development Server Setup
```bash
# Start development server
npm run dev

# Server will run on http://localhost:5173
# Hot reload enabled for development
```

---

## Build Process Setup

### Development Build
```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Development server
npm run dev
```

### Production Build
```bash
# Full production build
npm run build

# Output directory: dist/
# Optimized for deployment
```

### Testing Setup
```bash
# Run tests once
npm run test

# Watch mode for development
npm run test:watch
```

---

## Performance Considerations

### Bundle Size Expectations
- **Total Bundle**: ~2.5MB (including CloudScape components)
- **Tree Shaking**: Vite automatically removes unused code
- **Code Splitting**: Implement React.lazy() for route-based splitting
- **CloudScape**: Large but provides complete AWS Console experience

### Optimization Requirements
- Use React.memo for expensive components
- Implement useCallback for event handlers
- Use useMemo for expensive calculations
- Lazy load routes and heavy components

---

## Upgrade Guidelines

When upgrading dependencies:

1. **React**: Follow React upgrade guide, test all hooks and components
2. **CloudScape**: Check breaking changes in design system releases
3. **TypeScript**: Update type definitions, fix any type errors
4. **Vite**: Update build configuration if needed

**Critical**: CloudScape components must stay in sync with design tokens and global styles to maintain AWS Console consistency.