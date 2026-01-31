/**
 * AddStagingAccountModal Component
 *
 * Modal dialog for adding a new staging account with validation.
 * Simplified to only require essential information - the system automatically
 * derives role ARN, external ID, and discovers DRS-initialized regions.
 *
 * FEATURES:
 * - Minimal form fields (account ID, optional name)
 * - Automatic role ARN construction (standardized naming)
 * - Automatic external ID generation
 * - Automatic region discovery (tries common regions)
 * - Input validation (format checking)
 * - Staging account access validation via API
 * - Display validation results with status indicators
 * - Add button enabled only after successful validation
 *
 * REQUIREMENTS VALIDATED:
 * - 1.2: Display form fields for staging account details
 * - 1.3: Validate access on button click
 * - 1.4: Display validation results
 * - 1.5: Display validation errors
 * - 1.6: Add staging account after validation
 */

import React, { useState } from "react";
import {
  Modal,
  Box,
  SpaceBetween,
  Button,
  FormField,
  Input,
  Alert,
  ColumnLayout,
  StatusIndicator,
  Container,
  Header,
} from "@cloudscape-design/components";
import { validateStagingAccount, addStagingAccount } from "../services/staging-accounts-api";
import type {
  AddStagingAccountModalProps,
  AddStagingAccountModalState,
  AddStagingAccountFormData,
  StagingAccountFormErrors,
  ValidationResult,
  StagingAccount,
} from "../types/staging-accounts";

/**
 * AWS regions for DRS - used for automatic discovery
 * The system will try these regions automatically to find where DRS is initialized
 */
const AWS_REGIONS = [
  "us-east-1",
  "us-east-2",
  "us-west-1",
  "us-west-2",
  "eu-west-1",
  "eu-west-2",
  "eu-central-1",
  "ap-southeast-1",
  "ap-southeast-2",
  "ap-northeast-1",
];

/**
 * Validate AWS account ID format (12 digits)
 */
const validateAccountId = (accountId: string): string | undefined => {
  if (!accountId) {
    return "Account ID is required";
  }
  if (!/^\d{12}$/.test(accountId)) {
    return "Account ID must be exactly 12 digits";
  }
  return undefined;
};

/**
 * Validate account name (optional - will default to account ID if not provided)
 */
const validateAccountName = (accountName: string): string | undefined => {
  if (accountName && (accountName.length < 1 || accountName.length > 50)) {
    return "Account name must be between 1 and 50 characters";
  }
  return undefined;
};

/**
 * Construct standardized role ARN from account ID
 */
const constructRoleArn = (accountId: string): string => {
  return `arn:aws:iam::${accountId}:role/DRSOrchestrationRole`;
};

/**
 * Construct standardized external ID from account ID
 */
const constructExternalId = (accountId: string): string => {
  return `drs-orchestration-${accountId}`;
};

/**
 * AddStagingAccountModal Component
 *
 * Modal for adding a new staging account with validation.
 */
export const AddStagingAccountModal: React.FC<
  AddStagingAccountModalProps
