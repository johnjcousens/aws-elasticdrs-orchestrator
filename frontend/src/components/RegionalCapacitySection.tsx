/**
 * Regional Capacity Section
 * 
 * Displays combined per-region replication capacity across all accounts.
 * Replication capacity is unique as it's the only DRS quota that is per-account-per-region (300 max).
 */

import React from 'react';
import {
  Container,
  Header,
  SpaceBetween,
  Box,
  ColumnLayout,
  StatusIndicator,
} from '@cloudscape-design/components';
import { CapacityGauge } from './CapacityGauge';
import type { AccountCapacity, RegionalCapacity } from '../types/staging-accounts';

interface RegionalCapacitySectionProps {
  accounts: AccountCapacity[];
  combinedTotal: number;
  combinedMax: number;
  combinedPercent: number;
  combinedStatus: string;
}

interface CombinedRegionalCapacity {
  region: string;
  replicatingServers: number;
  maxReplicating: number;
  percentUsed: number;
  availableSlots: number;
  accountCount: number;
  // Recovery capacity (total servers in region, not just replicating)
  recoveryServers: number;
  recoveryMax: number;
  recoveryPercent: number;
  recoveryAvailable: number;
}

interface TargetAccountRegionalView {
  accountId: string;
  accountName: string;
  totalReplicating: number;
  totalMax: number;
  totalPercent: number;
  regions: CombinedRegionalCapacity[];
}

