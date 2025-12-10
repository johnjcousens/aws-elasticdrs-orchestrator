import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  SpaceBetween,
  Button,
  Container,
  Header,
  Grid,
  Icon,
  Link,
} from '@cloudscape-design/components';
import { ContentLayout } from '../components/cloudscape/ContentLayout';
import { PageTransition } from '../components/PageTransition';

const cardGridStyle: React.CSSProperties = { 
  display: 'grid', 
  gridTemplateColumns: 'repeat(3, 1fr)', 
  gap: '20px'
};
const cardWrapperStyle: React.CSSProperties = { 
  display: 'flex',
  flexDirection: 'column'
};
const containerWrapperStyle: React.CSSProperties = {
  flex: 1,
  display: 'flex',
  flexDirection: 'column'
};
const dividerStyle: React.CSSProperties = { border: 'none', borderTop: '1px solid #e9ebed', margin: '8px 0' };

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
          <div style={cardGridStyle}>
            <div style={cardWrapperStyle}>
              <div style={containerWrapperStyle}>
                <Container
                  header={
                    <Header variant="h2">
                      <SpaceBetween direction="horizontal" size="xs">
                        <Icon name="folder" />
                        <span>Protection Groups</span>
                      </SpaceBetween>
                    </Header>
                  }
                  fitHeight
                >
                  <SpaceBetween size="m">
                    <Box color="text-body-secondary">
                      Group DRS servers for coordinated recovery.
                    </Box>
                    <Button onClick={() => navigate('/protection-groups')} variant="primary" fullWidth>
                      View Protection Groups
                    </Button>
                  </SpaceBetween>
                </Container>
              </div>
            </div>

            <div style={cardWrapperStyle}>
              <div style={containerWrapperStyle}>
                <Container
                  header={
                    <Header variant="h2">
                      <SpaceBetween direction="horizontal" size="xs">
                        <Icon name="file" />
                        <span>Recovery Plans</span>
                      </SpaceBetween>
                    </Header>
                  }
                  fitHeight
                >
                  <SpaceBetween size="m">
                    <Box color="text-body-secondary">
                      Design multi-wave recovery sequences.
                    </Box>
                    <Button onClick={() => navigate('/recovery-plans')} variant="primary" fullWidth>
                      View Recovery Plans
                    </Button>
                  </SpaceBetween>
                </Container>
              </div>
            </div>

            <div style={cardWrapperStyle}>
              <div style={containerWrapperStyle}>
                <Container
                  header={
                    <Header variant="h2">
                      <SpaceBetween direction="horizontal" size="xs">
                        <Icon name="status-in-progress" />
                        <span>Execution History</span>
                      </SpaceBetween>
                    </Header>
                  }
                  fitHeight
                >
                  <SpaceBetween size="m">
                    <Box color="text-body-secondary">
                      Monitor and manage recovery executions.
                    </Box>
                    <Button onClick={() => navigate('/executions')} variant="primary" fullWidth>
                      View Executions
                    </Button>
                  </SpaceBetween>
                </Container>
              </div>
            </div>
          </div>

          <Container
            header={
              <Header variant="h2" description="Follow these steps to set up your first disaster recovery plan">
                Quick Start Guide
              </Header>
            }
          >
            <SpaceBetween size="l">
              <Grid gridDefinition={[{ colspan: 1 }, { colspan: 11 }]}>
                <Box textAlign="center">
                  <Box fontSize="heading-xl" fontWeight="bold" color="text-status-info">1</Box>
                </Box>
                <SpaceBetween size="xs">
                  <Box variant="h3">Create a Protection Group</Box>
                  <Box color="text-body-secondary">
                    Protection Groups organize your DRS source servers into logical units. Each server can only belong to one group to prevent recovery conflicts.
                  </Box>
                  <SpaceBetween size="xs">
                    <Box color="text-body-secondary">
                      <Icon name="angle-right" /> Navigate to <Link onFollow={() => navigate('/protection-groups')}>Protection Groups</Link> and click "Create Group"
                    </Box>
                    <Box color="text-body-secondary">
                      <Icon name="angle-right" /> Select a region where your DRS source servers are located
                    </Box>
                    <Box color="text-body-secondary">
                      <Icon name="angle-right" /> Give your group a descriptive name (e.g., "Database Servers", "Web Tier")
                    </Box>
                    <Box color="text-body-secondary">
                      <Icon name="angle-right" /> Select servers from the discovery panel - only servers with healthy replication are shown
                    </Box>
                  </SpaceBetween>
                </SpaceBetween>
              </Grid>

              <hr style={dividerStyle} />

              <Grid gridDefinition={[{ colspan: 1 }, { colspan: 11 }]}>
                <Box textAlign="center">
                  <Box fontSize="heading-xl" fontWeight="bold" color="text-status-info">2</Box>
                </Box>
                <SpaceBetween size="xs">
                  <Box variant="h3">Design a Recovery Plan</Box>
                  <Box color="text-body-secondary">
                    Recovery Plans define the sequence of waves for orchestrated recovery. Each wave can reference a different Protection Group and execute in order.
                  </Box>
                  <SpaceBetween size="xs">
                    <Box color="text-body-secondary">
                      <Icon name="angle-right" /> Navigate to <Link onFollow={() => navigate('/recovery-plans')}>Recovery Plans</Link> and click "Create Plan"
                    </Box>
                    <Box color="text-body-secondary">
                      <Icon name="angle-right" /> Give your plan a name (e.g., "Production DR Plan", "App Stack Recovery")
                    </Box>
                    <Box color="text-body-secondary">
                      <Icon name="angle-right" /> Add waves in the order you want servers recovered (e.g., Wave 1: Databases, Wave 2: App Servers)
                    </Box>
                    <Box color="text-body-secondary">
                      <Icon name="angle-right" /> For each wave, select a Protection Group and choose servers to include
                    </Box>
                    <Box color="text-body-secondary">
                      <Icon name="angle-right" /> Set "Depends On" to specify which wave must complete before this wave starts
                    </Box>
                    <Box color="text-body-secondary">
                      <Icon name="angle-right" /> Enable "Pause Before Wave" on any wave where you want to validate before continuing
                    </Box>
                  </SpaceBetween>
                </SpaceBetween>
              </Grid>

              <hr style={dividerStyle} />

              <Grid gridDefinition={[{ colspan: 1 }, { colspan: 11 }]}>
                <Box textAlign="center">
                  <Box fontSize="heading-xl" fontWeight="bold" color="text-status-info">3</Box>
                </Box>
                <SpaceBetween size="xs">
                  <Box variant="h3">Execute a Drill or Recovery</Box>
                  <Box color="text-body-secondary">
                    Test your plan with a Drill (non-disruptive) or execute an actual Recovery when disaster strikes.
                  </Box>
                  <SpaceBetween size="xs">
                    <Box color="text-body-secondary">
                      <Icon name="angle-right" /> From the Recovery Plans page, click the actions menu on your plan
                    </Box>
                    <Box color="text-body-secondary">
                      <Icon name="angle-right" /> Select "Run Drill" for testing or "Run Recovery" for actual failover
                    </Box>
                    <Box color="text-body-secondary">
                      <Icon name="angle-right" /> Monitor progress in real-time on the Execution Details page
                    </Box>
                    <Box color="text-body-secondary">
                      <Icon name="angle-right" /> If you enabled pause points, click "Resume" when ready to continue
                    </Box>
                    <Box color="text-body-secondary">
                      <Icon name="angle-right" /> After a successful drill, use "Terminate Instances" to clean up
                    </Box>
                  </SpaceBetween>
                </SpaceBetween>
              </Grid>

              <hr style={dividerStyle} />

              <Grid gridDefinition={[{ colspan: 1 }, { colspan: 11 }]}>
                <Box textAlign="center">
                  <Box fontSize="heading-xl" fontWeight="bold" color="text-status-success">
                    <Icon name="status-positive" size="big" />
                  </Box>
                </Box>
                <SpaceBetween size="xs">
                  <Box variant="h3">Best Practices</Box>
                  <SpaceBetween size="xs">
                    <Box color="text-body-secondary">
                      <Icon name="status-positive" /> Run drills regularly to validate your recovery plans work as expected
                    </Box>
                    <Box color="text-body-secondary">
                      <Icon name="status-positive" /> Use pause points between waves to verify each tier is healthy
                    </Box>
                    <Box color="text-body-secondary">
                      <Icon name="status-positive" /> Keep Protection Groups focused - group servers by application tier
                    </Box>
                    <Box color="text-body-secondary">
                      <Icon name="status-positive" /> Review execution history to identify and fix recurring issues
                    </Box>
                    <Box color="text-body-secondary">
                      <Icon name="status-positive" /> Always terminate drill instances after testing to avoid costs
                    </Box>
                  </SpaceBetween>
                </SpaceBetween>
              </Grid>
            </SpaceBetween>
          </Container>
        </SpaceBetween>
      </ContentLayout>
    </PageTransition>
  );
};
