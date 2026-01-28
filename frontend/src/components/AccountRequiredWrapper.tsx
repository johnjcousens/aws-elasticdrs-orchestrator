/**
 * Account Required Wrapper Component
 * 
 * Blocks page content when no account is selected and shows helpful guidance.
 * Used to enforce account selection across all protected pages.
 */

import React from 'react';
import {
  Container,
  Header,
  SpaceBetween,
  Box,
  StatusIndicator,
  Alert,
} from '@cloudscape-design/components';
import { useAccount } from '../contexts/AccountContext';

interface AccountRequiredWrapperProps {
  children: React.ReactNode;
  pageName?: string;
}

export const AccountRequiredWrapper: React.FC<AccountRequiredWrapperProps> = ({
  children,
  pageName = 'this page',
}) => {
  const {
    availableAccounts,
    accountsLoading,
    accountsError,
    hasSelectedAccount,
  } = useAccount();

  // Show loading state
  if (accountsLoading) {
    return (
      <Container>
        <Box textAlign="center" padding="xxl">
          <SpaceBetween size="m">
            <StatusIndicator type="loading">Loading accounts...</StatusIndicator>
            <Box variant="p" color="text-body-secondary">
              Please wait while we load your target accounts.
            </Box>
          </SpaceBetween>
        </Box>
      </Container>
    );
  }

  // Show error state
  if (accountsError) {
    return (
      <Container>
        <Box textAlign="center" padding="xxl">
          <SpaceBetween size="l">
            <StatusIndicator type="error">Account Loading Error</StatusIndicator>
            <Alert type="error" header="Unable to load accounts">
              {accountsError}
            </Alert>
            <Box variant="p" color="text-body-secondary">
              Please refresh the page or contact support if the problem persists.
            </Box>
          </SpaceBetween>
        </Box>
      </Container>
    );
  }

  // Show no accounts state - Setup Wizard
  if (!Array.isArray(availableAccounts) || availableAccounts.length === 0) {
    return (
      <Container
        header={
          <Header variant="h2">
            Welcome to DRS Orchestration
          </Header>
        }
      >
        <SpaceBetween size="l">
          <Alert type="info" header="Setup Required">
            Let's get you started by adding your first target account.
          </Alert>
          
          <Box>
            <SpaceBetween size="l">
              <Box variant="h3">What is a target account?</Box>
              <Box variant="p">
                A target account is an AWS account that contains the DRS source servers you want to orchestrate for disaster recovery.
              </Box>
              
              <Box variant="h3">Quick Setup:</Box>
              <SpaceBetween size="m">
                <Box variant="p">
                  <strong>Step 1:</strong> Click the Settings gear icon (⚙️) in the top navigation bar
                </Box>
                <Box variant="p">
                  <strong>Step 2:</strong> Go to the "Account Management" tab
                </Box>
                <Box variant="p">
                  <strong>Step 3:</strong> Click "Add Target Account" and enter your account details
                </Box>
                <Box variant="p">
                  <strong>Step 4:</strong> Save and start using DRS orchestration features
                </Box>
              </SpaceBetween>
              
              <Alert type="success" header="Pro Tip">
                If this solution is deployed in the same account as your DRS source servers, 
                just add that account ID with no cross-account role required.
              </Alert>
            </SpaceBetween>
          </Box>
        </SpaceBetween>
      </Container>
    );
  }

  // CRITICAL: Single account auto-selection logic
  // If only one account exists, it should be auto-selected as default
  // Multiple accounts require explicit selection (enforcement only for this case)
  if (Array.isArray(availableAccounts) && availableAccounts.length > 1 && !hasSelectedAccount) {
    return (
      <Container
        header={
          <Header variant="h2">
            Select Target Account
          </Header>
        }
      >
        <SpaceBetween size="l">
          <Alert type="info" header="Choose your target account">
            Please select which target account you want to work with for {pageName}.
          </Alert>
          
          <Box>
            <SpaceBetween size="m">
              <Box variant="h3">Available target accounts ({availableAccounts.length}):</Box>
              {availableAccounts.map(account => (
                <Box key={account.accountId} padding="s" variant="div">
                  <SpaceBetween size="xs">
                    <Box variant="strong">
                      {account.accountName || account.accountId}
                      {account.isCurrentAccount && ' (Current Account)'}
                    </Box>
                    <Box variant="small" color="text-body-secondary">
                      Account ID: {account.accountId}
                    </Box>
                  </SpaceBetween>
                </Box>
              ))}
              
              <Box variant="h3">How to select:</Box>
              <Box variant="p">
                Use the <strong>account selector dropdown</strong> in the top navigation bar to choose 
                which target account you want to work with. All features will then be available for that account.
              </Box>
              
              <Box variant="p" color="text-body-secondary">
                <strong>Tip:</strong> Set a default account preference in Settings → Account Management 
                to make selection easier next time.
              </Box>
            </SpaceBetween>
          </Box>
        </SpaceBetween>
      </Container>
    );
  }

  // Account is selected OR single account (auto-selected) - show normal content
  return <>{children}</>;
};