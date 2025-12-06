#!/usr/bin/env python3
"""
End-to-End Automated Test for AWS DRS Orchestration
Triggers execution → Monitors DRS → Validates EC2 → Reports results
"""
import json
import time
import boto3
import requests
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutomatedE2ETest:
    """End-to-end automated test orchestrator."""
    
    def __init__(self, api_endpoint: str, plan_id: str, region: str = 'us-east-1'):
        """
        Initialize test orchestrator.
        
        Args:
            api_endpoint: API Gateway endpoint URL
            plan_id: Recovery plan ID to execute
            region: AWS region
        """
        self.api_endpoint = api_endpoint.rstrip('/')
        self.plan_id = plan_id
        self.region = region
        
        # Initialize AWS clients
        self.drs = boto3.client('drs', region_name=region)
        self.ec2 = boto3.client('ec2', region_name=region)
        self.dynamodb = boto3.client('dynamodb', region_name=region)
        self.cognito = boto3.client('cognito-idp', region_name=region)
        
        # Test configuration
        self.execution_table = 'drs-orchestration-execution-history-test'
        self.max_wait_time = 1800  # 30 minutes
        self.poll_interval = 15  # 15 seconds
        
        # Cognito configuration
        self.user_pool_client_id = '48fk7bjefk88aejr1rc7dvmbv0'
        self.username = 'testuser@example.com'
        self.password = 'IiG2b1o+D$'
        self.auth_token = None
        
        # Test results
        self.results = {
            'test_start_time': None,
            'test_end_time': None,
            'execution_id': None,
            'execution_status': None,
            'waves': [],
            'drs_jobs': [],
            'ec2_instances': [],
            'success': False,
            'errors': [],
            'warnings': []
        }
    
    def run_test(self, is_drill: bool = True) -> Dict[str, Any]:
        """
        Run complete end-to-end test.
        
        Args:
            is_drill: True for drill, False for recovery
            
        Returns:
            Dictionary containing test results
        """
        try:
            self.results['test_start_time'] = datetime.now(timezone.utc).isoformat()
            logger.info("=" * 80)
            logger.info("STARTING END-TO-END AUTOMATED TEST")
            logger.info(f"Plan ID: {self.plan_id}")
            logger.info(f"Execution Type: {'DRILL' if is_drill else 'RECOVERY'}")
            logger.info("=" * 80)
            
            # Phase 0: Authenticate
            logger.info("\n[PHASE 0] Authenticating with Cognito...")
            self._authenticate()
            logger.info(f"✅ Authentication successful")
            
            # Phase 1: Trigger Execution
            logger.info("\n[PHASE 1] Triggering execution via API...")
            execution_id = self._trigger_execution(is_drill)
            self.results['execution_id'] = execution_id
            logger.info(f"✅ Execution triggered: {execution_id}")
            
            # Phase 2: Monitor Orchestration System
            logger.info("\n[PHASE 2] Monitoring orchestration system...")
            execution_data = self._monitor_orchestration(execution_id)
            logger.info(f"✅ Orchestration monitoring complete")
            
            # Phase 3: Monitor DRS Jobs
            logger.info("\n[PHASE 3] Monitoring DRS jobs...")
            drs_results = self._monitor_drs_jobs(execution_data)
            logger.info(f"✅ DRS monitoring complete")
            
            # Phase 4: Validate EC2 Instances
            logger.info("\n[PHASE 4] Validating EC2 instances...")
            ec2_results = self._validate_ec2_instances(drs_results)
            logger.info(f"✅ EC2 validation complete")
            
            # Phase 5: Generate Report
            logger.info("\n[PHASE 5] Generating test report...")
            self._generate_report()
            
            # Determine overall success
            self.results['success'] = (
                self.results['execution_status'] == 'COMPLETED' and
                all(w.get('status') == 'COMPLETED' for w in self.results['waves']) and
                all(j.get('success', False) for j in self.results['drs_jobs']) and
                all(i.get('running', False) for i in self.results['ec2_instances'])
            )
            
            self.results['test_end_time'] = datetime.now(timezone.utc).isoformat()
            
            logger.info("\n" + "=" * 80)
            if self.results['success']:
                logger.info("✅ TEST PASSED - All validations successful")
            else:
                logger.warning("❌ TEST FAILED - See errors below")
                for error in self.results['errors']:
                    logger.error(f"  - {error}")
            logger.info("=" * 80)
            
            return self.results
            
        except Exception as e:
            logger.error(f"❌ Test failed with exception: {str(e)}", exc_info=True)
            self.results['errors'].append(f"Test exception: {str(e)}")
            self.results['success'] = False
            self.results['test_end_time'] = datetime.now(timezone.utc).isoformat()
            return self.results
    
    def _authenticate(self) -> None:
        """Authenticate with Cognito and get JWT token."""
        try:
            response = self.cognito.initiate_auth(
                ClientId=self.user_pool_client_id,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': self.username,
                    'PASSWORD': self.password
                }
            )
            self.auth_token = response['AuthenticationResult']['IdToken']
            logger.info(f"  Token obtained (length: {len(self.auth_token)})")
        except Exception as e:
            logger.error(f"Failed to authenticate: {str(e)}")
            raise
    
    def _trigger_execution(self, is_drill: bool) -> str:
        """
        Trigger execution via API Gateway.
        
        Args:
            is_drill: True for drill, False for recovery
            
        Returns:
            Execution ID
        """
        try:
            url = f"{self.api_endpoint}/executions"
            payload = {
                'PlanId': self.plan_id,
                'ExecutionType': 'DRILL' if is_drill else 'RECOVERY',
                'InitiatedBy': self.username
            }
            headers = {
                'Authorization': f'Bearer {self.auth_token}',
                'Content-Type': 'application/json'
            }
            
            logger.info(f"POST {url}")
            logger.info(f"Payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            execution_id = result.get('executionId')
            
            if not execution_id:
                raise ValueError(f"No executionId in response: {result}")
            
            logger.info(f"Response: {json.dumps(result, indent=2)}")
            return execution_id
            
        except Exception as e:
            logger.error(f"Failed to trigger execution: {str(e)}")
            raise
    
    def _monitor_orchestration(self, execution_id: str) -> Dict[str, Any]:
        """
        Monitor orchestration system until execution completes.
        
        Args:
            execution_id: Execution ID to monitor
            
        Returns:
            Final execution data
        """
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < self.max_wait_time:
            try:
                # Query DynamoDB for execution state
                response = self.dynamodb.get_item(
                    TableName=self.execution_table,
                    Key={
                        'ExecutionId': {'S': execution_id},
                        'PlanId': {'S': self.plan_id}
                    }
                )
                
                if 'Item' not in response:
                    logger.warning(f"Execution not found in DynamoDB: {execution_id}")
                    time.sleep(self.poll_interval)
                    continue
                
                execution = self._parse_dynamodb_item(response['Item'])
                status = execution.get('Status', 'UNKNOWN')
                
                # Log status changes
                if status != last_status:
                    elapsed = int(time.time() - start_time)
                    logger.info(f"  [{elapsed}s] Status: {status}")
                    last_status = status
                
                # Check for completion
                if status in ['COMPLETED', 'FAILED', 'TIMEOUT']:
                    self.results['execution_status'] = status
                    self.results['waves'] = self._extract_wave_data(execution)
                    logger.info(f"  Execution {status} after {int(time.time() - start_time)}s")
                    return execution
                
                time.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"Error monitoring orchestration: {str(e)}")
                self.results['errors'].append(f"Orchestration monitoring error: {str(e)}")
                time.sleep(self.poll_interval)
        
        # Timeout
        logger.error(f"❌ Orchestration monitoring timed out after {self.max_wait_time}s")
        self.results['errors'].append(f"Orchestration timeout after {self.max_wait_time}s")
        raise TimeoutError(f"Execution monitoring timed out")
    
    def _monitor_drs_jobs(self, execution_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Monitor DRS jobs directly via DRS API.
        
        Args:
            execution_data: Execution data from DynamoDB
            
        Returns:
            List of DRS job results
        """
        drs_results = []
        waves = execution_data.get('Waves', [])
        
        for wave in waves:
            job_id = wave.get('JobId')
            wave_id = wave.get('WaveId', 'unknown')
            
            if not job_id:
                logger.warning(f"  Wave {wave_id} has no JobId")
                self.results['warnings'].append(f"Wave {wave_id} missing JobId")
                continue
            
            logger.info(f"  Monitoring DRS job {job_id} (Wave {wave_id})...")
            
            try:
                # Query DRS for job details
                response = self.drs.describe_jobs(
                    filters={'jobIDs': [job_id]}
                )
                
                if not response.get('items'):
                    logger.warning(f"  No DRS job found for ID {job_id}")
                    self.results['warnings'].append(f"DRS job {job_id} not found")
                    continue
                
                job = response['items'][0]
                job_status = job.get('status', 'UNKNOWN')
                servers = job.get('participatingServers', [])
                
                # Check server launch statuses
                all_launched = all(s.get('launchStatus') == 'LAUNCHED' for s in servers)
                any_failed = any(s.get('launchStatus') in ['LAUNCH_FAILED', 'FAILED', 'TERMINATED'] for s in servers)
                
                job_result = {
                    'job_id': job_id,
                    'wave_id': wave_id,
                    'job_status': job_status,
                    'servers': [{
                        'source_server_id': s.get('sourceServerID'),
                        'launch_status': s.get('launchStatus'),
                        'instance_id': s.get('recoveryInstanceID'),
                        'hostname': s.get('hostname', 'unknown')
                    } for s in servers],
                    'all_launched': all_launched,
                    'any_failed': any_failed,
                    'success': all_launched and not any_failed
                }
                
                drs_results.append(job_result)
                self.results['drs_jobs'].append(job_result)
                
                # Log results
                if job_result['success']:
                    logger.info(f"    ✅ All servers LAUNCHED ({len(servers)} servers)")
                else:
                    logger.error(f"    ❌ Job failed - {sum(1 for s in servers if s.get('launchStatus') != 'LAUNCHED')} server(s) failed")
                    self.results['errors'].append(f"DRS job {job_id} failed to launch servers")
                
            except Exception as e:
                logger.error(f"  Error monitoring DRS job {job_id}: {str(e)}")
                self.results['errors'].append(f"DRS monitoring error for job {job_id}: {str(e)}")
        
        return drs_results
    
    def _validate_ec2_instances(self, drs_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate EC2 instances were launched successfully.
        
        Args:
            drs_results: DRS job results with instance IDs
            
        Returns:
            List of EC2 validation results
        """
        ec2_results = []
        
        # Collect all instance IDs
        instance_ids = []
        for job_result in drs_results:
            for server in job_result.get('servers', []):
                instance_id = server.get('instance_id')
                if instance_id:
                    instance_ids.append(instance_id)
        
        if not instance_ids:
            logger.warning("  No EC2 instances to validate")
            self.results['warnings'].append("No EC2 instances found")
            return ec2_results
        
        logger.info(f"  Validating {len(instance_ids)} EC2 instance(s)...")
        
        try:
            # Query EC2 for instance details
            response = self.ec2.describe_instances(InstanceIds=instance_ids)
            
            for reservation in response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    instance_id = instance.get('InstanceId')
                    state = instance.get('State', {}).get('Name', 'unknown')
                    
                    instance_result = {
                        'instance_id': instance_id,
                        'state': state,
                        'instance_type': instance.get('InstanceType'),
                        'private_ip': instance.get('PrivateIpAddress'),
                        'public_ip': instance.get('PublicIpAddress'),
                        'subnet_id': instance.get('SubnetId'),
                        'vpc_id': instance.get('VpcId'),
                        'launch_time': instance.get('LaunchTime').isoformat() if instance.get('LaunchTime') else None,
                        'running': state == 'running'
                    }
                    
                    ec2_results.append(instance_result)
                    self.results['ec2_instances'].append(instance_result)
                    
                    # Log results
                    if instance_result['running']:
                        logger.info(f"    ✅ Instance {instance_id}: {state} ({instance.get('InstanceType')})")
                    else:
                        logger.warning(f"    ⚠️  Instance {instance_id}: {state} (expected: running)")
                        self.results['warnings'].append(f"Instance {instance_id} not running: {state}")
            
        except Exception as e:
            logger.error(f"  Error validating EC2 instances: {str(e)}")
            self.results['errors'].append(f"EC2 validation error: {str(e)}")
        
        return ec2_results
    
    def _generate_report(self) -> None:
        """Generate detailed test report."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST RESULTS SUMMARY")
        logger.info("=" * 80)
        
        logger.info(f"\nExecution ID: {self.results['execution_id']}")
        logger.info(f"Execution Status: {self.results['execution_status']}")
        logger.info(f"Test Duration: {self._calculate_duration()}")
        
        logger.info(f"\nWaves: {len(self.results['waves'])}")
        for wave in self.results['waves']:
            logger.info(f"  - Wave {wave.get('wave_id')}: {wave.get('status')}")
        
        logger.info(f"\nDRS Jobs: {len(self.results['drs_jobs'])}")
        for job in self.results['drs_jobs']:
            status = "✅ SUCCESS" if job.get('success') else "❌ FAILED"
            logger.info(f"  - Job {job.get('job_id')}: {status}")
        
        logger.info(f"\nEC2 Instances: {len(self.results['ec2_instances'])}")
        running_count = sum(1 for i in self.results['ec2_instances'] if i.get('running'))
        logger.info(f"  - Running: {running_count}/{len(self.results['ec2_instances'])}")
        
        if self.results['errors']:
            logger.info(f"\nErrors: {len(self.results['errors'])}")
            for error in self.results['errors']:
                logger.error(f"  - {error}")
        
        if self.results['warnings']:
            logger.info(f"\nWarnings: {len(self.results['warnings'])}")
            for warning in self.results['warnings']:
                logger.warning(f"  - {warning}")
    
    def _calculate_duration(self) -> str:
        """Calculate test duration."""
        if not self.results['test_start_time'] or not self.results['test_end_time']:
            return "unknown"
        
        start = datetime.fromisoformat(self.results['test_start_time'])
        end = datetime.fromisoformat(self.results['test_end_time'])
        duration = (end - start).total_seconds()
        
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        return f"{minutes}m {seconds}s"
    
    def _parse_dynamodb_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Parse DynamoDB item format to Python dict."""
        result = {}
        for key, value in item.items():
            if 'S' in value:
                result[key] = value['S']
            elif 'N' in value:
                result[key] = int(value['N']) if '.' not in value['N'] else float(value['N'])
            elif 'L' in value:
                result[key] = [self._parse_dynamodb_value(v) for v in value['L']]
            elif 'M' in value:
                result[key] = self._parse_dynamodb_item(value['M'])
            elif 'BOOL' in value:
                result[key] = value['BOOL']
        return result
    
    def _parse_dynamodb_value(self, value: Dict[str, Any]) -> Any:
        """Parse a single DynamoDB value."""
        if 'S' in value:
            return value['S']
        elif 'N' in value:
            return int(value['N']) if '.' not in value['N'] else float(value['N'])
        elif 'L' in value:
            return [self._parse_dynamodb_value(v) for v in value['L']]
        elif 'M' in value:
            return self._parse_dynamodb_item(value['M'])
        elif 'BOOL' in value:
            return value['BOOL']
        return value
    
    def _extract_wave_data(self, execution: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract simplified wave data."""
        waves = []
        for wave in execution.get('Waves', []):
            waves.append({
                'wave_id': wave.get('WaveId'),
                'status': wave.get('Status'),
                'job_id': wave.get('JobId'),
                'server_count': len(wave.get('Servers', []))
            })
        return waves


def main():
    """Main entry point for automated testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run end-to-end automated test')
    parser.add_argument('--api-endpoint', required=True, help='API Gateway endpoint URL')
    parser.add_argument('--plan-id', required=True, help='Recovery plan ID')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--recovery', action='store_true', help='Run recovery (default: drill)')
    
    args = parser.parse_args()
    
    # Run test
    test = AutomatedE2ETest(
        api_endpoint=args.api_endpoint,
        plan_id=args.plan_id,
        region=args.region
    )
    
    results = test.run_test(is_drill=not args.recovery)
    
    # Save results to file
    output_file = f"test_results_{results['execution_id']}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"\nResults saved to: {output_file}")
    
    # Exit with appropriate code
    exit(0 if results['success'] else 1)


if __name__ == '__main__':
    main()
