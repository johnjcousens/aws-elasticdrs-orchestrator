/**
 * TargetAccountSettingsModal Component
 *
 * Modal dialog for editing target account configuration including staging
 * accounts management. Provides UI for viewing, adding, and removing staging
 * accounts associated with a target account.
 *
 * FEATURES:
 * - Display target account details
 * - List staging accounts with status and server counts
 * - Add new staging accounts via nested modal
 * - Remove staging accounts with confirmation
 * - Warning for removing accounts with active servers
 *
 * REQUIREMENTS VALIDATED:
 * - 1.1: Display list of staging accounts with status and server counts
 * - 1.2: Open add staging account modal
 * - 1.6: Update staging accounts list after adding
 * - 2.1: Show confirmation dialog before removal
 * - 2.2: Delete staging account configuration
 * - 2.3: Update capacity dashboard after removal
 * - 2.4: Display warning for accounts with active servers
 */

import React, { useState } from "react";
import {
  Modal,
  Box,
  SpaceBetween,
  Button,
  FormField,
  Input,
  Alert,
  Table,
  Header,
  StatusIndicator,
  Badge,
} from "@cloudscape-design/components";
import type {
  TargetAccountSettingsModalProps,
  TargetAccountSettingsModalState,
  TargetAccount,
  StagingAccount,
} from "../types/staging-accounts";
import { AddStagingAccountModal } from "./AddStagingAccountModal";

/**
 * Get status indicator type for staging account status
 */
const getStatusType = (
  status?: "connected" | "error" | "validating"
): "success" | "error" | "loading" | "info" => {
  switch (status) {
    case "connected":
      return "success";
    case "error":
      return "error";
    case "validating":
      return "loading";
    default:
      return "info";
  }
};

/**
 * Get status label for staging account status
 */
const getStatusLabel = (status?: "connected" | "error" | "validating"): string => {
  switch (status) {
    case "connected":
      return "Connected";
    case "error":
      return "Error";
    case "validating":
      return "Validating";
    default:
      return "Unknown";
  }
};

/**
 * TargetAccountSettingsModal Component
 *
 * Modal for editing target account configuration and managing staging accounts.
 */
export const TargetAccountSettingsModal: React.FC<
  TargetAccountSettingsModalProps
