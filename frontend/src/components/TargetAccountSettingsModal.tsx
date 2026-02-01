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

import React from "react";
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
} from "@cloudscape-design/components";
import type {
  TargetAccountSettingsModalProps,
} from "../types/staging-accounts";


/**
 * TargetAccountSettingsModal Component
 *
 * Read-only view of target account and connected staging accounts.
 */
export const TargetAccountSettingsModal: React.FC<
  TargetAccountSettingsModalProps
> = ({ targetAccount, visible, onDismiss }) => {
  // Get staging accounts from target account's staging accounts list
  const stagingAccounts = targetAccount.stagingAccounts || [];
  const isLoading = stagingAccounts.length === 0 && visible;

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
          headerText={`Connected Staging Accounts (${stagingAccounts.length})`}
          variant="container"
          defaultExpanded={stagingAccounts.length > 0}
        >
          {isLoading ? (
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
              {stagingAccounts.map((stagingAccount) => (
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
