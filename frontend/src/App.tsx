/**
 * Main Application Component
 * 
 * Sets up routing, authentication, theming, and layout structure.
 * Entry point for the React application.
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './contexts/AuthContext';
import { ErrorBoundary } from './components/ErrorBoundary';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AppLayout } from './components/cloudscape/AppLayout';
import { LoginPage } from './pages/LoginPage';
import { Dashboard } from './pages/Dashboard';
import { ProtectionGroupsPage } from './pages/ProtectionGroupsPage';
import { ExecutionsPage } from './pages/ExecutionsPage';
import { ExecutionDetailsPage } from './pages/ExecutionDetailsPage';
import { RecoveryPlansPage } from './pages/RecoveryPlansPage';

/**
 * Main App Component
 * 
 * Provides routing, theming, and authentication context to the entire application.
 * API client is automatically initialized with AWS config from window.AWS_CONFIG.
 */
function App() {
  return (
    <>
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
            {/* Public routes - no AppLayout wrapper */}
            <Route path="/login" element={<LoginPage />} />
            
            {/* Protected routes - wrapped with AppLayout */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <Dashboard />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            
            {/* Protection Groups */}
            <Route
              path="/protection-groups"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <ProtectionGroupsPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            
            <Route
              path="/protection-groups/new"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <ProtectionGroupsPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            
            <Route
              path="/recovery-plans"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <RecoveryPlansPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            
            <Route
              path="/recovery-plans/new"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <RecoveryPlansPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            
            <Route
              path="/executions/:executionId"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <ExecutionDetailsPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            
            <Route
              path="/executions"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <ExecutionsPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            
            {/* Catch-all redirect to home */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          </ErrorBoundary>
        </BrowserRouter>
      </AuthProvider>
    </>
  );
}

export default App;
