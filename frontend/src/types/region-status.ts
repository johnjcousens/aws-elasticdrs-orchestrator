/**
 * Region Status Type Definitions
 * 
 * These types define the enhanced region status tracking system
 * that provides specific error information for DRS region availability.
 */

/**
 * Region status values returned by the backend
 */
export type RegionStatus =
  | 'ACTIVE'                    // Region is operational with DRS servers accessible
  | 'NOT_INITIALIZED'           // DRS service not initialized in the region
  | 'IAM_PERMISSION_DENIED'     // IAM permissions insufficient
  | 'SCP_DENIED'                // Service Control Policy blocking access
  | 'REGION_NOT_ENABLED'        // Region not enabled in AWS account
  | 'REGION_NOT_OPTED_IN'       // Region requires explicit opt-in
  | 'THROTTLED'                 // API rate limit exceeded
  | 'ENDPOINT_UNREACHABLE'      // Cannot connect to DRS endpoint
  | 'ERROR';                    // Other unclassified errors

/**
 * Region status information from backend
 */
export interface RegionStatusInfo {
  accountId: string;
  region: string;
  status: RegionStatus;
  serverCount: number;
  errorMessage?: string;
  lastUpdated: string;
}

/**
 * Error guidance for each status type
 */
export interface RegionStatusGuidance {
  title: string;
  message: string;
  actionable: boolean;
  actions?: string[];
  severity: 'error' | 'warning' | 'info';
}

/**
 * Get user-friendly guidance for a region status
 */
export function getRegionStatusGuidance(
  status: RegionStatus,
  region: string,
  errorMessage?: string
): RegionStatusGuidance {
  switch (status) {
    case 'ACTIVE':
      return {
        title: 'Region Active',
        message: `DRS is operational in ${region}`,
        actionable: false,
        severity: 'info',
      };

    case 'NOT_INITIALIZED':
      return {
        title: 'DRS Not Initialized',
        message: `AWS Elastic Disaster Recovery (DRS) is not initialized in ${region}. You need to initialize DRS before creating Protection Groups.`,
        actionable: true,
        actions: [
          'Go to the AWS DRS Console',
          'Complete the initialization wizard',
          'Return here to create Protection Groups',
        ],
        severity: 'warning',
      };

    case 'IAM_PERMISSION_DENIED':
      return {
        title: 'IAM Permission Denied',
        message: errorMessage || `Insufficient IAM permissions to access DRS in ${region}. The Lambda execution role needs additional permissions.`,
        actionable: true,
        actions: [
          'Check the Lambda execution role permissions',
          'Verify drs:DescribeSourceServers permission exists',
          'Add required DRS permissions to the role',
          'Contact your AWS administrator if needed',
        ],
        severity: 'error',
      };

    case 'SCP_DENIED':
      return {
        title: 'Service Control Policy Denied',
        message: errorMessage || `Organization-level Service Control Policy (SCP) is blocking DRS access in ${region}. This cannot be fixed at the IAM level.`,
        actionable: true,
        actions: [
          'Contact your AWS Organization administrator',
          'Request SCP modification to allow DRS access',
          'This requires organization-level policy changes',
        ],
        severity: 'error',
      };

    case 'REGION_NOT_ENABLED':
      return {
        title: 'Region Not Enabled',
        message: `The ${region} region is not enabled in your AWS account. You need to enable it before using DRS.`,
        actionable: true,
        actions: [
          'Go to AWS Account Settings',
          'Enable the region in your account',
          'Wait for region enablement to complete',
          'Return here to access DRS',
        ],
        severity: 'warning',
      };

    case 'REGION_NOT_OPTED_IN':
      return {
        title: 'Region Opt-In Required',
        message: `The ${region} region requires explicit opt-in before use. This is common for newer AWS regions.`,
        actionable: true,
        actions: [
          'Go to AWS Account Settings',
          'Opt in to the region',
          'Wait for opt-in to complete',
          'Return here to access DRS',
        ],
        severity: 'warning',
      };

    case 'THROTTLED':
      return {
        title: 'API Rate Limit Exceeded',
        message: `Too many requests to the DRS API in ${region}. This is a temporary condition.`,
        actionable: true,
        actions: [
          'Wait a few minutes before retrying',
          'The system will automatically retry with backoff',
          'If this persists, contact support',
        ],
        severity: 'warning',
      };

    case 'ENDPOINT_UNREACHABLE':
      return {
        title: 'DRS Endpoint Unreachable',
        message: errorMessage || `Cannot connect to the DRS service endpoint in ${region}. This may be a network connectivity issue.`,
        actionable: true,
        actions: [
          'Check VPC endpoint configuration if using private endpoints',
          'Verify network connectivity to AWS services',
          'Check AWS Service Health Dashboard for outages',
          'Contact AWS support if the issue persists',
        ],
        severity: 'error',
      };

    case 'ERROR':
    default:
      return {
        title: 'Region Error',
        message: errorMessage || `An error occurred while accessing DRS in ${region}. Please check the error details.`,
        actionable: true,
        actions: [
          'Review the error message for specific details',
          'Check AWS CloudWatch logs for more information',
          'Contact support if the issue persists',
        ],
        severity: 'error',
      };
  }
}

/**
 * Check if a status indicates DRS is not available
 */
export function isDrsUnavailable(status: RegionStatus): boolean {
  return status !== 'ACTIVE';
}

/**
 * Check if a status is a permission-related error
 */
export function isPermissionError(status: RegionStatus): boolean {
  return status === 'IAM_PERMISSION_DENIED' || status === 'SCP_DENIED';
}

/**
 * Check if a status is a region availability error
 */
export function isRegionAvailabilityError(status: RegionStatus): boolean {
  return status === 'REGION_NOT_ENABLED' || status === 'REGION_NOT_OPTED_IN';
}

/**
 * Check if a status is a temporary/transient error
 */
export function isTransientError(status: RegionStatus): boolean {
  return status === 'THROTTLED' || status === 'ENDPOINT_UNREACHABLE';
}
