/**
 * System Status Page
 * 
 * Comprehensive system health view including:
 * - Detailed DRS capacity breakdown
 * - Paused/waiting executions
 * - System warnings and alerts
 * - Regional capacity distribution
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  SpaceBetween,
  Container,
  Header,
  StatusIndicator,
  Spinner,
  Alert,
  Link,
} from '@cloudscape-design/components';
import { useNavigate } from 'react-router-dom';
import { ContentLayout } from '../components/cloudscape/ContentLayout';
import { PageTransition } from '../components/PageTransition';
import { CapacityDashboard } from '../components/CapacityDashboard';
import { AccountRequiredWrapper } from '../components/AccountRequiredWrapper';
import { useAccount } from '../contexts/AccountContext';
import apiClient from '../services/api';
import type { ExecutionListItem } from '../types';

export const SystemStatusPage: React.FC = () => {
  const navigate = useNavigate();
  const { selectedAccount, getCurrentAccountId } = useAccount();
  
  const [executions, setExecutions] = useState<ExecutionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchExecutions = useCallback(async () => {
    const accountId = getCurrentAccountId();
    if (!accountId) {
      setLoading(false);
      return;
    }

    try {
      const response = await apiClient.listExecutions({ 
        limit: 100,
        accountId 
      });
      setExecutions(Array.isArray(response?.items) ? response.items : []);
      setError(null);
    } catch (err) {
      setError('Failed to load executions');
      console.error('Error fetching executions:', err);
    } finally {
      setLoading(false);
    }
  }, [getCurrentAccountId]);

  useEffect(() => {
    fetchExecutions();
    const interval = setInterval(fetchExecutions, 30000);
    return () => clearInterval(interval);
  }, [fetchExecutions]);

  // Find paused executions
  const pausedExecutions = executions.filter(
    (e) => e.status === 'PAUSED' || e.status === 'paused'
  );

  // Find executions waiting for action
  const waitingExecutions = executions.filter(
    (e) => e.status === 'PENDING' || e.status === 'pending'
  );

  return (
    <PageTransition>
      <ContentLayout
        header={
          <Header
            variant="h1"
            description="Comprehensive system health and capacity monitoring"
          >
            System Status
          </Header>
        }
      >
        <AccountRequiredWrapper pageName="system status">
          {loading ? (
            <Box textAlign="center" padding="xxl">
              <Spinner size="large" />
            </Box>
          ) : error ? (
            <Container>
              <StatusIndicator type="error">{error}</StatusIndicator>
            </Container>
          ) : (
            <SpaceBetween size="l">
              {/* Alerts Section */}
              {(pausedExecutions.length > 0 || waitingExecutions.length > 0) && (
                <Container header={<Header variant="h2">Alerts</Header>}>
                  <SpaceBetween size="m">
                    {pausedExecutions.length > 0 && (
                      <Alert
                        type="warning"
                        header={`${pausedExecutions.length} execution${pausedExecutions.length > 1 ? 's' : ''} paused`}
                        action={
                          <Link onFollow={() => navigate('/executions')}>
                            View executions
                          </Link>
                        }
                      >
                        The following executions are paused and waiting for resume:
                        <Box padding={{ top: 's' }}>
                          <SpaceBetween size="xs">
                            {pausedExecutions.map((exec) => (
                              <Link
                                key={exec.executionId}
                                onFollow={() =>
                                  navigate(`/executions/${exec.executionId}`)
                                }
                              >
                                {exec.recoveryPlanName || exec.recoveryPlanId}
                              </Link>
                            ))}
                          </SpaceBetween>
                        </Box>
                      </Alert>
                    )}

                    {waitingExecutions.length > 0 && (
                      <Alert
                        type="info"
                        header={`${waitingExecutions.length} execution${waitingExecutions.length > 1 ? 's' : ''} pending`}
                      >
                        {waitingExecutions.length} execution
                        {waitingExecutions.length > 1 ? 's are' : ' is'} waiting
                        to start
                      </Alert>
                    )}
                  </SpaceBetween>
                </Container>
              )}

              {/* Detailed Capacity Dashboard */}
              <Container
                header={
                  <Header
                    variant="h2"
                    description="Combined capacity across target and staging accounts with regional breakdown"
                  >
                    DRS Capacity Details
                  </Header>
                }
              >
                {selectedAccount ? (
                  <CapacityDashboard
                    targetAccountId={getCurrentAccountId() || ''}
                    refreshInterval={30000}
                  />
                ) : (
                  <Box textAlign="center" padding="l" color="text-body-secondary">
                    Select a target account to view capacity
                  </Box>
                )}
              </Container>
            </SpaceBetween>
          )}
        </AccountRequiredWrapper>
      </ContentLayout>
    </PageTransition>
  );
};
