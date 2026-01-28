/**
 * API Context
 * 
 * Provides API methods to components via React context.
 * Wraps the api service for easy access throughout the app.
 */

import React, { createContext, useContext, type ReactNode } from 'react';
import apiClient from '../services/api';

// Define the context type based on apiClient methods
interface ApiContextType {
  exportConfiguration: typeof apiClient.exportConfiguration;
  importConfiguration: typeof apiClient.importConfiguration;
  listProtectionGroups: typeof apiClient.listProtectionGroups;
  listRecoveryPlans: typeof apiClient.listRecoveryPlans;
}

const ApiContext = createContext<ApiContextType | null>(null);

interface ApiProviderProps {
  children: ReactNode;
}

export const ApiProvider: React.FC<ApiProviderProps> = ({ children }) => {
  const value: ApiContextType = {
    exportConfiguration: apiClient.exportConfiguration.bind(apiClient),
    importConfiguration: apiClient.importConfiguration.bind(apiClient),
    listProtectionGroups: apiClient.listProtectionGroups.bind(apiClient),
    listRecoveryPlans: apiClient.listRecoveryPlans.bind(apiClient),
  };

  return <ApiContext.Provider value={value}>{children}</ApiContext.Provider>;
};

export const useApi = (): ApiContextType => {
  const context = useContext(ApiContext);
  if (!context) {
    throw new Error('useApi must be used within an ApiProvider');
  }
  return context;
};
