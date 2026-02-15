/**
 * TargetAccountSettingsModal Component
 *
 * Read-only modal dialog for viewing target account configuration and
 * connected staging accounts. Automatically discovers staging accounts
 * from DRS extended source servers.
 *
 * FEATURES:
 * - Display target account details (read-only)
 * - Auto-discover staging accounts from DRS
 * - Show connected staging accounts in collapsible section
 * - Display staging account status and server counts
 * - Auto-refresh when modal opens to show latest data
 *
 * REQUIREMENTS:
 * - View-only modal for target account information
 * - Automatic staging account discovery
 * - Collapsible staging accounts list
 * - No editing or removal capabilities
 */

import React, { useEffect, useState } from "react";
import {
  Modal,
  Box,
  SpaceBetween,
  Button,
  ColumnLayout,
  Container,
  Header,
  StatusIndicator,
  ExpandableSection,
  Spinner,
  Alert,
  Input,
} from "@cloudscape-design/components";
import apiClient from "../services/api";
import { removeStagingAccount } from "../services/staging-accounts-api";
import { AddStagingAccountModal } from "./AddStagingAccountModal";
import type {
  TargetAccountSettingsModalProps,
} from "../types/staging-accounts";


/**
 * TargetAccountSettingsModal Component
 *
 * Read-only view of target account and connected staging accounts.
 * Fetches fresh data when modal opens to ensure accuracy.
 */
export const TargetAccountSettingsModal: React.FC<
  TargetAccountSettingsModalProps
