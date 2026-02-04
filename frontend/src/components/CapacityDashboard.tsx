/**
 * CapacityDashboard Component
 *
 * Displays combined capacity metrics across target and staging accounts,
 * including per-account breakdown, recovery capacity, and warnings.
 *
 * FEATURES:
 * - Combined capacity display with status indicators
 * - Per-account capacity breakdown with regional details
 * - Recovery capacity metrics
 * - Automatic refresh with configurable interval
 * - Warning alerts with actionable guidance
 *
 * REQUIREMENTS VALIDATED:
 * - 4.1: Auto-refresh capacity data
 * - 4.3: Display combined capacity metrics
 * - 4.4: Display status indicators
 * - 4.5: Display progress bars
 * - 5.1: Display per-account breakdown
 * - 5.2: Display account details
 * - 5.7: Display regional breakdown
 * - 6.6: Display warnings prominently
 * - 10.1: Display recovery capacity
 */

import React, { useState, useEffect, useCallback } from "react";
import {
  Container,
  Header,
  SpaceBetween,
  Box,
  ProgressBar,
  StatusIndicator,
  Alert,
  Table,
  ColumnLayout,
  Button,
  Toggle,
  Spinner,
} from "@cloudscape-design/components";
import { getCombinedCapacity } from "../services/staging-accounts-api";
import type {
  CapacityDashboardProps,
  CapacityDashboardState,
  CombinedCapacityData,
  AccountCapacity,
  CapacityStatus,
} from "../types/staging-accounts";

/**
 * Get CloudScape status indicator type for capacity status
 */
