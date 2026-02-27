/**
 * Regional Capacity Section
 * 
 * Displays combined per-region replication capacity across all accounts.
 * Uses CloudScape ProgressBar for clean left-aligned layout.
 * Includes collapsible per-account breakdown.
 */

import React from 'react';
import {
  Container,
  Header,
  SpaceBetween,
  Box,
  ColumnLayout,
  ExpandableSection,
  ProgressBar,
  StatusIndicator,
} from '@cloudscape-design/components';
import type { RegionalCapacityBreakdown, AccountCapacity } from '../types/staging-accounts';

interface RegionalCapacitySectionProps {
  regionalCapacity: RegionalCapacityBreakdown[];
  accounts?: AccountCapacity[];
}

export const RegionalCapacitySection: React.FC<RegionalCapacitySectionProps> = ({
  regionalCapacity,
  accounts,
}) => {
  const activeRegions = regionalCapacity.filter(r => r.replicatingServers > 0);

  if (activeRegions.length === 0) {
    return null;
  }

  const getStatus = (pct: number): 'success' | 'error' | 'in-progress' => {
    if (pct >= 90) return 'error';
    return 'in-progress';
  };

  return (
    <Container
      header={
        <Header
          variant="h2"
          description="Per-region capacity across all accounts (300 per account per region)"
        >
          Regional Capacity
        </Header>
      }
    >
      <SpaceBetween size="l">
        {activeRegions.map((region) => {
          const replPct = region.maxReplicating > 0
            ? Math.round((region.replicatingServers / region.maxReplicating) * 100)
            : 0;
          const recovPct = region.recoveryMax > 0
            ? Math.round((region.recoveryServers / region.recoveryMax) * 100)
            : 0;

          const accountsInRegion = (accounts || [])
            .map((account) => {
              const rd = (account.regionalBreakdown || []).find(
                (r: { region: string }) => r.region === region.region
              );
              if (!rd || rd.replicatingServers === 0) return null;
              return { ...account, regionData: rd };
            })
            .filter(Boolean) as Array<AccountCapacity & { regionData: { replicatingServers: number } }>;

          return (
            <SpaceBetween key={region.region} size="s">
              <Box variant="h3">{region.region}</Box>

              <ColumnLayout columns={2} variant="text-grid">
                <SpaceBetween size="xxs">
                  <Box variant="awsui-key-label">
                    Replication ({region.accountCount} acct{region.accountCount !== 1 ? 's' : ''})
                  </Box>
                  <ProgressBar
                    value={replPct}
                    status={getStatus(replPct)}
                    additionalInfo={`${region.replicatingServers.toLocaleString()} / ${region.maxReplicating.toLocaleString()} servers`}
                    description={`${region.replicatingServers} servers used`}
                  />
                </SpaceBetween>

                <SpaceBetween size="xxs">
                  <Box variant="awsui-key-label">Recovery</Box>
                  <ProgressBar
                    value={recovPct}
                    status={getStatus(recovPct)}
                    additionalInfo={`${region.recoveryServers.toLocaleString()} / ${region.recoveryMax.toLocaleString()} instances`}
                    description={`${region.recoveryMax - region.recoveryServers} slots available`}
                  />
                </SpaceBetween>
              </ColumnLayout>

              {accountsInRegion.length > 0 && (
                <ExpandableSection
                  variant="footer"
                  headerText={`Account breakdown (${accountsInRegion.length} accounts)`}
                >
                  <ColumnLayout columns={accountsInRegion.length <= 2 ? accountsInRegion.length : 3} variant="text-grid">
                    {accountsInRegion.map((account) => {
                      const used = account.regionData.replicatingServers;
                      const pct = Math.round((used / 300) * 100);
                      const typeLabel = account.accountType === 'target' ? 'Target' : 'Staging';

                      return (
                        <SpaceBetween key={account.accountId} size="xxs">
                          <Box variant="awsui-key-label">
                            {account.accountName || account.accountId}
                            <Box variant="small" color="text-body-secondary" display="inline"> ({typeLabel})</Box>
                          </Box>
                          <ProgressBar
                            value={pct}
                            status={getStatus(pct)}
                            additionalInfo={`${used} / 300 servers`}
                            description={`${used} servers used`}
                          />
                        </SpaceBetween>
                      );
                    })}
                  </ColumnLayout>
                </ExpandableSection>
              )}
            </SpaceBetween>
          );
        })}
      </SpaceBetween>
    </Container>
  );
};
