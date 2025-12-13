/**
 * API Service Layer
 * 
 * Handles all HTTP communication with the backend API Gateway.
 * Uses AWS Amplify for authentication and Axios for HTTP requests.
 */

import axios, { AxiosError } from 'axios';
import type { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { fetchAuthSession } from 'aws-amplify/auth';
import { awsConfig } from '../aws-config';
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
  private axiosInstance: AxiosInstance;

  constructor() {
    // Don't read endpoint here - will be set dynamically in interceptor
    this.axiosInstance = axios.create({
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  /**
   * Setup request and response interceptors
   */
  private setupInterceptors(): void {
    // Request interceptor - Set baseURL dynamically and add auth token
    this.axiosInstance.interceptors.request.use(
      async (config: InternalAxiosRequestConfig) => {
        // Read endpoint fresh on each request (after window.AWS_CONFIG is loaded)
        const apiEndpoint = awsConfig.API?.REST?.DRSOrchestration?.endpoint || '';
        config.baseURL = apiEndpoint;

        try {
          // Get the current authentication session
          const session = await fetchAuthSession();
          const token = session.tokens?.idToken?.toString();

          if (token && config.headers) {
            config.headers.Authorization = `Bearer ${token}`;
          }
        } catch (error) {
          console.error('Error fetching auth token:', error);
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
          const data: any = error.response.data;

          if (status === 401) {
            // Unauthorized - token expired or invalid
            console.error('Authentication error - redirecting to login');
            // Trigger re-authentication
            window.location.href = '/login';
          } else if (status === 403) {
            // Forbidden - insufficient permissions
            console.error('Permission denied:', data);
          } else if (status === 409 && data?.error === 'VERSION_CONFLICT') {
            // Optimistic locking conflict - resource was modified by another user
            const versionError = new Error(data?.message || 'Resource was modified by another user. Please refresh and try again.');
            (versionError as any).isVersionConflict = true;
            (versionError as any).resourceId = data?.resourceId;
            (versionError as any).expectedVersion = data?.expectedVersion;
            (versionError as any).currentVersion = data?.currentVersion;
            throw versionError;
          } else if (status >= 500) {
            // Server error
            console.error('Server error:', data);
          }

          throw new Error(data?.message || `API Error: ${status}`);
        } else if (error.request) {
          // Request made but no response received
          console.error('No response from server:', error.request);
          throw new Error('No response from server. Please check your connection.');
        } else {
          // Something else happened
          console.error('Request error:', error.message);
          throw error;
        }
      }
    );
  }

  /**
   * Generic GET request
   */
  private async get<T>(path: string, params?: Record<string, any>): Promise<T> {
    const response = await this.axiosInstance.get<T>(path, { params });
    return response.data;
  }

  /**
   * Generic POST request
   */
  private async post<T>(path: string, data?: any): Promise<T> {
    const response = await this.axiosInstance.post<T>(path, data);
    return response.data;
  }

  /**
   * Generic PUT request
   */
  private async put<T>(path: string, data?: any): Promise<T> {
    const response = await this.axiosInstance.put<T>(path, data);
    return response.data;
  }

  /**
   * Generic DELETE request
   */
  private async delete<T>(path: string): Promise<T> {
    const response = await this.axiosInstance.delete<T>(path);
    return response.data;
  }

  // ============================================================================
  // Protection Groups API
  // ============================================================================

  /**
   * List all protection groups
   */
  public async listProtectionGroups(): Promise<ProtectionGroup[]> {
    const response = await this.get<{ groups: ProtectionGroup[]; count: number }>('/protection-groups');
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
      sourceServerId: string;
      hostname: string;
      replicationState: string;
      tags: Record<string, string>;
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
  public async listRecoveryPlans(): Promise<RecoveryPlan[]> {
    const response = await this.get<{ plans: RecoveryPlan[]; count: number }>('/recovery-plans');
    // API returns {plans: [...], count: N}
    return response.plans || [];
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
   * Note: Backend expects POST to /executions (not /recovery-plans/{id}/execute)
   * with PlanId in the body, not as a path parameter.
   */
  public async executeRecoveryPlan(
    data: ExecuteRecoveryPlanRequest
  ): Promise<Execution> {
    // Transform frontend request to backend format
    const backendRequest = {
      PlanId: data.recoveryPlanId,
      ExecutionType: data.executionType,  // DRILL or RECOVERY from user selection
      InitiatedBy: data.executedBy || 'unknown',
      DryRun: data.dryRun || false,
      TopicArn: data.topicArn || ''
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
  }): Promise<PaginatedResponse<ExecutionListItem>> {
    return this.get<PaginatedResponse<ExecutionListItem>>('/executions', params);
  }

  /**
   * Get execution details
   */
  public async getExecution(executionId: string): Promise<Execution> {
    return this.get<Execution>(`/executions/${executionId}`);
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
    const finalExecution = await this.getExecution(executionId);
    return finalExecution;
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

  // ============================================================================
  // DRS Source Servers API
  // ============================================================================

  /**
   * List DRS source servers in a region
   * 
   * @param region - AWS region
   * @param currentProtectionGroupId - Optional PG ID to exclude when editing
   * @param filterByProtectionGroup - Optional PG ID to filter servers (only show servers in this PG)
   */
  public async listDRSSourceServers(
    region: string, 
    currentProtectionGroupId?: string,
    filterByProtectionGroup?: string
  ): Promise<any> {
    const params = new URLSearchParams({ region });
    if (currentProtectionGroupId) {
      params.append('currentProtectionGroupId', currentProtectionGroupId);
    }
    if (filterByProtectionGroup) {
      params.append('filterByProtectionGroup', filterByProtectionGroup);
    }
    return this.get<any>(`/drs/source-servers?${params.toString()}`);
  }

  /**
   * Get DRS quotas and current usage for a region
   * 
   * Returns account capacity metrics including:
   * - Replicating servers count vs limit (300 hard limit)
   * - Concurrent jobs count vs limit (20 hard limit)
   * - Servers in active jobs vs limit (500 hard limit)
   * 
   * @param region - AWS region to check quotas for
   */
  public async getDRSQuotas(region: string): Promise<any> {
    return this.get<any>(`/drs/quotas?region=${region}`);
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
const apiClient = new ApiClient();

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
  healthCheck,
} = apiClient;
