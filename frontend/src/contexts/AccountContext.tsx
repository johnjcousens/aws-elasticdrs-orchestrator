/**
 * Account Context
 * 
 * Provides account selection state across the entire application.
 * This enables multi-account support for all operations.
 */

import React, { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
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
}

const AccountContext = createContext<AccountContextType | undefined>(undefined);

interface AccountProviderProps {
  children: ReactNode;
}

export const AccountProvider: React.FC<AccountProviderProps> = ({ children }) => {
  const [selectedAccount, setSelectedAccount] = useState<SelectProps.Option | null>(null);
  const [availableAccounts, setAvailableAccounts] = useState<TargetAccount[]>([]);
  const [accountsLoading, setAccountsLoading] = useState(true);
  const [accountsError, setAccountsError] = useState<string | null>(null);

  const refreshAccounts = async () => {
    // Don't fetch if not authenticated
    if (!isAuthenticated || authLoading) {
      setAccountsLoading(false);
      return;
    }

    setAccountsLoading(true);
    setAccountsError(null);
    
    try {
      const accounts = await apiClient.getTargetAccounts();
      setAvailableAccounts(accounts);
      
      // Auto-select current account (where solution is deployed) as default
      if (!selectedAccount) {
        const currentAccount = accounts.find((acc: TargetAccount) => acc.isCurrentAccount);
        if (currentAccount) {
          const accountOption = {
            value: currentAccount.accountId,
            label: currentAccount.accountName 
              ? `${currentAccount.accountName} (${currentAccount.accountId})`
              : currentAccount.accountId
          };
          setSelectedAccount(accountOption);
        }
      }
    } catch (err: any) {
      console.error('Error fetching accounts:', err);
      
      // Handle authentication errors specifically
      if (err?.response?.status === 401 || err?.message?.includes('Unauthorized')) {
        setAccountsError('Authentication required. Please sign in again.');
        // Clear accounts when authentication fails
        setAvailableAccounts([]);
        setSelectedAccount(null);
      } else if (err?.message?.includes('CORS') || err?.message?.includes('No response from server')) {
        setAccountsError('Connection error. Please check your network and try again.');
      } else {
        setAccountsError('Unable to fetch target accounts');
      }
    } finally {
      setAccountsLoading(false);
    }
  };

  const getCurrentAccountId = (): string | null => {
    return selectedAccount?.value || null;
  };

  const getCurrentAccountName = (): string | null => {
    const accountId = selectedAccount?.value;
    if (!accountId) return null;
    
    const account = availableAccounts.find(acc => acc.accountId === accountId);
    return account?.accountName || accountId;
  };

  const { isAuthenticated, loading: authLoading } = useAuth();

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
      setSelectedAccount(null);
      setAccountsLoading(false);
      setAccountsError(null);
    }
  }, [isAuthenticated, authLoading]);

  const contextValue: AccountContextType = {
    selectedAccount,
    setSelectedAccount,
    availableAccounts,
    accountsLoading,
    accountsError,
    refreshAccounts,
    getCurrentAccountId,
    getCurrentAccountName,
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