> = ({ targetAccount, visible, onDismiss, onSave }) => {
  const [state, setState] = useState<TargetAccountSettingsModalState>({
    formData: { ...targetAccount },
    showAddStaging: false,
    saving: false,
    error: null,
    removingAccount: null,
  });

  /**
   * Handle form field change
   */
  const handleFieldChange = (field: keyof TargetAccount, value: string) => {
    setState((prev) => ({
      ...prev,
      formData: {
        ...prev.formData,
        [field]: value,
      },
    }));
  };

  /**
   * Handle add staging account button click
   */
  const handleAddStagingClick = () => {
    setState((prev) => ({ ...prev, showAddStaging: true }));
  };

  /**
   * Handle add staging account modal dismiss
   */
  const handleAddStagingDismiss = () => {
    setState((prev) => ({ ...prev, showAddStaging: false }));
  };

  /**
   * Handle staging account added callback
   */
  const handleStagingAccountAdded = (stagingAccount: StagingAccount) => {
    setState((prev) => ({
      ...prev,
      formData: {
        ...prev.formData,
        stagingAccounts: [...prev.formData.stagingAccounts, stagingAccount],
      },
      showAddStaging: false,
    }));
  };

  /**
   * Handle remove staging account button click
   */
  const handleRemoveStagingClick = (stagingAccount: StagingAccount) => {
    setState((prev) => ({ ...prev, removingAccount: stagingAccount }));
  };

  /**
   * Handle remove staging account confirmation
   */
  const handleRemoveStagingConfirm = async () => {
    if (!state.removingAccount) {
      return;
    }

    const accountToRemove = state.removingAccount;

    try {
      // TODO: Replace with actual API call
      // await api.removeStagingAccount({
      //   targetAccountId: targetAccount.accountId,
      //   stagingAccountId: accountToRemove.accountId,
      // });

      // Remove staging account from list
      setState((prev) => ({
        ...prev,
        formData: {
          ...prev.formData,
          stagingAccounts: prev.formData.stagingAccounts.filter(
            (sa) => sa.accountId !== accountToRemove.accountId
          ),
        },
        removingAccount: null,
      }));
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : "Failed to remove staging account";

      setState((prev) => ({
        ...prev,
        error: errorMessage,
        removingAccount: null,
      }));
    }
  };

  /**
   * Handle remove staging account cancel
   */
  const handleRemoveStagingCancel = () => {
    setState((prev) => ({ ...prev, removingAccount: null }));
  };

  /**
   * Handle save button click
   */
  const handleSave = async () => {
    setState((prev) => ({ ...prev, saving: true, error: null }));

    try {
      await onSave(state.formData);

      // Reset state and close modal
      setState((prev) => ({
        ...prev,
        saving: false,
      }));

      onDismiss();
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to save changes";

      setState((prev) => ({
        ...prev,
        saving: false,
        error: errorMessage,
      }));
    }
  };

  /**
   * Handle modal dismiss
   */
  const handleDismiss = () => {
    // Reset form state to original target account
    setState({
      formData: { ...targetAccount },
      showAddStaging: false,
      saving: false,
      error: null,
      removingAccount: null,
    });

    onDismiss();
  };

  /**
   * Check if staging account has active servers
   */
  const hasActiveServers = (stagingAccount: StagingAccount): boolean => {
    return (stagingAccount.replicatingCount || 0) > 0;
  };

  /**
   * Render staging accounts table
   */
  const renderStagingAccountsTable = () => {
    return (
      <Table
        columnDefinitions={[
          {
            id: "accountId",
            header: "Account ID",
            cell: (item: StagingAccount) => item.accountId,
            sortingField: "accountId",
          },
          {
            id: "accountName",
            header: "Account Name",
            cell: (item: StagingAccount) => item.accountName,
            sortingField: "accountName",
          },
          {
            id: "status",
            header: "Status",
            cell: (item: StagingAccount) => (
              <StatusIndicator type={getStatusType(item.status)}>
                {getStatusLabel(item.status)}
              </StatusIndicator>
            ),
          },
          {
            id: "servers",
            header: "Servers",
            cell: (item: StagingAccount) => {
              const replicating = item.replicatingCount || 0;
              const total = item.serverCount || 0;
              return (
                <Box>
                  {replicating} replicating / {total} total
                </Box>
              );
            },
          },
          {
            id: "actions",
            header: "Actions",
            cell: (item: StagingAccount) => (
              <Button
                onClick={() => handleRemoveStagingClick(item)}
                disabled={state.saving}
              >
                Remove
              </Button>
            ),
          },
        ]}
        items={state.formData.stagingAccounts}
        empty={
          <Box textAlign="center" color="inherit">
            <SpaceBetween size="m">
              <b>No staging accounts</b>
              <Button onClick={handleAddStagingClick}>
                Add Staging Account
              </Button>
            </SpaceBetween>
          </Box>
        }
        header={
          <Header
            actions={
              <Button
                onClick={handleAddStagingClick}
                disabled={state.saving}
              >
                Add Staging Account
              </Button>
            }
          >
            Staging Accounts ({state.formData.stagingAccounts.length})
          </Header>
        }
      />
    );
  };

  /**
   * Render removal confirmation modal
   */
  const renderRemovalConfirmation = () => {
    if (!state.removingAccount) {
      return null;
    }

    const hasServers = hasActiveServers(state.removingAccount);

    return (
      <Modal
        visible={true}
        onDismiss={handleRemoveStagingCancel}
        header="Remove Staging Account"
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button onClick={handleRemoveStagingCancel}>Cancel</Button>
              <Button variant="primary" onClick={handleRemoveStagingConfirm}>
                Remove
              </Button>
            </SpaceBetween>
          </Box>
        }
      >
        <SpaceBetween size="m">
          <Box>
            Are you sure you want to remove staging account{" "}
            <strong>{state.removingAccount.accountName}</strong> (
            {state.removingAccount.accountId})?
          </Box>

          {hasServers && (
            <Alert type="warning" header="Active Servers Warning">
              This staging account has{" "}
              <strong>{state.removingAccount.replicatingCount}</strong>{" "}
              actively replicating servers. Removing this account will reduce
              your combined replication capacity by{" "}
              {state.removingAccount.replicatingCount} servers.
              <br />
              <br />
              Ensure you have sufficient capacity in other accounts before
              proceeding.
            </Alert>
          )}

          <Alert type="info">
            This action will remove the staging account configuration from this
            target account. The staging account itself and its DRS resources
            will not be affected.
          </Alert>
        </SpaceBetween>
      </Modal>
    );
  };

  return (
    <>
      <Modal
        visible={visible}
        onDismiss={handleDismiss}
        header="Target Account Settings"
        size="large"
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button onClick={handleDismiss} disabled={state.saving}>
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleSave}
                loading={state.saving}
              >
                Save Changes
              </Button>
            </SpaceBetween>
          </Box>
        }
      >
        <SpaceBetween size="l">
          {state.error && (
            <Alert
              type="error"
              dismissible
              onDismiss={() => setState((prev) => ({ ...prev, error: null }))}
            >
              {state.error}
            </Alert>
          )}

          <SpaceBetween size="m">
            <Header variant="h3">Target Account Details</Header>

            <FormField label="Account ID" description="AWS account ID">
              <Input
                value={state.formData.accountId}
                disabled={true}
                readOnly={true}
              />
            </FormField>

            <FormField
              label="Account Name"
              description="Human-readable name for this target account"
            >
              <Input
                value={state.formData.accountName}
                onChange={({ detail }) =>
                  handleFieldChange("accountName", detail.value)
                }
                disabled={state.saving}
              />
            </FormField>

            {state.formData.roleArn && (
              <FormField
                label="Role ARN"
                description="IAM role ARN for cross-account access"
              >
                <Input
                  value={state.formData.roleArn}
                  onChange={({ detail }) =>
                    handleFieldChange("roleArn", detail.value)
                  }
                  disabled={state.saving}
                />
              </FormField>
            )}

            {state.formData.externalId && (
              <FormField
                label="External ID"
                description="External ID for role assumption"
              >
                <Input
                  value={state.formData.externalId}
                  onChange={({ detail }) =>
                    handleFieldChange("externalId", detail.value)
                  }
                  disabled={state.saving}
                />
              </FormField>
            )}

            {state.formData.status && (
              <FormField label="Status">
                <Badge
                  color={
                    state.formData.status === "active" ? "green" : "grey"
                  }
                >
                  {state.formData.status.toUpperCase()}
                </Badge>
              </FormField>
            )}
          </SpaceBetween>

          {renderStagingAccountsTable()}
        </SpaceBetween>
      </Modal>

      {/* Add Staging Account Modal */}
      <AddStagingAccountModal
        visible={state.showAddStaging}
        onDismiss={handleAddStagingDismiss}
        onAdd={handleStagingAccountAdded}
        targetAccountId={targetAccount.accountId}
      />

      {/* Removal Confirmation Modal */}
      {renderRemovalConfirmation()}
    </>
  );
};

export default TargetAccountSettingsModal;
