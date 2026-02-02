"""
AWS DRS Agent Deployment Lambda Function

This Lambda function automatically discovers and deploys DRS agents to EC2
instances tagged with dr:enabled=true AND dr:recovery-strategy=drs.

Features:
- Auto-discovery of instances with DR tags
- Cross-account role assumption (source and staging accounts)
- SSM-based agent deployment
- Cross-account DRS replication (source → staging)
- Wave-based orchestration
- Status monitoring and reporting

Environment Variables:
- TARGET_REGION: Region to replicate to (default: us-west-2)
- PROJECT_NAME: Project name for External ID generation (required)
- ENVIRONMENT: Environment name for External ID generation (required)
- SNS_TOPIC_ARN: SNS topic for notifications (optional)

Event Structure:
{
    "source_account_id": "111122223333",
    "staging_account_id": "444455556666",
    "source_region": "us-east-1",
    "target_region": "us-west-2",
    "source_role_arn": "arn:aws:iam::111122223333:role/DRSOrchestrationRole-dev",
    "staging_role_arn": "arn:aws:iam::444455556666:role/DRSOrchestrationRole-dev",
    "external_id": "drs-orchestration-dev-111122223333",  # Auto-generated if not provided
    "wait_for_completion": true,
    "timeout_seconds": 600
}

External ID Pattern:
- Auto-generated: {PROJECT_NAME}-{ENVIRONMENT}-{TARGET_ACCOUNT_ID}
- Example: drs-orchestration-dev-111122223333
- Can be overridden in event payload

Cross-Account Replication Pattern:
- Agents installed in source_account_id (e.g., 111122223333)
- Agents replicate TO staging_account_id (e.g., 444455556666)
- DRS staging area created in staging account
- Recovery instances launched in staging account during DR events
"""