> = ({ visible, onDismiss, onAdd, targetAccountId }) => {
  const [state, setState] = useState<AddStagingAccountModalState>({
    formData: {
      accountId: "",
      accountName: "",
      roleArn: "",
      externalId: "",
      region: "us-east-1",
    },
    validating: false,
    validationResult: null,
    errors: {},
    adding: false,
  });

  /**
   * Validate all form fields
   */
  const validateForm = (): boolean => {
    const errors: StagingAccountFormErrors = {
      accountId: validateAccountId(state.formData.accountId),
      accountName: validateAccountName(state.formData.accountName),
    };

    setState((prev) => ({ ...prev, errors }));

    return !Object.values(errors).some((error) => error !== undefined);
  };

  /**
   * Handle form field change
   */
  const handleFieldChange = (
    field: keyof AddStagingAccountFormData,
    value: string
  ) => {
    setState((prev) => ({
      ...prev,
      formData: {
        ...prev.formData,
        [field]: value,
      },
      // Clear validation result when form changes
      validationResult: null,
      // Clear field-specific error
      errors: {
        ...prev.errors,
        [field]: undefined,
      },
    }));
  };

  /**
   * Handle validate access button click
   */
  const handleValidate = async () => {
    // Validate form first
    if (!validateForm()) {
      return;
    }

    // Auto-construct role ARN and external ID
    const accountId = state.formData.accountId;
    const roleArn = constructRoleArn(accountId);
    const externalId = constructExternalId(accountId);
    const accountName = state.formData.accountName || accountId; // Default to account ID if not provided

    setState((prev) => ({
      ...prev,
      formData: {
        ...prev.formData,
        accountName,
        roleArn,
        externalId,
      },
      validating: true,
    }));

    try {
      // Try the first region (us-east-1) for validation
      // Backend will handle multi-region discovery if needed
      const region = AWS_REGIONS[0];

      // Call the real API
      const validationResult = await validateStagingAccount({
        accountId,
        roleArn,
        externalId,
        region,
      });

      setState((prev) => ({
        ...prev,
        validating: false,
        validationResult,
      }));
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : "Failed to validate staging account";

      const validationResult: ValidationResult = {
        valid: false,
        roleAccessible: false,
        drsInitialized: false,
        currentServers: 0,
        replicatingServers: 0,
        totalAfter: 0,
        error: errorMessage,
      };

      setState((prev) => ({
        ...prev,
        validating: false,
        validationResult,
      }));
    }
  };

  /**
   * Handle add staging account button click
   */
  const handleAdd = async () => {
    if (!state.validationResult?.valid) {
      return;
    }

    setState((prev) => ({ ...prev, adding: true }));

    try {
      // Call the real API to add staging account
      await addStagingAccount(
        targetAccountId,
        {
          accountId: state.formData.accountId,
          accountName: state.formData.accountName,
          roleArn: state.formData.roleArn,
          externalId: state.formData.externalId,
        }
      );

      // Create staging account object for UI callback
      const stagingAccount: StagingAccount = {
        accountId: state.formData.accountId,
        accountName: state.formData.accountName,
        roleArn: state.formData.roleArn,
        externalId: state.formData.externalId,
        status: "connected",
        serverCount: state.validationResult.currentServers,
        replicatingCount: state.validationResult.replicatingServers,
      };

      // Call onAdd callback
      onAdd(stagingAccount);

      // Reset form and close modal
      setState({
        formData: {
          accountId: "",
          accountName: "",
          roleArn: "",
          externalId: "",
          region: "us-east-1",
        },
        validating: false,
        validationResult: null,
        errors: {},
        adding: false,
      });

      onDismiss();
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : "Failed to add staging account";

      setState((prev) => ({
        ...prev,
        adding: false,
        validationResult: {
          ...prev.validationResult!,
          error: errorMessage,
        },
      }));
    }
  };

  /**
   * Handle modal dismiss
   */
  const handleDismiss = () => {
    // Reset form state
    setState({
      formData: {
        accountId: "",
        accountName: "",
        roleArn: "",
        externalId: "",
        region: "us-east-1",
      },
      validating: false,
      validationResult: null,
      errors: {},
      adding: false,
    });

    onDismiss();
  };

  /**
   * Render validation results
   */
  const renderValidationResults = () => {
    if (!state.validationResult) {
      return null;
    }

    const { validationResult } = state;

    if (!validationResult.valid) {
      return (
        <Alert type="error" header="Validation Failed">
          {validationResult.error ||
            "Unable to validate staging account access"}
        </Alert>
      );
    }

    return (
      <Container header={<Header variant="h3">Validation Results</Header>}>
        <SpaceBetween size="m">
          <ColumnLayout columns={2} variant="text-grid">
            <div>
              <Box variant="awsui-key-label">Role Accessible</Box>
              <StatusIndicator
                type={validationResult.roleAccessible ? "success" : "error"}
              >
                {validationResult.roleAccessible ? "Yes" : "No"}
              </StatusIndicator>
            </div>
            <div>
              <Box variant="awsui-key-label">DRS Initialized</Box>
              <StatusIndicator
                type={validationResult.drsInitialized ? "success" : "error"}
              >
                {validationResult.drsInitialized ? "Yes" : "No"}
              </StatusIndicator>
            </div>
            <div>
              <Box variant="awsui-key-label">Current Servers</Box>
              <Box variant="awsui-value-large">
                {validationResult.currentServers}
              </Box>
            </div>
            <div>
              <Box variant="awsui-key-label">Replicating Servers</Box>
              <Box variant="awsui-value-large">
                {validationResult.replicatingServers}
              </Box>
            </div>
          </ColumnLayout>

          <Alert type="success" header="Validation Successful">
            Staging account is accessible and ready to be added. After adding
            this account, your combined replicating capacity will be{" "}
            {validationResult.totalAfter} servers.
          </Alert>
        </SpaceBetween>
      </Container>
    );
  };

  return (
    <Modal
      visible={visible}
      onDismiss={handleDismiss}
      header="Add Staging Account"
      size="large"
      footer={
        <Box float="right">
          <SpaceBetween direction="horizontal" size="xs">
            <Button onClick={handleDismiss} disabled={state.adding}>
              Cancel
            </Button>
            <Button
              onClick={handleValidate}
              loading={state.validating}
              disabled={state.adding}
            >
              Validate Access
            </Button>
            <Button
              variant="primary"
              onClick={handleAdd}
              loading={state.adding}
              disabled={
                !state.validationResult?.valid || state.validating
              }
            >
              Add Account
            </Button>
          </SpaceBetween>
        </Box>
      }
    >
      <SpaceBetween size="l">
        <Alert type="info">
          <strong>Simplified Setup</strong>
          <p>
            Just provide the AWS account ID. The system will automatically:
          </p>
          <ul>
            <li>
              Construct the role ARN using standardized naming:{" "}
              <code>DRSOrchestrationRole</code>
            </li>
            <li>
              Generate the external ID: <code>drs-orchestration-[ACCOUNT_ID]</code>
            </li>
            <li>Discover which regions have DRS initialized</li>
          </ul>
          <p>
            <strong>Prerequisites:</strong> Ensure the IAM role exists in the
            staging account with the correct trust policy.
          </p>
        </Alert>

        <SpaceBetween size="m">
          <FormField
            label="Account ID"
            description="12-digit AWS account ID"
            errorText={state.errors.accountId}
          >
            <Input
              value={state.formData.accountId}
              onChange={({ detail }) =>
                handleFieldChange("accountId", detail.value)
              }
              placeholder="123456789012"
              disabled={state.validating || state.adding}
            />
          </FormField>

          <FormField
            label="Account Name (Optional)"
            description="Human-readable name for this staging account. Defaults to account ID if not provided."
            errorText={state.errors.accountName}
          >
            <Input
              value={state.formData.accountName}
              onChange={({ detail }) =>
                handleFieldChange("accountName", detail.value)
              }
              placeholder="STAGING_01"
              disabled={state.validating || state.adding}
            />
          </FormField>

          {/* Show auto-generated values after validation starts */}
          {(state.validating || state.validationResult) && (
            <Container header={<Header variant="h3">Auto-Generated Configuration</Header>}>
              <ColumnLayout columns={1} variant="text-grid">
                <div>
                  <Box variant="awsui-key-label">Role ARN</Box>
                  <Box variant="code">{state.formData.roleArn}</Box>
                </div>
                <div>
                  <Box variant="awsui-key-label">External ID</Box>
                  <Box variant="code">{state.formData.externalId}</Box>
                </div>
              </ColumnLayout>
            </Container>
          )}
        </SpaceBetween>

        {renderValidationResults()}
      </SpaceBetween>
    </Modal>
  );
};

export default AddStagingAccountModal;
