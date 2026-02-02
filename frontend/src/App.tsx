/**
 * Main Application Component
 * 
 * Sets up routing, authentication, theming, and layout structure.
 * Entry point for the React application.
 * Build: 2026-01-25T02:25:00Z
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { PermissionsProvider } from './contexts/PermissionsContext';
import { NotificationProvider } from './contexts/NotificationContext';
import { ApiProvider } from './contexts/ApiContext';
import { AccountProvider } from './contexts/AccountContext';
import { SettingsProvider } from './contexts/SettingsContext';
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
 * Uses single AppLayout instance for AWS console-style navigation.
 */
function App() {
  // Force cache bust: 2026-01-25T02:26:00Z
  console.log('DR Orchestrator v2026.01.25');
  
  return (
    <AuthProvider>
      <SettingsProvider>
        <PermissionsProvider>
          <NotificationProvider>
            <ApiProvider>
              <AccountProvider>
                <BrowserRouter>
                  <ErrorBoundary>
                    <Routes>
                    {/* Public routes - no AppLayout wrapper */}
                    <Route path="/login" element={<LoginPage />} />
                    
                    {/* Protected routes - single AppLayout wrapper */}
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
                      path="/executions"
                      element={
                        <ProtectedRoute>
                          <AppLayout>
                            <ExecutionsPage />
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
                    
                    {/* Catch-all redirect to home */}
                    <Route path="*" element={<Navigate to="/" replace />} />
                  </Routes>
                </ErrorBoundary>
              </BrowserRouter>
            </AccountProvider>
          </ApiProvider>
        </NotificationProvider>
      </PermissionsProvider>
      </SettingsProvider>
    </AuthProvider>
  );
}

export default App;