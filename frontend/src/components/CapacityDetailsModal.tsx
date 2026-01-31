/**
 * CapacityDetailsModal Component
 *
 * Detailed modal view showing per-account and per-region capacity breakdown
 * with capacity planning recommendations.
 *
 * FEATURES:
 * - Detailed per-account metrics display
 * - Regional breakdown tables for each account
 * - Capacity planning recommendations based on current usage
 * - Status indicators and warnings
 * - Actionable guidance for capacity management
 *
 * REQUIREMENTS VALIDATED:
 * - 5.1: Display per-account capacity breakdown
 * - 5.7: Display regional breakdown for each account
 */

import React from "react";
import {
  Modal,
  Box,
  SpaceBetween,
  Button,
  Container,
  Header,
  ColumnLayout,
  StatusIndicator,
  Table,
  ProgressBar,
  Alert,
  ExpandableSection,
} from "@cloudscape-design/components";
import type {
  CapacityDetailsModalProps,
  AccountCapacity,
  RegionalCapacity,
  CapacityStatus,
} from "../types/staging-accounts";

/**
 * Get CloudScape status indicator type for capacity status
 */
const getStatusType = (
  status: CapacityStatus | "OK" | "WARNING" | "CRITICAL"
): "success" | "warning" | "error" | "info" => {
  switch (status) {
    case "OK":
      return "success";
    case "INFO":
      return "info";
    case "WARNING":
      return "warning";
    case "CRITICAL":
    case "HYPER-CRITICAL":
      return "error";
    default:
      return "info";
  }
};

/**
 * Get progress bar status based on percentage
 */
const getProgressBarStatus = (
  percentUsed: number
): "success" | "in-progress" | "error" => {
  if (percentUsed < 67) return "success";
  if (percentUsed < 83) return "in-progress";
  return "error";
};

/**
 * Format number with thousands separator
 */
const formatNumber = (num: number): string => {
  return num.toLocaleString();
};

/**
 * Generate capacity planning recommendations based on current usage
 */
const generateCapacityRecommendations = (
  accounts: AccountCapacity[]
): string[] => {
  const recommendations: string[] = [];

  // Check for accounts approaching limits
  const criticalAccounts = accounts.filter(
    (acc) => acc.status === "CRITICAL" || acc.status === "HYPER-CRITICAL"
  );
  const warningAccounts = accounts.filter((acc) => acc.status === "WARNING");
  const infoAccounts = accounts.filter((acc) => acc.status === "INFO");

  if (criticalAccounts.length > 0) {
    recommendations.push(
      `⚠️ URGENT: ${criticalAccounts.length} account(s) at critical capacity (>83%). Add staging accounts immediately to avoid hitting hard limits.`
    );
  }

  if (warningAccounts.length > 0) {
    recommendations.push(
      `⚠️ ${warningAccounts.length} account(s) at warning level (75-83%). Plan to add staging accounts soon.`
    );
  }

  if (infoAccounts.length > 0) {
    recommendations.push(
      `ℹ️ ${infoAccounts.length} account(s) at info level (67-75%). Monitor capacity and consider adding staging accounts.`
    );
  }

  // Check for unbalanced distribution
  const targetAccount = accounts.find((acc) => acc.accountType === "target");
  const stagingAccounts = accounts.filter(
    (acc) => acc.accountType === "staging"
  );

  if (targetAccount && stagingAccounts.length > 0) {
    const avgStagingUsage =
      stagingAccounts.reduce((sum, acc) => sum + acc.percentUsed, 0) /
      stagingAccounts.length;

    if (
      targetAccount.percentUsed > 75 &&
      avgStagingUsage < 50 &&
      stagingAccounts.length > 0
    ) {
      recommendations.push(
        `💡 Target account is at ${targetAccount.percentUsed.toFixed(
          1
        )}% while staging accounts average ${avgStagingUsage.toFixed(
          1
        )}%. Consider rebalancing server distribution.`
      );
    }
  }

  // General recommendations
  if (accounts.every((acc) => acc.percentUsed < 50)) {
    recommendations.push(
      `✅ All accounts are below 50% capacity. Current configuration is healthy.`
    );
  }

  if (stagingAccounts.length === 0 && targetAccount && targetAccount.percentUsed > 50) {
    recommendations.push(
      `💡 Consider adding staging accounts to increase capacity and provide redundancy.`
    );
  }

  // Regional distribution recommendations
  const accountsWithMultipleRegions = accounts.filter(
    (acc) => acc.regionalBreakdown.length > 1
  );
  if (accountsWithMultipleRegions.length > 0) {
    recommendations.push(
      `✅ ${accountsWithMultipleRegions.length} account(s) using multi-region distribution for better resilience.`
    );
  }

  return recommendations;
};

