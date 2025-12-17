/**
 * Account Required Guard
 * 
 * Blocks functionality until a target account is selected.
 * Shows a helpful message with account selection options.
 */

import React from 'react';
import {
  Box,
  SpaceBetween,
  Alert,
  Button,
  Header,
  Container,
  FormField,
  Spinner,
} from '@cloudscape-design/components';
import { AccountSelector } from './AccountSelector';
import { useAccount } from '../contexts/AccountContext';

interface AccountRequiredGuardProps {
  children: React.ReactNode;
  feature?: string; // Name of the feature being blocked
}

export const AccountRequiredGuard: React.FC<AccountRequiredGuardProps> = ({
  children,
  feature = 'this feature',
}) => {
  const { selectedAccount, availableAccounts, accountsLoading } = useAccount();

  // Show loading state while accounts are being fetched
  if (accountsLoading) {
    return (
      <Box textAlign="center" padding="xxl">
        <SpaceBetween size="m">
          <Spinner size="large" />
          <div>Loading target accounts...</div>
        </SpaceBetween>
      </Box>
    );
  }

  // Show no accounts message if none are available
  if (availableAccounts.length === 0) {
    return (
      <Container
        header={<Header variant="h2">No Target Accounts Available</Header>}
      >
        <SpaceBetween size="l">
          <Alert type="warning">
            <strong>Target accounts must be configured before you can use {feature}.</strong>
            <br />
            Contact your administrator to set up target accounts for DRS operations.
          </Alert>
          
          <Box textAlign="center">
            <Button
              variant="primary"
              onClick={() => window.location.reload()}
              iconName="refresh"
            >
              Refresh Page
            </Button>
          </Box>
        </SpaceBetween>
      </Container>
    );
  }

  // Show account selection prompt if no account is selected
  if (!selectedAccount) {
    return (
      <Container
        header={<Header variant="h2">Select Target Account</Header>}
      >
        <SpaceBetween size="l">
          <Alert type="info">
            <strong>Please select a target account to use {feature}.</strong>
            <br />
            All DRS operations will be performed in the selected AWS account.
          </Alert>
          
          <FormField
            label="Target Account"
            description="Select the AWS account where your DRS source servers are located"
          >
            <AccountSelector />
          </FormField>
          
          {availableAccounts.length === 1 && (
            <Alert type="success">
              <strong>Single Account Environment:</strong> You have one target account available. 
              Select it above to continue.
            </Alert>
          )}
        </SpaceBetween>
      </Container>
    );
  }

  // Account is selected - render the protected content
  return <>{children}</>;
};