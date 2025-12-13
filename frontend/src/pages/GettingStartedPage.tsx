import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  SpaceBetween,
  Button,
  Container,
  Header,
  Icon,
  Link,
  ColumnLayout,
} from '@cloudscape-design/components';
import { ContentLayout } from '../components/cloudscape/ContentLayout';
import { PageTransition } from '../components/PageTransition';

const stepCardStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'flex-start',
  gap: '16px',
  padding: '16px 0',
};

const stepNumberStyle: React.CSSProperties = {
  width: '36px',
  height: '36px',
  borderRadius: '50%',
  backgroundColor: '#0972d3',
  color: 'white',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontWeight: 'bold',
  fontSize: '16px',
  flexShrink: 0,
};

const tipStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '8px',
};

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
          {/* Navigation Cards */}
          <ColumnLayout columns={3} variant="default">
            <Container
              header={
                <Header variant="h2">
                  <SpaceBetween direction="horizontal" size="xs">
                    <Icon name="group-active" />
                    <span>Protection Groups</span>
                  </SpaceBetween>
                </Header>
              }
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

            <Container
              header={
                <Header variant="h2">
                  <SpaceBetween direction="horizontal" size="xs">
                    <Icon name="script" />
                    <span>Recovery Plans</span>
                  </SpaceBetween>
                </Header>
              }
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

            <Container
              header={
                <Header variant="h2">
                  <SpaceBetween direction="horizontal" size="xs">
                    <Icon name="status-in-progress" />
                    <span>Execution History</span>
                  </SpaceBetween>
                </Header>
              }
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
          </ColumnLayout>

          {/* Quick Start Guide */}
          <Container
            header={
              <Header variant="h2">
                Quick Start Guide
              </Header>
            }
          >
            <SpaceBetween size="m">
              {/* Step 1 */}
              <div style={stepCardStyle}>
                <div style={stepNumberStyle}>1</div>
                <SpaceBetween size="xxs">
                  <Box variant="h3">Create a Protection Group</Box>
                  <Box color="text-body-secondary">
                    Go to <Link onFollow={() => navigate('/protection-groups')}>Protection Groups</Link> → Create Group → Select region → Add servers from discovery panel.
                  </Box>
                </SpaceBetween>
              </div>

              {/* Step 2 */}
              <div style={stepCardStyle}>
                <div style={stepNumberStyle}>2</div>
                <SpaceBetween size="xxs">
                  <Box variant="h3">Design a Recovery Plan</Box>
                  <Box color="text-body-secondary">
                    Go to <Link onFollow={() => navigate('/recovery-plans')}>Recovery Plans</Link> → Create Plan → Add waves in recovery order → Set dependencies and pause points.
                  </Box>
                </SpaceBetween>
              </div>

              {/* Step 3 */}
              <div style={stepCardStyle}>
                <div style={stepNumberStyle}>3</div>
                <SpaceBetween size="xxs">
                  <Box variant="h3">Execute a Drill or Recovery</Box>
                  <Box color="text-body-secondary">
                    From Recovery Plans, select "Run Drill" (testing) or "Run Recovery" (failover) → Monitor progress → Resume at pause points → Terminate instances after drills.
                  </Box>
                </SpaceBetween>
              </div>
            </SpaceBetween>
          </Container>

          {/* Best Practices */}
          <Container
            header={
              <Header variant="h2">
                <SpaceBetween direction="horizontal" size="xs">
                  <Icon name="status-positive" />
                  <span>Best Practices</span>
                </SpaceBetween>
              </Header>
            }
          >
            <ColumnLayout columns={2} variant="text-grid">
              <div style={tipStyle}>
                <Icon name="check" variant="success" />
                <Box color="text-body-secondary">Run drills regularly to validate recovery plans</Box>
              </div>
              <div style={tipStyle}>
                <Icon name="check" variant="success" />
                <Box color="text-body-secondary">Use pause points to verify each tier is healthy</Box>
              </div>
              <div style={tipStyle}>
                <Icon name="check" variant="success" />
                <Box color="text-body-secondary">Group servers by application tier</Box>
              </div>
              <div style={tipStyle}>
                <Icon name="check" variant="success" />
                <Box color="text-body-secondary">Terminate drill instances to avoid costs</Box>
              </div>
            </ColumnLayout>
          </Container>
        </SpaceBetween>
      </ContentLayout>
    </PageTransition>
  );
};
