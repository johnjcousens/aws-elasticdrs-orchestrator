import React, { useState, useEffect } from 'react';
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
  Select,
} from '@cloudscape-design/components';
import type { SelectProps } from '@cloudscape-design/components';
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
  const [accounts, setAccounts] = useState<TargetAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingAccount, setEditingAccount] = useState<TargetAccount | null>(null);
  
  // Get account context for default account management
  const { defaultAccountId, setDefaultAccountId, applyDefaultAccount } = useAccount();
  
  // Form state
  const [formData, setFormData] = useState({
    accountId: '',
    accountName: '',
    stagingAccountId: '',
    stagingAccountName: '',
    crossAccountRoleArn: '',
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  const refreshAccounts = async () => {
    setLoading(true);
    setError(null);
    try {
      const fetchedAccounts = await apiClient.getTargetAccounts();
      setAccounts(fetchedAccounts);
      onAccountsChange?.(fetchedAccounts);
      
      // Auto-set default account if only one account exists and no default is set
      if (fetchedAccounts.length === 1 && !defaultAccountId) {
        const singleAccount = fetchedAccounts[0];
        setDefaultAccountId(singleAccount.accountId);
        // Apply the default account selection immediately
        applyDefaultAccount(singleAccount.accountId);
      }
    } catch (err: any) {
      console.error('Error fetching accounts:', err);
      setError(err.message || 'Failed to load target accounts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshAccounts();
  }, []);
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

  // Handle default account selection
  const handleDefaultAccountChange = ({ detail }: { detail: { selectedOption: SelectProps.Option | null } }) => {
    const accountId = detail.selectedOption?.value || null;
    setDefaultAccountId(accountId);
    
    // Apply the new default immediately if no account is currently selected
    if (accountId) {
      applyDefaultAccount(accountId);
      toast.success('Default account updated');
    } else {
      toast.success('Default account cleared');
    }
  };

  // Create options for default account selector
  const defaultAccountOptions: SelectProps.Option[] = [
    { value: '', label: 'No default account' },
    ...accounts.map(account => ({
      value: account.accountId,
      label: account.accountName 
        ? `${account.accountName} (${account.accountId})`
        : account.accountId,
    })),
  ];

  const selectedDefaultOption = defaultAccountId 
    ? defaultAccountOptions.find(opt => opt.value === defaultAccountId) || null
    : defaultAccountOptions[0];

  const getStatusIndicator = (status: string) => {
    switch (status) {
      case 'active':
        return <StatusIndicator type="success">Active</StatusIndicator>;
      case 'pending':
        return <StatusIndicator type="pending">Pending</StatusIndicator>;
      case 'error':
        return <StatusIndicator type="error">Error</StatusIndicator>;
      default:
        return <StatusIndicator type="info">Unknown</StatusIndicator>;
    }
  };

  const columnDefinitions = [
    {
      id: 'accountId',
      header: 'Account ID',
      cell: (item: TargetAccount) => (
        <Box>
          {item.accountId}
          {item.isCurrentAccount && (
            <Box variant="small" color="text-body-secondary">
              {' '}(Current)
            </Box>
          )}
        </Box>
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
        return (
          <Box>
            {item.stagingAccountId}
            {item.stagingAccountName && (
              <Box variant="small" color="text-body-secondary">
                {item.stagingAccountName}
              </Box>
            )}
          </Box>
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
      cell: (item: TargetAccount) => (
        <SpaceBetween direction="horizontal" size="xs">
          <Button
            variant="icon"
            iconName="edit"
            ariaLabel="Edit account"
            onClick={() => handleOpenModal(item)}
          />
          <Button
            variant="icon"
            iconName="refresh"
            ariaLabel="Validate account"
            onClick={() => handleValidate(item.accountId)}
          />
          <Button
            variant="icon"
            iconName="remove"
            ariaLabel="Remove account"
            onClick={() => handleDelete(item.accountId)}
          />
        </SpaceBetween>
      ),
      width: 120,
    },
  ];

  return (
    <SpaceBetween size="l">
      <TextContent>
        <h3>Target Account Management</h3>
        <p>
          Configure target accounts for DRS orchestration. Add accounts that contain DRS source servers you want to orchestrate.
        </p>
        <ul>
          <li>
            <strong>Target Account:</strong> AWS account containing DRS source servers to orchestrate
          </li>
          <li>
            <strong>Same Account:</strong> If target account is the same as this solution account, no cross-account role is needed
          </li>
          <li>
            <strong>Cross-Account Role:</strong> Required only for accessing different AWS accounts - leave empty for same account
          </li>
          <li>
            <strong>Staging Account:</strong> Optional trusted account for staging/testing operations
          </li>
        </ul>
      </TextContent>

      {error && (
        <Alert type="error" dismissible={false}>
          {error}
        </Alert>
      )}

      {/* Default Account Preference */}
      <Container
        header={
          <Header variant="h2">
            Default Account Preference
          </Header>
        }
      >
        <SpaceBetween size="m">
          <TextContent>
            <p>
              Set a preferred default account to make selection easier. For security, you must still 
              explicitly select an account each session - this preference just highlights your 
              preferred choice in the account selector dropdown.
            </p>
          </TextContent>
          
          <FormField
            label="Default Account Preference"
            description="Choose your preferred default account. Note: You will still need to explicitly select an account each session for security - this just makes selection easier by highlighting your preferred choice."
          >
            <Select
              selectedOption={selectedDefaultOption}
              onChange={handleDefaultAccountChange}
              options={defaultAccountOptions}
              placeholder="Select default account"
              disabled={loading || accounts.length === 0}
            />
          </FormField>
        </SpaceBetween>
      </Container>

      <Container
        header={
          <Header
            variant="h2"
            counter={`(${accounts.length})`}
            actions={
              <Button
                variant="primary"
                iconName="add-plus"
                onClick={() => handleOpenModal()}
              >
                Add Target Account
              </Button>
            }
          >
            Target Accounts
          </Header>
        }
      >
        <Table
          items={accounts}
          columnDefinitions={columnDefinitions}
          loading={loading}
          loadingText="Loading target accounts..."
          empty={
            <Box textAlign="center" color="inherit">
              <SpaceBetween size="m">
                <b>No target accounts configured</b>
                <p>Add target accounts to enable cross-account DRS orchestration.</p>
                <Button
                  variant="primary"
                  onClick={() => handleOpenModal()}
                >
                  Add Target Account
                </Button>
              </SpaceBetween>
            </Box>
          }
          sortingDisabled={true}
        />
      </Container>

      <Modal
        visible={modalVisible}
        onDismiss={handleCloseModal}
        header={editingAccount ? 'Edit Target Account' : 'Add Target Account'}
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button onClick={handleCloseModal}>Cancel</Button>
              <Button
                variant="primary"
                onClick={handleSave}
                loading={saving}
              >
                {editingAccount ? 'Update' : 'Add'}
              </Button>
            </SpaceBetween>
          </Box>
        }
        size="medium"
      >
        <SpaceBetween size="l">
          <FormField
            label="Account ID"
            description="12-digit AWS account ID"
            errorText={formErrors.accountId}
          >
            <Input
              value={formData.accountId}
              onChange={({ detail }) => setFormData(prev => ({ ...prev, accountId: detail.value }))}
              placeholder="123456789012"
              disabled={!!editingAccount}
            />
          </FormField>

          <FormField
            label="Account Name"
            description="Optional friendly name for the account"
            errorText={formErrors.accountName}
          >
            <Input
              value={formData.accountName}
              onChange={({ detail }) => setFormData(prev => ({ ...prev, accountName: detail.value }))}
              placeholder="Production Account"
            />
          </FormField>

          <FormField
            label="Staging Account ID"
            description="Optional staging account for testing operations"
            errorText={formErrors.stagingAccountId}
          >
            <Input
              value={formData.stagingAccountId}
              onChange={({ detail }) => setFormData(prev => ({ ...prev, stagingAccountId: detail.value }))}
              placeholder="123456789013"
            />
          </FormField>

          <FormField
            label="Staging Account Name"
            description="Optional friendly name for the staging account"
            errorText={formErrors.stagingAccountName}
          >
            <Input
              value={formData.stagingAccountName}
              onChange={({ detail }) => setFormData(prev => ({ ...prev, stagingAccountName: detail.value }))}
              placeholder="Staging Account"
            />
          </FormField>

          <FormField
            label="Cross-Account Role ARN"
            description="Required only for different AWS accounts. Leave empty if target account is the same as this solution account."
            errorText={formErrors.crossAccountRoleArn}
          >
            <Input
              value={formData.crossAccountRoleArn}
              onChange={({ detail }) => setFormData(prev => ({ ...prev, crossAccountRoleArn: detail.value }))}
              placeholder="arn:aws:iam::123456789012:role/DRSOrchestrationCrossAccountRole"
            />
          </FormField>
        </SpaceBetween>
      </Modal>
    </SpaceBetween>
  );
};

export default AccountManagementPanel;