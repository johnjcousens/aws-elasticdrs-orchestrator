/**
 * DRS Agent Deployment Types
 */

export interface DRSAgentDeploymentRequest {
  account_id: string;
  source_region: string;
  target_region: string;
  role_arn?: string;
  external_id?: string;
  wait_for_completion?: boolean;
  timeout_seconds?: number;
}

export interface DRSSourceServer {
  source_server_id: string;
  hostname: string;
  replication_state: string;
  last_launch_result: string;
}

export interface DRSAgentDeploymentResult {
  status: 'success' | 'error' | 'no_instances' | 'partial_failure';
  account_id: string;
  source_region: string;
  target_region: string;
  instances_discovered?: number;
  instances_online?: number;
  instances_deployed?: number;
  command_id?: string;
  command_results?: {
    status: string;
    success_count?: number;
    failed_count?: number;
    invocations?: Array<{
      instance_id: string;
      status: string;
      status_details: string;
    }>;
  };
  source_servers?: DRSSourceServer[];
  duration_seconds?: number;
  timestamp?: string;
  message?: string;
  error?: string;
}

export interface DRSAgentDeploymentStatus {
  deployment_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  account_id: string;
  source_region: string;
  target_region: string;
  started_at: string;
  completed_at?: string;
  progress?: {
    current: number;
    total: number;
    message: string;
  };
  result?: DRSAgentDeploymentResult;
}
