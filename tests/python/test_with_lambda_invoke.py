#!/usr/bin/env python3
"""
Automated test using direct Lambda invocation (bypasses API Gateway auth)
"""
import json
import time
import boto3
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DirectLambdaTest:
    """Test using direct Lambda invocation."""
    
    def __init__(self, plan_id: str, region: str = 'us-east-1'):
        self.plan_id = plan_id
        self.region = region
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.dynamodb = boto3.client('dynamodb', region_name=region)
        self.drs = boto3.client('drs', region_name=region)
        self.execution_table = 'drs-orchestration-execution-history-test'
        self.lambda_function = 'drs-orchestration-api-handler-test'
        
    def run_test(self) -> dict:
        """Run end-to-end test."""
        try:
            logger.info("="*80)
            logger.info("AUTOMATED TEST - Direct Lambda Invocation")
            logger.info(f"Plan ID: {self.plan_id}")
            logger.info("="*80)
            
            # Phase 1: Trigger execution via Lambda
            logger.info("\n[PHASE 1] Invoking Lambda to trigger execution...")
            execution_id = self._invoke_lambda_to_execute()
            logger.info(f"✅ Execution ID: {execution_id}")
            
            # Phase 2: Monitor execution
            logger.info("\n[PHASE 2] Monitoring execution...")
            execution_data = self._monitor_execution(execution_id)
            logger.info(f"✅ Execution Status: {execution_data.get('Status')}")
            
            # Phase 3: Verify wave data
            logger.info("\n[PHASE 3] Verifying wave data...")
            waves = self._verify_waves(execution_data)
            logger.info(f"✅ Waves verified: {len(waves)}")
            
            # Phase 4: Check DRS jobs
            logger.info("\n[PHASE 4] Checking DRS jobs...")
            drs_status = self._check_drs_jobs(waves)
            logger.info(f"✅ DRS jobs checked")
            
            # Results
            logger.info("\n" + "="*80)
            logger.info("TEST RESULTS")
            logger.info("="*80)
            logger.info(f"Execution ID: {execution_id}")
            logger.info(f"Status: {execution_data.get('Status')}")
            logger.info(f"Waves: {len(waves)}")
            
            for wave in waves:
                job_id = wave.get('JobId', 'NO JOB ID')
                status = wave.get('Status', 'UNKNOWN')
                logger.info(f"  Wave {wave.get('WaveId')}: {status} (Job: {job_id})")
            
            logger.info("\n✅ TEST COMPLETED")
            
            return {
                'success': True,
                'execution_id': execution_id,
                'status': execution_data.get('Status'),
                'waves': waves
            }
            
        except Exception as e:
            logger.error(f"❌ Test failed: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _invoke_lambda_to_execute(self) -> str:
        """Invoke Lambda to execute recovery plan."""
        payload = {
            'httpMethod': 'POST',
            'path': f'/api/recovery-plans/{self.plan_id}/execute',
            'body': json.dumps({'isDrill': True})
        }
        
        response = self.lambda_client.invoke(
            FunctionName=self.lambda_function,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') != 200:
            raise Exception(f"Lambda invocation failed: {result}")
        
        body = json.loads(result.get('body', '{}'))
        execution_id = body.get('ExecutionId')
        
        if not execution_id:
            raise Exception(f"No ExecutionId in response: {body}")
        
        return execution_id
    
    def _monitor_execution(self, execution_id: str, timeout: int = 300) -> dict:
        """Monitor execution until complete or timeout."""
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < timeout:
            response = self.dynamodb.get_item(
                TableName=self.execution_table,
                Key={
                    'ExecutionId': {'S': execution_id},
                    'PlanId': {'S': self.plan_id}
                }
            )
            
            if 'Item' not in response:
                logger.warning("Execution not found, waiting...")
                time.sleep(5)
                continue
            
            execution = self._parse_item(response['Item'])
            status = execution.get('Status', 'UNKNOWN')
            
            if status != last_status:
                logger.info(f"  Status: {status} (elapsed: {int(time.time() - start_time)}s)")
                last_status = status
            
            if status in ['COMPLETED', 'FAILED', 'TIMEOUT']:
                return execution
            
            time.sleep(15)
        
        raise TimeoutError(f"Execution monitoring timed out after {timeout}s")
    
    def _verify_waves(self, execution_data: dict) -> list:
        """Verify wave data structure."""
        waves = execution_data.get('Waves', [])
        
        for wave in waves:
            wave_id = wave.get('WaveId', 'unknown')
            job_id = wave.get('JobId')
            
            if job_id:
                logger.info(f"  ✅ Wave {wave_id}: JobId = {job_id}")
            else:
                logger.warning(f"  ⚠️  Wave {wave_id}: NO JobId (BUG 1 present!)")
        
        return waves
    
    def _check_drs_jobs(self, waves: list) -> dict:
        """Check DRS job status."""
        results = {}
        
        for wave in waves:
            job_id = wave.get('JobId')
            if not job_id:
                continue
            
            try:
                response = self.drs.describe_jobs(filters={'jobIDs': [job_id]})
                if response.get('items'):
                    job = response['items'][0]
                    status = job.get('status', 'UNKNOWN')
                    logger.info(f"  DRS Job {job_id}: {status}")
                    results[job_id] = status
            except Exception as e:
                logger.error(f"  Error checking job {job_id}: {str(e)}")
        
        return results
    
    def _parse_item(self, item: dict) -> dict:
        """Parse DynamoDB item to dict."""
        result = {}
        for key, value in item.items():
            if 'S' in value:
                result[key] = value['S']
            elif 'N' in value:
                result[key] = int(value['N'])
            elif 'L' in value:
                result[key] = [self._parse_value(v) for v in value['L']]
            elif 'M' in value:
                result[key] = self._parse_item(value['M'])
            elif 'BOOL' in value:
                result[key] = value['BOOL']
        return result
    
    def _parse_value(self, value: dict):
        """Parse DynamoDB value."""
        if 'S' in value:
            return value['S']
        elif 'N' in value:
            return int(value['N'])
        elif 'M' in value:
            return self._parse_item(value['M'])
        return value


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-id', required=True)
    parser.add_argument('--region', default='us-east-1')
    args = parser.parse_args()
    
    test = DirectLambdaTest(args.plan_id, args.region)
    results = test.run_test()
    
    # Save results
    output_file = f"test_results_{results.get('execution_id', 'failed')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"\nResults saved to: {output_file}")
    exit(0 if results['success'] else 1)


if __name__ == '__main__':
    main()
