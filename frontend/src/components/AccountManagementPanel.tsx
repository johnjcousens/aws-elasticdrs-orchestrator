import React, { useState, useCallback } from 'react';
import {
  Container,
  Header,
  SpaceBetween,
  Table,
  Button,
  Modal,
  FormField,
  Input,
  Box,
  StatusIndicator,
  Alert,
  TextContent,
} from '@cloudscape-design/components';
import toast from 'react-hot-toast';
import apiClient from '../services/api';
import { useAccount } from '../contexts/AccountContext';

export interface TargetAccount {
  accountId: string;
  accountName?: string;
  stagingAccountId?: string;
  stagingAccountName?: string;
  isCurrentAccount: boolean;
  status: 'active' | 'pending' | 'error';
  lastValidated?: string;
  crossAccountRoleArn?: string;
}

interface AccountManagementPanelProps {
  onAccountsChange?: (accounts: TargetAccount[]) => void;
}

const AccountManagementPanel: React.FC<AccountManagementPanelProps> = ({
  onAccountsChange,
}) => {
  const { availableAccounts: accounts, accountsLoading: loading, accountsError: error, refreshAccounts } = useAccount();
  const [modalVisible, setModalVisible] = useState(false);
  const [editingAccount, setEditingAccount] = useState<TargetAccount | null>(null);
  
  // Form state
  const [formData, setFormData] = useState({
    accountId: '',
    accountName: '',
    stagingAccountId: '',
    stagingAccountName: '',
    crossAccountRoleArn: '',
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);

  // Notify parent component when accounts change
  React.useEffect(() => {
    onAccountsChange?.(accounts);
  }, [accounts, onAccountsChange]);

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};
    
    if (!formData.accountId.trim()) {
      errors.accountId = 'Account ID is required';
    } else if (!/^\d{12}$/.test(formData.accountId.trim())) {
      errors.accountId = 'Account ID must be 12 digits';
    }
    
    if (formData.stagingAccountId && !/^\d{12}$/.test(formData.stagingAccountId.trim())) {
      errors.stagingAccountId = 'Staging Account ID must be 12 digits';
    }
    
    // Cross-account role validation: only validate format if provided
    if (formData.crossAccountRoleArn && formData.crossAccountRoleArn.trim() && !formData.crossAccountRoleArn.startsWith('arn:aws:iam::')) {
      errors.crossAccountRoleArn = 'Must be a valid IAM role ARN';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSave = async () => {
    if (!validateForm()) return;
    
    setSaving(true);
    try {
      const accountData: Partial<TargetAccount> = {
        accountId: formData.accountId.trim(),
        accountName: formData.accountName.trim() || undefined,
        stagingAccountId: formData.stagingAccountId.trim() || undefined,
        stagingAccountName: formData.stagingAccountName.trim() || undefined,
        crossAccountRoleArn: formData.crossAccountRoleArn.trim() || undefined,
      };

      if (editingAccount) {
        await apiClient.updateTargetAccount(editingAccount.accountId, accountData);
        toast.success('Target account updated successfully');
      } else {
        await apiClient.createTargetAccount(accountData);
        toast.success('Target account added successfully');
      }
      
      await refreshAccounts();
      handleCloseModal();
    } catch (err: any) {
      console.error('Error saving target account:', err);
      toast.error(err.message || 'Failed to save target account');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (accountId: string) => {
    if (!confirm('Are you sure you want to remove this target account?')) return;
    
    try {
      await apiClient.deleteTargetAccount(accountId);
      toast.success('Target account removed successfully');
      await refreshAccounts();
    } catch (err: any) {
      console.error('Error deleting target account:', err);
      toast.error(err.message || 'Failed to remove target account');
    }
  };

  const handleValidate = async (accountId: string) => {
    try {
      await apiClient.validateTargetAccount(accountId);
      toast.success('Account validation successful');
      await refreshAccounts();
    } catch (err: any) {
      console.error('Error validating target account:', err);
      toast.error(err.message || 'Account validation failed');
    }
  };

  const handleOpenModal = (account?: TargetAccount) => {
    setEditingAccount(account || null);
    setFormData({
      accountId: account?.accountId || '',
      accountName: account?.accountName || '',
      stagingAccountId: account?.stagingAccountId || '',
      stagingAccountName: account?.stagingAccountName || '',
      crossAccountRoleArn: account?.crossAccountRoleArn || '',
    });
    setFormErrors({});
    setModalVisible(true);
  };

  const handleCloseModal = () => {
    setModalVisible(false);
    setEditingAccount(null);
    setFormData({
      accountId: '',
      accountName: '',
      stagingAccountId: '',
      stagingAccountName: '',
      crossAccountRoleArn: '',
    });
    setFormErrors({});
  };

  const getStatusIndicator = (status: string) => {
    switch (status) {
      case 'active':
        return React.createElement(StatusIndicator, { type: 'success' }, 'Active');
      case 'pending':
        return React.createElement(StatusIndicator, { type: 'pending' }, 'Pending');
      case 'error':
        return React.createElement(StatusIndicator, { type: 'error' }, 'Error');
      default:
        return React.createElement(StatusIndicator, { type: 'info' }, 'Unknown');
    }
  };

  const columnDefinitions = [
    {
      id: 'accountId',
      header: 'Account ID',
      cell: (item: TargetAccount) => React.createElement(
        Box,
        {},
        item.accountId,
        item.isCurrentAccount && React.createElement(
          Box,
          { variant: 'small', color: 'text-body-secondary' },
          ' (Current)'
        )
      ),
      sortingField: 'accountId',
      width: 150,
    },
    {
      id: 'accountName',
      header: 'Account Name',
      cell: (item: TargetAccount) => item.accountName || '-',
      sortingField: 'accountName',
      width: 200,
    },
    {
      id: 'stagingAccount',
      header: 'Staging Account',
      cell: (item: TargetAccount) => {
        if (!item.stagingAccountId) return '-';
        return React.createElement(
          Box,
          {},
          item.stagingAccountId,
          item.stagingAccountName && React.createElement(
            Box,
            { variant: 'small', color: 'text-body-secondary' },
            item.stagingAccountName
          )
        );
      },
      width: 200,
    },
    {
      id: 'status',
      header: 'Status',
      cell: (item: TargetAccount) => getStatusIndicator(item.status),
      width: 120,
    },
    {
      id: 'lastValidated',
      header: 'Last Validated',
      cell: (item: TargetAccount) => {
        if (!item.lastValidated) return '-';
        return new Date(item.lastValidated).toLocaleDateString();
      },
      width: 150,
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: (item: TargetAccount) => React.createElement(
        SpaceBetween,
        { direction: 'horizontal', size: 'xs' },
        React.createElement(Button, {
          variant: 'icon',
          iconName: 'edit',
          ariaLabel: 'Edit account',
          onClick: () => handleOpenModal(item),
          disabled: item.isCurrentAccount,
        }),
        React.createElement(Button, {
          variant: 'icon',
          iconName: 'refresh',
          ariaLabel: 'Validate account',
          onClick: () => handleValidate(item.accountId),
        }),
        !item.isCurrentAccount && React.createElement(Button, {
          variant: 'icon',
          iconName: 'remove',
          ariaLabel: 'Remove account',
          onClick: () => handleDelete(item.accountId),
        })
      ),
      width: 120,
    },
  ];
  return React.createElement(
    SpaceBetween,
    { size: 'l' },
    React.createElement(
      TextContent,
      {},
      React.createElement('h3', {}, 'Target Account Management'),
      React.createElement(
        'p',
        {},
        'Configure target accounts for cross-account DRS orchestration. Add accounts that contain DRS source servers you want to orchestrate. If the current account has DRS, add it explicitly as a target account.'
      ),
      React.createElement(
        'ul',
        {},
        React.createElement(
          'li',
          {},
          React.createElement('strong', {}, 'Target Account:'),
          ' AWS account containing DRS source servers to orchestrate'
        ),
        React.createElement(
          'li',
          {},
          React.createElement('strong', {}, 'Staging Account:'),
          ' Optional trusted account for staging/testing operations'
        ),
        React.createElement(
          'li',
          {},
          React.createElement('strong', {}, 'Cross-Account Role:'),
          ' IAM role ARN for accessing the target account'
        )
      )
    ),
    error && React.createElement(
      Alert,
      {
        type: 'error',
        dismissible: false,
      },
      error
    ),
    React.createElement(
      Container,
      {
        header: React.createElement(
          Header,
          {
            variant: 'h2',
            counter: `(${accounts.length})`,
            actions: React.createElement(
              Button,
              {
                variant: 'primary',
                iconName: 'add-plus',
                onClick: () => handleOpenModal(),
              },
              'Add Target Account'
            ),
          },
          'Target Accounts'
        ),
      },
      React.createElement(Table, {
        items: accounts,
        columnDefinitions: columnDefinitions,
        loading: loading,
        loadingText: 'Loading target accounts...',
        empty: React.createElement(
          Box,
          { textAlign: 'center', color: 'inherit' },
          React.createElement(
            SpaceBetween,
            { size: 'm' },
            React.createElement('b', {}, 'No target accounts configured'),
            React.createElement('p', {}, 'Add target accounts to enable cross-account DRS orchestration.'),
            React.createElement(
              Button,
              {
                variant: 'primary',
                onClick: () => handleOpenModal(),
              },
              'Add Target Account'
            )
          )
        ),
        sortingDisabled: true,
      })
    ),
    React.createElement(
      Modal,
      {
        visible: modalVisible,
        onDismiss: handleCloseModal,
        header: editingAccount ? 'Edit Target Account' : 'Add Target Account',
        footer: React.createElement(
          Box,
          { float: 'right' },
          React.createElement(
            SpaceBetween,
            { direction: 'horizontal', size: 'xs' },
            React.createElement(Button, { onClick: handleCloseModal }, 'Cancel'),
            React.createElement(
              Button,
              {
                variant: 'primary',
                onClick: handleSave,
                loading: saving,
              },
              editingAccount ? 'Update' : 'Add'
            )
          )
        ),
        size: 'medium',
      },
      React.createElement(
        SpaceBetween,
        { size: 'l' },
        React.createElement(
          FormField,
          {
            label: 'Account ID',
            description: '12-digit AWS account ID',
            errorText: formErrors.accountId,
          },
          React.createElement(Input, {
            value: formData.accountId,
            onChange: ({ detail }) => setFormData(prev => ({ ...prev, accountId: detail.value })),
            placeholder: '123456789012',
            disabled: !!editingAccount,
          })
        ),
        React.createElement(
          FormField,
          {
            label: 'Account Name',
            description: 'Optional friendly name for the account',
            errorText: formErrors.accountName,
          },
          React.createElement(Input, {
            value: formData.accountName,
            onChange: ({ detail }) => setFormData(prev => ({ ...prev, accountName: detail.value })),
            placeholder: 'Production Account',
          })
        ),
        React.createElement(
          FormField,
          {
            label: 'Staging Account ID',
            description: 'Optional staging account for testing operations',
            errorText: formErrors.stagingAccountId,
          },
          React.createElement(Input, {
            value: formData.stagingAccountId,
            onChange: ({ detail }) => setFormData(prev => ({ ...prev, stagingAccountId: detail.value })),
            placeholder: '123456789013',
          })
        ),
        React.createElement(
          FormField,
          {
            label: 'Staging Account Name',
            description: 'Optional friendly name for the staging account',
            errorText: formErrors.stagingAccountName,
          },
          React.createElement(Input, {
            value: formData.stagingAccountName,
            onChange: ({ detail }) => setFormData(prev => ({ ...prev, stagingAccountName: detail.value })),
            placeholder: 'Staging Account',
          })
        ),
        React.createElement(
          FormField,
          {
            label: 'Cross-Account Role ARN',
            description: 'IAM role ARN for accessing the target account (leave empty for current account)',
            errorText: formErrors.crossAccountRoleArn,
          },
          React.createElement(Input, {
            value: formData.crossAccountRoleArn,
            onChange: ({ detail }) => setFormData(prev => ({ ...prev, crossAccountRoleArn: detail.value })),
            placeholder: 'arn:aws:iam::123456789012:role/DRSOrchestrationCrossAccountRole',
          })
        )
      )
    )
  );
};

export default AccountManagementPanel;