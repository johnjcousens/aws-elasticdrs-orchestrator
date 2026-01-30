/**
 * Account Context
 * 
 * Provides account selection state across the entire application.
 * This enables multi-account support for all operations.
 */

import React, { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import type { SelectProps } from '@cloudscape-design/components';
import apiClient from '../services/api';
import type { TargetAccount } from '../components/AccountManagementPanel';
import { useAuth } from './AuthContext';

interface AccountContextType {
  // Account selection
  selectedAccount: SelectProps.Option | null;
  setSelectedAccount: (account: SelectProps.Option | null) => void;
  
  // Available accounts
  availableAccounts: TargetAccount[];
  accountsLoading: boolean;
  accountsError: string | null;
  
  // Helper functions
  refreshAccounts: () => Promise<void>;
  getCurrentAccountId: () => string | null;
  getCurrentAccountName: () => string | null;
  
  // Auto-selection based on settings
  applyDefaultAccount: (defaultAccountId?: string) => void;
  
  // Account enforcement
  isAccountRequired: boolean;
  hasSelectedAccount: boolean;
  defaultAccountId: string | null;
  setDefaultAccountId: (accountId: string | null) => void;
  
  // Helper methods
  isFeatureEnabled: () => boolean;
  getAccountSelectionMessage: () => string;
}

const AccountContext = createContext<AccountContextType | undefined>(undefined);

interface AccountProviderProps {
  children: ReactNode;
}

const DEFAULT_ACCOUNT_STORAGE_KEY = 'drs-orchestration-default-account';
const SELECTED_ACCOUNT_STORAGE_KEY = 'drs-orchestration-selected-account';

export const AccountProvider: React.FC<AccountProviderProps> = ({ children }) => {
  const [selectedAccount, setSelectedAccountState] = useState<SelectProps.Option | null>(null);
  const [availableAccounts, setAvailableAccounts] = useState<TargetAccount[]>([]);
  const [accountsLoading, setAccountsLoading] = useState(true);
  const [accountsError, setAccountsError] = useState<string | null>(null);
  const [defaultAccountId, setDefaultAccountIdState] = useState<string | null>(null);

  const { isAuthenticated, loading: authLoading } = useAuth();

  // Wrapper to log account changes and persist to localStorage
  const setSelectedAccount = (account: SelectProps.Option | null) => {
    console.log('[AccountContext] setSelectedAccount called:', account);
    console.log('[AccountContext] Previous account:', selectedAccount);
    setSelectedAccountState(account);
    
    // Persist selected account to localStorage
    try {
      if (account?.value) {
        localStorage.setItem(SELECTED_ACCOUNT_STORAGE_KEY, account.value);
      } else {
        localStorage.removeItem(SELECTED_ACCOUNT_STORAGE_KEY);
      }
    } catch (error) {
      console.warn('Failed to save selected account to localStorage:', error);
    }
  };

  // Load default account preference from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem(DEFAULT_ACCOUNT_STORAGE_KEY);
      if (stored) {
        setDefaultAccountIdState(stored);
      }
    } catch (error) {
      console.warn('Failed to load default account preference:', error);
    }
  }, []);
  
  // Restore selected account from localStorage on mount
  useEffect(() => {
    try {
      const storedAccountId = localStorage.getItem(SELECTED_ACCOUNT_STORAGE_KEY);
      if (storedAccountId && availableAccounts.length > 0) {
        const account = availableAccounts.find(acc => acc.accountId === storedAccountId);
        if (account) {
          setSelectedAccountState({
            value: account.accountId,
            label: account.accountName || account.accountId,
          });
        }
      }
    } catch (error) {
      console.warn('Failed to restore selected account from localStorage:', error);
    }
  }, [availableAccounts.length]); // Only run when accounts are loaded

  // Save default account preference to localStorage
  const setDefaultAccountId = (accountId: string | null) => {
    setDefaultAccountIdState(accountId);
    try {
      if (accountId) {
        localStorage.setItem(DEFAULT_ACCOUNT_STORAGE_KEY, accountId);
      } else {
        localStorage.removeItem(DEFAULT_ACCOUNT_STORAGE_KEY);
      }
    } catch (error) {
      console.warn('Failed to save default account preference:', error);
    }
  };

  const applyDefaultAccount = useCallback((overrideDefaultId?: string) => {
    if (availableAccounts.length === 0) return;
    
    // Only apply default if no account is currently selected
    if (selectedAccount) return;
    
    // If only one account, auto-select it
    if (availableAccounts.length === 1) {
      const account = availableAccounts[0];
      setSelectedAccountState({
        value: account.accountId,
        label: account.accountName || account.accountId,
      });
      return;
    }
    
    // Use override or stored default account preference
    const targetDefaultId = overrideDefaultId || defaultAccountId;
    
    // If default account is specified and exists, select it
    if (targetDefaultId) {
      const account = availableAccounts.find(acc => acc.accountId === targetDefaultId);
      if (account) {
        setSelectedAccountState({
          value: account.accountId,
          label: account.accountName || account.accountId,
        });
        return;
      }
    }
    
    // Otherwise, don't auto-select - enforce user selection for multiple accounts
  }, [availableAccounts, defaultAccountId, selectedAccount]);

  // Account enforcement helper methods
  const isAccountRequired = true; // Always require account selection
  const hasSelectedAccount = selectedAccount !== null;
  
  const isFeatureEnabled = (): boolean => {
    return hasSelectedAccount;
  };
  
  const getAccountSelectionMessage = (): string => {
    if (accountsLoading) {
      return 'Loading accounts...';
    }
    if (accountsError) {
      return 'Error loading accounts. Please check your connection and try again.';
    }
    if (availableAccounts.length === 0) {
      return 'No target accounts configured. Please add a target account in Settings to continue.';
    }
    return 'Please select a target account to continue. You can set a default account in Settings.';
  };

  const refreshAccounts = useCallback(async () => {
    // Don't fetch if not authenticated
    if (!isAuthenticated || authLoading) {
      setAccountsLoading(false);
      return;
    }

    setAccountsLoading(true);
    setAccountsError(null);
    
    try {
      const accounts = await apiClient.getTargetAccounts();
      // Defensive check: ensure accounts is an array before setting state
      if (Array.isArray(accounts)) {
        setAvailableAccounts(accounts);
      } else {
        console.warn('getTargetAccounts returned non-array:', accounts);
        setAvailableAccounts([]);
      }
      
      // Auto-selection will be handled by applyDefaultAccount when called from settings
    } catch (err: unknown) {
      console.error('Error fetching accounts:', err);
      
      const error = err as { response?: { status?: number; data?: { message?: string } }; message?: string; code?: string };
      
      // Handle specific error types with descriptive messages
      if (error?.response?.status === 401 || error?.message?.includes('Unauthorized')) {
        setAccountsError('Authentication expired. Please sign in again to continue.');
        // Clear accounts when authentication fails
        setAvailableAccounts([]);
        setSelectedAccount(null);
      } else if (error?.response?.status === 403) {
        setAccountsError('Access denied. You do not have permission to view target accounts.');
      } else if (error?.response?.status === 404) {
        setAccountsError('Target accounts service not found. Please contact your administrator.');
      } else if (error?.response?.status && error.response.status >= 500) {
        setAccountsError('Server error occurred while loading target accounts. Please try again in a few moments.');
      } else if (error?.message?.includes('timeout')) {
        setAccountsError('Request timed out. The server may be busy - please try again.');
      } else if (error?.message?.includes('CORS')) {
        setAccountsError('Cross-origin request blocked. Please check your browser settings or contact support.');
      } else if (error?.message?.includes('No response from server')) {
        setAccountsError('Unable to reach the server. Please check your internet connection and try again.');
      } else if (error?.code === 'NETWORK_ERROR' || error?.message?.includes('Network Error')) {
        setAccountsError('Network connection failed. Please check your internet connection.');
      } else if (error?.response?.data?.message) {
        // Use specific error message from API if available
        setAccountsError(`Error: ${error.response.data.message}`);
      } else {
        setAccountsError('Failed to load target accounts. Please refresh the page and try again.');
      }
    } finally {
      setAccountsLoading(false);
    }
  }, [isAuthenticated, authLoading]);

  const getCurrentAccountId = (): string | null => {
    return selectedAccount?.value || null;
  };

  const getCurrentAccountName = (): string | null => {
    const accountId = selectedAccount?.value;
    if (!accountId) return null;
    
    const account = availableAccounts.find(acc => acc.accountId === accountId);
    return account?.accountName || accountId;
  };

  // Apply default account selection when accounts are loaded (only once)
  useEffect(() => {
    if (!accountsLoading && availableAccounts.length > 0 && !selectedAccount) {
      applyDefaultAccount();
    }
  }, [availableAccounts.length, accountsLoading]); // Removed selectedAccount and defaultAccountId from deps

  // Load accounts only after authentication is complete and not loading
  useEffect(() => {
    if (isAuthenticated && !authLoading) {
      // Add a small delay to ensure auth token is fully available
      const timer = setTimeout(() => {
        refreshAccounts();
      }, 100);
      
      return () => clearTimeout(timer);
    } else if (!isAuthenticated && !authLoading) {
      // Clear accounts when not authenticated
      setAvailableAccounts([]);
      setSelectedAccountState(null);
      setAccountsLoading(false);
      setAccountsError(null);
    }
  }, [isAuthenticated, authLoading, refreshAccounts]);

  const contextValue: AccountContextType = {
    selectedAccount,
    setSelectedAccount,
    availableAccounts,
    accountsLoading,
    accountsError,
    refreshAccounts,
    getCurrentAccountId,
    getCurrentAccountName,
    applyDefaultAccount,
    isAccountRequired,
    hasSelectedAccount,
    defaultAccountId,
    setDefaultAccountId,
    isFeatureEnabled,
    getAccountSelectionMessage,
  };

  return (
    <AccountContext.Provider value={contextValue}>
      {children}
    </AccountContext.Provider>
  );
};

export const useAccount = (): AccountContextType => {
  const context = useContext(AccountContext);
  if (context === undefined) {
    throw new Error('useAccount must be used within an AccountProvider');
  }
  return context;
};