const getStatusType = (
  status: CapacityStatus
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
 * Get CloudScape alert type for capacity status
 */
const getAlertType = (
  status: CapacityStatus
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
 * Get progress bar color based on percentage and limits
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
const formatNumber = (num: number | undefined): string => {
  if (num === undefined || num === null) {
    return "0";
  }
  return num.toLocaleString();
};

/**
 * CapacityDashboard Component
 *
 * Main component for displaying capacity metrics across all accounts.
 */
export const CapacityDashboard: React.FC<CapacityDashboardProps> = ({
  targetAccountId,
  refreshInterval = 30000,
  autoRefresh = true,
  onCapacityLoaded,
  onError,
}) => {
  const [state, setState] = useState<CapacityDashboardState>({
    loading: true,
    error: null,
    capacityData: null,
    lastRefresh: null,
    autoRefreshEnabled: autoRefresh,
  });

  /**
   * Fetch capacity data from API
   */
  const fetchCapacity = useCallback(async () => {
    try {
      setState((prev) => ({ ...prev, loading: true, error: null }));

      // Call the real API
      const data = await getCombinedCapacity(targetAccountId || "", true);

      setState((prev) => ({
        ...prev,
        loading: false,
        capacityData: data,
        lastRefresh: new Date(),
      }));

      if (onCapacityLoaded) {
        onCapacityLoaded(data);
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to load capacity data";
      setState((prev) => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));

      if (onError) {
        onError(
          error instanceof Error ? error : new Error("Failed to load capacity")
        );
      }
    }
  }, [targetAccountId, onCapacityLoaded, onError]);

  /**
   * Set up auto-refresh interval
   */
  useEffect(() => {
    // Initial fetch
    fetchCapacity();

    // Set up interval if auto-refresh is enabled
    if (state.autoRefreshEnabled && refreshInterval > 0) {
      const intervalId = setInterval(fetchCapacity, refreshInterval);
      return () => clearInterval(intervalId);
    }
  }, [fetchCapacity, state.autoRefreshEnabled, refreshInterval]);

  /**
   * Toggle auto-refresh
   */
  const handleToggleAutoRefresh = (checked: boolean) => {
    setState((prev) => ({ ...prev, autoRefreshEnabled: checked }));
  };

  /**
   * Manual refresh
   */
  const handleManualRefresh = () => {
    fetchCapacity();
  };

  /**
   * Render loading state
   */
  if (state.loading && !state.capacityData) {
    return (
      <Container>
        <Box textAlign="center" padding="xxl">
          <Spinner size="large" />
          <Box variant="p" padding={{ top: "s" }}>
            Loading capacity data...
          </Box>
        </Box>
      </Container>
    );
  }

  /**
   * Render error state
   */
  if (state.error && !state.capacityData) {
    return (
      <Container>
        <Alert type="error" header="Failed to load capacity data">
          {state.error}
          <Box margin={{ top: "s" }}>
            <Button onClick={handleManualRefresh}>Retry</Button>
          </Box>
        </Alert>
      </Container>
    );
  }

  const { capacityData } = state;

  if (!capacityData) {
    return null;
  }

  return (
    <SpaceBetween size="l">
      {/* Warnings Section */}
      {capacityData.warnings.length > 0 && (
        <SpaceBetween size="s">
          {capacityData.warnings.map((warning, index) => (
            <Alert
              key={index}
              type={getAlertType(capacityData.combined.status)}
              header="Capacity Warning"
            >
              {warning}
            </Alert>
          ))}
        </SpaceBetween>
      )}

      {/* Combined Capacity Section */}
      <Container
        header={
          <Header
            variant="h2"
            actions={
              <SpaceBetween direction="horizontal" size="xs">
                <Toggle
                  checked={state.autoRefreshEnabled}
                  onChange={({ detail }) =>
                    handleToggleAutoRefresh(detail.checked)
                  }
                >
                  Auto-refresh
                </Toggle>
                <Button
                  iconName="refresh"
                  onClick={handleManualRefresh}
                  loading={state.loading}
                >
                  Refresh
                </Button>
              </SpaceBetween>
            }
            description={
              state.lastRefresh
                ? `Last updated: ${state.lastRefresh.toLocaleTimeString()}`
                : undefined
            }
          >
            Combined Replication Capacity
          </Header>
        }
      >
        <SpaceBetween size="l">
          <ColumnLayout columns={4} variant="text-grid">
            <div>
              <Box variant="awsui-key-label">Total Replicating</Box>
              <Box variant="awsui-value-large">
                {formatNumber(capacityData.combined.totalReplicating)} /{" "}
                {formatNumber(capacityData.combined.maxReplicating)}
              </Box>
            </div>
            <div>
              <Box variant="awsui-key-label">Percentage Used</Box>
              <Box variant="awsui-value-large">
                {capacityData.combined.percentUsed.toFixed(1)}%
              </Box>
            </div>
            <div>
              <Box variant="awsui-key-label">Available Slots</Box>
              <Box variant="awsui-value-large">
                {formatNumber(capacityData.combined.availableSlots)}
              </Box>
            </div>
            <div>
              <Box variant="awsui-key-label">Status</Box>
              <StatusIndicator type={getStatusType(capacityData.combined.status)}>
                {capacityData.combined.status}
              </StatusIndicator>
            </div>
          </ColumnLayout>

          <div>
            <Box variant="awsui-key-label" margin={{ bottom: "xs" }}>
              Capacity Usage
            </Box>
            <ProgressBar
              value={capacityData.combined.percentUsed}
              status={getProgressBarStatus(capacityData.combined.percentUsed)}
              label={capacityData.combined.message}
              description={`${formatNumber(
                capacityData.combined.totalReplicating
              )} of ${formatNumber(
                capacityData.combined.maxReplicating
              )} servers`}
            />
          </div>
        </SpaceBetween>
      </Container>

      {/* Per-Account Capacity Breakdown */}
      <Container
        header={<Header variant="h2">Per-Account Capacity Breakdown</Header>}
      >
        <Table
          columnDefinitions={[
            {
              id: "accountName",
              header: "Account",
              cell: (item: AccountCapacity) => (
                <div>
                  <div>
                    <strong>{item.accountName}</strong>
                  </div>
                  <div style={{ fontSize: "0.875rem", color: "#5f6b7a" }}>
                    {item.accountId}
                  </div>
                </div>
              ),
              sortingField: "accountName",
            },
            {
              id: "accountType",
              header: "Type",
              cell: (item: AccountCapacity) => (
                <Box
                  variant="span"
                  color={
                    item.accountType === "target" ? "text-status-info" : undefined
                  }
                >
                  <span style={{ textTransform: "capitalize" }}>
                    {item.accountType}
                  </span>
                </Box>
              ),
              sortingField: "accountType",
            },
            {
              id: "replicatingServers",
              header: "Replicating Servers",
              cell: (item: AccountCapacity) =>
                `${formatNumber(item.replicatingServers)} / ${formatNumber(
                  item.maxReplicating
                )}`,
              sortingField: "replicatingServers",
            },
            {
              id: "percentUsed",
              header: "Percentage Used",
              cell: (item: AccountCapacity) => (
                <div>
                  <div>{item.percentUsed.toFixed(1)}%</div>
                  <ProgressBar
                    value={item.percentUsed}
                    status={getProgressBarStatus(item.percentUsed)}
                    variant="standalone"
                  />
                </div>
              ),
              sortingField: "percentUsed",
            },
            {
              id: "availableSlots",
              header: "Available Slots",
              cell: (item: AccountCapacity) =>
                formatNumber(item.availableSlots),
              sortingField: "availableSlots",
            },
            {
              id: "status",
              header: "Status",
              cell: (item: AccountCapacity) => (
                <StatusIndicator type={getStatusType(item.status)}>
                  {item.status}
                </StatusIndicator>
              ),
              sortingField: "status",
            },
            {
              id: "regions",
              header: "Regions",
              cell: (item: AccountCapacity) => (
                <div>
                  {item.regionalBreakdown.map((region, idx) => (
                    <div
                      key={region.region}
                      style={{
                        fontSize: "0.875rem",
                        marginBottom:
                          idx < item.regionalBreakdown.length - 1
                            ? "4px"
                            : "0",
                      }}
                    >
                      <strong>{region.region}:</strong>{" "}
                      {formatNumber(region.replicatingServers)} servers
                    </div>
                  ))}
                </div>
              ),
            },
          ]}
          items={capacityData.accounts}
          sortingDisabled={false}
          variant="embedded"
          empty={
            <Box textAlign="center" color="inherit">
              <b>No accounts</b>
              <Box variant="p" color="inherit">
                No capacity data available
              </Box>
            </Box>
          }
        />

        {/* Account-specific warnings */}
        {capacityData.accounts.some((acc) => acc.warnings.length > 0) && (
          <Box margin={{ top: "m" }}>
            <SpaceBetween size="s">
              {capacityData.accounts
                .filter((acc) => acc.warnings.length > 0)
                .map((acc) =>
                  acc.warnings.map((warning, idx) => (
                    <Alert
                      key={`${acc.accountId}-${idx}`}
                      type={getAlertType(acc.status)}
                      header={`${acc.accountName} Warning`}
                    >
                      {warning}
                    </Alert>
                  ))
                )}
            </SpaceBetween>
          </Box>
        )}
      </Container>

      {/* Recovery Capacity Section */}
      <Container
        header={<Header variant="h2">Recovery Capacity (Target Account)</Header>}
      >
        <SpaceBetween size="l">
          <ColumnLayout columns={4} variant="text-grid">
            <div>
              <Box variant="awsui-key-label">Current Servers</Box>
              <Box variant="awsui-value-large">
                {formatNumber(capacityData.recoveryCapacity.currentServers)} /{" "}
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
              <Box variant="awsui-key-label">Available Slots</Box>
              <Box variant="awsui-value-large">
                {formatNumber(capacityData.recoveryCapacity.availableSlots)}
              </Box>
            </div>
            <div>
              <Box variant="awsui-key-label">Status</Box>
              <StatusIndicator
                type={getStatusType(
                  capacityData.recoveryCapacity.status as CapacityStatus
                )}
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
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  );
};

export default CapacityDashboard;
