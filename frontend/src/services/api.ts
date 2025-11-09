/**
 * API Service Layer
 * 
 * Handles all HTTP communication with the backend API Gateway.
 * Uses AWS Amplify for authentication and Axios for HTTP requests.
 */

import axios, { AxiosError } from 'axios';
import type { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { fetchAuthSession } from 'aws-amplify/auth';
import { API_NAME } from '../aws-config';
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
  ApiResponse,
  PaginatedResponse,
} from '../types';

// API configuration
const API_TIMEOUT = 30000; // 30 seconds
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

/**
 * API Client Class
 * 
 * Singleton class that manages all API requests with automatic
 * authentication token injection and error handling.
 */
class ApiClient {
  private axiosInstance: AxiosInstance;
  private apiEndpoint: string = '';

  constructor() {
    this.axiosInstance = axios.create({
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  /**
   * Initialize the API client with the endpoint
   */
  public initialize(endpoint: string): void {
    this.apiEndpoint = endpoint;
    this.axiosInstance.defaults.baseURL = endpoint;
  }

  /**
   * Setup request and response interceptors
   */
  private setupInterceptors(): void {
    // Request interceptor - Add authentication token
    this.axiosInstance.interceptors.request.use(
      async (config: InternalAxiosRequestConfig) => {
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
    return this.get<ProtectionGroup[]>('/protection-groups');
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

  // ============================================================================
  // Recovery Plans API
  // ============================================================================

  /**
   * List all recovery plans
   */
  public async listRecoveryPlans(): Promise<RecoveryPlan[]> {
    return this.get<RecoveryPlan[]>('/recovery-plans');
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
   */
  public async executeRecoveryPlan(
    id: string,
    data: ExecuteRecoveryPlanRequest
  ): Promise<Execution> {
    return this.post<Execution>(`/recovery-plans/${id}/execute`, data);
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
  initialize,
  listProtectionGroups,
  getProtectionGroup,
  createProtectionGroup,
  updateProtectionGroup,
  deleteProtectionGroup,
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
  healthCheck,
} = apiClient;
