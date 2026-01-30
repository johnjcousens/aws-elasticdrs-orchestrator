/**
 * Account Selector Component
 * 
 * Provides account selection dropdown in the top navigation.
 * Shows current account or prompts user to select one.
 */

import React from 'react';
import {
  Select,
  Box,
  StatusIndicator,
} from '@cloudscape-design/components';
import type { SelectProps } from '@cloudscape-design/components';
import { useAccount } from '../contexts/AccountContext';

export const AccountSelector: React.FC = () => {
  const {
    selectedAccount,
    setSelectedAccount,
    availableAccounts,
    accountsLoading,
    accountsError,
    hasSelectedAccount,
  } = useAccount();

  // Convert accounts to select options (defensive check for non-array responses)
  const accountOptions: SelectProps.Option[] = Array.isArray(availableAccounts) 
    ? availableAccounts.map(account => ({
        value: account.accountId,
        label: account.accountName 
          ? `${account.accountName} (${account.accountId})`
          : account.accountId,
        description: account.isCurrentAccount ? 'Current account' : undefined,
      }))
    : [];

  const handleSelectionChange = ({ detail }: { detail: { selectedOption: SelectProps.Option } }) => {
    console.log('[AccountSelector] Account selection changed:', detail.selectedOption);
    console.log('[AccountSelector] Previous account:', selectedAccount);
    setSelectedAccount(detail.selectedOption);
  };

  if (accountsLoading) {
    return (
      <Box padding={{ horizontal: 's' }}>
        <StatusIndicator type="loading">Loading accounts...</StatusIndicator>
      </Box>
    );
  }

  if (accountsError) {
    return (
      <Box padding={{ horizontal: 's' }}>
        <StatusIndicator type="error">Account error</StatusIndicator>
      </Box>
    );
  }

  if (!Array.isArray(availableAccounts) || availableAccounts.length === 0) {
    return (
      <Box padding={{ horizontal: 's' }}>
        <StatusIndicator type="warning">No accounts</StatusIndicator>
      </Box>
    );
  }

  // Always show the dropdown, even for single accounts
  // This ensures users can see which account is selected and change it if needed

  return (
    <div style={{ minWidth: '300px' }}>
      <Select
        selectedOption={selectedAccount}
        onChange={handleSelectionChange}
        options={accountOptions}
        placeholder="Select target account"
        statusType={hasSelectedAccount ? "finished" : "pending"}
        ariaLabel="Select target account"
        expandToViewport={true}
        disabled={false}
        filteringType="auto"
      />
    </div>
  );
};