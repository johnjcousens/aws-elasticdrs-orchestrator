/**
 * TargetAccountSettingsModal Component
 *
 * Read-only modal dialog for viewing target account configuration and
 * connected staging accounts. Provides a simple view of account details
 * and staging account relationships.
 *
 * FEATURES:
 * - Display target account details (read-only)
 * - Show connected staging accounts in collapsible section
 * - Display staging account status and server counts
 *
 * REQUIREMENTS:
 * - View-only modal for target account information
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
 * Read-only view of target account and connected staging accounts.
 */
export const TargetAccountSettingsModal: React.FC<
  TargetAccountSettingsModalProps
> = ({ targetAccount, visible, onDismiss }) => {
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
          headerText={`Connected Staging Accounts (${targetAccount.stagingAccounts.length})`}
          variant="container"
          defaultExpanded={targetAccount.stagingAccounts.length > 0}
        >
          {targetAccount.stagingAccounts.length === 0 ? (
            <Box textAlign="center" color="inherit" padding="l">
              No staging accounts connected
            </Box>
          ) : (
            <SpaceBetween size="m">
              {targetAccount.stagingAccounts.map((stagingAccount) => (
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
                        {stagingAccount.replicatingCount || 0} replicating /{" "}
                        {stagingAccount.serverCount || 0} total
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
