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
} from "@cloudscape-design/components";
import apiClient from "../services/api";
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
                <div>{displayAccount.accountName || "—"}</div>
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
                <Box key={stagingAccount.accountId} padding="s">
                  <strong>{stagingAccount.accountName}</strong> ({stagingAccount.accountId})
                </Box>
              ))}
            </SpaceBetween>
          )}
        </ExpandableSection>
      </SpaceBetween>
    </Modal>
  );
};

export default TargetAccountSettingsModal;
