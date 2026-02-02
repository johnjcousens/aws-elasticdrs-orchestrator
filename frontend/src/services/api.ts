/**
 * API Service Layer
 * 
 * Handles all HTTP communication with the backend API Gateway.
 * Uses AWS Amplify for authentication and Axios for HTTP requests.
 */

import axios, { AxiosError } from 'axios';
import type { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { fetchAuthSession } from 'aws-amplify/auth';
import type { DRSQuotaStatus } from './drsQuotaService';
import { sanitizeErrorMessage, sanitizeForLogging } from '../utils/security';
import { recordActivity } from '../utils/activityTracker';
import type {
  ProtectionGroup,
  CreateProtectionGroupRequest,
  UpdateProtectionGroupRequest,
  RecoveryPlan,
  CreateRecoveryPlanRequest,
  UpdateRecoveryPlanRequest,
  Execution,
  ExecuteRecoveryPlanRequest,
  ExecutionListItem,
  PaginatedResponse,
  SubnetOption,
  SecurityGroupOption,
  InstanceProfileOption,
  InstanceTypeOption,
  DRSServer,
  LaunchConfig,
} from '../types';

// API configuration
const API_TIMEOUT = 30000; // 30 seconds

/**
 * API Client Class
 * 
 * Singleton class that manages all API requests with automatic
 * authentication token injection and error handling.
 */
class ApiClient {
  private static instance: ApiClient;
  private axiosInstance: AxiosInstance;

  private constructor() {
    // Don't read endpoint here - will be set dynamically in interceptor
    this.axiosInstance = axios.create({
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  public static getInstance(): ApiClient {
    if (!ApiClient.instance) {
      ApiClient.instance = new ApiClient();
    }
    return ApiClient.instance;
  }

  /**
   * Get user-friendly message for HTTP status codes
   */
  private getStatusCodeMessage(status: number): string {
    switch (status) {
      case 400:
        return 'Invalid request. Please check your input and try again.';
      case 401:
        return 'Authentication required. Please sign in again.';
      case 403:
        return 'Access denied. You do not have permission for this action.';
      case 404:
        return 'Resource not found. The requested item may have been deleted.';
      case 409:
        return 'Conflict occurred. The resource may have been modified by another user.';
      case 422:
        return 'Invalid data provided. Please check your input.';
      case 429:
        return 'Too many requests. Please wait a moment and try again.';
      default:
        return `Request failed with status ${status}. Please try again or contact support.`;
    }
  }

  /**
   * Setup request and response interceptors
   */
  private setupInterceptors(): void {
    // Request interceptor - Set baseURL dynamically and add auth token
    this.axiosInstance.interceptors.request.use(
      async (config: InternalAxiosRequestConfig) => {
        // Record user activity for API calls
        recordActivity();
        
        // Wait for AWS config to be loaded if available
        if (window.configReady) {
          await window.configReady;
        }

        // Read endpoint fresh from window.AWS_CONFIG (not cached awsConfig)
        const apiEndpoint = window.AWS_CONFIG?.API?.REST?.DRSOrchestration?.endpoint || '';
        config.baseURL = apiEndpoint;

        try {
          // Get the current authentication session
          const session = await fetchAuthSession();

          // Extract token (only idToken is available in AWS Amplify v6)
          let token = null;
          
          if (session.tokens?.idToken) {
            token = session.tokens.idToken.toString();
          }

          if (token && config.headers) {
            // Validate token format before sending
            if (typeof token !== 'string' || token.trim().length === 0) {
              console.error('Invalid token format:', {
                type: typeof token,
                length: token?.length,
                sample: token?.substring(0, 50) + '...'
              });
              throw new Error('Invalid authentication token format');
            }

            // Ensure clean token (remove any whitespace/newlines)
            const cleanToken = token.trim().replace(/\s+/g, '');
            
            // Validate JWT format (should have 3 parts separated by dots)
            const tokenParts = cleanToken.split('.');
            if (tokenParts.length !== 3) {
              console.error('Invalid JWT format - expected 3 parts, got:', {
                parts: tokenParts.length,
                tokenStart: cleanToken.substring(0, 50),
                tokenEnd: cleanToken.substring(cleanToken.length - 50)
              });
              throw new Error('Invalid JWT token format');
            }

            // Additional validation: check each part is base64-like
            const base64Pattern = /^[A-Za-z0-9+/=_-]+$/;
            for (let i = 0; i < tokenParts.length; i++) {
              if (!base64Pattern.test(tokenParts[i])) {
                console.error('JWT part contains invalid characters:', i + 1, tokenParts[i].substring(0, 20));
                throw new Error(`Invalid JWT token format - part ${i + 1} contains invalid characters`);
              }
            }

            config.headers.Authorization = `Bearer ${cleanToken}`;
          } else {
            console.warn('No auth token available:', {
              hasSession: !!session,
              hasTokens: !!session.tokens,
              tokenKeys: session.tokens ? Object.keys(session.tokens) : null
            });
          }
        } catch (error) {
          const err = error as Error;
          const sanitizedError = sanitizeForLogging({
            error: err?.message || 'Unknown error',
            name: err?.name
          });
          console.error('Error fetching auth token:', sanitizedError);
          throw error;
        }

        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor - Handle errors
    this.axiosInstance.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response) {
          // Server responded with error status
          const status = error.response.status;
          const data: unknown = error.response.data;

          if (status === 401) {
            // Unauthorized - token expired or invalid
            console.error('Authentication error - token expired or invalid');
            // Instead of hard redirect, throw error to let components handle auth failure
            throw new Error('Authentication required. Please sign in again.');
          } else if (status === 403) {
            // Forbidden - insufficient permissions
            const sanitizedMessage = sanitizeErrorMessage(data);
            console.error('Permission denied:', sanitizedMessage);
          } else if (status === 409 && data && typeof data === 'object' && 'error' in data && data.error === 'VERSION_CONFLICT') {
            // Optimistic locking conflict - resource modified concurrently
            const errorData = data as { message?: string; resourceId?: string; expectedVersion?: string; currentVersion?: string };
            const versionError = new Error(errorData.message || 'Resource was modified by another user. Please refresh and try again.');
            (versionError as Error & { isVersionConflict: boolean; resourceId?: string; expectedVersion?: string; currentVersion?: string }).isVersionConflict = true;
            (versionError as Error & { isVersionConflict: boolean; resourceId?: string; expectedVersion?: string; currentVersion?: string }).resourceId = errorData.resourceId;
            (versionError as Error & { isVersionConflict: boolean; resourceId?: string; expectedVersion?: string; currentVersion?: string }).expectedVersion = errorData.expectedVersion;
            (versionError as Error & { isVersionConflict: boolean; resourceId?: string; expectedVersion?: string; currentVersion?: string }).currentVersion = errorData.currentVersion;
            throw versionError;
          } else if (status >= 500) {
            // Server error - provide specific messages based on status code
            const sanitizedMessage = sanitizeErrorMessage(data);
            console.error('Server error:', sanitizedMessage);
            let serverErrorMessage = (data && typeof data === 'object' && 'message' in data) ? sanitizeErrorMessage(String(data.message)) : undefined;
            
            if (!serverErrorMessage) {
              switch (status) {
                case 500:
                  serverErrorMessage = 'Internal server error occurred. Please try again in a few moments.';
                  break;
                case 502:
                  serverErrorMessage = 'Service temporarily unavailable. Please try again shortly.';
                  break;
                case 503:
                  serverErrorMessage = 'Service is currently under maintenance. Please try again later.';
                  break;
                case 504:
                  serverErrorMessage = 'Server timeout occurred. Please try again.';
                  break;
                default:
                  serverErrorMessage = `Server error (${status}). Please contact support if this persists.`;
              }
            }
            
            throw new Error(serverErrorMessage);
          }

          // Provide specific error message or fallback with status code
          const errorMessage = (data && typeof data === 'object' && 'message' in data) ? sanitizeErrorMessage(String(data.message)) : this.getStatusCodeMessage(status);
          throw new Error(errorMessage);
        } else if (error.request) {
          // Request made but no response received
          const sanitizedRequest = sanitizeForLogging(error.request);
          console.error('No response from server:', sanitizedRequest);
          
          // Provide more specific error messages based on error type
          if (error.code === 'ECONNABORTED') {
            throw new Error('Request timed out. The server may be busy - please try again.');
          } else if (error.code === 'ERR_NETWORK') {
            throw new Error('Network connection failed. Please check your internet connection.');
          } else if (error.code === 'ERR_INTERNET_DISCONNECTED') {
            throw new Error('No internet connection. Please check your network and try again.');
          } else {
            throw new Error('Unable to reach the server. Please check your internet connection and try again.');
          }
        } else {
          // Something else happened
          const sanitizedMessage = sanitizeErrorMessage(error.message || '');
          console.error('Request error:', sanitizedMessage);
          
          // Provide more descriptive error for common issues
          if (error.message?.includes('CORS')) {
            throw new Error('Cross-origin request blocked. Please contact your administrator.');
          } else if (error.message?.includes('timeout')) {
            throw new Error('Request timed out. Please try again.');
          } else {
            throw error;
          }
        }
      }
    );
  }

  /**
   * Generic GET request
   */
  private async get<T>(path: string, params?: Record<string, unknown>): Promise<T> {
    const response = await this.axiosInstance.get<T>(path, { params });
    
    // API Gateway returns data directly (not in Lambda proxy format)
    return response.data;
  }

  /**
   * Generic POST request
   */
  private async post<T>(path: string, data?: unknown): Promise<T> {
    const response = await this.axiosInstance.post<T>(path, data);
    return response.data;
  }

  /**
   * Generic PUT request
   */
  private async put<T>(path: string, data?: unknown): Promise<T> {
    const response = await this.axiosInstance.put<T>(path, data);
    return response.data;
  }

  /**
   * Generic DELETE request
   */
  private async delete<T>(path: string, data?: unknown): Promise<T> {
    const config = data ? { data } : {};
    const response = await this.axiosInstance.delete<T>(path, config);
    return response.data;
  }

  // ============================================================================
  // Protection Groups API
  // ============================================================================

  /**
   * List all protection groups
   */
  public async listProtectionGroups(params?: { accountId?: string }): Promise<ProtectionGroup[]> {
    const response = await this.get<{ groups: ProtectionGroup[]; count: number }>('/protection-groups', params);
    // API returns {groups: [...], count: N}
    return response.groups || [];
  }

  /**
   * Get a specific protection group
   */
  public async getProtectionGroup(id: string): Promise<ProtectionGroup> {
    return this.get<ProtectionGroup>(`/protection-groups/${id}`);
  }

  /**
   * Create a new protection group
   */
  public async createProtectionGroup(
    data: CreateProtectionGroupRequest
  ): Promise<ProtectionGroup> {
    return this.post<ProtectionGroup>('/protection-groups', data);
  }

  /**
   * Update an existing protection group
   */
  public async updateProtectionGroup(
    id: string,
    data: UpdateProtectionGroupRequest
  ): Promise<ProtectionGroup> {
    return this.put<ProtectionGroup>(`/protection-groups/${id}`, data);
  }

  /**
   * Delete a protection group
   */
  public async deleteProtectionGroup(id: string): Promise<void> {
    return this.delete<void>(`/protection-groups/${id}`);
  }

  /**
   * Resolve protection group tags to actual servers
   * 
   * Queries DRS API to find servers matching the specified tags.
   * Used for previewing which servers will be included at execution time.
   * 
   * @param region - AWS region to query
   * @param tags - Tag key-value pairs (AND logic - all must match)
   * @returns List of resolved servers with their details
   */
  public async resolveProtectionGroupTags(
    region: string,
    tags: Record<string, string>
  ): Promise<{
    region: string;
    tags: Record<string, string>;
    resolvedServers: Array<{
      sourceServerID: string;  // Fixed: uppercase 'ID' to match DRSServer interface
      hostname: string;
      fqdn?: string;
      nameTag?: string;
      sourceInstanceId?: string;
      sourceIp?: string;
      sourceMac?: string;
      sourceRegion?: string;
      sourceAccount?: string;
      os?: string;
      state?: string;
      replicationState: string;
      lagDuration?: string;
      lastSeen?: string;
      hardware?: {
        cpus?: Array<{
          modelName: string;
          cores: number;
        }>;
        totalCores?: number;
        ramBytes?: number;
        ramGiB?: number;
        disks?: Array<{
          deviceName: string;
          bytes: number;
          sizeGiB: number;
        }>;
        totalDiskGiB?: number;
      };
      networkInterfaces?: Array<{
        ips: string[];
        macAddress: string;
        isPrimary: boolean;
      }>;
      drsTags?: Record<string, string>;
      tags: Record<string, string>;
      assignedToProtectionGroup?: {
        protectionGroupId: string;
        protectionGroupName: string;
      } | null;
      selectable?: boolean;
    }>;
    serverCount: number;
    resolvedAt: number;
  }> {
    return this.post(`/protection-groups/resolve`, { region, tags });
  }

  // ============================================================================
  // Recovery Plans API
  // ============================================================================

  /**
   * List all recovery plans
   */
  public async listRecoveryPlans(params?: { accountId?: string }): Promise<RecoveryPlan[]> {
    const response = await this.get<{ recoveryPlans: RecoveryPlan[]; count: number }>('/recovery-plans', params);
    return response.recoveryPlans || [];
  }

  /**
   * Get a specific recovery plan
   */
  public async getRecoveryPlan(id: string): Promise<RecoveryPlan> {
    return this.get<RecoveryPlan>(`/recovery-plans/${id}`);
  }

  /**
   * Create a new recovery plan
   */
  public async createRecoveryPlan(
    data: CreateRecoveryPlanRequest
  ): Promise<RecoveryPlan> {
    return this.post<RecoveryPlan>('/recovery-plans', data);
  }

  /**
   * Update an existing recovery plan
   */
  public async updateRecoveryPlan(
    id: string,
    data: UpdateRecoveryPlanRequest
  ): Promise<RecoveryPlan> {
    return this.put<RecoveryPlan>(`/recovery-plans/${id}`, data);
  }

  /**
   * Delete a recovery plan
   */
  public async deleteRecoveryPlan(id: string): Promise<void> {
    return this.delete<void>(`/recovery-plans/${id}`);
  }

  /**
   * Execute a recovery plan
   * 
   * Check for existing recovery instances for servers in a recovery plan.
   * Used to warn user before starting a new drill if instances exist.
   */
  public async checkExistingRecoveryInstances(planId: string): Promise<{
    hasExistingInstances: boolean;
    existingInstances: Array<{
      sourceServerId: string;
      recoveryInstanceId: string;
      ec2InstanceId: string;
      ec2InstanceState: string;
      sourceExecutionId?: string;
      sourcePlanName?: string;
      region: string;
    }>;
    instanceCount: number;
    planId: string;
  }> {
    return this.get(`/recovery-plans/${planId}/check-existing-instances`);
  }

  /**
   * Note: Backend expects POST to /executions (not /recovery-plans/{id}/execute)
   * with planId in the body, not as a path parameter.
   */
  public async executeRecoveryPlan(
    data: ExecuteRecoveryPlanRequest
  ): Promise<Execution> {
    // Backend now expects camelCase field names
    const backendRequest = {
      planId: data.planId || data.recoveryPlanId,  // Support both field names
      executionType: data.executionType,  // DRILL or RECOVERY from user selection
      initiatedBy: data.executedBy || 'unknown',
      dryRun: data.dryRun || false,
      topicArn: data.topicArn || ''
    };
    
    return this.post<Execution>('/executions', backendRequest);
  }

  // ============================================================================
  // Executions API
  // ============================================================================

  /**
   * List execution history
   */
  public async listExecutions(params?: {
    limit?: number;
    nextToken?: string;
    accountId?: string;
  }): Promise<PaginatedResponse<ExecutionListItem>> {
    return this.get<PaginatedResponse<ExecutionListItem>>('/executions', params);
  }

  /**
   * Get execution details
   */
  public async getExecution(executionId: string, bustCache = false): Promise<Execution> {
    // Add timestamp parameter to bust browser cache when explicitly requested
    const params = bustCache ? { _t: Date.now() } : undefined;
    return this.get<Execution>(`/executions/${executionId}`, params);
  }

  /**
   * Poll execution status until completion
   * 
   * Polls GET /executions/{executionId} every 5 seconds until:
   * - Status is COMPLETED, FAILED, PARTIAL, or CANCELLED
   * - Maximum polling duration (15 minutes) is reached
   * 
   * @param executionId - Execution ID to poll
   * @param onUpdate - Optional callback fired on each status update
   * @param pollInterval - Polling interval in ms (default: 5000)
   * @param maxDuration - Maximum polling duration in ms (default: 900000 = 15 min)
   * @returns Final execution status
   */
  public async pollExecutionStatus(
    executionId: string,
    onUpdate?: (execution: Execution) => void,
    pollInterval: number = 5000,
    maxDuration: number = 900000
  ): Promise<Execution> {
    const startTime = Date.now();
    const terminalStatuses = ['COMPLETED', 'FAILED', 'PARTIAL', 'CANCELLED'];

    while (Date.now() - startTime < maxDuration) {
      try {
        const execution = await this.getExecution(executionId);
        
        // Fire update callback if provided
        if (onUpdate) {
          onUpdate(execution);
        }

        // Check if execution reached terminal status
        if (terminalStatuses.includes(execution.status)) {
          return execution;
        }

        // Wait before next poll
        await new Promise(resolve => setTimeout(resolve, pollInterval));
      } catch (error) {
        console.error('Error polling execution status:', error);
        // Continue polling despite errors (execution might still be running)
        await new Promise(resolve => setTimeout(resolve, pollInterval));
      }
    }

    // Max duration reached - fetch final status
    try {
      const finalExecution = await this.getExecution(executionId);
      return finalExecution;
    } catch (error) {
      console.error('Error fetching final execution status:', error);
      throw new Error('Failed to retrieve final execution status after polling timeout');
    }
  }

  /**
   * Cancel a running execution
   */
  public async cancelExecution(executionId: string): Promise<void> {
    return this.post<void>(`/executions/${executionId}/cancel`);
  }

  /**
   * Pause a running execution
   */
  public async pauseExecution(executionId: string): Promise<void> {
    return this.post<void>(`/executions/${executionId}/pause`);
  }

  /**
   * Resume a paused execution
   */
  public async resumeExecution(executionId: string): Promise<void> {
    return this.post<void>(`/executions/${executionId}/resume`);
  }

  /**
   * Get recovery instances for an execution
   * 
   * Returns all EC2 recovery instances that were launched as part of this execution's waves.
   * This allows the frontend to show users exactly what instances will be terminated.
   * 
   * @param executionId - Execution ID to get recovery instances for
   * @returns List of recovery instances with details
   */
  public async getRecoveryInstances(executionId: string): Promise<{
    executionId: string;
    instances: Array<{
      instanceId: string;
      recoveryInstanceId: string;
      sourceServerId: string;
      region: string;
      waveName: string;
      waveNumber: number;
      jobId: string;
      status: string;
      hostname?: string;
      serverName?: string;
    }>;
    totalInstances: number;
    message: string;
  }> {
    return this.get(`/executions/${executionId}/recovery-instances`);
  }

  /**
   * Terminate all recovery instances from an execution
   * 
   * This will terminate all EC2 recovery instances that were launched
   * as part of this execution's waves.
   * 
   * @param executionId - Execution ID to terminate instances for
   * @returns Summary of terminated instances
   */
  public async terminateRecoveryInstances(executionId: string): Promise<{
    executionId: string;
    message: string;
    terminated: Array<{
      instanceId: string;
      region: string;
      previousState: string;
      currentState: string;
    }>;
    failed: Array<{
      instanceId: string;
      region: string;
      error: string;
    }>;
    totalFound: number;
    totalTerminated: number;
    totalFailed: number;
    alreadyTerminated?: boolean;
  }> {
    return this.post(`/executions/${executionId}/terminate-instances`);
  }

  /**
   * Get DRS job log items for an execution
   * 
   * Returns detailed progress events like:
   * - SNAPSHOT_START / SNAPSHOT_END
   * - CONVERSION_START / CONVERSION_END
   * - LAUNCH_START / LAUNCH_END
   * 
   * @param executionId - Execution ID
   * @param jobId - Optional specific job ID (if not provided, returns all waves)
   */
  public async getJobLogs(executionId: string, jobId?: string): Promise<{
    executionId: string;
    jobLogs: Array<{
      waveNumber: number;
      jobId: string;
      events: Array<{
        event: string;
        eventData: Record<string, unknown>;
        logDateTime: string;
        sourceServerId?: string;
        error?: string;
        conversionServerId?: string;
      }>;
      error?: string;
    }>;
  }> {
    const params = jobId ? `?jobId=${jobId}` : '';
    return this.get(`/executions/${executionId}/job-logs${params}`);
  }

  /**
   * Get termination job status for progress tracking
   */
  public async getTerminationStatus(executionId: string, jobIds: string[], region: string): Promise<{
    executionId: string;
    jobs: Array<{
      jobId: string;
      status: string;
      type: string;
      totalServers: number;
      completedServers: number;
      failedServers: number;
    }>;
    totalServers: number;
    completedServers: number;
    progressPercent: number;
    allCompleted: boolean;
    anyFailed: boolean;
  }> {
    const jobIdsParam = jobIds.join(',');
    return this.get(`/executions/${executionId}/termination-status?jobIds=${jobIdsParam}&region=${region}`);
  }

  /**
   * Delete all completed executions (bulk operation)
   * 
   * Safely removes only terminal state executions:
   * - COMPLETED, PARTIAL, FAILED, CANCELLED
   * 
   * Active executions (PENDING, POLLING, IN_PROGRESS, etc.) are preserved.
   * 
   * @returns Summary of deletion operation including counts
   */
  public async deleteCompletedExecutions(): Promise<{
    message: string;
    deletedCount: number;
    totalScanned: number;
    completedFound: number;
    activePreserved: number;
  }> {
    return this.delete<{
      message: string;
      deletedCount: number;
      totalScanned: number;
      completedFound: number;
      activePreserved: number;
    }>('/executions');
  }

  /**
   * Delete specific executions by their IDs (selective operation)
   * 
   * Safely removes only terminal state executions:
   * - COMPLETED, PARTIAL, FAILED, CANCELLED (without active DRS jobs)
   * 
   * Active executions are preserved and reported in the response.
   * 
   * @param executionIds - Array of execution IDs to delete
   * @returns Summary of deletion operation including counts and any failures
   */
  public async deleteExecutions(executionIds: string[]): Promise<{
    message: string;
    deletedCount: number;
    totalRequested: number;
    notFound: number;
    activeSkipped: number;
    failed: number;
    notFoundIds?: string[];
    activeExecutionsSkipped?: Array<{
      executionId: string;
      status: string;
      reason: string;
    }>;
    failedDeletes?: Array<{
      executionId: string;
      error: string;
    }>;
    warning?: string;
  }> {
    // Backend expects IDs as query parameter: DELETE /executions?ids=id1,id2,id3
    const idsParam = executionIds.join(',');
    const result = await this.delete<{
      message: string;
      deletedCount: number;
      totalRequested: number;
      notFound: number;
      activeSkipped: number;
      failed: number;
      notFoundIds?: string[];
      activeExecutionsSkipped?: Array<{
        executionId: string;
        status: string;
        reason: string;
      }>;
      failedDeletes?: Array<{
        executionId: string;
        error: string;
      }>;
      warning?: string;
    }>(`/executions?ids=${encodeURIComponent(idsParam)}`);
    
    return result;
  }

  // ============================================================================
  // DRS Source Servers API
  // ============================================================================

  /**
   * List DRS source servers in a region
   * 
   * @param region - AWS region
   * @param accountId - Optional account ID for cross-account queries
   * @param currentProtectionGroupId - Optional PG ID to exclude when editing
   * @param filterByProtectionGroup - Optional PG ID to filter servers (only show servers in this PG)
   */
  public async listDRSSourceServers(
    region: string, 
    accountId?: string,
    currentProtectionGroupId?: string,
    filterByProtectionGroup?: string
  ): Promise<{
    servers: DRSServer[];
    serverCount: number;
    region: string;
  }> {
    const queryParams: Record<string, string> = { region };
    if (accountId) {
      queryParams.accountId = accountId;
    }
    if (currentProtectionGroupId) {
      queryParams.currentProtectionGroupId = currentProtectionGroupId;
    }
    if (filterByProtectionGroup) {
      queryParams.filterByProtectionGroup = filterByProtectionGroup;
    }
    
    const response = await this.get<{
      servers: DRSServer[];
      serverCount: number;
      region: string;
    }>('/drs/source-servers', queryParams);
    
    return response;
  }

  /**
   * Get DRS quotas and current usage for a region
   * 
   * Returns account capacity metrics including:
   * - Replicating servers count vs limit (300 hard limit)
   * - Concurrent jobs count vs limit (20 hard limit)
   * - Servers in active jobs vs limit (500 hard limit)
   * 
   * @param accountId - AWS account ID to check quotas for
   * @param region - Optional AWS region (defaults to current region)
   */
  public async getDRSQuotas(accountId: string, region?: string): Promise<DRSQuotaStatus> {
    const params = new URLSearchParams({ accountId });
    if (region) {
      params.append('region', region);
    }
    return this.get<DRSQuotaStatus>(`/drs/quotas?${params.toString()}`);
  }



  /**
   * Target Account Management
   */
  public async getTargetAccounts(): Promise<Array<{
    accountId: string;
    accountName: string;
    roleArn: string;
    isCurrentAccount: boolean;
    status: 'ACTIVE' | 'INACTIVE' | 'ERROR';
    lastValidated?: string;
    error?: string;
  }>> {
    return this.get<Array<{
      accountId: string;
      accountName: string;
      roleArn: string;
      isCurrentAccount: boolean;
      status: 'ACTIVE' | 'INACTIVE' | 'ERROR';
      lastValidated?: string;
      error?: string;
    }>>('/accounts/targets');
  }

  /**
   * Get a single target account with staging accounts
   */
  public async getTargetAccount(accountId: string): Promise<{
    accountId: string;
    accountName: string;
    roleArn?: string;
    externalId?: string;
    stagingAccounts: Array<{
      accountId: string;
      accountName: string;
      roleArn: string;
      externalId: string;
      addedAt?: string;
      addedBy?: string;
    }>;
    status: string;
    isCurrentAccount?: boolean;
    createdAt?: string;
    updatedAt?: string;
  }> {
    return this.get<{
      accountId: string;
      accountName: string;
      roleArn?: string;
      externalId?: string;
      stagingAccounts: Array<{
        accountId: string;
        accountName: string;
        roleArn: string;
        externalId: string;
        addedAt?: string;
        addedBy?: string;
      }>;
      status: string;
      isCurrentAccount?: boolean;
      createdAt?: string;
      updatedAt?: string;
    }>(`/accounts/targets/${accountId}`);
  }

  /**
   * Get current account information for setup wizard
   */
  public async getCurrentAccount(): Promise<{
    accountId: string;
    accountName: string;
    isCurrentAccount: boolean;
  }> {
    return this.get<{
      accountId: string;
      accountName: string;
      isCurrentAccount: boolean;
    }>('/accounts/current');
  }

  public async createTargetAccount(accountData: {
    accountId: string;
    accountName: string;
    roleArn: string;
  }): Promise<{
    accountId: string;
    accountName: string;
    roleArn: string;
    isCurrentAccount: boolean;
    status: 'ACTIVE' | 'INACTIVE' | 'ERROR';
    lastValidated?: string;
    error?: string;
    message?: string;
    discoveredStagingAccounts?: string[];
  }> {
    return this.post<{
      accountId: string;
      accountName: string;
      roleArn: string;
      isCurrentAccount: boolean;
      status: 'ACTIVE' | 'INACTIVE' | 'ERROR';
      lastValidated?: string;
      error?: string;
      message?: string;
      discoveredStagingAccounts?: string[];
    }>('/accounts/targets', accountData);
  }

  public async updateTargetAccount(accountId: string, accountData: {
    accountName?: string;
    roleArn?: string;
  }): Promise<{
    accountId: string;
    accountName: string;
    roleArn: string;
    isCurrentAccount: boolean;
    status: 'ACTIVE' | 'INACTIVE' | 'ERROR';
    lastValidated?: string;
    error?: string;
  }> {
    return this.put<{
      accountId: string;
      accountName: string;
      roleArn: string;
      isCurrentAccount: boolean;
      status: 'ACTIVE' | 'INACTIVE' | 'ERROR';
      lastValidated?: string;
      error?: string;
    }>(`/accounts/targets/${accountId}`, accountData);
  }

  public async deleteTargetAccount(accountId: string): Promise<{ message: string }> {
    return this.delete<{ message: string }>(`/accounts/targets/${accountId}`);
  }

  public async validateTargetAccount(accountId: string): Promise<{
    accountId: string;
    valid: boolean;
    message: string;
    details?: {
      roleExists: boolean;
      roleAccessible: boolean;
      requiredPermissions: boolean;
      error?: string;
    };
  }> {
    return this.post<{
      accountId: string;
      valid: boolean;
      message: string;
      details?: {
        roleExists: boolean;
        roleAccessible: boolean;
        requiredPermissions: boolean;
        error?: string;
      };
    }>(`/accounts/targets/${accountId}/validate`, {});
  }

  /**
   * Trigger on-demand DRS tag synchronization
   * Syncs EC2 instance tags to DRS source servers across all regions
   * @param accountId - AWS account ID to sync tags for
   */
  public async triggerTagSync(accountId?: string): Promise<{ message: string; functionName: string; statusCode: number }> {
    const body = accountId ? { accountId } : {};
    return this.post<{ message: string; functionName: string; statusCode: number }>('/drs/tag-sync', body);
  }

  /**
   * Discover staging accounts from DRS extended source servers
   * 
   * Automatically finds staging accounts by querying DRS for extended source servers
   * and extracting their staging account IDs. This should be called when:
   * - Extended source servers are added/removed in DRS
   * - User wants to refresh staging account list
   * - Opening settings modal to show current state
   * 
   * @param targetAccountId - Target account ID to discover staging accounts for
   * @returns List of discovered staging accounts with server counts
   */
  public async discoverStagingAccounts(targetAccountId: string): Promise<{
    targetAccountId: string;
    stagingAccounts: Array<{
      accountId: string;
      accountName: string;
      serverCount: number;
    }>;
    totalServers: number;
    message: string;
  }> {
    return this.get(`/accounts/targets/${targetAccountId}/staging-accounts/discover`);
  }

  // ============================================================================
  // Per-Server Launch Configuration API
  // ============================================================================

  /**
   * Get per-server launch configuration
   * 
   * @param groupId - Protection group ID
   * @param serverId - Source server ID
   * @returns Server launch configuration with effective config preview
   */
  public async getServerLaunchConfig(
    groupId: string,
    serverId: string
  ): Promise<{
    sourceServerId: string;
    instanceId?: string;
    instanceName?: string;
    tags?: Record<string, string>;
    useGroupDefaults: boolean;
    launchTemplate?: Partial<LaunchConfig>;
    effectiveConfig?: LaunchConfig;
  }> {
    return this.get(`/protection-groups/${groupId}/servers/${serverId}/launch-config`);
  }

  /**
   * Update per-server launch configuration
   * 
   * @param groupId - Protection group ID
   * @param serverId - Source server ID
   * @param config - Server launch configuration to apply
   * @returns Updated server configuration
   */
  public async updateServerLaunchConfig(
    groupId: string,
    serverId: string,
    config: {
      useGroupDefaults: boolean;
      launchTemplate?: Partial<LaunchConfig>;
    }
  ): Promise<{
    sourceServerId: string;
    instanceId?: string;
    instanceName?: string;
    tags?: Record<string, string>;
    useGroupDefaults: boolean;
    launchTemplate?: Partial<LaunchConfig>;
    effectiveConfig?: LaunchConfig;
    message: string;
  }> {
    return this.put(`/protection-groups/${groupId}/servers/${serverId}/launch-config`, config);
  }

  /**
   * Delete per-server launch configuration (reset to group defaults)
   * 
   * @param groupId - Protection group ID
   * @param serverId - Source server ID
   * @returns Confirmation message
   */
  public async deleteServerLaunchConfig(
    groupId: string,
    serverId: string
  ): Promise<{
    message: string;
    sourceServerId: string;
  }> {
    return this.delete(`/protection-groups/${groupId}/servers/${serverId}/launch-config`);
  }

  /**
   * Validate static private IP address
   * 
   * Checks if the IP is:
   * - Valid IPv4 format
   * - Within subnet CIDR range
   * - Not in reserved range (first 4, last 1)
   * - Available (not already assigned)
   * 
   * @param groupId - Protection group ID
   * @param serverId - Source server ID
   * @param ip - Static private IP address to validate
   * @param subnetId - Target subnet ID
   * @returns Validation result with detailed feedback
   */
  public async validateStaticIP(
    groupId: string,
    serverId: string,
    ip: string,
    subnetId: string
  ): Promise<{
    valid: boolean;
    ip: string;
    subnetId: string;
    error?: string;
    message?: string;
    details?: {
      inCidrRange?: boolean;
      notReserved?: boolean;
      available?: boolean;
      subnetCidr?: string;
    };
    conflictingResource?: {
      type: string;
      id: string;
      name?: string;
      isDrsResource?: boolean;
    };
  }> {
    return this.post(`/protection-groups/${groupId}/servers/${serverId}/validate-ip`, {
      staticPrivateIp: ip,
      subnetId,
    });
  }

  /**
   * Bulk update server launch configurations
   * 
   * Applies the same configuration to multiple servers at once.
   * Validates all configurations before applying.
   * 
   * @param groupId - Protection group ID
   * @param configs - Array of server configurations to apply
   * @returns Summary of applied/failed configurations
   */
  public async bulkUpdateServerConfigs(
    groupId: string,
    configs: Array<{
      serverId: string;
      useGroupDefaults: boolean;
      launchTemplate?: Partial<LaunchConfig>;
    }>
  ): Promise<{
    message: string;
    totalRequested: number;
    successCount: number;
    failureCount: number;
    results: Array<{
      serverId: string;
      success: boolean;
      message?: string;
      error?: string;
    }>;
  }> {
    return this.post(`/protection-groups/${groupId}/servers/bulk-launch-config`, {
      servers: configs,
    });
  }

  /**
   * Get server configuration change history (audit log)
   * 
   * Retrieves chronological list of all configuration changes for a server.
   * Supports date range filtering.
   * 
   * @param groupId - Protection group ID
   * @param serverId - Source server ID
   * @param params - Optional query parameters (startDate, endDate)
   * @returns Array of configuration change entries
   */
  public async getServerConfigHistory(
    groupId: string,
    serverId: string,
    params?: Record<string, string>
  ): Promise<Array<{
    timestamp: string;
    user: string;
    action: string;
    protectionGroupId: string;
    serverId: string;
    changes: Array<{
      field: string;
      oldValue: string | null;
      newValue: string | null;
    }>;
  }>> {
    return this.get(`/protection-groups/${groupId}/servers/${serverId}/audit-log`, params);
  }

  // ============================================================================
  // EC2 Resources API (for Launch Config dropdowns)
  // ============================================================================

  /**
   * Get VPC subnets for dropdown selection
   */
  public async getEC2Subnets(region: string): Promise<SubnetOption[]> {
    const response = await this.get<{ subnets: SubnetOption[] }>('/ec2/subnets', { region });
    return response.subnets || [];
  }

  /**
   * Get security groups for dropdown selection
   */
  public async getEC2SecurityGroups(region: string, vpcId?: string): Promise<SecurityGroupOption[]> {
    const params: Record<string, string> = { region };
    if (vpcId) params.vpcId = vpcId;
    const response = await this.get<{ securityGroups: SecurityGroupOption[] }>('/ec2/security-groups', params);
    return response.securityGroups || [];
  }

  /**
   * Get IAM instance profiles for dropdown selection
   */
  public async getEC2InstanceProfiles(region: string): Promise<InstanceProfileOption[]> {
    const response = await this.get<{ instanceProfiles: InstanceProfileOption[] }>('/ec2/instance-profiles', { region });
    return response.instanceProfiles || [];
  }

  /**
   * Get EC2 instance types for dropdown selection
   */
  public async getEC2InstanceTypes(region: string): Promise<InstanceTypeOption[]> {
    const response = await this.get<{ instanceTypes: InstanceTypeOption[] }>('/ec2/instance-types', { region });
    return response.instanceTypes || [];
  }

  // ============================================================================
  // Configuration Export/Import API
  // ============================================================================

  /**
   * Export all Protection Groups and Recovery Plans to JSON
   */
  public async exportConfiguration(): Promise<{
    metadata: {
      schemaVersion: string;
      exportedAt: string;
      sourceRegion: string;
      exportedBy: string;
    };
    protectionGroups: Array<Record<string, unknown>>;
    recoveryPlans: Array<Record<string, unknown>>;
  }> {
    return this.get('/config/export');
  }

  /**
   * Import Protection Groups and Recovery Plans from JSON
   * 
   * @param config - Configuration data to import
   * @param dryRun - If true, validate without making changes
   */
  public async importConfiguration(
    config: Record<string, unknown>,
    dryRun: boolean = false
  ): Promise<{
    success: boolean;
    dryRun: boolean;
    correlationId: string;
    summary: {
      protectionGroups: { created: number; skipped: number; failed: number };
      recoveryPlans: { created: number; skipped: number; failed: number };
    };
    created: Array<{ type: string; name: string; details?: Record<string, unknown> }>;
    skipped: Array<{ type: string; name: string; reason: string; details?: Record<string, unknown> }>;
    failed: Array<{ type: string; name: string; reason: string; details?: Record<string, unknown> }>;
  }> {
    return this.post('/config/import', { config, dryRun });
  }

  // ============================================================================
  // Tag Sync Configuration API
  // ============================================================================

  /**
   * Get current tag sync configuration settings
   */
  public async getTagSyncSettings(): Promise<{
    enabled: boolean;
    intervalHours: number;
    scheduleExpression: string;
    ruleName: string;
    lastModified: string | null;
    message?: string;
  }> {
    return this.get('/config/tag-sync');
  }

  /**
   * Update tag sync configuration settings
   */
  public async updateTagSyncSettings(settings: {
    enabled: boolean;
    intervalHours?: number;
  }): Promise<{
    message: string;
    enabled: boolean;
    intervalHours: number;
    scheduleExpression: string;
    ruleName: string;
    lastModified: string | null;
  }> {
    return this.put('/config/tag-sync', settings);
  }

  // ============================================================================
  // Health Check API
  // ============================================================================

  /**
   * Health check endpoint
   */
  public async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.get<{ status: string; timestamp: string }>('/health');
  }
}

// Create singleton instance
const apiClient = ApiClient.getInstance();

// Export the singleton instance
export default apiClient;

// Export individual methods for convenience
export const {
  listProtectionGroups,
  getProtectionGroup,
  createProtectionGroup,
  updateProtectionGroup,
  deleteProtectionGroup,
  resolveProtectionGroupTags,
  listRecoveryPlans,
  getRecoveryPlan,
  createRecoveryPlan,
  updateRecoveryPlan,
  deleteRecoveryPlan,
  executeRecoveryPlan,
  listExecutions,
  getExecution,
  cancelExecution,
  pauseExecution,
  resumeExecution,
  deleteCompletedExecutions,
  getServerLaunchConfig,
  updateServerLaunchConfig,
  deleteServerLaunchConfig,
  validateStaticIP,
  bulkUpdateServerConfigs,
  getServerConfigHistory,
  exportConfiguration,
  importConfiguration,
  getTagSyncSettings,
  updateTagSyncSettings,
  triggerTagSync,
  healthCheck,
} = apiClient;
