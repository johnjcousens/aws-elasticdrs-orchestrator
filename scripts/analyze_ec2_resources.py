#!/usr/bin/env python3
"""
Analyze EC2 subnets and security groups across all accounts in us-east-2
"""
import boto3
import json
from botocore.exceptions import ClientError

REGION = "us-east-2"

# All accounts
ACCOUNTS = {
    "891376951562": "Orchestration Account",
    "851725249649": "Target Account", 
    "339712742264": "Staging Account 1",
    "339712866401": "Staging Account 2"
}

def get_session(account_id):
    """Get boto3 session for account"""
    profile_name = f"{account_id}_AWSAdministratorAccess"
    try:
        session = boto3.Session(profile_name=profile_name, region_name=REGION)
        # Test credentials
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        print(f"✓ Connected to {account_id} as {identity['Arn']}")
        return session
    except Exception as e:
        print(f"✗ Failed to connect to {account_id}: {e}")
        return None

def analyze_subnets(session, account_id, account_name):
    """Analyze subnets in account"""
    try:
        ec2 = session.client('ec2')
        response = ec2.describe_subnets()
        subnets = response.get('Subnets', [])
        
        print(f"\n{'='*80}")
        print(f"SUBNETS in {account_name} ({account_id})")
        print(f"{'='*80}")
        print(f"Total: {len(subnets)} subnets\n")
        
        for subnet in subnets:
            subnet_id = subnet['SubnetId']
            cidr = subnet['CidrBlock']
            az = subnet['AvailabilityZone']
            vpc_id = subnet['VpcId']
            
            # Get subnet name from tags
            name = "unnamed"
            for tag in subnet.get('Tags', []):
                if tag['Key'] == 'Name':
                    name = tag['Value']
                    break
            
            print(f"  {name}")
            print(f"    ID: {subnet_id}")
            print(f"    CIDR: {cidr}")
            print(f"    AZ: {az}")
            print(f"    VPC: {vpc_id}")
            
            # Check for "onprem" in name
            if "onprem" in name.lower():
                print(f"    ⚠️  FOUND 'onprem' SUBNET!")
            
            print()
        
        return subnets
        
    except ClientError as e:
        print(f"✗ Error querying subnets: {e}")
        return []

def analyze_security_groups(session, account_id, account_name):
    """Analyze security groups in account"""
    try:
        ec2 = session.client('ec2')
        response = ec2.describe_security_groups()
        sgs = response.get('SecurityGroups', [])
        
        print(f"\n{'='*80}")
        print(f"SECURITY GROUPS in {account_name} ({account_id})")
        print(f"{'='*80}")
        print(f"Total: {len(sgs)} security groups\n")
        
        # Group by VPC
        by_vpc = {}
        for sg in sgs:
            vpc_id = sg.get('VpcId', 'no-vpc')
            if vpc_id not in by_vpc:
                by_vpc[vpc_id] = []
            by_vpc[vpc_id].append(sg)
        
        for vpc_id, vpc_sgs in by_vpc.items():
            print(f"  VPC: {vpc_id} ({len(vpc_sgs)} security groups)")
            for sg in vpc_sgs[:10]:  # Show first 10
                sg_id = sg['GroupId']
                sg_name = sg['GroupName']
                print(f"    {sg_name} ({sg_id})")
            if len(vpc_sgs) > 10:
                print(f"    ... and {len(vpc_sgs) - 10} more")
            print()
        
        return sgs
        
    except ClientError as e:
        print(f"✗ Error querying security groups: {e}")
        return []

def main():
    print("Analyzing EC2 resources across all accounts in us-east-2\n")
    
    results = {}
    
    for account_id, account_name in ACCOUNTS.items():
        session = get_session(account_id)
        if not session:
            continue
        
        results[account_id] = {
            'name': account_name,
            'subnets': analyze_subnets(session, account_id, account_name),
            'security_groups': analyze_security_groups(session, account_id, account_name)
        }
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    for account_id, data in results.items():
        print(f"{data['name']} ({account_id}):")
        print(f"  Subnets: {len(data['subnets'])}")
        print(f"  Security Groups: {len(data['security_groups'])}")
    
    # Check for "onprem" across all accounts
    print(f"\n{'='*80}")
    print("SEARCHING FOR 'onprem' SUBNETS")
    print(f"{'='*80}")
    found_onprem = False
    for account_id, data in results.items():
        for subnet in data['subnets']:
            name = "unnamed"
            for tag in subnet.get('Tags', []):
                if tag['Key'] == 'Name':
                    name = tag['Value']
                    break
            
            if "onprem" in name.lower():
                found_onprem = True
                print(f"✓ FOUND in {data['name']} ({account_id}):")
                print(f"  Name: {name}")
                print(f"  ID: {subnet['SubnetId']}")
                print(f"  CIDR: {subnet['CidrBlock']}")
                print(f"  AZ: {subnet['AvailabilityZone']}")
                print()
    
    if not found_onprem:
        print("✗ NO 'onprem' subnets found in any account!")
        print("This suggests the data is coming from somewhere else (cache, hardcoded, etc.)")

if __name__ == '__main__':
    main()
