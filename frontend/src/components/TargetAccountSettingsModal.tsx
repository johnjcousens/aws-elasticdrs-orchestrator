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
} from "@cloudscape-design/components";
import type {
  TargetAccountSettingsModalProps,
  StagingAccount,
} from "../types/staging-accounts";


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
 * Read-only view of target account and auto-discovered staging accounts.
 */
export const TargetAccountSettingsModal: React.FC<
  TargetAccountSettingsModalProps
> = ({ targetAccount, visible, onDismiss }) => {
  const [discoveredStagingAccounts, setDiscoveredStagingAccounts] = useState<
    StagingAccount[]
  >([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Discover staging accounts when modal opens
  useEffect(() => {
    if (visible && targetAccount.accountId) {
      discoverStagingAccounts();
    }
  }, [visible, targetAccount.accountId]);

  const discoverStagingAccounts = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/accounts/${targetAccount.accountId}/staging-accounts/discover`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to discover staging accounts: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.stagingAccounts) {
        setDiscoveredStagingAccounts(data.stagingAccounts);
      }
    } catch (err: any) {
      console.error("Failed to discover staging accounts:", err);
      setError(err.message || "Failed to discover staging accounts");
    } finally {
      setLoading(false);
    }
  };

  // Use discovered staging accounts if available, otherwise use provided ones
  const stagingAccountsToDisplay =
    discoveredStagingAccounts.length > 0
      ? discoveredStagingAccounts
      : targetAccount.stagingAccounts;

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
        {/* Target Account Information */}
        <Container header={<Header variant="h3">Account Information</Header>}>
          <ColumnLayout columns={2} variant="text-grid">
            <div>
              <Box variant="awsui-key-label">Account ID</Box>
              <div>{targetAccount.accountId}</div>
            </div>
            <div>
              <Box variant="awsui-key-label">Account Name</Box>
              <div>{targetAccount.accountName || "—"}</div>
            </div>
            {targetAccount.roleArn && (
              <div>
                <Box variant="awsui-key-label">Role ARN</Box>
                <div>{targetAccount.roleArn}</div>
              </div>
            )}
            {targetAccount.externalId && (
              <div>
                <Box variant="awsui-key-label">External ID</Box>
                <div>{targetAccount.externalId}</div>
              </div>
            )}
            {targetAccount.status && (
              <div>
                <Box variant="awsui-key-label">Status</Box>
                <StatusIndicator
                  type={targetAccount.status === "active" ? "success" : "info"}
                >
                  {targetAccount.status.toUpperCase()}
                </StatusIndicator>
              </div>
            )}
          </ColumnLayout>
        </Container>

        {/* Connected Staging Accounts */}
        <ExpandableSection
          headerText={`Connected Staging Accounts (${stagingAccountsToDisplay.length})`}
          variant="container"
          defaultExpanded={stagingAccountsToDisplay.length > 0}
        >
          {loading ? (
            <Box textAlign="center" padding="l">
              <Spinner size="large" />
              <Box variant="p" padding={{ top: "s" }}>
                Discovering staging accounts...
              </Box>
            </Box>
          ) : error ? (
            <Alert type="error" header="Discovery Failed">
              {error}
            </Alert>
          ) : stagingAccountsToDisplay.length === 0 ? (
            <Box textAlign="center" color="inherit" padding="l">
              No staging accounts discovered
            </Box>
          ) : (
            <SpaceBetween size="m">
              {stagingAccountsToDisplay.map((stagingAccount) => (
                <Container key={stagingAccount.accountId}>
                  <ColumnLayout columns={2} variant="text-grid">
                    <div>
                      <Box variant="awsui-key-label">Account ID</Box>
                      <div>{stagingAccount.accountId}</div>
                    </div>
                    <div>
                      <Box variant="awsui-key-label">Account Name</Box>
                      <div>{stagingAccount.accountName}</div>
                    </div>
                    <div>
                      <Box variant="awsui-key-label">Status</Box>
                      <StatusIndicator type={getStatusType(stagingAccount.status)}>
                        {getStatusLabel(stagingAccount.status)}
                      </StatusIndicator>
                    </div>
                    <div>
                      <Box variant="awsui-key-label">Servers</Box>
                      <div>
                        {(stagingAccount as any).replicatingCount || (stagingAccount as any).replicatingServers || 0} replicating /{" "}
                        {(stagingAccount as any).serverCount || (stagingAccount as any).totalServers || 0} total
                      </div>
                    </div>
                  </ColumnLayout>
                </Container>
              ))}
            </SpaceBetween>
          )}
        </ExpandableSection>
      </SpaceBetween>
    </Modal>
  );
};

export default TargetAccountSettingsModal;
