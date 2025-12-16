import React from 'react';
import {
  Box,
  SpaceBetween,
  Container,
  Header,
  Button,
  Alert,
  Spinner,
} from '@cloudscape-design/components';
import { useNavigate } from 'react-router-dom';
import { ContentLayout } from '../components/cloudscape/ContentLayout';
import { PageTransition } from '../components/PageTransition';
import { useAccount } from '../contexts/AccountContext';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { availableAccounts, accountsLoading } = useAccount();
  
  // Check if no target accounts are configured (only after loading is complete)
  const hasNoAccounts = !accountsLoading && availableAccounts.length === 0;

  // Show loading state while accounts are being fetched
  if (accountsLoading) {
    return (
      <PageTransition>
        <ContentLayout
          header={
            <Header
              variant="h1"
              description="Real-time execution status and system metrics"
            >
              Dashboard
            </Header>
          }
        >
          <Container>
            <Box textAlign="center" padding="xxl">
              <Spinner size="large" />
              <Box variant="p" color="text-body-secondary" margin={{ top: 's' }}>
                Loading dashboard...
              </Box>
            </Box>
          </Container>
        </ContentLayout>
      </PageTransition>
    );
  }

  // Empty state when no target accounts are configured
  if (hasNoAccounts) {
    return (
      <PageTransition>
        <ContentLayout
          header={
            <Header
              variant="h1"
              description="Real-time execution status and system metrics"
            >
              Dashboard
            </Header>
          }
        >
          <Container>
            <SpaceBetween size="l">
              <Alert
                type="info"
                header="No Target Accounts Configured"
              >
                <SpaceBetween size="m">
                  <Box>
                    To get started with AWS DRS Orchestration, you need to configure at least one target account where your DRS source servers are located.
                  </Box>
                  
                  <Box variant="h3">Setup Options:</Box>
                  
                  <SpaceBetween size="s">
                    <Box>
                      <Box variant="strong">Same Account Setup (Recommended for single account):</Box>
                      <Box color="text-body-secondary">
                        If your DRS source servers are in the same AWS account as this orchestration solution, 
                        simply add your current account without specifying a cross-account role ARN. 
                        Leave the role field empty - no additional IAM configuration needed.
                      </Box>
                    </Box>
                    
                    <Box>
                      <Box variant="strong">Cross-Account Setup (For multi-account environments):</Box>
                      <Box color="text-body-secondary">
                        If your DRS source servers are in different AWS accounts, you'll need to create 
                        cross-account IAM roles with DRS permissions and specify the role ARN when adding each account.
                      </Box>
                    </Box>
                  </SpaceBetween>
                  
                  <Box>
                    <Button 
                      variant="primary" 
                      iconName="add-plus"
                      onClick={() => navigate('/getting-started')}
                    >
                      Get Started
                    </Button>
                  </Box>
                </SpaceBetween>
              </Alert>
            </SpaceBetween>
          </Container>
        </ContentLayout>
      </PageTransition>
    );
  }

  // Regular dashboard when accounts are configured
  return (
    <PageTransition>
      <ContentLayout
        header={
          <Header
            variant="h1"
            description="Real-time execution status and system metrics"
          >
            Dashboard
          </Header>
        }
      >
        <Container>
          <Box>Dashboard content will be shown here when accounts are configured.</Box>
        </Container>
      </ContentLayout>
    </PageTransition>
  );
};