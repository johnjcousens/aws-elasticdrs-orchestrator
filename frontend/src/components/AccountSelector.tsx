/**
 * Account Selector Component
 * 
 * Provides account selection UI that integrates with AccountContext.
 * Can be used in headers, toolbars, or anywhere account selection is needed.
 */

import React from 'react';
import { Select, StatusIndicator, type SelectProps } from '@cloudscape-design/components';
import { useAccount } from '../contexts/AccountContext';

interface AccountSelectorProps {
  placeholder?: string;
  disabled?: boolean;
  variant?: 'default' | 'compact';
}

export const AccountSelector: React.FC<AccountSelectorProps> = ({
  placeholder = "Select account",
  disabled = false,
  variant = 'default'
}) => {
  const {
    selectedAccount,
    setSelectedAccount,
    availableAccounts,
    accountsLoading,
    accountsError
  } = useAccount();

  if (accountsError) {
    return (
      <StatusIndicator type="error">
        {accountsError}
      </StatusIndicator>
    );
  }

  const accountOptions: SelectProps.Option[] = availableAccounts.map(account => ({
    value: account.accountId,
    label: account.accountName 
      ? `${account.accountName} (${account.accountId})`
      : account.accountId,
    description: account.isCurrentAccount ? 'Default (Solution Deployed Here)' : 'Target Account'
  }));

  return (
    <Select
      selectedOption={selectedAccount}
      onChange={({ detail }) => setSelectedAccount(detail.selectedOption)}
      options={accountOptions}
      placeholder={placeholder}
      disabled={disabled || accountsLoading || availableAccounts.length === 0}
      loadingText="Loading accounts..."
      statusType={accountsLoading ? "loading" : undefined}
      expandToViewport={variant === 'compact'}
    />
  );
};