> = ({ targetAccount, visible, onDismiss }) => {
  const [freshAccountData, setFreshAccountData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAddStagingModal, setShowAddStagingModal] = useState(false);
  const [removingAccountId, setRemovingAccountId] = useState<string | null>(null);
  const [editingAccountName, setEditingAccountName] = useState(false);
  const [editedAccountName, setEditedAccountName] = useState("");
  const [savingAccountName, setSavingAccountName] = useState(false);

  // Handle edit account name
  const handleStartEditAccountName = () => {
    setEditedAccountName(displayAccount.accountName || "");
    setEditingAccountName(true);
  };

  const handleCancelEditAccountName = () => {
    setEditingAccountName(false);
    setEditedAccountName("");
  };

  const handleSaveAccountName = async () => {
    setSavingAccountName(true);
    
    try {
      await apiClient.updateTargetAccount(displayAccount.accountId, {
        accountName: editedAccountName,
      });
      
      // Refresh account data after updating
      const data = await apiClient.getTargetAccount(displayAccount.accountId);
      setFreshAccountData(data);
      setEditingAccountName(false);
    } catch (err) {
      console.error('Error updating account name:', err);
      setError(`Failed to update account name: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setSavingAccountName(false);
    }
  };

  // Handle remove staging account
  const handleRemoveStagingAccount = async (stagingAccountId: string) => {
    if (!confirm(`Are you sure you want to remove staging account ${stagingAccountId}?`)) {
      return;
    }

    setRemovingAccountId(stagingAccountId);
    
    try {
      await removeStagingAccount(displayAccount.accountId, stagingAccountId);
      
      // Refresh account data after removing
      const data = await apiClient.getTargetAccount(displayAccount.accountId);
      setFreshAccountData(data);
    } catch (err) {
      console.error('Error removing staging account:', err);
      setError(`Failed to remove staging account: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setRemovingAccountId(null);
    }
  };

  // Fetch fresh account data when modal opens
  useEffect(() => {
    if (visible && targetAccount.accountId) {
      setLoading(true);
      setError(null);
      
      apiClient.getTargetAccount(targetAccount.accountId)
        .then((data) => {
          setFreshAccountData(data);
        })
        .catch((err) => {
          console.error('Error fetching fresh account data:', err);
          setError('Failed to load latest account data');
          // Fall back to prop data
          setFreshAccountData(targetAccount);
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, [visible, targetAccount.accountId]);

  // Use fresh data if available, otherwise fall back to prop
  const displayAccount = freshAccountData || targetAccount;
  
  // Get staging accounts from account data
  const stagingAccounts = displayAccount.stagingAccounts || [];
  const isLoadingData = loading && !freshAccountData;

  return (
    <Modal
      visible={visible}
      onDismiss={onDismiss}
      header="Target Account Details"
      size="medium"
      footer={
        <Box float="right">
          <Button onClick={onDismiss} variant="primary">
            Close
          </Button>
        </Box>
      }
    >
      <SpaceBetween size="l">
        {error && (
          <Alert type="error" dismissible onDismiss={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Target Account Information */}
        <Container header={<Header variant="h3">Account Information</Header>}>
          {isLoadingData ? (
            <Box textAlign="center" padding="l">
              <Spinner size="large" />
              <Box variant="p" color="text-body-secondary" padding={{ top: "s" }}>
                Loading account details...
              </Box>
            </Box>
          ) : (
            <ColumnLayout columns={2} variant="text-grid">
              <div>
                <Box variant="awsui-key-label">Account ID</Box>
                <div>{displayAccount.accountId}</div>
              </div>
              <div>
                <Box variant="awsui-key-label">Account Name</Box>
                {editingAccountName ? (
                  <SpaceBetween direction="horizontal" size="xs">
                    <Input
                      value={editedAccountName}
                      onChange={({ detail }) => setEditedAccountName(detail.value)}
                      placeholder="Enter account name"
                      disabled={savingAccountName}
                    />
                    <Button
                      onClick={handleSaveAccountName}
                      variant="primary"
                      loading={savingAccountName}
                      disabled={savingAccountName}
                    >
                      Save
                    </Button>
                    <Button
                      onClick={handleCancelEditAccountName}
                      disabled={savingAccountName}
                    >
                      Cancel
                    </Button>
                  </SpaceBetween>
                ) : (
                  <SpaceBetween direction="horizontal" size="xs">
                    <div>{displayAccount.accountName || "—"}</div>
                    <Button
                      onClick={handleStartEditAccountName}
                      iconName="edit"
                      variant="inline-icon"
                      ariaLabel="Edit account name"
                    />
                  </SpaceBetween>
                )}
              </div>
              {displayAccount.roleArn && (
                <div>
                  <Box variant="awsui-key-label">Role ARN</Box>
                  <div>{displayAccount.roleArn}</div>
                </div>
              )}
              {displayAccount.externalId && (
                <div>
                  <Box variant="awsui-key-label">External ID</Box>
                  <div>{displayAccount.externalId}</div>
                </div>
              )}
              {displayAccount.status && (
                <div>
                  <Box variant="awsui-key-label">Status</Box>
                  <StatusIndicator
                    type={displayAccount.status === "active" ? "success" : "info"}
                  >
                    {displayAccount.status.toUpperCase()}
                  </StatusIndicator>
                </div>
              )}
            </ColumnLayout>
          )}
        </Container>

        {/* Connected Staging Accounts */}
        <ExpandableSection
          headerText={`Connected Staging Accounts (${stagingAccounts.length})`}
          variant="container"
          defaultExpanded={stagingAccounts.length > 0}
          headerActions={
            <Button
              onClick={() => setShowAddStagingModal(true)}
              iconName="add-plus"
            >
              Add Staging Account
            </Button>
          }
        >
          {isLoadingData ? (
            <Box textAlign="center" padding="l">
              <Spinner size="large" />
              <Box variant="p" color="text-body-secondary" padding={{ top: "s" }}>
                Loading staging accounts...
              </Box>
            </Box>
          ) : stagingAccounts.length === 0 ? (
            <Box textAlign="center" color="inherit" padding="l">
              No staging accounts connected
            </Box>
          ) : (
            <SpaceBetween size="m">
              {stagingAccounts.map((stagingAccount: any) => (
                <Container key={stagingAccount.accountId}>
                  <SpaceBetween size="s">
                    <ColumnLayout columns={2} variant="text-grid">
                      <div>
                        <Box variant="awsui-key-label">Account Name</Box>
                        <div>{stagingAccount.accountName}</div>
                      </div>
                      <div>
                        <Box variant="awsui-key-label">Account ID</Box>
                        <div>{stagingAccount.accountId}</div>
                      </div>
                      <div>
                        <Box variant="awsui-key-label">Role ARN</Box>
                        <div style={{ fontSize: '12px', wordBreak: 'break-all' }}>
                          {stagingAccount.roleArn}
                        </div>
                      </div>
                      <div>
                        <Box variant="awsui-key-label">Status</Box>
                        <StatusIndicator type={!stagingAccount.status || stagingAccount.status === 'connected' ? 'success' : 'error'}>
                          {stagingAccount.status || 'connected'}
                        </StatusIndicator>
                      </div>
                    </ColumnLayout>
                    <Box float="right">
                      <Button
                        onClick={() => handleRemoveStagingAccount(stagingAccount.accountId)}
                        iconName="remove"
                        variant="normal"
                        loading={removingAccountId === stagingAccount.accountId}
                        disabled={removingAccountId !== null}
                      >
                        Remove
                      </Button>
                    </Box>
                  </SpaceBetween>
                </Container>
              ))}
            </SpaceBetween>
          )}
        </ExpandableSection>
      </SpaceBetween>

      {/* Add Staging Account Modal */}
      <AddStagingAccountModal
        visible={showAddStagingModal}
        onDismiss={() => setShowAddStagingModal(false)}
        targetAccountId={displayAccount.accountId}
        onAdd={(stagingAccount) => {
          // Refresh account data after adding
          setShowAddStagingModal(false);
          setLoading(true);
          apiClient.getTargetAccount(displayAccount.accountId)
            .then((data) => {
              setFreshAccountData(data);
            })
            .catch((err) => {
              console.error('Error refreshing account data:', err);
            })
            .finally(() => {
              setLoading(false);
            });
        }}
      />
    </Modal>
  );
};

export default TargetAccountSettingsModal;
