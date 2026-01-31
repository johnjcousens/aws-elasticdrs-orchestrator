/**
 * Type Tests for Staging Accounts Management
 *
 * These tests verify that TypeScript interfaces are correctly defined
 * and can be used in type-safe code.
 */

import { describe, it, expect } from 'vitest';
import type {
  StagingAccount,
  TargetAccount,
  AccountCapacity,
  RegionalCapacity,
  CombinedCapacityData,
  ValidationResult,
  CapacityStatus,
  AccountType,
  RecoveryCapacity,
  AddStagingAccountFormData,
  StagingAccountFormErrors,
} from '../staging-accounts';
import {
  CAPACITY_LIMITS,
  DEFAULT_CAPACITY_THRESHOLDS,
} from '../staging-accounts';

describe('Staging Accounts Type Definitions', () => {
  describe('StagingAccount interface', () => {
    it('should accept valid staging account object', () => {
      const stagingAccount: StagingAccount = {
        accountId: '444455556666',
        accountName: 'STAGING_01',
        roleArn: 'arn:aws:iam::444455556666:role/DRSOrchestrationRole-test',
        externalId: 'drs-orchestration-test-444455556666',
        addedAt: '2024-01-15T10:30:00Z',
        addedBy: 'admin@example.com',
        status: 'connected',
        serverCount: 42,
        replicatingCount: 42,
      };

      expect(stagingAccount.accountId).toBe('444455556666');
      expect(stagingAccount.accountName).toBe('STAGING_01');
      expect(stagingAccount.status).toBe('connected');
    });

    it('should accept minimal staging account object', () => {
      const stagingAccount: StagingAccount = {
        accountId: '444455556666',
        accountName: 'STAGING_01',
        roleArn: 'arn:aws:iam::444455556666:role/DRSRole',
        externalId: 'external-id-123',
      };

      expect(stagingAccount.accountId).toBe('444455556666');
    });
  });

  describe('TargetAccount interface', () => {
    it('should accept target account with staging accounts', () => {
      const targetAccount: TargetAccount = {
        accountId: '111122223333',
        accountName: 'DEMO_TARGET',
        roleArn: 'arn:aws:iam::111122223333:role/DRSRole',
        externalId: 'external-id-target',
        stagingAccounts: [
          {
            accountId: '444455556666',
            accountName: 'STAGING_01',
            roleArn: 'arn:aws:iam::444455556666:role/DRSRole',
            externalId: 'external-id-staging',
          },
        ],
        status: 'active',
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-15T10:30:00Z',
        createdBy: 'system',
      };

      expect(targetAccount.stagingAccounts).toHaveLength(1);
      expect(targetAccount.status).toBe('active');
    });

    it('should accept target account with empty staging accounts', () => {
      const targetAccount: TargetAccount = {
        accountId: '111122223333',
        accountName: 'DEMO_TARGET',
        stagingAccounts: [],
      };

      expect(targetAccount.stagingAccounts).toHaveLength(0);
    });
  });

  describe('CapacityStatus type', () => {
    it('should accept all valid status values', () => {
      const statuses: CapacityStatus[] = [
        'OK',
        'INFO',
        'WARNING',
        'CRITICAL',
        'HYPER-CRITICAL',
      ];

      expect(statuses).toHaveLength(5);
    });
  });

  describe('AccountType type', () => {
    it('should accept valid account types', () => {
      const targetType: AccountType = 'target';
      const stagingType: AccountType = 'staging';

      expect(targetType).toBe('target');
      expect(stagingType).toBe('staging');
    });
  });

  describe('RegionalCapacity interface', () => {
    it('should accept regional capacity data', () => {
      const regional: RegionalCapacity = {
        region: 'us-east-1',
        totalServers: 50,
        replicatingServers: 45,
      };

      expect(regional.region).toBe('us-east-1');
      expect(regional.replicatingServers).toBe(45);
    });
  });

  describe('AccountCapacity interface', () => {
    it('should accept complete account capacity data', () => {
      const capacity: AccountCapacity = {
        accountId: '111122223333',
        accountName: 'DEMO_TARGET',
        accountType: 'target',
        replicatingServers: 225,
        totalServers: 230,
        maxReplicating: 300,
        percentUsed: 75,
        availableSlots: 75,
        status: 'WARNING',
        regionalBreakdown: [
          {
            region: 'us-east-1',
            totalServers: 150,
            replicatingServers: 145,
          },
          {
            region: 'us-west-2',
            totalServers: 80,
            replicatingServers: 80,
          },
        ],
        warnings: ['Account at 75% capacity - consider adding staging account'],
        accessible: true,
      };

      expect(capacity.status).toBe('WARNING');
      expect(capacity.regionalBreakdown).toHaveLength(2);
      expect(capacity.warnings).toHaveLength(1);
    });

    it('should accept account capacity with error', () => {
      const capacity: AccountCapacity = {
        accountId: '444455556666',
        accountName: 'STAGING_01',
        accountType: 'staging',
        replicatingServers: 0,
        totalServers: 0,
        maxReplicating: 300,
        percentUsed: 0,
        availableSlots: 300,
        status: 'OK',
        regionalBreakdown: [],
        warnings: [],
        accessible: false,
        error: 'Unable to assume role: Access Denied',
      };

      expect(capacity.accessible).toBe(false);
      expect(capacity.error).toBeDefined();
    });
  });

  describe('RecoveryCapacity interface', () => {
    it('should accept recovery capacity data', () => {
      const recovery: RecoveryCapacity = {
        currentServers: 225,
        maxRecoveryInstances: 4000,
        percentUsed: 5.625,
        availableSlots: 3775,
        status: 'OK',
      };

      expect(recovery.maxRecoveryInstances).toBe(4000);
      expect(recovery.status).toBe('OK');
    });
  });

  describe('CombinedCapacityData interface', () => {
    it('should accept complete combined capacity data', () => {
      const data: CombinedCapacityData = {
        combined: {
          totalReplicating: 267,
          maxReplicating: 1200,
          percentUsed: 22.25,
          status: 'OK',
          message: 'Capacity OK - 933 slots available',
          availableSlots: 933,
        },
        accounts: [
          {
            accountId: '111122223333',
            accountName: 'DEMO_TARGET',
            accountType: 'target',
            replicatingServers: 225,
            totalServers: 230,
            maxReplicating: 300,
            percentUsed: 75,
            availableSlots: 75,
            status: 'WARNING',
            regionalBreakdown: [],
            warnings: [],
          },
          {
            accountId: '444455556666',
            accountName: 'STAGING_01',
            accountType: 'staging',
            replicatingServers: 42,
            totalServers: 42,
            maxReplicating: 300,
            percentUsed: 14,
            availableSlots: 258,
            status: 'OK',
            regionalBreakdown: [],
            warnings: [],
          },
        ],
        recoveryCapacity: {
          currentServers: 225,
          maxRecoveryInstances: 4000,
          percentUsed: 5.625,
          availableSlots: 3775,
          status: 'OK',
        },
        warnings: ['DEMO_TARGET at 75% capacity - consider adding staging account'],
        timestamp: '2024-01-15T10:30:00Z',
      };

      expect(data.combined.totalReplicating).toBe(267);
      expect(data.accounts).toHaveLength(2);
      expect(data.warnings).toHaveLength(1);
    });
  });

  describe('ValidationResult interface', () => {
    it('should accept successful validation result', () => {
      const result: ValidationResult = {
        valid: true,
        roleAccessible: true,
        drsInitialized: true,
        currentServers: 42,
        replicatingServers: 42,
        totalAfter: 267,
        details: {
          initializedRegions: ['us-east-1', 'us-west-2'],
          uninitializedRegions: [],
        },
      };

      expect(result.valid).toBe(true);
      expect(result.roleAccessible).toBe(true);
      expect(result.drsInitialized).toBe(true);
    });

    it('should accept failed validation result', () => {
      const result: ValidationResult = {
        valid: false,
        roleAccessible: false,
        drsInitialized: false,
        currentServers: 0,
        replicatingServers: 0,
        totalAfter: 0,
        error: 'Unable to assume role: Access Denied',
        details: {
          roleErrorCode: 'AccessDenied',
        },
      };

      expect(result.valid).toBe(false);
      expect(result.error).toBeDefined();
    });
  });

  describe('Form data types', () => {
    it('should accept form data', () => {
      const formData: AddStagingAccountFormData = {
        accountId: '444455556666',
        accountName: 'STAGING_01',
        roleArn: 'arn:aws:iam::444455556666:role/DRSRole',
        externalId: 'external-id-123',
        region: 'us-east-1',
      };

      expect(formData.accountId).toBe('444455556666');
    });

    it('should accept form errors', () => {
      const errors: StagingAccountFormErrors = {
        accountId: 'Must be 12 digits',
        roleArn: 'Invalid ARN format',
      };

      expect(errors.accountId).toBeDefined();
      expect(errors.roleArn).toBeDefined();
    });
  });

  describe('Constants', () => {
    it('should export capacity limits', () => {
      expect(CAPACITY_LIMITS.OPERATIONAL_LIMIT).toBe(250);
      expect(CAPACITY_LIMITS.HARD_LIMIT).toBe(300);
      expect(CAPACITY_LIMITS.RECOVERY_LIMIT).toBe(4000);
    });

    it('should export default thresholds', () => {
      expect(DEFAULT_CAPACITY_THRESHOLDS.ok).toBe(200);
      expect(DEFAULT_CAPACITY_THRESHOLDS.info).toBe(225);
      expect(DEFAULT_CAPACITY_THRESHOLDS.warning).toBe(250);
      expect(DEFAULT_CAPACITY_THRESHOLDS.critical).toBe(280);
      expect(DEFAULT_CAPACITY_THRESHOLDS.hyperCritical).toBe(300);
    });
  });
});
