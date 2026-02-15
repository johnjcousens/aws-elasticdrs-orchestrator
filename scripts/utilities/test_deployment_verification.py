#!/usr/bin/env python3
"""
Verify that the latest deployment changes are in place.

Tests:
1. DynamoDB tables exist (DRSRegionStatusTable, SourceServerInventoryTable)
2. API Gateway resources exist (source-server-inventory endpoint)
3. Lambda functions have updated code (new handler functions)
"""

import boto3
import json
from botocore.exceptions import ClientError

REGION = "us-east-2"
STACK_NAME = "hrp-drs-tech-adapter-dev"
PROJECT_NAME = "hrp-drs-tech-adapter"
ENVIRONMENT = "dev"
AWS_PROFILE = "AWSAdministratorAccess-891376951562"

# Initialize AWS session with profile
session = boto3.Session(profile_name=AWS_PROFILE)

def check_dynamodb_tables():
    """Check if new DynamoDB tables exist."""
    dynamodb = session.client("dynamodb", region_name=REGION)
    
    tables_to_check = [
        f"{PROJECT_NAME}-drs-region-status-{ENVIRONMENT}",
        f"{PROJECT_NAME}-source-server-inventory-{ENVIRONMENT}",
    ]
    
    results = {}
    for table_name in tables_to_check:
        try:
            response = dynamodb.describe_table(TableName=table_name)
            results[table_name] = {
                "exists": True,
                "status": response["Table"]["TableStatus"],
                "created": str(response["Table"]["CreationDateTime"])
            }
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                results[table_name] = {"exists": False, "error": "Table not found"}
            else:
                results[table_name] = {"exists": False, "error": str(e)}
    
    return results

def check_lambda_code():
    """Check if Lambda functions have the new code."""
    lambda_client = session.client("lambda", region_name=REGION)
    
    function_name = f"{PROJECT_NAME}-query-handler-{ENVIRONMENT}"
    
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        last_modified = response["Configuration"]["LastModified"]
        code_sha256 = response["Configuration"]["CodeSha256"]
        
        # Try to invoke with new operation
        test_event = {
            "operation": "get_source_server_inventory",
            "accountId": "891376951562"
        }
        
        invoke_response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(test_event)
        )
        
        payload = json.loads(invoke_response["Payload"].read())
        
        return {
            "function_name": function_name,
            "last_modified": last_modified,
            "code_sha256": code_sha256,
            "test_invocation": {
                "status_code": invoke_response["StatusCode"],
                "response": payload
            }
        }
    except ClientError as e:
        return {
            "function_name": function_name,
            "error": str(e)
        }

def check_api_gateway_resources():
    """Check if new API Gateway resources exist."""
    apigw = session.client("apigateway", region_name=REGION)
    cfn = session.client("cloudformation", region_name=REGION)
    
    try:
        # Get API Gateway ID from stack outputs
        stack_response = cfn.describe_stacks(StackName=STACK_NAME)
        outputs = stack_response["Stacks"][0]["Outputs"]
        
        api_id = None
        for output in outputs:
            if output["OutputKey"] == "ApiId":
                api_id = output["OutputValue"]
                break
        
        if not api_id:
            return {"error": "Could not find ApiId in stack outputs"}
        
        # Get all resources
        resources = apigw.get_resources(restApiId=api_id, limit=500)
        
        # Look for source-server-inventory resource
        inventory_resource = None
        for resource in resources["items"]:
            if resource.get("pathPart") == "source-server-inventory":
                inventory_resource = resource
                break
        
        return {
            "api_id": api_id,
            "source_server_inventory_resource": {
                "exists": inventory_resource is not None,
                "details": inventory_resource if inventory_resource else None
            }
        }
    except ClientError as e:
        return {"error": str(e)}

def main():
    print("=" * 80)
    print("DEPLOYMENT VERIFICATION TEST")
    print("=" * 80)
    print()
    
    print("1. Checking DynamoDB Tables...")
    print("-" * 80)
    tables = check_dynamodb_tables()
    for table_name, info in tables.items():
        status = "✓ EXISTS" if info.get("exists") else "✗ MISSING"
        print(f"{status}: {table_name}")
        if info.get("exists"):
            print(f"  Status: {info.get('status')}")
            print(f"  Created: {info.get('created')}")
        else:
            print(f"  Error: {info.get('error')}")
    print()
    
    print("2. Checking Lambda Code Updates...")
    print("-" * 80)
    lambda_info = check_lambda_code()
    if "error" in lambda_info:
        print(f"✗ ERROR: {lambda_info['error']}")
    else:
        print(f"✓ Function: {lambda_info['function_name']}")
        print(f"  Last Modified: {lambda_info['last_modified']}")
        print(f"  Code SHA256: {lambda_info['code_sha256'][:16]}...")
        print(f"  Test Invocation Status: {lambda_info['test_invocation']['status_code']}")
        print(f"  Response: {json.dumps(lambda_info['test_invocation']['response'], indent=2)[:200]}...")
    print()
    
    print("3. Checking API Gateway Resources...")
    print("-" * 80)
    api_info = check_api_gateway_resources()
    if "error" in api_info:
        print(f"✗ ERROR: {api_info['error']}")
    else:
        print(f"✓ API ID: {api_info['api_id']}")
        inventory = api_info["source_server_inventory_resource"]
        if inventory["exists"]:
            print(f"✓ source-server-inventory resource exists")
            print(f"  Resource ID: {inventory['details']['id']}")
            print(f"  Path: {inventory['details']['path']}")
        else:
            print(f"✗ source-server-inventory resource NOT FOUND")
    print()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    # Determine overall status
    tables_ok = all(info.get("exists") for info in tables.values())
    lambda_ok = "error" not in lambda_info
    api_ok = "error" not in api_info and api_info.get("source_server_inventory_resource", {}).get("exists")
    
    if tables_ok and lambda_ok and api_ok:
        print("✓ ALL CHECKS PASSED - Deployment is complete")
    else:
        print("✗ SOME CHECKS FAILED - Deployment may be incomplete")
        if not tables_ok:
            print("  - DynamoDB tables missing")
        if not lambda_ok:
            print("  - Lambda code not updated")
        if not api_ok:
            print("  - API Gateway resources missing")
        print()
        print("RECOMMENDATION: Run full deployment to update nested stacks:")
        print(f"  ./scripts/deploy.sh {ENVIRONMENT}")

if __name__ == "__main__":
    main()