/**
 * Render detailed account metrics
 */
const renderAccountDetails = (account: AccountCapacity) => {
  return (
    <Container
      header={
        <Header
          variant="h3"
          description={`Account ID: ${account.accountId}`}
        >
          {account.accountName}
        </Header>
      }
    >
      <SpaceBetween size="l">
        {/* Account Status and Metrics */}
        <ColumnLayout columns={4} variant="text-grid">
          <div>
            <Box variant="awsui-key-label">Account Type</Box>
            <Box
              variant="awsui-value-large"
              color={
                account.accountType === "target"
                  ? "text-status-info"
                  : undefined
              }
            >
              <span style={{ textTransform: "capitalize" }}>
                {account.accountType}
              </span>
            </Box>
          </div>
          <div>
            <Box variant="awsui-key-label">Status</Box>
            <StatusIndicator type={getStatusType(account.status)}>
              {account.status}
            </StatusIndicator>
          </div>
          <div>
            <Box variant="awsui-key-label">Replicating Servers</Box>
            <Box variant="awsui-value-large">
              {formatNumber(account.replicatingServers)} /{" "}
              {formatNumber(account.maxReplicating)}
            </Box>
          </div>
          <div>
            <Box variant="awsui-key-label">Available Slots</Box>
            <Box variant="awsui-value-large">
              {formatNumber(account.availableSlots)}
            </Box>
          </div>
        </ColumnLayout>

        {/* Capacity Usage Progress Bar */}
        <div>
          <Box variant="awsui-key-label" margin={{ bottom: "xs" }}>
            Capacity Usage
          </Box>
          <ProgressBar
            value={account.percentUsed}
            status={getProgressBarStatus(account.percentUsed)}
            label={`${account.percentUsed.toFixed(1)}% used`}
            description={`${formatNumber(
              account.replicatingServers
            )} of ${formatNumber(account.maxReplicating)} servers`}
          />
        </div>

        {/* Account-specific warnings */}
        {account.warnings.length > 0 && (
          <SpaceBetween size="s">
            {account.warnings.map((warning, idx) => (
              <Alert
                key={idx}
                type={getStatusType(account.status)}
                header="Account Warning"
              >
                {warning}
              </Alert>
            ))}
          </SpaceBetween>
        )}

        {/* Regional Breakdown */}
        {account.regionalBreakdown.length > 0 && (
          <div>
            <Box variant="h4" margin={{ bottom: "s" }}>
              Regional Breakdown
            </Box>
            <Table
              columnDefinitions={[
                {
                  id: "region",
                  header: "Region",
                  cell: (item: RegionalCapacity) => item.region,
                  sortingField: "region",
                },
                {
                  id: "totalServers",
                  header: "Total Servers",
                  cell: (item: RegionalCapacity) =>
                    formatNumber(item.totalServers),
                  sortingField: "totalServers",
                },
                {
                  id: "replicatingServers",
                  header: "Replicating Servers",
                  cell: (item: RegionalCapacity) =>
                    formatNumber(item.replicatingServers),
                  sortingField: "replicatingServers",
                },
                {
                  id: "percentage",
                  header: "% of Account Total",
                  cell: (item: RegionalCapacity) => {
                    const percentage =
                      account.totalServers > 0
                        ? (item.totalServers / account.totalServers) * 100
                        : 0;
                    return `${percentage.toFixed(1)}%`;
                  },
                },
              ]}
              items={account.regionalBreakdown}
              sortingDisabled={false}
              variant="embedded"
              empty={
                <Box textAlign="center" color="inherit">
                  <b>No regional data</b>
                  <Box variant="p" color="inherit">
                    No servers in any region
                  </Box>
                </Box>
              }
            />
          </div>
        )}

        {/* Error state for inaccessible accounts */}
        {account.accessible === false && account.error && (
          <Alert type="error" header="Account Inaccessible">
            {account.error}
          </Alert>
        )}
      </SpaceBetween>
    </Container>
  );
};

