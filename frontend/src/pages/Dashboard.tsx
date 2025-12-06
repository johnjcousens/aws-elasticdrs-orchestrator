/**
 * Dashboard Page Component
 * 
 * Main dashboard showing overview of DRS orchestration status.
 * Displays protection groups, recovery plans, and recent executions.
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  SpaceBetween,
  Button,
  Container,
  Header,
  ColumnLayout,
} from '@cloudscape-design/components';
import { ContentLayout } from '../components/cloudscape/ContentLayout';
import { PageTransition } from '../components/PageTransition';

/**
 * Dashboard Page
 * 
 * Landing page after authentication showing system overview.
 */
export const Dashboard: React.FC = () => {
  const navigate = useNavigate();

  return (
    <PageTransition>
      <ContentLayout
        header={
          <Header
            variant="h1"
            description="AWS Disaster Recovery Service Orchestration Platform"
          >
            Dashboard
          </Header>
        }
      >
        <SpaceBetween size="l">
          {/* Quick Action Cards */}
          <ColumnLayout columns={3} variant="text-grid">
            {/* Protection Groups Card */}
            <Container
              header={
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '24px' }}>🛡️</span>
                  <Header variant="h2">Protection Groups</Header>
                </div>
              }
            >
              <SpaceBetween size="m">
                <div style={{ color: '#5f6b7a' }}>
                  Manage and configure protection groups for disaster recovery.
                </div>
                <Button
                  onClick={() => navigate('/protection-groups')}
                  fullWidth
                >
                  View Protection Groups
                </Button>
              </SpaceBetween>
            </Container>

            {/* Recovery Plans Card */}
            <Container
              header={
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '24px' }}>🗺️</span>
                  <Header variant="h2">Recovery Plans</Header>
                </div>
              }
            >
              <SpaceBetween size="m">
                <div style={{ color: '#5f6b7a' }}>
                  Design and manage multi-wave recovery orchestration plans.
                </div>
                <Button
                  onClick={() => navigate('/recovery-plans')}
                  fullWidth
                >
                  View Recovery Plans
                </Button>
              </SpaceBetween>
            </Container>

            {/* Execution History Card */}
            <Container
              header={
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '24px' }}>▶️</span>
                  <Header variant="h2">Execution History</Header>
                </div>
              }
            >
              <SpaceBetween size="m">
                <div style={{ color: '#5f6b7a' }}>
                  View active recoveries and historical execution records.
                </div>
                <Button
                  onClick={() => navigate('/executions')}
                  fullWidth
                >
                  View Executions
                </Button>
              </SpaceBetween>
            </Container>
          </ColumnLayout>

          {/* Quick Start Guide */}
          <Container header={<Header variant="h2">Quick Start Guide</Header>}>
            <SpaceBetween size="s">
              <div>
                <strong>Step 1:</strong> Create a Protection Group to define which servers to protect
              </div>
              <div>
                <strong>Step 2:</strong> Design a Recovery Plan with orchestrated waves
              </div>
              <div>
                <strong>Step 3:</strong> Execute the Recovery Plan when needed
              </div>
            </SpaceBetween>
          </Container>
        </SpaceBetween>
      </ContentLayout>
    </PageTransition>
  );
};
