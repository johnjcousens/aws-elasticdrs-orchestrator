/**
 * Staging Accounts API Client
 *
 * API client functions for staging accounts management feature.
 * Handles validation, addition, removal, and capacity queries for staging accounts.
 *
 * REQUIREMENTS VALIDATED:
 * - 1.6: Add staging account to target account
 * - 2.2: Remove staging account from target account
 * - 3.1: Validate staging account access
 * - 4.1: Query combined capacity across all accounts
 */

import apiClient from "./api";
import type {
  ValidationResult,
  ValidateStagingAccountRequest,
  AddStagingAccountRequest,
  StagingAccountOperationResponse,
  RemoveStagingAccountRequest,
  CombinedCapacityData,
  GetCombinedCapacityRequest,
} from "../types/staging-accounts";

// ============================================================================
// Staging Account Validation API
// ============================================================================

/**
 * Validate staging account access before adding.
 *
 * Checks:
 * - IAM role accessibility via AssumeRole
 * - DRS initialization status in specified region
 * - Current server counts in staging account
 *
 * Validates: Requirement 3.1
 *
 * @param request - Validation request with account credentials
 * @returns Validation result with detailed checks
 * @throws Error if validation request fails
 */
export async function validateStagingAccount(
  request: ValidateStagingAccountRequest
): Promise<ValidationResult> {
  try {
    const response = await apiClient["post"]<ValidationResult>(
      "/staging-accounts/validate",
      request
    );
    return response;
  } catch (error) {
    // Re-throw with context for better error messages
    const err = error as Error;
    throw new Error(
      `Failed to validate staging account: ${err.message || "Unknown error"}`
    );
  }
}

// ============================================================================
// Staging Account Management API
// ============================================================================

/**
 * Add staging account to target account configuration.
 *
 * Persists staging account credentials to DynamoDB Target Accounts table.
 * The staging account will be included in future capacity queries.
 *
 * Validates: Requirement 1.6
 *
 * @param targetAccountId - Target account ID to add staging account to
 * @param stagingAccount - Staging account configuration
 * @param addedBy - User adding the staging account (optional)
 * @returns Operation response with updated staging accounts list
 * @throws Error if add operation fails
 */
export async function addStagingAccount(
  targetAccountId: string,
  stagingAccount: {
    accountId: string;
    accountName: string;
    roleArn: string;
    externalId: string;
  },
  addedBy?: string
): Promise<StagingAccountOperationResponse> {
  try {
    const request: AddStagingAccountRequest = {
      targetAccountId,
      stagingAccount,
      addedBy,
    };

    const response = await apiClient["post"]<StagingAccountOperationResponse>(
      `/api/accounts/${targetAccountId}/staging-accounts`,
      request
    );
    return response;
  } catch (error) {
    // Re-throw with context for better error messages
    const err = error as Error;
    throw new Error(
      `Failed to add staging account: ${err.message || "Unknown error"}`
    );
  }
}

/**
 * Remove staging account from target account configuration.
 *
 * Removes staging account credentials from DynamoDB Target Accounts table.
 * The staging account will no longer be included in capacity queries.
 *
 * Validates: Requirement 2.2
 *
 * @param targetAccountId - Target account ID
 * @param stagingAccountId - Staging account ID to remove
 * @returns Operation response with updated staging accounts list
 * @throws Error if remove operation fails
 */
export async function removeStagingAccount(
  targetAccountId: string,
  stagingAccountId: string
): Promise<StagingAccountOperationResponse> {
  try {
    const response = await apiClient["delete"]<StagingAccountOperationResponse>(
      `/api/accounts/${targetAccountId}/staging-accounts/${stagingAccountId}`
    );
    return response;
  } catch (error) {
    // Re-throw with context for better error messages
    const err = error as Error;
    throw new Error(
      `Failed to remove staging account: ${err.message || "Unknown error"}`
    );
  }
}

// ============================================================================
// Combined Capacity Query API
// ============================================================================

/**
 * Get combined capacity for ALL target accounts (universal dashboard view).
 *
 * This endpoint returns capacity data for all target accounts in a single call,
 * making the dashboard load much faster than fetching each account separately.
 *
 * Validates: Requirement 4.1
 *
 * @returns Combined capacity data for all target accounts
 * @throws Error if capacity query fails
 */
export async function getAllAccountsCapacity(): Promise<CombinedCapacityData> {
  try {
    const response = await apiClient["get"]<CombinedCapacityData>(
      `/accounts/capacity/all`
    );
    return response;
  } catch (error) {
    // Re-throw with context for better error messages
    const err = error as Error;
    throw new Error(
      `Failed to get all accounts capacity: ${err.message || "Unknown error"}`
    );
  }
}

/**
 * Get combined capacity metrics across target and staging accounts.
 *
 * Queries DRS capacity concurrently across:
 * - Target account (all regions)
 * - All staging accounts (all regions)
 *
 * Returns aggregated metrics with per-account breakdown, status indicators,
 * and warnings based on capacity thresholds.
 *
 * Validates: Requirement 4.1
 *
 * @param targetAccountId - Target account ID
 * @param includeRegionalBreakdown - Whether to include per-region metrics (default: true)
 * @returns Combined capacity data with account breakdown
 * @throws Error if capacity query fails
 */
export async function getCombinedCapacity(
  targetAccountId: string,
  includeRegionalBreakdown: boolean = true
): Promise<CombinedCapacityData> {
  try {
    const params: Record<string, string> = {};
    if (includeRegionalBreakdown !== undefined) {
      params.includeRegionalBreakdown = String(includeRegionalBreakdown);
    }

    const response = await apiClient["get"]<CombinedCapacityData>(
      `/accounts/targets/${targetAccountId}/capacity`,
      params
    );
    return response;
  } catch (error) {
    // Re-throw with context for better error messages
    const err = error as Error;
    throw new Error(
      `Failed to get combined capacity: ${err.message || "Unknown error"}`
    );
  }
}

// ============================================================================
// Export all functions
// ============================================================================

export default {
  validateStagingAccount,
  addStagingAccount,
  removeStagingAccount,
  getCombinedCapacity,
  getAllAccountsCapacity,
};