/**
 * Render capacity planning recommendations
 */
const renderCapacityPlanning = (accounts: AccountCapacity[]) => {
  const recommendations = generateCapacityRecommendations(accounts);

  if (recommendations.length === 0) {
    return null;
  }

  return (
    <Container
      header={
        <Header variant="h3" description="Based on current capacity usage">
          Capacity Planning Recommendations
        </Header>
      }
    >
      <SpaceBetween size="s">
        {recommendations.map((recommendation, idx) => {
          // Determine alert type based on recommendation content
          let alertType: "success" | "info" | "warning" | "error" = "info";
          if (recommendation.includes("URGENT") || recommendation.includes("⚠️")) {
            alertType = recommendation.includes("URGENT") ? "error" : "warning";
          } else if (recommendation.includes("✅")) {
            alertType = "success";
          }

          return (
            <Alert key={idx} type={alertType}>
              {recommendation}
            </Alert>
          );
        })}
      </SpaceBetween>
    </Container>
  );
};

/**
 * CapacityDetailsModal Component
 *
 * Displays detailed capacity information for all accounts with
 * regional breakdown and planning recommendations.
 */
export const CapacityDetailsModal: React.FC<CapacityDetailsModalProps> = ({
  capacityData,
  visible,
  onDismiss,
}) => {
  return (
    <Modal
      visible={visible}
      onDismiss={onDismiss}
      header="Capacity Details"
      size="max"
      footer={
        <Box float="right">
          <Button variant="primary" onClick={onDismiss}>
            Close
          </Button>
        </Box>
      }
    >
      <SpaceBetween size="l">
        {/* Summary Section */}
        <Container
          header={
            <Header
              variant="h2"
              description={
                capacityData.timestamp
                  ? `Last updated: ${new Date(
                      capacityData.timestamp
                    ).toLocaleString()}`
                  : undefined
              }
            >
              Capacity Summary
            </Header>
          }
        >
          <ColumnLayout columns={3} variant="text-grid">
            <div>
              <Box variant="awsui-key-label">Total Accounts</Box>
              <Box variant="awsui-value-large">
                {capacityData.accounts.length}
              </Box>
              <Box variant="small" color="text-body-secondary">
                {
                  capacityData.accounts.filter(
                    (acc) => acc.accountType === "target"
                  ).length
                }{" "}
                target,{" "}
                {
                  capacityData.accounts.filter(
                    (acc) => acc.accountType === "staging"
                  ).length
                }{" "}
                staging
              </Box>
            </div>
            <div>
              <Box variant="awsui-key-label">Combined Capacity</Box>
              <Box variant="awsui-value-large">
                {formatNumber(capacityData.combined.totalReplicating)} /{" "}
                {formatNumber(capacityData.combined.maxReplicating)}
              </Box>
              <Box variant="small" color="text-body-secondary">
                {capacityData.combined.percentUsed.toFixed(1)}% used
              </Box>
            </div>
            <div>
              <Box variant="awsui-key-label">Combined Status</Box>
              <StatusIndicator
                type={getStatusType(capacityData.combined.status)}
              >
                {capacityData.combined.status}
              </StatusIndicator>
              <Box variant="small" color="text-body-secondary">
                {formatNumber(capacityData.combined.availableSlots)} slots
                available
              </Box>
            </div>
          </ColumnLayout>
        </Container>

        {/* Capacity Planning Recommendations */}
        {renderCapacityPlanning(capacityData.accounts)}

        {/* Per-Account Details */}
        <Container
          header={
            <Header variant="h2">Per-Account Details</Header>
          }
        >
          <SpaceBetween size="l">
            {capacityData.accounts.map((account) => (
              <ExpandableSection
                key={account.accountId}
                headerText={`${account.accountName} (${account.accountId})`}
                headerDescription={`${account.accountType} • ${account.replicatingServers} servers • ${account.percentUsed.toFixed(1)}% used`}
                defaultExpanded={
                  account.status === "CRITICAL" ||
                  account.status === "HYPER-CRITICAL" ||
                  account.warnings.length > 0
                }
              >
                {renderAccountDetails(account)}
              </ExpandableSection>
            ))}
          </SpaceBetween>
        </Container>

        {/* Recovery Capacity Details */}
        <Container
          header={
            <Header
              variant="h2"
              description="Recovery instance capacity in target account"
            >
              Recovery Capacity
            </Header>
          }
        >
          <SpaceBetween size="l">
            <ColumnLayout columns={4} variant="text-grid">
              <div>
                <Box variant="awsui-key-label">Current Servers</Box>
                <Box variant="awsui-value-large">
                  {formatNumber(capacityData.recoveryCapacity.currentServers)}
                </Box>
              </div>
              <div>
                <Box variant="awsui-key-label">Max Recovery Instances</Box>
                <Box variant="awsui-value-large">
                  {formatNumber(
                    capacityData.recoveryCapacity.maxRecoveryInstances
                  )}
                </Box>
              </div>
              <div>
                <Box variant="awsui-key-label">Percentage Used</Box>
                <Box variant="awsui-value-large">
                  {capacityData.recoveryCapacity.percentUsed.toFixed(1)}%
                </Box>
              </div>
              <div>
                <Box variant="awsui-key-label">Status</Box>
                <StatusIndicator
                  type={getStatusType(capacityData.recoveryCapacity.status)}
                >
                  {capacityData.recoveryCapacity.status}
                </StatusIndicator>
              </div>
            </ColumnLayout>

            <div>
              <Box variant="awsui-key-label" margin={{ bottom: "xs" }}>
                Recovery Instance Capacity
              </Box>
              <ProgressBar
                value={capacityData.recoveryCapacity.percentUsed}
                status={
                  capacityData.recoveryCapacity.percentUsed < 80
                    ? "success"
                    : capacityData.recoveryCapacity.percentUsed < 90
                    ? "in-progress"
                    : "error"
                }
                description={`${formatNumber(
                  capacityData.recoveryCapacity.currentServers
                )} of ${formatNumber(
                  capacityData.recoveryCapacity.maxRecoveryInstances
                )} recovery instances`}
              />
            </div>

            {capacityData.recoveryCapacity.percentUsed >= 80 && (
              <Alert
                type={
                  capacityData.recoveryCapacity.percentUsed >= 90
                    ? "error"
                    : "warning"
                }
                header="Recovery Capacity Warning"
              >
                {capacityData.recoveryCapacity.percentUsed >= 90
                  ? "Recovery capacity is above 90%. Consider reducing server count or increasing recovery instance limits."
                  : "Recovery capacity is above 80%. Monitor usage and plan for capacity expansion."}
              </Alert>
            )}
          </SpaceBetween>
        </Container>

        {/* System-wide Warnings */}
        {capacityData.warnings.length > 0 && (
          <Container header={<Header variant="h2">System Warnings</Header>}>
            <SpaceBetween size="s">
              {capacityData.warnings.map((warning, idx) => (
                <Alert
                  key={idx}
                  type={getStatusType(capacityData.combined.status)}
                  header="System Warning"
                >
                  {warning}
                </Alert>
              ))}
            </SpaceBetween>
          </Container>
        )}
      </SpaceBetween>
    </Modal>
  );
};

export default CapacityDetailsModal;