import json
import os
import time
import boto3
from typing import Dict, List, Any, Optional
from datetime import datetime
from botocore.exceptions import ClientError


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for DRS agent deployment.

    Supports two deployment patterns:
    1. Same-account replication: source_account_id replicates to same account
    2. Cross-account replication: source_account_id replicates to staging_account_id

    Args:
        event: Lambda event containing deployment parameters
        context: Lambda context object

    Returns:
        Deployment results with status and details
    """
    print(f"Event received: {json.dumps(event)}")

    # Parse event parameters - support both old and new formats
    source_account_id = event.get("source_account_id") or event.get("account_id")
    staging_account_id = event.get("staging_account_id")
    source_region = event.get("source_region", "us-east-1")
    target_region = event.get("target_region", os.environ.get("TARGET_REGION", "us-west-2"))
    source_role_arn = event.get("source_role_arn") or event.get("role_arn")
    staging_role_arn = event.get("staging_role_arn")

    # External ID: Use event value, or auto-generate from environment
    external_id = event.get("external_id")
    if not external_id:
        project_name = os.environ.get("PROJECT_NAME", "drs-orchestration")
        environment = os.environ.get("ENVIRONMENT", "dev")
        # Use source account for External ID (where role is being assumed)
        external_id = f"{project_name}-{environment}-{source_account_id}"
        print(f"Auto-generated External ID: {external_id}")

    wait_for_completion = event.get("wait_for_completion", True)
    timeout_seconds = event.get("timeout_seconds", 600)

    if not source_account_id:
        return error_response("source_account_id is required")

    # Determine deployment pattern
    if staging_account_id:
        deployment_pattern = "cross-account"
        print(f"Cross-account deployment: {source_account_id} → {staging_account_id}")
    else:
        deployment_pattern = "same-account"
        staging_account_id = source_account_id
        print(f"Same-account deployment: {source_account_id}")

    try:
        # Initialize deployer
        deployer = DRSAgentDeployer(
            source_account_id=source_account_id,
            staging_account_id=staging_account_id,
            source_region=source_region,
            target_region=target_region,
            source_role_arn=source_role_arn,
            staging_role_arn=staging_role_arn,
            external_id=external_id,
            deployment_pattern=deployment_pattern,
        )

        # Execute deployment
        result = deployer.deploy_agents(
            wait_for_completion=wait_for_completion,
            timeout_seconds=timeout_seconds,
        )

        # Send notification if configured
        sns_topic_arn = os.environ.get("SNS_TOPIC_ARN")
        if sns_topic_arn:
            send_notification(sns_topic_arn, result)

        return success_response(result)

    except Exception as e:
        print(f"Error: {str(e)}")
        return error_response(str(e))


class DRSAgentDeployer:
    """Handles DRS agent deployment to EC2 instances."""

    def __init__(
        self,
        source_account_id: str,
        staging_account_id: str,
        source_region: str,
        target_region: str,
        source_role_arn: Optional[str] = None,
        staging_role_arn: Optional[str] = None,
        external_id: Optional[str] = None,
        deployment_pattern: str = "same-account",
    ):
        """
        Initialize DRS agent deployer.

        Args:
            source_account_id: Account where agents are installed
            staging_account_id: Account where DRS staging area is created
            source_region: Region where instances are located
            target_region: Region to replicate to
            source_role_arn: Role ARN in source account (optional)
            staging_role_arn: Role ARN in staging account (optional)
            external_id: External ID for role assumption (optional)
            deployment_pattern: 'same-account' or 'cross-account'
        """
        self.source_account_id = source_account_id
        self.staging_account_id = staging_account_id
        self.source_region = source_region
        self.target_region = target_region
        self.source_role_arn = source_role_arn
        self.staging_role_arn = staging_role_arn
        self.external_id = external_id
        self.deployment_pattern = deployment_pattern

        # Get credentials for source account
        if source_role_arn:
            self.source_credentials = self._assume_role(
                source_role_arn, "DRSAgentDeployment-Source"
            )
        else:
            self.source_credentials = None

        # Get credentials for staging account (if different)
        if deployment_pattern == "cross-account" and staging_role_arn:
            self.staging_credentials = self._assume_role(
                staging_role_arn, "DRSAgentDeployment-Staging"
            )
        else:
            self.staging_credentials = self.source_credentials

        # Initialize AWS clients
        # EC2 and SSM use source account (where instances are)
        self.ec2_client = self._get_client("ec2", source_region, self.source_credentials)
        self.ssm_client = self._get_client("ssm", source_region, self.source_credentials)

        # DRS uses staging account (where replication goes)
        self.drs_client = self._get_client("drs", target_region, self.staging_credentials)

    def _assume_role(self, role_arn: str, session_name: str) -> Dict[str, str]:
        """
        Assume cross-account role.

        Args:
            role_arn: ARN of role to assume
            session_name: Session name for the assumed role

        Returns:
            Credentials dictionary
        """
        print(f"Assuming role: {role_arn}")

        sts_client = boto3.client("sts")

        assume_role_params = {
            "RoleArn": role_arn,
            "RoleSessionName": session_name,
        }

        if self.external_id:
            assume_role_params["ExternalId"] = self.external_id

        response = sts_client.assume_role(**assume_role_params)

        credentials = response["Credentials"]
        account_id = role_arn.split(":")[4]
        print(f"✅ Assumed role in account {account_id}")

        return {
            "aws_access_key_id": credentials["AccessKeyId"],
            "aws_secret_access_key": credentials["SecretAccessKey"],
            "aws_session_token": credentials["SessionToken"],
        }

    def _get_client(self, service: str, region: str, credentials: Optional[Dict[str, str]]):
        """
        Get AWS service client with appropriate credentials.

        Args:
            service: AWS service name
            region: AWS region
            credentials: Credentials dict (optional)

        Returns:
            Boto3 client
        """
        if credentials:
            return boto3.client(service, region_name=region, **credentials)
        else:
            return boto3.client(service, region_name=region)

    def discover_instances(self) -> List[Dict[str, Any]]:
        """
        Discover EC2 instances with DR tags.

        Returns:
            List of instances with metadata
        """
        print("Discovering instances with DR tags...")

        try:
            response = self.ec2_client.describe_instances(
                Filters=[
                    {"Name": "tag:dr:enabled", "Values": ["true"]},
                    {"Name": "tag:dr:recovery-strategy", "Values": ["drs"]},
                    {"Name": "instance-state-name", "Values": ["running"]},
                ]
            )

            instances = []
            for reservation in response["Reservations"]:
                for instance in reservation["Instances"]:
                    # Extract tags
                    tags = {tag["Key"]: tag["Value"] for tag in instance.get("Tags", [])}

                    instances.append(
                        {
                            "instance_id": instance["InstanceId"],
                            "name": tags.get("Name", "Unknown"),
                            "wave": tags.get("dr:wave", "unassigned"),
                            "priority": tags.get("dr:priority", "unknown"),
                            "private_ip": instance.get("PrivateIpAddress"),
                            "instance_type": instance["InstanceType"],
                            "platform": instance.get("Platform", "Linux"),
                        }
                    )

            # Sort by wave
            instances.sort(key=lambda x: x["wave"])

            print(f"Found {len(instances)} instances")
            self._print_instances_by_wave(instances)

            return instances

        except ClientError as e:
            print(f"Error discovering instances: {e}")
            raise

    def _print_instances_by_wave(self, instances: List[Dict[str, Any]]):
        """Print instances grouped by wave."""
        waves = {}
        for instance in instances:
            wave = instance["wave"]
            if wave not in waves:
                waves[wave] = []
            waves[wave].append(instance)

        print("\nInstances by DR Wave:")
        print("=" * 60)
        for wave in sorted(waves.keys()):
            print(f"\nDR Wave {wave}:")
            for inst in waves[wave]:
                print(f"  - {inst['instance_id']} ({inst['name']})")

    def check_ssm_status(self, instance_ids: List[str], max_wait: int = 300) -> Dict[str, str]:
        """
        Check SSM agent status for instances.

        Args:
            instance_ids: List of instance IDs
            max_wait: Maximum seconds to wait for agents

        Returns:
            Dict mapping instance_id to ping status
        """
        print(f"\nChecking SSM agent status for {len(instance_ids)} instances...")

        wait_interval = 15
        elapsed = 0

        while elapsed < max_wait:
            try:
                response = self.ssm_client.describe_instance_information(
                    Filters=[{"Key": "InstanceIds", "Values": instance_ids}]
                )

                status_map = {
                    info["InstanceId"]: info["PingStatus"]
                    for info in response["InstanceInformationList"]
                }

                online_count = sum(1 for status in status_map.values() if status == "Online")

                print(f"[{elapsed}s] SSM agents online: " f"{online_count}/{len(instance_ids)}")

                if online_count == len(instance_ids):
                    print("✅ All SSM agents are online")
                    return status_map

                time.sleep(wait_interval)
                elapsed += wait_interval

            except ClientError as e:
                print(f"Error checking SSM status: {e}")
                raise

        print(f"⚠️  Only {online_count}/{len(instance_ids)} " f"SSM agents online after {max_wait}s")
        return status_map

    def deploy_agents(
        self, wait_for_completion: bool = True, timeout_seconds: int = 600
    ) -> Dict[str, Any]:
        """
        Deploy DRS agents to discovered instances.

        Args:
            wait_for_completion: Wait for command completion
            timeout_seconds: Maximum seconds to wait

        Returns:
            Deployment results
        """
        start_time = datetime.utcnow()

        print(f"\n{'='*60}")
        print(f"DRS Agent Deployment - {self.deployment_pattern.upper()}")
        print(f"{'='*60}")
        print(f"Source Account: {self.source_account_id}")
        print(f"Staging Account: {self.staging_account_id}")
        print(f"Source Region: {self.source_region}")
        print(f"Target Region: {self.target_region}")
        print(f"{'='*60}\n")

        # Discover instances
        instances = self.discover_instances()

        if not instances:
            return {
                "status": "no_instances",
                "message": "No instances found with DR tags",
                "source_account_id": self.source_account_id,
                "staging_account_id": self.staging_account_id,
                "source_region": self.source_region,
                "target_region": self.target_region,
                "deployment_pattern": self.deployment_pattern,
            }

        instance_ids = [inst["instance_id"] for inst in instances]

        # Check SSM status
        ssm_status = self.check_ssm_status(instance_ids)
        online_instances = [iid for iid, status in ssm_status.items() if status == "Online"]

        if not online_instances:
            return {
                "status": "error",
                "message": "No instances have SSM agent online",
                "source_account_id": self.source_account_id,
                "staging_account_id": self.staging_account_id,
                "instances_discovered": len(instances),
                "instances_online": 0,
                "deployment_pattern": self.deployment_pattern,
            }

        # Send SSM command to install DRS agents
        print(f"\nInstalling DRS agents on {len(online_instances)} instances...")
        print(f"Agents will replicate to staging account: {self.staging_account_id}")
        print(f"Target region: {self.target_region}\n")

        try:
            response = self.ssm_client.send_command(
                InstanceIds=online_instances,
                DocumentName="AWSDisasterRecovery-InstallDRAgentOnInstance",
                Parameters={
                    "Region": [self.target_region],
                    "StagingAccountID": [self.staging_account_id],
                },
                Comment=(
                    f"DRS agent deployment: "
                    f"{self.source_account_id} → {self.staging_account_id}"
                ),
            )

            command_id = response["Command"]["CommandId"]
            print(f"Command ID: {command_id}")

            # Wait for completion if requested
            if wait_for_completion:
                command_results = self._wait_for_command(
                    command_id, online_instances, timeout_seconds
                )
            else:
                command_results = {
                    "status": "in_progress",
                    "command_id": command_id,
                }

            # Check DRS source servers in staging account
            print(f"\nVerifying DRS registration in staging account...")
            time.sleep(30)  # Wait for DRS registration
            source_servers = self._get_source_servers()

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            return {
                "status": "success",
                "source_account_id": self.source_account_id,
                "staging_account_id": self.staging_account_id,
                "source_region": self.source_region,
                "target_region": self.target_region,
                "deployment_pattern": self.deployment_pattern,
                "instances_discovered": len(instances),
                "instances_online": len(online_instances),
                "instances_deployed": len(online_instances),
                "command_id": command_id,
                "command_results": command_results,
                "source_servers": source_servers,
                "duration_seconds": duration,
                "timestamp": end_time.isoformat(),
            }

        except ClientError as e:
            print(f"Error deploying agents: {e}")
            return {
                "status": "error",
                "message": str(e),
                "source_account_id": self.source_account_id,
                "staging_account_id": self.staging_account_id,
                "deployment_pattern": self.deployment_pattern,
            }

    def _wait_for_command(
        self, command_id: str, instance_ids: List[str], timeout_seconds: int
    ) -> Dict[str, Any]:
        """Wait for SSM command completion."""
        print(f"\nWaiting for command completion (timeout: {timeout_seconds}s)...")

        wait_interval = 20
        elapsed = 0

        while elapsed < timeout_seconds:
            try:
                response = self.ssm_client.list_command_invocations(
                    CommandId=command_id, Details=True
                )

                invocations = response["CommandInvocations"]

                status_counts = {
                    "Success": 0,
                    "InProgress": 0,
                    "Failed": 0,
                    "Cancelled": 0,
                    "TimedOut": 0,
                }

                for inv in invocations:
                    status = inv["Status"]
                    status_counts[status] = status_counts.get(status, 0) + 1

                print(
                    f"[{elapsed}s] Success: {status_counts['Success']} | "
                    f"InProgress: {status_counts['InProgress']} | "
                    f"Failed: {status_counts['Failed']}"
                )

                # Check if all completed
                if status_counts["Success"] == len(instance_ids):
                    print("✅ All agents installed successfully")
                    return {
                        "status": "completed",
                        "success_count": status_counts["Success"],
                        "failed_count": status_counts["Failed"],
                        "invocations": [
                            {
                                "instance_id": inv["InstanceId"],
                                "status": inv["Status"],
                                "status_details": inv.get("StatusDetails", ""),
                            }
                            for inv in invocations
                        ],
                    }

                # Check if any failed and none in progress
                if status_counts["Failed"] > 0 and status_counts["InProgress"] == 0:
                    print(f"❌ {status_counts['Failed']} installations failed")
                    return {
                        "status": "partial_failure",
                        "success_count": status_counts["Success"],
                        "failed_count": status_counts["Failed"],
                        "invocations": [
                            {
                                "instance_id": inv["InstanceId"],
                                "status": inv["Status"],
                                "status_details": inv.get("StatusDetails", ""),
                            }
                            for inv in invocations
                        ],
                    }

                time.sleep(wait_interval)
                elapsed += wait_interval

            except ClientError as e:
                print(f"Error checking command status: {e}")
                raise

        print(f"⏱️  Command timed out after {timeout_seconds}s")
        return {
            "status": "timeout",
            "message": f"Command did not complete within {timeout_seconds}s",
        }

    def _get_source_servers(self) -> List[Dict[str, Any]]:
        """
        Get DRS source servers in staging account's target region.

        Note: This queries the staging account's DRS service to verify
        that agents from the source account have registered successfully.
        """
        try:
            print(f"Querying DRS in staging account {self.staging_account_id}...")
            response = self.drs_client.describe_source_servers()

            servers = []
            for item in response.get("items", []):
                servers.append(
                    {
                        "source_server_id": item["sourceServerID"],
                        "hostname": item.get("sourceProperties", {})
                        .get("identificationHints", {})
                        .get("hostname", "Unknown"),
                        "replication_state": item.get("dataReplicationInfo", {}).get(
                            "dataReplicationState", "Unknown"
                        ),
                        "last_launch_result": item.get("lastLaunchResult", "NOT_STARTED"),
                    }
                )

            print(f"✅ Found {len(servers)} DRS source servers in staging account")
            return servers

        except ClientError as e:
            print(f"Error getting source servers: {e}")
            return []


def send_notification(topic_arn: str, result: Dict[str, Any]):
    """Send SNS notification with deployment results."""
    try:
        sns_client = boto3.client("sns")

        subject = f"DRS Agent Deployment - {result['status'].upper()}"

        message = f"""
DRS Agent Deployment Results

Account: {result.get('account_id')}
Source Region: {result.get('source_region')}
Target Region: {result.get('target_region')}
Status: {result.get('status')}

Instances Discovered: {result.get('instances_discovered', 0)}
Instances Online: {result.get('instances_online', 0)}
Instances Deployed: {result.get('instances_deployed', 0)}

Source Servers: {len(result.get('source_servers', []))}

Duration: {result.get('duration_seconds', 0):.1f} seconds
Timestamp: {result.get('timestamp')}
"""

        sns_client.publish(TopicArn=topic_arn, Subject=subject, Message=message)

        print(f"✅ Notification sent to {topic_arn}")

    except Exception as e:
        print(f"Error sending notification: {e}")


def success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Format success response."""
    return {"statusCode": 200, "body": json.dumps(data, default=str)}


def error_response(message: str) -> Dict[str, Any]:
    """Format error response."""
    return {
        "statusCode": 400,
        "body": json.dumps({"status": "error", "message": message}),
    }
