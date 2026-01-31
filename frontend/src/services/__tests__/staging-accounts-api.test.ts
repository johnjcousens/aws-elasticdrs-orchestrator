/**
 * Unit Tests for Staging Accounts API Client
 *
 * Tests all API client functions for staging accounts management.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import apiClient from "../api";
import {
  validateStagingAccount,
  addStagingAccount,
  removeStagingAccount,
  getCombinedCapacity,
} from "../staging-accounts-api";
import type {
  ValidationResult,
  ValidateStagingAccountRequest,
  StagingAccountOperationResponse,
  CombinedCapacityData,
} from "../../types/staging-accounts";

// Mock the API client
vi.mock("../api", () => ({
  default: {
    post: vi.fn(),
    delete: vi.fn(),
    get: vi.fn(),
  },
}));

describe("Staging Accounts API Client", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("validateStagingAccount", () => {
    it("should validate staging account successfully", async () => {
      const request: ValidateStagingAccountRequest = {
        accountId: "123456789012",
        accountName: "Staging Account 1",
        roleArn: "arn:aws:iam::123456789012:role/DRSRole",
        externalId: "external-123",
        region: "us-east-1",
      };

      const mockResponse: ValidationResult = {
        valid: true,
        roleAccessible: true,
        drsInitialized: true,
        currentServers: 50,
        replicatingServers: 40,
        totalAfter: 140,
      };

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

      const result = await validateStagingAccount(request);

      expect(apiClient.post).toHaveBeenCalledWith(
        "/staging-accounts/validate",
        request
      );
      expect(result).toEqual(mockResponse);
    });

    it("should handle validation failure", async () => {
      const request: ValidateStagingAccountRequest = {
        accountId: "123456789012",
        accountName: "Staging Account 1",
        roleArn: "arn:aws:iam::123456789012:role/DRSRole",
        externalId: "external-123",
        region: "us-east-1",
      };

      const mockResponse: ValidationResult = {
        valid: false,
        roleAccessible: false,
        drsInitialized: false,
        currentServers: 0,
        replicatingServers: 0,
        totalAfter: 0,
        error: "Role not accessible",
      };

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

      const result = await validateStagingAccount(request);

      expect(result.valid).toBe(false);
      expect(result.error).toBe("Role not accessible");
    });

    it("should throw error on API failure", async () => {
      const request: ValidateStagingAccountRequest = {
        accountId: "123456789012",
        accountName: "Staging Account 1",
        roleArn: "arn:aws:iam::123456789012:role/DRSRole",
        externalId: "external-123",
        region: "us-east-1",
      };

      vi.mocked(apiClient.post).mockRejectedValue(
        new Error("Network error")
      );

      await expect(validateStagingAccount(request)).rejects.toThrow(
        "Failed to validate staging account: Network error"
      );
    });
  });

  describe("addStagingAccount", () => {
    it("should add staging account successfully", async () => {
      const targetAccountId = "999888777666";
      const stagingAccount = {
        accountId: "123456789012",
        accountName: "Staging Account 1",
        roleArn: "arn:aws:iam::123456789012:role/DRSRole",
        externalId: "external-123",
      };
      const addedBy = "user@example.com";

      const mockResponse: StagingAccountOperationResponse = {
        success: true,
        message: "Staging account added successfully",
        stagingAccounts: [
          {
            ...stagingAccount,
            addedAt: "2024-01-15T10:00:00Z",
            addedBy,
          },
        ],
      };

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

      const result = await addStagingAccount(
        targetAccountId,
        stagingAccount,
        addedBy
      );

      expect(apiClient.post).toHaveBeenCalledWith(
        `/api/accounts/${targetAccountId}/staging-accounts`,
        {
          targetAccountId,
          stagingAccount,
          addedBy,
        }
      );
      expect(result).toEqual(mockResponse);
      expect(result.success).toBe(true);
    });

    it("should handle add failure", async () => {
      const targetAccountId = "999888777666";
      const stagingAccount = {
        accountId: "123456789012",
        accountName: "Staging Account 1",
        roleArn: "arn:aws:iam::123456789012:role/DRSRole",
        externalId: "external-123",
      };

      vi.mocked(apiClient.post).mockRejectedValue(
        new Error("Account already exists")
      );

      await expect(
        addStagingAccount(targetAccountId, stagingAccount)
      ).rejects.toThrow(
        "Failed to add staging account: Account already exists"
      );
    });
  });

  describe("removeStagingAccount", () => {
    it("should remove staging account successfully", async () => {
      const targetAccountId = "999888777666";
      const stagingAccountId = "123456789012";

      const mockResponse: StagingAccountOperationResponse = {
        success: true,
        message: "Staging account removed successfully",
        stagingAccounts: [],
      };

      vi.mocked(apiClient.delete).mockResolvedValue(mockResponse);

      const result = await removeStagingAccount(
        targetAccountId,
        stagingAccountId
      );

      expect(apiClient.delete).toHaveBeenCalledWith(
        `/api/accounts/${targetAccountId}/staging-accounts/${stagingAccountId}`
      );
      expect(result).toEqual(mockResponse);
      expect(result.success).toBe(true);
    });

    it("should handle remove failure", async () => {
      const targetAccountId = "999888777666";
      const stagingAccountId = "123456789012";

      vi.mocked(apiClient.delete).mockRejectedValue(
        new Error("Account not found")
      );

      await expect(
        removeStagingAccount(targetAccountId, stagingAccountId)
      ).rejects.toThrow(
        "Failed to remove staging account: Account not found"
      );
    });
  });

  describe("getCombinedCapacity", () => {
    it("should get combined capacity successfully", async () => {
      const targetAccountId = "999888777666";

      const mockResponse: CombinedCapacityData = {
        combined: {
          totalReplicating: 140,
          maxReplicating: 600,
          percentUsed: 23.3,
          status: "OK",
          message: "Capacity is healthy",
          availableSlots: 460,
        },
        accounts: [
          {
            accountId: targetAccountId,
            accountName: "Target Account",
            accountType: "target",
            replicatingServers: 100,
            totalServers: 120,
            maxReplicating: 300,
            percentUsed: 33.3,
            availableSlots: 200,
            status: "OK",
            regionalBreakdown: [
              {
                region: "us-east-1",
                totalServers: 120,
                replicatingServers: 100,
              },
            ],
            warnings: [],
          },
          {
            accountId: "123456789012",
            accountName: "Staging Account 1",
            accountType: "staging",
            replicatingServers: 40,
            totalServers: 50,
            maxReplicating: 300,
            percentUsed: 13.3,
            availableSlots: 260,
            status: "OK",
            regionalBreakdown: [
              {
                region: "us-east-1",
                totalServers: 50,
                replicatingServers: 40,
              },
            ],
            warnings: [],
          },
        ],
        recoveryCapacity: {
          currentServers: 170,
          maxRecoveryInstances: 4000,
          percentUsed: 4.25,
          availableSlots: 3830,
          status: "OK",
        },
        warnings: [],
        timestamp: "2024-01-15T10:00:00Z",
      };

      vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

      const result = await getCombinedCapacity(targetAccountId);

      expect(apiClient.get).toHaveBeenCalledWith(
        `/accounts/targets/${targetAccountId}/capacity`,
        { includeRegionalBreakdown: "true" }
      );
      expect(result).toEqual(mockResponse);
      expect(result.combined.totalReplicating).toBe(140);
      expect(result.accounts).toHaveLength(2);
    });

    it("should get combined capacity without regional breakdown", async () => {
      const targetAccountId = "999888777666";

      const mockResponse: CombinedCapacityData = {
        combined: {
          totalReplicating: 140,
          maxReplicating: 600,
          percentUsed: 23.3,
          status: "OK",
          message: "Capacity is healthy",
          availableSlots: 460,
        },
        accounts: [
          {
            accountId: targetAccountId,
            accountName: "Target Account",
            accountType: "target",
            replicatingServers: 100,
            totalServers: 120,
            maxReplicating: 300,
            percentUsed: 33.3,
            availableSlots: 200,
            status: "OK",
            regionalBreakdown: [],
            warnings: [],
          },
        ],
        recoveryCapacity: {
          currentServers: 120,
          maxRecoveryInstances: 4000,
          percentUsed: 3.0,
          availableSlots: 3880,
          status: "OK",
        },
        warnings: [],
      };

      vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

      const result = await getCombinedCapacity(targetAccountId, false);

      expect(apiClient.get).toHaveBeenCalledWith(
        `/accounts/targets/${targetAccountId}/capacity`,
        { includeRegionalBreakdown: "false" }
      );
      expect(result).toEqual(mockResponse);
    });

    it("should handle capacity query failure", async () => {
      const targetAccountId = "999888777666";

      vi.mocked(apiClient.get).mockRejectedValue(
        new Error("Service unavailable")
      );

      await expect(getCombinedCapacity(targetAccountId)).rejects.toThrow(
        "Failed to get combined capacity: Service unavailable"
      );
    });

    it("should handle capacity with warnings", async () => {
      const targetAccountId = "999888777666";

      const mockResponse: CombinedCapacityData = {
        combined: {
          totalReplicating: 280,
          maxReplicating: 300,
          percentUsed: 93.3,
          status: "HYPER-CRITICAL",
          message: "Capacity critically low",
          availableSlots: 20,
        },
        accounts: [
          {
            accountId: targetAccountId,
            accountName: "Target Account",
            accountType: "target",
            replicatingServers: 280,
            totalServers: 290,
            maxReplicating: 300,
            percentUsed: 93.3,
            availableSlots: 20,
            status: "HYPER-CRITICAL",
            regionalBreakdown: [],
            warnings: [
              "Account is at 93% capacity (280/300 servers)",
              "Consider adding staging accounts",
            ],
          },
        ],
        recoveryCapacity: {
          currentServers: 290,
          maxRecoveryInstances: 4000,
          percentUsed: 7.25,
          availableSlots: 3710,
          status: "OK",
        },
        warnings: [
          "Target account is at HYPER-CRITICAL capacity (93%)",
          "Add staging accounts to increase capacity",
        ],
      };

      vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

      const result = await getCombinedCapacity(targetAccountId);

      expect(result.combined.status).toBe("HYPER-CRITICAL");
      expect(result.warnings).toHaveLength(2);
      expect(result.accounts[0].warnings).toHaveLength(2);
    });
  });
});
