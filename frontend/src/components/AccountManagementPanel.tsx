import React, { useState, useEffect, useCallback } from 'react';
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
  Spinner,
} from '@cloudscape-design/components';
import type { SelectProps } from '@cloudscape-design/components';
import toast from 'react-hot-toast';
import apiClient from '../services/api';
import { useAccount } from '../contexts/AccountContext';
import { PermissionAwareButton } from './PermissionAware';
import { DRSPermission } from '../types/permissions';

export interface TargetAccount {
  accountId: string;
  accountName?: string;
  isCurrentAccount: boolean;
  status: 'active' | 'pending' | 'error' | 'ACTIVE' | 'INACTIVE' | 'ERROR';
  lastValidated?: string;
  crossAccountRoleArn?: string;
}

interface AccountManagementPanelProps {
  onAccountsChange?: (accounts: TargetAccount[]) => void;
  showWizardMode?: boolean; // New prop to enable wizard-style UI for first-time setup
}

const AccountManagementPanel: React.FC<AccountManagementPanelProps> = ({
  onAccountsChange,
  showWizardMode = false,
}) => {
  const [accounts, setAccounts] = useState<TargetAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingAccount, setEditingAccount] = useState<TargetAccount | null>(null);
  
  // Current account info for wizard
  const [currentAccount, setCurrentAccount] = useState<{
    accountId: string;
    accountName: string;
    isCurrentAccount: boolean;
  } | null>(null);
  const [loadingCurrentAccount, setLoadingCurrentAccount] = useState(false);
  
  // Get account context for default account management
  const { defaultAccountId, setDefaultAccountId, applyDefaultAccount } = useAccount();
  
  // Form state
  const [formData, setFormData] = useState({
    accountId: '',
    accountName: '',
    crossAccountRoleArn: '',
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  
  // Auto-populate cross-account role ARN based on account ID
  // Pattern: arn:aws:iam::{AccountId}:role/DRSOrchestrationRole-{Environment}
  const autoGenerateRoleArn = useCallback((accountId: string): string => {
    if (!accountId || !/^\d{12}$/.test(accountId.trim())) {
      return '';
    }
    // Get environment from window config or default to 'dev'
    const environment = (window as any).AWS_CONFIG?.environment || 'dev';
    return `arn:aws:iam::${accountId.trim()}:role/DRSOrchestrationRole-${environment}`;
  }, []);

  // Fetch current account info for wizard
  const fetchCurrentAccount = useCallback(async () => {
    if (!showWizardMode) return;
    
    setLoadingCurrentAccount(true);
    try {
      const currentAccountInfo = await apiClient.getCurrentAccount();
      setCurrentAccount(currentAccountInfo);
    } catch (err) {
      console.error('Error fetching current account:', err);
      // Don't show error toast for this - it's not critical
    } finally {
      setLoadingCurrentAccount(false);
    }
  }, [showWizardMode]);

  const refreshAccounts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const fetchedAccounts = await apiClient.getTargetAccounts();
      // Defensive check: ensure fetchedAccounts is an array
      const accountsArray = Array.isArray(fetchedAccounts) ? fetchedAccounts : [];
      setAccounts(accountsArray);
      onAccountsChange?.(accountsArray);
      
      // Auto-set default account if only one account exists and no default is set
      if (accountsArray.length === 1 && !defaultAccountId) {
        const singleAccount = accountsArray[0];
        setDefaultAccountId(singleAccount.accountId);
        // Don't apply the default account selection here - let the context handle it
      }
    } catch (err) {
      console.error('Error fetching accounts:', err);
      setError(err instanceof Error ? err.message : 'Failed to load target accounts');
    } finally {
      setLoading(false);
    }
  }, [defaultAccountId, onAccountsChange, setDefaultAccountId]);

  useEffect(() => {
    refreshAccounts();
    fetchCurrentAccount();
  }, [showWizardMode, refreshAccounts, fetchCurrentAccount]);

  // Notify parent component when accounts change
  React.useEffect(() => {
    onAccountsChange?.(accounts);
  }, [accounts, onAccountsChange]);

  // Quick add current account function for wizard
  const handleQuickAddCurrentAccount = async () => {
    if (!currentAccount) return;
    
    setSaving(true);
    try {
      const accountData = {
        accountId: currentAccount.accountId,
        accountName: currentAccount.accountName,
        // No cross-account role needed for same account
      };

      await apiClient.createTargetAccount({
        accountId: accountData.accountId,
        accountName: accountData.accountName,
        roleArn: '',  // No cross-account role needed for same account
      });
      toast.success(`Current account ${currentAccount.accountName} (${currentAccount.accountId}) added successfully and set as default`);
      
      await refreshAccounts();
    } catch (err) {
      console.error('Error adding current account:', err);
      toast.error(err instanceof Error ? err.message : 'Failed to add current account');
    } finally {
      setSaving(false);
    }
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};
    
    if (!formData.accountId.trim()) {
      errors.accountId = 'Account ID is required';
    } else if (!/^\d{12}$/.test(formData.accountId.trim())) {
      errors.accountId = 'Account ID must be 12 digits';
    }
    
    // Enhanced wizard validation for cross-account role
    if (showWizardMode && currentAccount) {
      const isSameAccount = formData.accountId.trim() === currentAccount.accountId;
      
      if (isSameAccount && formData.crossAccountRoleArn.trim()) {
        errors.crossAccountRoleArn = 'Cross-account role is not needed when adding the same account where this solution is deployed. Please leave this field empty.';
      } else if (!isSameAccount && !formData.crossAccountRoleArn.trim()) {
        errors.crossAccountRoleArn = `This account (${formData.accountId}) is different from where the solution is deployed (${currentAccount.accountId}). Please provide a cross-account IAM role ARN with DRS permissions.`;
      } else if (formData.crossAccountRoleArn.trim() && !formData.crossAccountRoleArn.startsWith('arn:aws:iam::')) {
        errors.crossAccountRoleArn = 'Must be a valid IAM role ARN (arn:aws:iam::account:role/role-name)';
      }
    } else {
      // Standard validation for non-wizard mode
      if (formData.crossAccountRoleArn && formData.crossAccountRoleArn.trim() && !formData.crossAccountRoleArn.startsWith('arn:aws:iam::')) {
        errors.crossAccountRoleArn = 'Must be a valid IAM role ARN';
      }
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSave = async () => {
    if (!validateForm()) return;
    
    setSaving(true);
    try {
      const accountData = {
        accountId: formData.accountId.trim(),
        accountName: formData.accountName.trim(),
        crossAccountRoleArn: formData.crossAccountRoleArn.trim(),
      };

      if (editingAccount) {
        await apiClient.updateTargetAccount(editingAccount.accountId, {
          accountName: accountData.accountName,
          roleArn: accountData.crossAccountRoleArn,
        });
        toast.success('Target account updated successfully');
      } else {
        await apiClient.createTargetAccount({
          accountId: accountData.accountId,
          accountName: accountData.accountName,
          roleArn: accountData.crossAccountRoleArn,
        });
        toast.success('Target account added successfully');
      }
      
      await refreshAccounts();
      handleCloseModal();
    } catch (err) {
      console.error('Error saving target account:', err);
      toast.error(err instanceof Error ? err.message : 'Failed to save target account');
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
    } catch (err) {
      console.error('Error deleting target account:', err);
      toast.error(err instanceof Error ? err.message : 'Failed to remove target account');
    }
  };

  const handleValidate = async (accountId: string) => {
    try {
      await apiClient.validateTargetAccount(accountId);
      toast.success('Account validation successful');
      await refreshAccounts();
    } catch (err) {
      console.error('Error validating target account:', err);
      toast.error(err instanceof Error ? err.message : 'Account validation failed');
    }
  };

  const handleOpenModal = (account?: TargetAccount) => {
    setEditingAccount(account || null);
    const accountId = account?.accountId || '';
    const roleArn = account?.crossAccountRoleArn || (accountId ? autoGenerateRoleArn(accountId) : '');
    
    setFormData({
      accountId,
      accountName: account?.accountName || '',
      crossAccountRoleArn: roleArn,
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
      crossAccountRoleArn: '',
    });
    setFormErrors({});
  };

  // Handle default account selection
  const handleDefaultAccountChange = ({ detail }: { detail: { selectedOption: SelectProps.Option | null } }) => {
    const accountId = detail.selectedOption?.value || null;
    setDefaultAccountId(accountId);
    
    // Just save the preference - don't force account selection
    // The user can manually select the account from the dropdown
    if (accountId) {
      toast.success('Default account preference saved');
    } else {
      toast.success('Default account preference cleared');
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
        try {
          const date = new Date(item.lastValidated);
          // Check if date is valid
          if (isNaN(date.getTime())) return '-';
          return date.toLocaleString();
        } catch (e) {
          return '-';
        }
      },
      width: 150,
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: (item: TargetAccount) => (
        <SpaceBetween direction="horizontal" size="xs">
          <PermissionAwareButton
            variant="icon"
            iconName="edit"
            ariaLabel="Edit account"
            onClick={() => handleOpenModal(item)}
            requiredPermission={DRSPermission.MODIFY_ACCOUNTS}
            fallbackTooltip="Requires account modification permission"
          />
          <Button
            variant="icon"
            iconName="refresh"
            ariaLabel="Validate account access (available to all users)"
            onClick={() => handleValidate(item.accountId)}
          />
          <PermissionAwareButton
            variant="icon"
            iconName="remove"
            ariaLabel="Remove account"
            onClick={() => handleDelete(item.accountId)}
            requiredPermission={DRSPermission.DELETE_ACCOUNTS}
            fallbackTooltip="Requires account deletion permission"
          />
        </SpaceBetween>
      ),
      width: 120,
    },
  ];

  return (
    <SpaceBetween size="l">
      {showWizardMode && (
        <TextContent>
          <h3>Account Setup Wizard</h3>
          <p>
            Configure target accounts for DRS orchestration. Add accounts that contain DRS source servers you want to orchestrate.
          </p>
        </TextContent>
      )}

      {!showWizardMode && (
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
      )}

      {error && (
        <Alert type="error" dismissible={false}>
          {error}
        </Alert>
      )}

      {/* Quick Add Current Account - Wizard Mode Only */}
      {showWizardMode && accounts.length === 0 && (
        <Container
          header={
            <Header variant="h2">
              Quick Setup - Add Current Account
            </Header>
          }
        >
          <SpaceBetween size="m">
            {loadingCurrentAccount ? (
              <Box textAlign="center" padding="l">
                <Spinner size="normal" />
                <Box variant="p" color="text-body-secondary" margin={{ top: 's' }}>
                  Loading current account information...
                </Box>
              </Box>
            ) : currentAccount ? (
              <>
                <Alert
                  type="info"
                  header="Recommended: Add Current Account"
                >
                  <SpaceBetween size="s">
                    <Box>
                      This solution is deployed in account <strong>{currentAccount.accountName} ({currentAccount.accountId})</strong>.
                    </Box>
                    <Box>
                      If your DRS source servers are in this same account, you can add it quickly with one click. 
                      No cross-account IAM role configuration needed.
                    </Box>
                  </SpaceBetween>
                </Alert>
                
                <Box>
                  <PermissionAwareButton
                    variant="primary"
                    iconName="add-plus"
                    onClick={handleQuickAddCurrentAccount}
                    loading={saving}
                    requiredPermission={DRSPermission.REGISTER_ACCOUNTS}
                    fallbackTooltip="Requires account registration permission"
                  >
                    Add Current Account ({currentAccount.accountId})
                  </PermissionAwareButton>
                </Box>
                
                <Box variant="p" color="text-body-secondary">
                  Or use "Add Target Account" below to add a different account or configure advanced options.
                </Box>
              </>
            ) : (
              <Alert type="warning">
                Unable to detect current account information. Please use "Add Target Account" below to configure manually.
              </Alert>
            )}
          </SpaceBetween>
        </Container>
      )}

      {/* Default Account Preference - Only show when not in wizard mode */}
      {!showWizardMode && (
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
      )}

      <Container
        header={
          <Header
            variant="h2"
            counter={`(${accounts.length})`}
            actions={
              <PermissionAwareButton
                variant="primary"
                iconName="add-plus"
                onClick={() => handleOpenModal()}
                requiredPermission={DRSPermission.REGISTER_ACCOUNTS}
                fallbackTooltip="Requires account registration permission"
              >
                {showWizardMode ? 'Add Target Account' : 'Add Target Account'}
              </PermissionAwareButton>
            }
          >
            {showWizardMode ? 'Target Accounts' : 'Target Accounts'}
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
                <b>{showWizardMode ? 'No target accounts configured yet' : 'No target accounts configured'}</b>
                <p>
                  {showWizardMode 
                    ? 'Add your first target account to get started with DRS orchestration.'
                    : 'Add target accounts to enable cross-account DRS orchestration.'
                  }
                </p>
                <PermissionAwareButton
                  variant="primary"
                  onClick={() => handleOpenModal()}
                  requiredPermission={DRSPermission.REGISTER_ACCOUNTS}
                  fallbackTooltip="Requires account registration permission"
                >
                  Add Target Account
                </PermissionAwareButton>
              </SpaceBetween>
            </Box>
          }
          sortingDisabled={true}
        />
      </Container>

      <Modal
        visible={modalVisible}
        onDismiss={handleCloseModal}
        header={editingAccount ? 'Edit Target Account' : (showWizardMode ? 'Add Target Account - Setup Wizard' : 'Add Target Account')}
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button onClick={handleCloseModal}>Cancel</Button>
              <PermissionAwareButton
                variant="primary"
                onClick={handleSave}
                loading={saving}
                requiredPermission={editingAccount ? DRSPermission.MODIFY_ACCOUNTS : DRSPermission.REGISTER_ACCOUNTS}
                fallbackTooltip={editingAccount ? "Requires account modification permission" : "Requires account registration permission"}
              >
                {editingAccount ? 'Update' : 'Add'}
              </PermissionAwareButton>
            </SpaceBetween>
          </Box>
        }
        size="medium"
      >
        <SpaceBetween size="l">
          {showWizardMode && !editingAccount && currentAccount && (
            <Alert
              type="info"
              header="Account Setup Guidance"
            >
              <SpaceBetween size="s">
                <Box>
                  <strong>This solution is deployed in:</strong> {currentAccount.accountName} ({currentAccount.accountId})
                </Box>
                <Box>
                  <strong>Same Account:</strong> If you enter {currentAccount.accountId}, leave the cross-account role field empty.
                </Box>
                <Box>
                  <strong>Different Account:</strong> If you enter a different account ID, you must provide a cross-account IAM role ARN.
                </Box>
              </SpaceBetween>
            </Alert>
          )}

          <FormField
            label="Account ID"
            description="12-digit AWS account ID"
            errorText={formErrors.accountId}
          >
            <Input
              value={formData.accountId}
              onChange={({ detail }: { detail: { value: string } }) => {
                const newAccountId = detail.value;
                setFormData(prev => {
                  // Auto-populate role ARN if account ID is valid and different from current account
                  const isSameAccount = currentAccount && newAccountId.trim() === currentAccount.accountId;
                  const newRoleArn = isSameAccount ? '' : autoGenerateRoleArn(newAccountId);
                  
                  return {
                    ...prev,
                    accountId: newAccountId,
                    crossAccountRoleArn: newRoleArn,
                  };
                });
              }}
              placeholder={showWizardMode && currentAccount ? `e.g., ${currentAccount.accountId} (current) or 123456789012` : "123456789012"}
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
              onChange={({ detail }: { detail: { value: string } }) => setFormData(prev => ({ ...prev, accountName: detail.value }))}
              placeholder="Production Account"
            />
          </FormField>

          <FormField
            label="Cross-Account Role ARN"
            description={
              showWizardMode && currentAccount
                ? `Auto-populated based on account ID. Pattern: arn:aws:iam::{AccountId}:role/DRSOrchestrationRole-{Environment}. Leave empty if target account is ${currentAccount.accountId} (same as solution account).`
                : "Auto-populated based on account ID. Pattern: arn:aws:iam::{AccountId}:role/DRSOrchestrationRole-{Environment}. Leave empty if target account is the same as this solution account."
            }
            errorText={formErrors.crossAccountRoleArn}
            info={
              formData.crossAccountRoleArn && formData.accountId && currentAccount && formData.accountId !== currentAccount.accountId
                ? "Auto-generated based on standard role naming convention. You can edit this if your role has a different name."
                : undefined
            }
          >
            <Input
              value={formData.crossAccountRoleArn}
              onChange={({ detail }: { detail: { value: string } }) => setFormData(prev => ({ ...prev, crossAccountRoleArn: detail.value }))}
              placeholder={
                formData.accountId && !/^\d{12}$/.test(formData.accountId.trim())
                  ? "Enter a valid 12-digit account ID first"
                  : formData.accountId && currentAccount && formData.accountId === currentAccount.accountId
                  ? "Not needed for same account"
                  : "Will auto-populate when you enter account ID"
              }
            />
          </FormField>
        </SpaceBetween>
      </Modal>
    </SpaceBetween>
  );
};

export default AccountManagementPanel;