export const RegionalCapacitySection: React.FC<RegionalCapacitySectionProps> = ({
  accounts,
  combinedTotal,
  combinedMax,
  combinedPercent,
  combinedStatus,
}) => {
  const getStatusType = (status: string): 'success' | 'error' | 'warning' | 'info' => {
    switch (status) {
      case 'OK':
        return 'success';
      case 'INFO':
        return 'info';
      case 'WARNING':
        return 'warning';
      case 'CRITICAL':
      case 'HYPER-CRITICAL':
        return 'error';
      default:
        return 'info';
    }
  };

  // Calculate total recovery capacity across all regions
  const uniqueRegions = new Set<string>();
  accounts.forEach(account => {
    account.regionalBreakdown.forEach(region => {
      uniqueRegions.add(region.region);
    });
  });
  const totalRegions = uniqueRegions.size;
  const recoveryCapacityMax = totalRegions * 4000; // 4,000 per region
  const recoveryCapacityUsed = accounts
    .filter(acc => acc.accountType === 'target')
    .reduce((sum, acc) => sum + acc.totalServers, 0);
  const recoveryCapacityPercent = recoveryCapacityMax > 0 
    ? (recoveryCapacityUsed / recoveryCapacityMax) * 100 
    : 0;
  const recoveryCapacityStatus = recoveryCapacityPercent < 80 
    ? 'success' 
    : recoveryCapacityPercent < 90 
      ? 'warning' 
      : 'error';

  // Group by target account and combine with staging accounts per region
  const targetAccountViews: TargetAccountRegionalView[] = [];
  
  accounts.filter(acc => acc.accountType === 'target' && acc.accessible).forEach((targetAccount) => {
    const regionalCapacity: Record<string, CombinedRegionalCapacity> = {};
    
    // Add target account's regional data
    targetAccount.regionalBreakdown.forEach((region) => {
      if (!regionalCapacity[region.region]) {
        regionalCapacity[region.region] = {
          region: region.region,
          replicatingServers: 0,
          maxReplicating: 0,
          percentUsed: 0,
          availableSlots: 0,
          accountCount: 0,
          recoveryServers: 0,
          recoveryMax: 0,
          recoveryPercent: 0,
          recoveryAvailable: 0,
        };
      }
      
      regionalCapacity[region.region].replicatingServers += region.replicatingServers;
      regionalCapacity[region.region].maxReplicating += (region.maxReplicating || 300);
      regionalCapacity[region.region].accountCount += 1;
      
      // Recovery capacity: count ALL servers in target account for this region
      // Use totalServers (includes replicating + other states)
      regionalCapacity[region.region].recoveryServers += (region.totalServers || region.replicatingServers);
      regionalCapacity[region.region].recoveryMax = 4000; // Per region limit
    });
    
    // Add staging accounts' regional data for this target
    accounts.filter(acc => acc.accountType === 'staging' && acc.accessible).forEach((stagingAccount) => {
      stagingAccount.regionalBreakdown.forEach((region) => {
        if (!regionalCapacity[region.region]) {
          regionalCapacity[region.region] = {
            region: region.region,
            replicatingServers: 0,
            maxReplicating: 0,
            percentUsed: 0,
            availableSlots: 0,
            accountCount: 0,
            recoveryServers: 0,
            recoveryMax: 4000,
            recoveryPercent: 0,
            recoveryAvailable: 0,
          };
        }
        
        regionalCapacity[region.region].replicatingServers += region.replicatingServers;
        regionalCapacity[region.region].maxReplicating += (region.maxReplicating || 300);
        regionalCapacity[region.region].accountCount += 1;
        
        // Recovery capacity: ADD staging account servers too
        // All servers (target + staging) count toward recovery capacity
        regionalCapacity[region.region].recoveryServers += (region.totalServers || region.replicatingServers);
      });
    });
    
    // Calculate percentages and available slots
    let totalReplicating = 0;
    let totalMax = 0;
    Object.values(regionalCapacity).forEach((region) => {
      region.percentUsed = region.maxReplicating > 0 
        ? (region.replicatingServers / region.maxReplicating) * 100 
        : 0;
      region.availableSlots = region.maxReplicating - region.replicatingServers;
      
      // Calculate recovery capacity metrics
      region.recoveryPercent = region.recoveryMax > 0
        ? (region.recoveryServers / region.recoveryMax) * 100
        : 0;
      region.recoveryAvailable = region.recoveryMax - region.recoveryServers;
      
      totalReplicating += region.replicatingServers;
      totalMax += region.maxReplicating;
    });
    
    // Sort regions by name
    const sortedRegions = Object.values(regionalCapacity).sort((a, b) => 
      a.region.localeCompare(b.region)
    );
    
    targetAccountViews.push({
      accountId: targetAccount.accountId,
      accountName: targetAccount.accountName,
      totalReplicating,
      totalMax,
      totalPercent: totalMax > 0 ? (totalReplicating / totalMax) * 100 : 0,
      regions: sortedRegions,
    });
  });

  const getRegionStatus = (percentUsed: number): 'success' | 'info' | 'warning' | 'error' => {
    if (percentUsed < 67) return 'success';
    if (percentUsed < 75) return 'info';
    if (percentUsed < 83) return 'warning';
    return 'error';
  };

  const getAccountStatus = (percentUsed: number): 'success' | 'info' | 'warning' | 'error' => {
    if (percentUsed < 67) return 'success';
    if (percentUsed < 75) return 'info';
    if (percentUsed < 83) return 'warning';
    return 'error';
  };

  return (
    <Container
      header={
        <Header
          variant="h2"
          description="Replication capacity (300 max per account per region) and recovery capacity (4,000 max per account per region)"
        >
          Regional Replication Capacity
        </Header>
      }
    >
      <SpaceBetween size="l">
        {/* Summary Cards - Compact view for multiple accounts */}
        {targetAccountViews.length > 1 && (
          <ColumnLayout columns={targetAccountViews.length > 2 ? 3 : targetAccountViews.length} variant="text-grid">
            {targetAccountViews.map((targetView) => (
              <Container key={targetView.accountId}>
                <SpaceBetween size="xs">
                  <Box variant="h4">
                    {targetView.accountName}
                  </Box>
                  <CapacityGauge
                    used={targetView.totalReplicating}
                    total={targetView.totalMax}
                    size="small"
                    label={`${targetView.totalReplicating} / ${targetView.totalMax} servers`}
                  />
                  <Box textAlign="center">
                    <StatusIndicator type={getAccountStatus(targetView.totalPercent)}>
                      {targetView.regions.length} region{targetView.regions.length !== 1 ? 's' : ''}
                    </StatusIndicator>
                  </Box>
                </SpaceBetween>
              </Container>
            ))}
          </ColumnLayout>
        )}

        {/* Detailed Regional Breakdown per Target Account */}
        {targetAccountViews.length > 0 ? (
          targetAccountViews.map((targetView) => (
            <Container key={targetView.accountId}>
              <SpaceBetween size="m">
                <Box variant="h3">
                  {targetView.accountName}
                  <Box display="inline" padding={{ left: 'xs' }} color="text-body-secondary" fontSize="body-s">
                    ({targetView.accountId})
                  </Box>
                </Box>
                
                {targetView.regions.length > 0 ? (
                  <ColumnLayout columns={Math.min(targetView.regions.length, 4)} variant="text-grid">
                    {targetView.regions.map((region) => (
                      <div key={region.region}>
                        <SpaceBetween size="s">
                          <Box variant="h5">{region.region}</Box>
                          
                          {/* Replication Capacity */}
                          <div>
                            <Box textAlign="center" variant="small" color="text-body-secondary" padding={{ bottom: 'xxs' }}>
                              Replication: {region.replicatingServers} / {region.maxReplicating} servers
                              {region.accountCount > 1 && ` (${region.accountCount} accounts)`}
                            </Box>
                            <CapacityGauge
                              used={region.replicatingServers}
                              total={region.maxReplicating}
                              size="small"
                              label={`${region.percentUsed.toFixed(1)}%`}
                            />
                            <Box textAlign="center" padding={{ top: 'xxs' }}>
                              <Box variant="small" color="text-body-secondary">
                                {region.availableSlots} available
                              </Box>
                            </Box>
                          </div>
                          
                          {/* Recovery Capacity */}
                          <div>
                            <Box textAlign="center" variant="small" color="text-body-secondary" padding={{ bottom: 'xxs' }}>
                              Recovery: {region.recoveryServers} / {region.recoveryMax.toLocaleString()} servers
                            </Box>
                            <CapacityGauge
                              used={region.recoveryServers}
                              total={region.recoveryMax}
                              size="small"
                              label={`${region.recoveryPercent.toFixed(1)}%`}
                            />
                            <Box textAlign="center" padding={{ top: 'xxs' }}>
                              <Box variant="small" color="text-body-secondary">
                                {region.recoveryAvailable.toLocaleString()} available
                              </Box>
                            </Box>
                          </div>
                        </SpaceBetween>
                      </div>
                    ))}
                  </ColumnLayout>
                ) : (
                  <Box textAlign="center" padding="l" color="text-body-secondary">
                    No active regions
                  </Box>
                )}
              </SpaceBetween>
            </Container>
          ))
        ) : (
          <Box textAlign="center" padding="l" color="text-body-secondary">
            No target accounts configured
          </Box>
        )}
      </SpaceBetween>
    </Container>
  );
};
