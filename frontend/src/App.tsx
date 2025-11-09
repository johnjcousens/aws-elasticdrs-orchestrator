/**
 * Main Application Component
 * 
 * Sets up routing, authentication, theming, and layout structure.
 * Entry point for the React application.
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './contexts/AuthContext';
import { ErrorBoundary } from './components/ErrorBoundary';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Layout } from './components/Layout';
import { LoginPage } from './pages/LoginPage';
import { Dashboard } from './pages/Dashboard';
import { ProtectionGroupsPage } from './pages/ProtectionGroupsPage';
import { ExecutionsPage } from './pages/ExecutionsPage';
import { RecoveryPlansPage } from './pages/RecoveryPlansPage';
import { theme } from './theme';
import apiClient from './services/api';
import { awsConfig } from './aws-config';

// Initialize API client with endpoint from AWS config
const apiEndpoint = awsConfig.API.REST.DRSOrchestration.endpoint;
apiClient.initialize(apiEndpoint);

/**
 * Main App Component
 * 
 * Provides routing, theming, and authentication context to the entire application.
 */
function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Toaster
        position="top-right"
        toastOptions={{
          // Default options for all toasts
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            duration: 3000,
            iconTheme: {
              primary: '#4caf50',
              secondary: '#fff',
            },
          },
          error: {
            duration: 5000,
            iconTheme: {
              primary: '#f44336',
              secondary: '#fff',
            },
          },
        }}
      />
      <AuthProvider>
        <BrowserRouter>
          <ErrorBoundary>
            <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginPage />} />
            
            {/* Protected routes */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Dashboard />
                  </Layout>
                </ProtectedRoute>
              }
            />
            
            {/* Protection Groups */}
            <Route
              path="/protection-groups"
              element={
                <ProtectedRoute>
                  <Layout>
                    <ProtectionGroupsPage />
                  </Layout>
                </ProtectedRoute>
              }
            />
            
            <Route
              path="/recovery-plans"
              element={
                <ProtectedRoute>
                  <Layout>
                    <RecoveryPlansPage />
                  </Layout>
                </ProtectedRoute>
              }
            />
            
            <Route
              path="/executions"
              element={
                <ProtectedRoute>
                  <Layout>
                    <ExecutionsPage />
                  </Layout>
                </ProtectedRoute>
              }
            />
            
            <Route
              path="/history"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Dashboard />
                  </Layout>
                </ProtectedRoute>
              }
            />
            
            {/* Catch-all redirect to home */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          </ErrorBoundary>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
