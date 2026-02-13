#!/usr/bin/env python3
"""
Complete DR Workflow Example using Direct Lambda Invocation

This script demonstrates a complete disaster recovery workflow using direct
Lambda invocations without API Gateway or Cognito authentication.

Workflow Steps:
1. List protection groups and recovery plans
2. Start a recovery execution (DRILL mode)
3. Monitor execution progress in real-time
4. Get recovery instance details
5. Terminate recovery instances after testing

Requirements:
- AWS credentials configured (AWS CLI profile, environment variables, or IAM role)
- IAM permissions for lambda:InvokeFunction on DRS Orchestration Lambda functions
- Python 3.8+
- boto3 library

Usage:
    python complete_dr_workflow.py --plan-id <recovery-plan-id> [--environment test]
    python complete_dr_workflow.py --list-plans  # List available recovery plans
    python complete_dr_workflow.py --help        # Show help message
"""

import boto3
import json
import time
import sys
import argparse
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class DROrchestrationClient:
    """
    Client for AWS DRS Orchestration Platform using direct Lambda invocation.
    
    This client provides methods to interact with the DRS Orchestration Platform
    without requiring API Gateway or Cognito authentication. It uses IAM-based
    authorization through direct Lambda function invocation.
    """
    
    def __init__(self, environment: str = 'test', region: str = 'us-east-1'):
        """
        Initialize the DR Orchestration client.
        
        Args:
            environment: Deployment environment (dev, test, staging, prod)
            region: AWS region where Lambda functions are deployed
        """
        self.environment = environment
        self.region = region
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.project_name = 'hrp-drs-tech-adapter'
        
        # Function names
        self.query_handler = f'{self.project_name}-query-handler-{environment}'
        self.execution_handler = f'{self.project_name}-execution-handler-{environment}'
        self.data_mgmt_handler = f'{self.project_name}-data-management-handler-{environment}'
        
        logger.info(f"Initialized DR Orchestration client for environment: {environment}")
    
    def _invoke_lambda(self, function_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke a Lambda function and return the parsed response.
        
        Args:
            function_name: Name of the Lambda function to invoke
            payload: JSON payload to send to the function
            
        Returns:
            Parsed JSON response from the Lambda function
            
        Raises:
            Exception: If Lambda invocation fails or returns an error
        """
        try:
            logger.debug(f"Invoking {function_name} with payload: {json.dumps(payload, indent=2)}")
            
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            # Parse response
            result = json.loads(response['Payload'].read())
            
            # Check for errors in response
            if 'error' in result:
                error_msg = f"{result['error']}: {result.get('message', 'Unknown error')}"
                logger.error(f"Lambda returned error: {error_msg}")
                raise Exception(error_msg)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to invoke {function_name}: {str(e)}")
            raise
    
    # Query Handler Operations
    
    def list_protection_groups(self) -> List[Dict[str, Any]]:
        """
        List all protection groups.
        
        Returns:
            List of protection group dictionaries
        """
        logger.info("Listing protection groups...")
        result = self._invoke_lambda(
            self.query_handler,
            {"operation": "list_protection_groups"}
        )
        
        groups = result.get('protectionGroups', [])
        logger.info(f"Found {len(groups)} protection groups")
        return groups
    
    def get_protection_group(self, group_id: str) -> Dict[str, Any]:
        """
        Get details of a specific protection group.
        
        Args:
            group_id: Protection group ID
            
        Returns:
            Protection group details
        """
        logger.info(f"Getting protection group: {group_id}")
        return self._invoke_lambda(
            self.query_handler,
            {
                "operation": "get_protection_group",
                "groupId": group_id
            }
        )
    
    def list_recovery_plans(self) -> List[Dict[str, Any]]:
        """
        List all recovery plans.
        
        Returns:
            List of recovery plan dictionaries
        """
        logger.info("Listing recovery plans...")
        result = self._invoke_lambda(
            self.query_handler,
            {"operation": "list_recovery_plans"}
        )
        
        plans = result.get('recoveryPlans', [])
        logger.info(f"Found {len(plans)} recovery plans")
        return plans
    
    def get_recovery_plan(self, plan_id: str) -> Dict[str, Any]:
        """
        Get details of a specific recovery plan.
        
        Args:
            plan_id: Recovery plan ID
            
        Returns:
            Recovery plan details including waves
        """
        logger.info(f"Getting recovery plan: {plan_id}")
        return self._invoke_lambda(
            self.query_handler,
            {
                "operation": "get_recovery_plan",
                "planId": plan_id
            }
        )
    
    def list_executions(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List recovery plan executions.
        
        Args:
            status: Optional status filter (RUNNING, PAUSED, COMPLETED, FAILED, CANCELLED)
            
        Returns:
            List of execution dictionaries
        """
        logger.info(f"Listing executions{f' with status={status}' if status else ''}...")
        
        payload = {"operation": "list_executions"}
        if status:
            payload["queryParams"] = {"status": status}
        
        result = self._invoke_lambda(self.query_handler, payload)
        
        executions = result.get('executions', [])
        logger.info(f"Found {len(executions)} executions")
        return executions
    
    def get_execution(self, execution_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Execution details including wave status
        """
        logger.info(f"Getting execution: {execution_id}")
        return self._invoke_lambda(
            self.query_handler,
            {
                "operation": "get_execution",
                "executionId": execution_id
            }
        )
    
    # Execution Handler Operations
    
    def start_execution(
        self,
        plan_id: str,
        execution_type: str = 'DRILL',
        initiated_by: str = 'automation'
    ) -> Dict[str, Any]:
        """
        Start a new recovery plan execution.
        
        Args:
            plan_id: Recovery plan ID to execute
            execution_type: DRILL or RECOVERY
            initiated_by: Identifier of who/what started the execution
            
        Returns:
            Execution start response with executionId and status
        """
        logger.info(f"Starting {execution_type} execution for plan: {plan_id}")
        
        result = self._invoke_lambda(
            self.execution_handler,
            {
                "operation": "start_execution",
                "parameters": {
                    "planId": plan_id,
                    "executionType": execution_type,
                    "initiatedBy": initiated_by
                }
            }
        )
        
        logger.info(f"Execution started: {result.get('executionId')}")
        return result
    
    def cancel_execution(self, execution_id: str, reason: str = '') -> Dict[str, Any]:
        """
        Cancel a running execution.
        
        Args:
            execution_id: Execution ID to cancel
            reason: Optional reason for cancellation
            
        Returns:
            Cancellation response
        """
        logger.info(f"Cancelling execution: {execution_id}")
        
        payload = {
            "operation": "cancel_execution",
            "parameters": {"executionId": execution_id}
        }
        if reason:
            payload["parameters"]["reason"] = reason
        
        return self._invoke_lambda(self.execution_handler, payload)
    
    def pause_execution(self, execution_id: str, reason: str = '') -> Dict[str, Any]:
        """
        Pause a running execution at the next wave boundary.
        
        Args:
            execution_id: Execution ID to pause
            reason: Optional reason for pausing
            
        Returns:
            Pause response
        """
        logger.info(f"Pausing execution: {execution_id}")
        
        payload = {
            "operation": "pause_execution",
            "parameters": {"executionId": execution_id}
        }
        if reason:
            payload["parameters"]["reason"] = reason
        
        return self._invoke_lambda(self.execution_handler, payload)
    
    def resume_execution(self, execution_id: str) -> Dict[str, Any]:
        """
        Resume a paused execution.
        
        Args:
            execution_id: Execution ID to resume
            
        Returns:
            Resume response
        """
        logger.info(f"Resuming execution: {execution_id}")
        
        return self._invoke_lambda(
            self.execution_handler,
            {
                "operation": "resume_execution",
                "parameters": {"executionId": execution_id}
            }
        )
    
    def get_recovery_instances(self, execution_id: str) -> Dict[str, Any]:
        """
        Get details of all recovery instances from an execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Recovery instances details
        """
        logger.info(f"Getting recovery instances for execution: {execution_id}")
        
        return self._invoke_lambda(
            self.execution_handler,
            {
                "operation": "get_recovery_instances",
                "parameters": {"executionId": execution_id}
            }
        )
    
    def terminate_instances(self, execution_id: str) -> Dict[str, Any]:
        """
        Terminate all recovery instances from a completed execution.
        
        Args:
            execution_id: Execution ID whose instances should be terminated
            
        Returns:
            Termination response
        """
        logger.info(f"Terminating instances for execution: {execution_id}")
        
        return self._invoke_lambda(
            self.execution_handler,
            {
                "operation": "terminate_instances",
                "parameters": {"executionId": execution_id}
            }
        )


class DRWorkflowRunner:
    """
    Orchestrates a complete DR workflow from start to finish.
    """
    
    def __init__(self, client: DROrchestrationClient):
        """
        Initialize the workflow runner.
        
        Args:
            client: DR Orchestration client instance
        """
        self.client = client
    
    def list_available_plans(self):
        """
        List all available recovery plans with their details.
        """
        print("\n" + "="*80)
        print("AVAILABLE RECOVERY PLANS")
        print("="*80)
        
        plans = self.client.list_recovery_plans()
        
        if not plans:
            print("No recovery plans found.")
            return
        
        for plan in plans:
            print(f"\nPlan ID: {plan['planId']}")
            print(f"Name: {plan['name']}")
            print(f"Description: {plan.get('description', 'N/A')}")
            print(f"Protection Group: {plan.get('protectionGroupName', 'N/A')}")
            print(f"Waves: {plan.get('waveCount', 0)}")
            print(f"Status: {plan.get('status', 'N/A')}")
    
    def run_complete_workflow(self, plan_id: str, execution_type: str = 'DRILL'):
        """
        Run a complete DR workflow from start to finish.
        
        Args:
            plan_id: Recovery plan ID to execute
            execution_type: DRILL or RECOVERY
        """
        print("\n" + "="*80)
        print(f"STARTING COMPLETE DR WORKFLOW - {execution_type} MODE")
        print("="*80)
        
        # Step 1: Get recovery plan details
        print("\n[Step 1/6] Getting recovery plan details...")
        try:
            plan = self.client.get_recovery_plan(plan_id)
            print(f"✓ Plan: {plan['name']}")
            print(f"  Protection Group: {plan.get('protectionGroupName', 'N/A')}")
            print(f"  Waves: {len(plan.get('waves', []))}")
            
            # Display wave information
            for wave in plan.get('waves', []):
                print(f"    - Wave {wave['waveNumber']}: {wave['name']} ({wave.get('serverCount', 0)} servers)")
        
        except Exception as e:
            print(f"✗ Failed to get recovery plan: {str(e)}")
            return
        
        # Step 2: Start execution
        print(f"\n[Step 2/6] Starting {execution_type} execution...")
        try:
            start_result = self.client.start_execution(
                plan_id=plan_id,
                execution_type=execution_type,
                initiated_by='complete_dr_workflow.py'
            )
            
            execution_id = start_result['executionId']
            print(f"✓ Execution started: {execution_id}")
            print(f"  Status: {start_result['status']}")
            
        except Exception as e:
            print(f"✗ Failed to start execution: {str(e)}")
            return
        
        # Step 3: Monitor execution progress
        print(f"\n[Step 3/6] Monitoring execution progress...")
        print("  (Press Ctrl+C to stop monitoring and continue to next step)")
        
        try:
            self._monitor_execution(execution_id)
        except KeyboardInterrupt:
            print("\n  Monitoring interrupted by user")
        
        # Step 4: Get final execution status
        print(f"\n[Step 4/6] Getting final execution status...")
        try:
            execution = self.client.get_execution(execution_id)
            status = execution['status']
            
            print(f"✓ Execution Status: {status}")
            print(f"  Current Wave: {execution.get('currentWave', 'N/A')}/{execution.get('totalWaves', 'N/A')}")
            
            # Display wave status
            for wave in execution.get('waves', []):
                wave_status = wave.get('status', 'UNKNOWN')
                servers_launched = wave.get('serversLaunched', 0)
                server_count = wave.get('serverCount', 0)
                print(f"    - {wave['waveName']}: {wave_status} ({servers_launched}/{server_count} servers)")
            
            # Only proceed to instance operations if execution completed
            if status not in ['COMPLETED', 'PARTIAL']:
                print(f"\n⚠ Execution is not complete (status: {status})")
                print("  Skipping instance operations")
                return
        
        except Exception as e:
            print(f"✗ Failed to get execution status: {str(e)}")
            return
        
        # Step 5: Get recovery instance details
        print(f"\n[Step 5/6] Getting recovery instance details...")
        try:
            instances_result = self.client.get_recovery_instances(execution_id)
            instances = instances_result.get('instances', [])
            
            print(f"✓ Found {len(instances)} recovery instances:")
            
            for instance in instances:
                print(f"\n  Instance: {instance['name']}")
                print(f"    EC2 ID: {instance['ec2InstanceId']}")
                print(f"    State: {instance['ec2InstanceState']}")
                print(f"    Type: {instance['instanceType']}")
                print(f"    Region: {instance['region']}")
                print(f"    Private IP: {instance.get('privateIp', 'N/A')}")
                print(f"    Public IP: {instance.get('publicIp', 'N/A')}")
                print(f"    Wave: {instance.get('waveName', 'N/A')}")
        
        except Exception as e:
            print(f"✗ Failed to get recovery instances: {str(e)}")
            return
        
        # Step 6: Terminate instances (with confirmation)
        print(f"\n[Step 6/6] Terminating recovery instances...")
        
        # Ask for confirmation
        response = input(f"  Terminate {len(instances)} recovery instances? (yes/no): ")
        if response.lower() != 'yes':
            print("  Skipping instance termination")
            return
        
        try:
            terminate_result = self.client.terminate_instances(execution_id)
            
            print(f"✓ Termination initiated: {terminate_result['status']}")
            print(f"  Total instances: {terminate_result['details']['totalInstances']}")
            
            for job in terminate_result['details']['terminationJobs']:
                print(f"    - Job {job['jobId']}: {job['instanceCount']} instances in {job['region']}")
        
        except Exception as e:
            print(f"✗ Failed to terminate instances: {str(e)}")
            return
        
        print("\n" + "="*80)
        print("WORKFLOW COMPLETED SUCCESSFULLY")
        print("="*80)
    
    def _monitor_execution(self, execution_id: str, poll_interval: int = 30):
        """
        Monitor execution progress in real-time.
        
        Args:
            execution_id: Execution ID to monitor
            poll_interval: Seconds between status checks
        """
        terminal_statuses = ['COMPLETED', 'FAILED', 'CANCELLED', 'PARTIAL']
        
        while True:
            try:
                execution = self.client.get_execution(execution_id)
                status = execution['status']
                current_wave = execution.get('currentWave', 0)
                total_waves = execution.get('totalWaves', 0)
                
                # Display current status
                timestamp = datetime.now().strftime('%H:%M:%S')
                print(f"  [{timestamp}] Status: {status}, Wave: {current_wave}/{total_waves}")
                
                # Check if execution is complete
                if status in terminal_statuses:
                    print(f"  Execution finished with status: {status}")
                    break
                
                # Wait before next poll
                time.sleep(poll_interval)
            
            except Exception as e:
                logger.error(f"Error monitoring execution: {str(e)}")
                break


def main():
    """
    Main entry point for the DR workflow script.
    """
    parser = argparse.ArgumentParser(
        description='Complete DR Workflow using Direct Lambda Invocation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available recovery plans
  python complete_dr_workflow.py --list-plans

  # Run complete DR drill workflow
  python complete_dr_workflow.py --plan-id 550e8400-e29b-41d4-a716-446655440000

  # Run in different environment
  python complete_dr_workflow.py --plan-id <plan-id> --environment dev

  # Enable debug logging
  python complete_dr_workflow.py --plan-id <plan-id> --debug
        """
    )
    
    parser.add_argument(
        '--plan-id',
        help='Recovery plan ID to execute'
    )
    
    parser.add_argument(
        '--list-plans',
        action='store_true',
        help='List all available recovery plans'
    )
    
    parser.add_argument(
        '--environment',
        default='test',
        choices=['dev', 'test', 'staging', 'prod'],
        help='Deployment environment (default: test)'
    )
    
    parser.add_argument(
        '--region',
        default='us-east-1',
        help='AWS region (default: us-east-1)'
    )
    
    parser.add_argument(
        '--execution-type',
        default='DRILL',
        choices=['DRILL', 'RECOVERY'],
        help='Execution type (default: DRILL)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize client
    try:
        client = DROrchestrationClient(
            environment=args.environment,
            region=args.region
        )
    except Exception as e:
        print(f"Failed to initialize DR Orchestration client: {str(e)}")
        sys.exit(1)
    
    # Initialize workflow runner
    runner = DRWorkflowRunner(client)
    
    # Execute requested operation
    if args.list_plans:
        runner.list_available_plans()
    elif args.plan_id:
        runner.run_complete_workflow(
            plan_id=args.plan_id,
            execution_type=args.execution_type
        )
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
