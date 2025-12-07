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

export const GettingStartedPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <PageTransition>
      <ContentLayout
        header={
          <Header variant="h1" description="AWS Disaster Recovery Service Orchestration Platform">
            Getting Started
          </Header>
        }
      >
        <SpaceBetween size="l">
          <ColumnLayout columns={3} variant="text-grid">
            <Container header={<Header variant="h2">Protection Groups</Header>}>
              <SpaceBetween size="m">
                <Box color="text-body-secondary">
                  Manage and configure protection groups for disaster recovery.
                </Box>
                <Button onClick={() => navigate('/protection-groups')} fullWidth>
                  View Protection Groups
                </Button>
              </SpaceBetween>
            </Container>

            <Container header={<Header variant="h2">Recovery Plans</Header>}>
              <SpaceBetween size="m">
                <Box color="text-body-secondary">
                  Design and manage multi-wave recovery orchestration plans.
                </Box>
                <Button onClick={() => navigate('/recovery-plans')} fullWidth>
                  View Recovery Plans
                </Button>
              </SpaceBetween>
            </Container>

            <Container header={<Header variant="h2">History</Header>}>
              <SpaceBetween size="m">
                <Box color="text-body-secondary">
                  View active recoveries and historical records.
                </Box>
                <Button onClick={() => navigate('/executions')} fullWidth>
                  View History
                </Button>
              </SpaceBetween>
            </Container>
          </ColumnLayout>

          <Container header={<Header variant="h2">Quick Start Guide</Header>}>
            <SpaceBetween size="m">
              <Box>
                <Box variant="strong">Step 1: Create a Protection Group</Box>
                <Box color="text-body-secondary">
                  Define which servers to protect by discovering DRS source servers and grouping them logically.
                </Box>
              </Box>
              <Box>
                <Box variant="strong">Step 2: Design a Recovery Plan</Box>
                <Box color="text-body-secondary">
                  Create orchestrated waves with dependencies to control recovery sequence.
                </Box>
              </Box>
              <Box>
                <Box variant="strong">Step 3: Execute Recovery</Box>
                <Box color="text-body-secondary">
                  Run drills to test your plan or execute actual recovery when needed.
                </Box>
              </Box>
            </SpaceBetween>
          </Container>
        </SpaceBetween>
      </ContentLayout>
    </PageTransition>
  );
};
