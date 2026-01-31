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
  Alert,
  Spinner,
} from '@cloudscape-design/components';
import { ContentLayout } from '../components/cloudscape/ContentLayout';
import { PageTransition } from '../components/PageTransition';
import { useAccount } from '../contexts/AccountContext';
import { useSettings } from '../contexts/SettingsContext';

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
  const { availableAccounts, accountsLoading, getCurrentAccountId, refreshAccounts } = useAccount();
  const { openSettingsModal } = useSettings();
  
  const currentAccountId = getCurrentAccountId();
  const currentAccount = availableAccounts.find(acc => acc.accountId === currentAccountId);
  const hasAccounts = availableAccounts.length > 0;
  
  React.useEffect(() => {
    refreshAccounts();
  }, [refreshAccounts]);
  
  if (accountsLoading) {
    return (
      <PageTransition>
        <ContentLayout
          header={
            <Header variant="h1" description="AWS Disaster Recovery Service Orchestration Platform">
              Getting Started
            </Header>
          }
        >
          <Container>
            <Box textAlign="center" padding="xxl">
              <Spinner size="large" />
              <Box variant="p" color="text-body-secondary" margin={{ top: 's' }}>
                Loading...
              </Box>
            </Box>
          </Container>
        </ContentLayout>
      </PageTransition>
    );
  }

  if (!hasAccounts) {
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
            <Alert
              type="info"
              header="Welcome to AWS DRS Orchestration Platform"
              action={
                <Button
                  onClick={() => openSettingsModal('accounts')}
                  variant="primary"
                  iconName="add-plus"
                >
                  Add Target Account
                </Button>
              }
            >
              To get started, you need to add at least one target account where your DRS source servers are replicating.
            </Alert>

            <Container
              header={
                <Header variant="h2">
                  Quick Setup
                </Header>
              }
            >
              <SpaceBetween size="l">
                <div style={stepCardStyle}>
                  <div style={stepNumberStyle}>1</div>
                  <SpaceBetween size="xxs">
                    <Box variant="h3">Add Your First Target Account</Box>
                    <Box color="text-body-secondary">
                      Click the <strong>Add Target Account</strong> button above to configure your first target account where DRS source servers are replicating.
                    </Box>
                  </SpaceBetween>
                </div>

                <div style={stepCardStyle}>
                  <div style={stepNumberStyle}>2</div>
                  <SpaceBetween size="xxs">
                    <Box variant="h3">Review Capacity Dashboard</Box>
                    <Box color="text-body-secondary">
                      After adding an account, view your DRS capacity and server status on the dashboard.
                    </Box>
                  </SpaceBetween>
                </div>

                <div style={stepCardStyle}>
                  <div style={stepNumberStyle}>3</div>
                  <SpaceBetween size="xxs">
                    <Box variant="h3">Create Protection Groups</Box>
                    <Box color="text-body-secondary">
                      Organize your source servers into protection groups for easier management.
                    </Box>
                  </SpaceBetween>
                </div>

                <div style={stepCardStyle}>
                  <div style={stepNumberStyle}>4</div>
                  <SpaceBetween size="xxs">
                    <Box variant="h3">Build Recovery Plans</Box>
                    <Box color="text-body-secondary">
                      Create recovery plans with multiple waves to orchestrate your DR operations.
                    </Box>
                  </SpaceBetween>
                </div>
              </SpaceBetween>
            </Container>

            <Container
              header={
                <Header variant="h2">Prerequisites</Header>
              }
            >
              <SpaceBetween size="m">
                <Box variant="p">
                  Before adding accounts, ensure you have:
                </Box>
                <ul>
                  <li>
                    <strong>AWS DRS Initialized:</strong> DRS must be initialized in at least one region of your target account
                  </li>
                  <li>
                    <strong>Cross-Account IAM Role:</strong> Deploy the <code>DRSOrchestrationRole</code> in each target/staging account
                  </li>
                  <li>
                    <strong>Source Servers:</strong> At least one source server configured for replication in DRS
                  </li>
                </ul>
              </SpaceBetween>
            </Container>
          </SpaceBetween>
        </ContentLayout>
      </PageTransition>
    );
  }

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
          {currentAccount && (
            <Alert
              type="success"
              header="Account Configured"
            >
              <SpaceBetween size="s">
                <Box>
                  Your account is configured for DRS orchestration. 
                  You can now create protection groups and recovery plans.
                </Box>
                <Box>
                  <strong>Selected Account:</strong> {currentAccount.accountName || currentAccount.accountId} ({currentAccount.accountId})
                </Box>
              </SpaceBetween>
            </Alert>
          )}

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
