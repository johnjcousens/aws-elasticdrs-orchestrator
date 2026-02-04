"""
Launch configuration validation utilities for per-server customization.

This module provides validation functions for launch template fields,
with primary focus on static private IP address validation and AWS-
approved field enforcement. All validations follow AWS specifications
and best practices per AWS Configuration Synchronizer.

Key Functions:
- validate_static_ip: Validate static private IP addresses
- validate_aws_approved_fields: Enforce AWS-approved field restrictions

Validates: Requirements 3.1, 3.1.1, 3.1.2, 3.2, 4.1.5, 9.1
"""

import ipaddress
from typing import Dict, Any, Optional

import boto3
from botocore.exceptions import ClientError


def validate_static_ip(ip: str, subnet_id: str, region: str) -> Dict[str, Any]:
    """
    Validate static private IP address for launch template assignment.

    This function performs comprehensive validation:
    1. IPv4 format validation
    2. IP within subnet CIDR range
    3. IP not in reserved range (first 4, last 1 addresses)
    4. IP availability check via AWS API

    Args:
        ip: IPv4 address to validate (e.g., "10.0.1.100")
        subnet_id: Target subnet ID (e.g., "subnet-xxx")
        region: AWS region (e.g., "us-east-1")

    Returns:
        Dict containing validation result:
        {
            "valid": bool,
            "message": str (optional),
            "conflictingResource": dict (optional)
        }

    Example:
        >>> result = validate_static_ip(
        ...     "10.0.1.100",
        ...     "subnet-xxx",
        ...     "us-east-1"
        ... )
        >>> result["valid"]
        True

    Validates: Requirements 3.1, 3.2, 4.1.5, 9.1
    """
    # Step 1: Validate IPv4 format
    format_result = _validate_ip_format(ip)
    if not format_result["valid"]:
        return format_result

    # Step 2: Get subnet CIDR and validate IP is within range
    try:
        ec2_client = boto3.client("ec2", region_name=region)
        subnet_info = _get_subnet_info(ec2_client, subnet_id)

        if not subnet_info:
            return {
                "valid": False,
                "error": "SUBNET_NOT_FOUND",
                "message": f"Subnet {subnet_id} not found in region " f"{region}",
                "field": "subnetId",
            }

        cidr = subnet_info["cidr"]
        vpc_id = subnet_info["vpcId"]

    except ClientError as e:
        return {
            "valid": False,
            "error": "AWS_API_ERROR",
            "message": f"Failed to query subnet: {str(e)}",
            "field": "staticPrivateIp",
        }

    # Step 3: Validate IP within CIDR range
    cidr_result = _validate_ip_in_cidr(ip, cidr)
    if not cidr_result["valid"]:
        cidr_result["subnet"] = subnet_id
        cidr_result["cidr"] = cidr
        return cidr_result

    # Step 4: Check IP not in reserved range
    reserved_result = _validate_ip_not_reserved(ip, cidr)
    if not reserved_result["valid"]:
        return reserved_result

    # Step 5: Check IP availability in AWS
    try:
        availability_result = _check_ip_availability(ec2_client, ip, subnet_id, vpc_id)

        # Add subnet CIDR to success response
        if availability_result.get("valid"):
            availability_result["subnetCidr"] = cidr

        return availability_result

    except ClientError as e:
        return {
            "valid": False,
            "error": "AWS_API_ERROR",
            "message": f"Failed to check IP availability: {str(e)}",
            "field": "staticPrivateIp",
        }


def _validate_ip_format(ip: str) -> Dict[str, Any]:
    """
    Validate IPv4 address format.

    Args:
        ip: IP address string to validate

    Returns:
        Dict with validation result
    """
    try:
        # Use ipaddress module for robust validation
        ip_obj = ipaddress.IPv4Address(ip)

        # Additional check: ensure it's a private IP
        if not ip_obj.is_private:
            return {
                "valid": False,
                "error": "IP_NOT_PRIVATE",
                "message": f"IP address {ip} is not a private IP address. "
                "Only private IPs (10.0.0.0/8, 172.16.0.0/12, "
                "192.168.0.0/16) are allowed.",
                "field": "staticPrivateIp",
                "value": ip,
            }

        return {"valid": True}

    except ValueError:
        return {
            "valid": False,
            "error": "INVALID_IP_FORMAT",
            "message": f"IP address '{ip}' is not a valid IPv4 address. " "Format must be X.X.X.X where X is 0-255.",
            "field": "staticPrivateIp",
            "value": ip,
        }


def _get_subnet_info(ec2_client, subnet_id: str) -> Optional[Dict[str, str]]:
    """
    Get subnet CIDR and VPC ID from AWS.

    Args:
        ec2_client: Boto3 EC2 client
        subnet_id: Subnet ID to query

    Returns:
        Dict with cidr and vpcId, or None if not found
    """
    try:
        response = ec2_client.describe_subnets(SubnetIds=[subnet_id])

        if not response.get("Subnets"):
            return None

        subnet = response["Subnets"][0]
        return {"cidr": subnet["CidrBlock"], "vpcId": subnet["VpcId"]}

    except ClientError as e:
        if e.response["Error"]["Code"] == "InvalidSubnetID.NotFound":
            return None
        raise


def _validate_ip_in_cidr(ip: str, cidr: str) -> Dict[str, Any]:
    """
    Validate IP address is within subnet CIDR range.

    Args:
        ip: IP address to validate
        cidr: Subnet CIDR (e.g., "10.0.1.0/24")

    Returns:
        Dict with validation result
    """
    try:
        ip_obj = ipaddress.IPv4Address(ip)
        network = ipaddress.IPv4Network(cidr, strict=False)

        if ip_obj not in network:
            return {
                "valid": False,
                "error": "IP_OUT_OF_RANGE",
                "message": f"IP {ip} is not within subnet CIDR range " f"{cidr}",
                "field": "staticPrivateIp",
            }

        return {"valid": True}

    except ValueError as e:
        return {
            "valid": False,
            "error": "INVALID_CIDR",
            "message": f"Invalid CIDR format: {str(e)}",
            "field": "staticPrivateIp",
        }


def _validate_ip_not_reserved(ip: str, cidr: str) -> Dict[str, Any]:
    """
    Validate IP is not in AWS reserved range.

    AWS reserves the first 4 and last 1 IP addresses in each subnet:
    - First IP (network address): .0
    - Second IP (VPC router): .1
    - Third IP (DNS server): .2
    - Fourth IP (future use): .3
    - Last IP (broadcast): .255 (for /24)

    Args:
        ip: IP address to validate
        cidr: Subnet CIDR

    Returns:
        Dict with validation result
    """
    try:
        ip_obj = ipaddress.IPv4Address(ip)
        network = ipaddress.IPv4Network(cidr, strict=False)

        # Get first 4 and last 1 addresses
        network_hosts = list(network.hosts())
        reserved_ips = []

        # First 4 IPs (including network address)
        reserved_ips.append(network.network_address)
        if len(network_hosts) >= 3:
            reserved_ips.extend(network_hosts[:3])

        # Last IP (broadcast address)
        reserved_ips.append(network.broadcast_address)

        if ip_obj in reserved_ips:
            # Format reserved range for error message
            first_reserved = str(network.network_address)
            if len(network_hosts) >= 3:
                last_first_four = str(network_hosts[2])
            else:
                last_first_four = str(network.network_address)

            broadcast = str(network.broadcast_address)

            return {
                "valid": False,
                "error": "IP_RESERVED",
                "message": f"IP {ip} is in AWS reserved range. "
                f"AWS reserves first 4 addresses ({first_reserved} - "
                f"{last_first_four}) and last address ({broadcast}) "
                "in each subnet.",
                "field": "staticPrivateIp",
                "reservedRange": f"{first_reserved} - {last_first_four}, " f"{broadcast}",
            }

        return {"valid": True}

    except ValueError as e:
        return {
            "valid": False,
            "error": "VALIDATION_ERROR",
            "message": f"Error validating reserved range: {str(e)}",
            "field": "staticPrivateIp",
        }


def _check_ip_availability(ec2_client, ip: str, subnet_id: str, vpc_id: str) -> Dict[str, Any]:
    """
    Check if IP address is available (not already assigned).

    Queries AWS to check if the IP is assigned to any network interface
    or instance in the subnet.

    Args:
        ec2_client: Boto3 EC2 client
        ip: IP address to check
        subnet_id: Subnet ID
        vpc_id: VPC ID

    Returns:
        Dict with validation result and conflicting resource info
    """
    try:
        # Query network interfaces with this private IP
        response = ec2_client.describe_network_interfaces(
            Filters=[
                {"Name": "private-ip-address", "Values": [ip]},
                {"Name": "subnet-id", "Values": [subnet_id]},
            ]
        )

        network_interfaces = response.get("NetworkInterfaces", [])

        if network_interfaces:
            # IP is in use - get details of conflicting resource
            eni = network_interfaces[0]
            conflict_info = _get_conflict_info(eni)

            return {
                "valid": False,
                "error": "IP_IN_USE",
                "message": f"IP {ip} is already assigned to " f"{conflict_info['type']} {conflict_info['id']}",
                "field": "staticPrivateIp",
                "conflictingResource": conflict_info,
            }

        # IP is available
        return {
            "valid": True,
            "message": f"IP {ip} is available in subnet {subnet_id}",
        }

    except ClientError as e:
        # If we can't check availability, fail safe
        return {
            "valid": False,
            "error": "AWS_API_ERROR",
            "message": f"Unable to verify IP availability: {str(e)}",
            "field": "staticPrivateIp",
        }


def _get_conflict_info(eni: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract conflicting resource information from network interface.

    Args:
        eni: Network interface description from AWS API

    Returns:
        Dict with resource type, id, and name
    """
    conflict_info = {
        "type": "network-interface",
        "id": eni.get("NetworkInterfaceId", "unknown"),
        "name": None,
    }

    # Check if attached to an instance
    attachment = eni.get("Attachment", {})
    instance_id = attachment.get("InstanceId")

    if instance_id:
        conflict_info["type"] = "instance"
        conflict_info["id"] = instance_id

        # Try to get instance name from tags
        tags = eni.get("TagSet", [])
        name_tag = next((tag for tag in tags if tag.get("Key") == "Name"), None)
        if name_tag:
            conflict_info["name"] = name_tag.get("Value")

    # Check for DRS-specific tags
    tags = eni.get("TagSet", [])
    drs_tag = next(
        (tag for tag in tags if tag.get("Key") == "AWSElasticDisasterRecovery"),
        None,
    )
    if drs_tag:
        conflict_info["isDrsResource"] = True

    return conflict_info


# AWS-approved fields per AWS Configuration Synchronizer
# These fields are safe for customer modification and will persist
# through DRS operations
ALLOWED_FIELDS = [
    "staticPrivateIp",  # Maps to NetworkInterfaces[0].PrivateIpAddress
    "subnetId",  # Maps to NetworkInterfaces[0].SubnetId
    "securityGroupIds",  # Maps to NetworkInterfaces[0].Groups
    "instanceType",  # Maps to InstanceType
    "instanceProfileName",  # Maps to IamInstanceProfile
    "associatePublicIp",  # Maps to NetworkInterfaces[0].AssociatePublicIpAddress
    "monitoring",  # Maps to Monitoring.Enabled
    "ebsOptimized",  # Maps to EbsOptimized
    "disableApiTermination",  # Maps to DisableApiTermination
    "tags",  # Maps to TagSpecifications
    "creditSpecification",  # Maps to CreditSpecification
]

# DRS-managed fields that MUST NOT be modified by customers
# These fields are controlled by AWS DRS and modifications will be
# ignored or cause recovery failures
BLOCKED_FIELDS = [
    "imageId",  # DRS creates recovery-specific AMIs
    "userData",  # DRS may inject recovery scripts
    "blockDeviceMappings",  # DRS manages disk mappings from source
    "placementGroup",  # DRS manages placement for recovery
    "availabilityZone",  # DRS determines AZ based on subnet
    "keyName",  # DRS manages SSH keys separately
]


def validate_aws_approved_fields(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that configuration only contains AWS-approved fields.

    This function ensures that only fields officially supported by AWS
    DRS Configuration Synchronizer are present in the configuration.
    Any DRS-managed fields will be rejected with clear error messages.

    AWS-approved fields (safe for customer modification):
    - staticPrivateIp: Static private IP address
    - subnetId: Target subnet for recovery instance
    - securityGroupIds: Security groups for network access
    - instanceType: EC2 instance type
    - instanceProfileName: IAM instance profile
    - associatePublicIp: Public IP assignment
    - monitoring: CloudWatch detailed monitoring
    - ebsOptimized: EBS optimization setting
    - disableApiTermination: Termination protection
    - tags: Resource tags
    - userData: User data script
    - creditSpecification: T-series CPU credits

    DRS-managed fields (MUST NOT be modified):
    - imageId: DRS creates recovery-specific AMIs
    - placementGroup: DRS manages placement for recovery
    - availabilityZone: DRS determines AZ based on subnet
    - keyName: DRS manages SSH keys separately

    Args:
        config: Launch template configuration dict to validate

    Returns:
        Dict containing validation result:
        {
            "valid": bool,
            "message": str (optional),
            "blockedFields": list (optional),
            "unknownFields": list (optional)
        }

    Example:
        >>> config = {
        ...     "staticPrivateIp": "10.0.1.100",
        ...     "instanceType": "c6a.xlarge",
        ...     "imageId": "ami-xxx"  # BLOCKED
        ... }
        >>> result = validate_aws_approved_fields(config)
        >>> result["valid"]
        False
        >>> result["blockedFields"]
        ["imageId"]

    Validates: Requirements 3.1.1, 3.1.2
    """
    if not config:
        return {"valid": True}

    # Check for blocked fields
    blocked_found = []
    for field in config.keys():
        if field in BLOCKED_FIELDS:
            blocked_found.append(field)

    if blocked_found:
        blocked_list = ", ".join(blocked_found)
        return {
            "valid": False,
            "error": "BLOCKED_FIELDS_PRESENT",
            "message": f"Configuration contains DRS-managed fields that "
            f"cannot be modified: {blocked_list}. These fields are "
            "controlled by AWS DRS and will cause recovery failures "
            "if overridden.",
            "blockedFields": blocked_found,
            "field": "launchTemplate",
        }

    # Check for unknown fields (not in allowed list)
    unknown_found = []
    for field in config.keys():
        if field not in ALLOWED_FIELDS:
            unknown_found.append(field)

    if unknown_found:
        unknown_list = ", ".join(unknown_found)
        allowed_list = ", ".join(ALLOWED_FIELDS)
        return {
            "valid": False,
            "error": "UNKNOWN_FIELDS_PRESENT",
            "message": f"Configuration contains unknown fields: "
            f"{unknown_list}. Only AWS-approved fields are allowed: "
            f"{allowed_list}",
            "unknownFields": unknown_found,
            "field": "launchTemplate",
        }

    # All fields are approved
    return {
        "valid": True,
        "message": "All fields are AWS-approved for customer modification",
    }


def validate_security_groups(sg_ids: list, vpc_id: str, region: str) -> Dict[str, Any]:
    """
    Validate security group IDs exist and belong to specified VPC.

    This function verifies:
    1. Security group ID format (sg-[0-9a-f]{8,17})
    2. Security groups exist in AWS
    3. Security groups belong to the specified VPC

    Args:
        sg_ids: List of security group IDs to validate
        vpc_id: VPC ID that security groups must belong to
        region: AWS region (e.g., "us-east-1")

    Returns:
        Dict containing validation result:
        {
            "valid": bool,
            "message": str (optional),
            "invalidGroups": list (optional),
            "details": dict (optional)
        }

    Example:
        >>> result = validate_security_groups(
        ...     ["sg-00d3ed189b8073ea4"],
        ...     "vpc-xxx",
        ...     "us-east-1"
        ... )
        >>> result["valid"]
        True

    Validates: Requirements 4.1, 4.1.1
    """
    import re

    if not sg_ids:
        return {"valid": True, "message": "No security groups to validate"}

    # Pattern for security group IDs: sg- followed by 8-17 hex chars
    sg_pattern = re.compile(r"^sg-[0-9a-f]{8,17}$")

    # Step 1: Validate format
    invalid_format = []
    for sg_id in sg_ids:
        if not sg_pattern.match(sg_id):
            invalid_format.append(sg_id)

    if invalid_format:
        return {
            "valid": False,
            "error": "INVALID_SECURITY_GROUP_FORMAT",
            "message": f"Security group IDs have invalid format: "
            f"{', '.join(invalid_format)}. Format must be "
            "sg-[0-9a-f]{{8,17}}",
            "field": "securityGroupIds",
            "invalidGroups": invalid_format,
        }

    # Step 2: Query AWS to verify existence and VPC membership
    try:
        ec2_client = boto3.client("ec2", region_name=region)
        response = ec2_client.describe_security_groups(GroupIds=sg_ids)

        found_groups = response.get("SecurityGroups", [])
        found_ids = {sg["GroupId"] for sg in found_groups}

        # Check for missing security groups
        missing_groups = [sg_id for sg_id in sg_ids if sg_id not in found_ids]

        if missing_groups:
            return {
                "valid": False,
                "error": "SECURITY_GROUPS_NOT_FOUND",
                "message": f"Security groups not found: " f"{', '.join(missing_groups)}",
                "field": "securityGroupIds",
                "invalidGroups": missing_groups,
            }

        # Check VPC membership
        wrong_vpc = []
        for sg in found_groups:
            if sg.get("VpcId") != vpc_id:
                wrong_vpc.append(
                    {
                        "groupId": sg["GroupId"],
                        "actualVpcId": sg.get("VpcId"),
                        "expectedVpcId": vpc_id,
                    }
                )

        if wrong_vpc:
            wrong_vpc_ids = [sg["groupId"] for sg in wrong_vpc]
            return {
                "valid": False,
                "error": "SECURITY_GROUPS_WRONG_VPC",
                "message": f"Security groups do not belong to VPC " f"{vpc_id}: {', '.join(wrong_vpc_ids)}",
                "field": "securityGroupIds",
                "invalidGroups": wrong_vpc_ids,
                "details": {"wrongVpcGroups": wrong_vpc},
            }

        # All security groups are valid
        return {
            "valid": True,
            "message": f"All {len(sg_ids)} security groups are valid " f"and belong to VPC {vpc_id}",
        }

    except ClientError as e:
        error_code = e.response["Error"]["Code"]

        if error_code == "InvalidGroup.NotFound":
            return {
                "valid": False,
                "error": "SECURITY_GROUPS_NOT_FOUND",
                "message": f"One or more security groups not found: " f"{str(e)}",
                "field": "securityGroupIds",
            }

        return {
            "valid": False,
            "error": "AWS_API_ERROR",
            "message": f"Failed to validate security groups: {str(e)}",
            "field": "securityGroupIds",
        }


def validate_instance_type(instance_type: str, region: str) -> Dict[str, Any]:
    """
    Validate instance type is available in the specified region.

    This function uses EC2 DescribeInstanceTypeOfferings API to verify
    the instance type is available in the target region.

    Args:
        instance_type: EC2 instance type (e.g., "c6a.xlarge")
        region: AWS region (e.g., "us-east-1")

    Returns:
        Dict containing validation result:
        {
            "valid": bool,
            "message": str (optional),
            "details": dict (optional)
        }

    Example:
        >>> result = validate_instance_type("c6a.xlarge", "us-east-1")
        >>> result["valid"]
        True

    Validates: Requirements 4.2, 4.1.2
    """
    if not instance_type:
        return {
            "valid": False,
            "error": "MISSING_INSTANCE_TYPE",
            "message": "Instance type is required",
            "field": "instanceType",
        }

    try:
        ec2_client = boto3.client("ec2", region_name=region)

        # Query instance type offerings in the region
        response = ec2_client.describe_instance_type_offerings(
            LocationType="region",
            Filters=[{"Name": "instance-type", "Values": [instance_type]}],
        )

        offerings = response.get("InstanceTypeOfferings", [])

        if not offerings:
            return {
                "valid": False,
                "error": "INSTANCE_TYPE_UNAVAILABLE",
                "message": f"Instance type {instance_type} is not " f"available in region {region}",
                "field": "instanceType",
                "details": {"instanceType": instance_type, "region": region},
            }

        # Instance type is available
        return {
            "valid": True,
            "message": f"Instance type {instance_type} is available in " f"region {region}",
            "details": {"instanceType": instance_type, "region": region},
        }

    except ClientError as e:
        return {
            "valid": False,
            "error": "AWS_API_ERROR",
            "message": f"Failed to validate instance type: {str(e)}",
            "field": "instanceType",
        }


def validate_iam_profile(profile_name: str, region: str) -> Dict[str, Any]:
    """
    Validate IAM instance profile exists.

    This function uses IAM GetInstanceProfile API to verify the
    instance profile exists and is accessible.

    Args:
        profile_name: IAM instance profile name (e.g., "demo-ec2-profile")
        region: AWS region (used for client initialization)

    Returns:
        Dict containing validation result:
        {
            "valid": bool,
            "message": str (optional),
            "details": dict (optional)
        }

    Example:
        >>> result = validate_iam_profile(
        ...     "demo-ec2-profile",
        ...     "us-east-1"
        ... )
        >>> result["valid"]
        True

    Validates: Requirements 4.3, 4.1.4
    """
    if not profile_name:
        return {
            "valid": False,
            "error": "MISSING_IAM_PROFILE",
            "message": "IAM instance profile name is required",
            "field": "instanceProfileName",
        }

    try:
        # IAM is global, but we accept region for consistency
        iam_client = boto3.client("iam", region_name=region)

        # Query instance profile
        response = iam_client.get_instance_profile(InstanceProfileName=profile_name)

        profile = response.get("InstanceProfile", {})
        profile_arn = profile.get("Arn")

        # Instance profile exists
        return {
            "valid": True,
            "message": f"IAM instance profile {profile_name} exists",
            "details": {
                "profileName": profile_name,
                "profileArn": profile_arn,
            },
        }

    except ClientError as e:
        error_code = e.response["Error"]["Code"]

        if error_code == "NoSuchEntity":
            return {
                "valid": False,
                "error": "IAM_PROFILE_NOT_FOUND",
                "message": f"IAM instance profile '{profile_name}' does " "not exist",
                "field": "instanceProfileName",
                "details": {"profileName": profile_name},
            }

        return {
            "valid": False,
            "error": "AWS_API_ERROR",
            "message": f"Failed to validate IAM instance profile: " f"{str(e)}",
            "field": "instanceProfileName",
        }


def validate_subnet(subnet_id: str, region: str) -> Dict[str, Any]:
    """
    Validate subnet exists and return subnet details.

    This function uses EC2 DescribeSubnets API to verify the subnet
    exists and returns subnet details including CIDR, VPC ID, and AZ.

    Args:
        subnet_id: Subnet ID (e.g., "subnet-05271904a7c44689f")
        region: AWS region (e.g., "us-east-1")

    Returns:
        Dict containing validation result:
        {
            "valid": bool,
            "message": str (optional),
            "details": dict (optional with cidr, vpcId, availabilityZone)
        }

    Example:
        >>> result = validate_subnet(
        ...     "subnet-05271904a7c44689f",
        ...     "us-east-1"
        ... )
        >>> result["valid"]
        True
        >>> result["details"]["cidr"]
        "10.0.1.0/24"

    Validates: Requirements 4.1.3
    """
    import re

    if not subnet_id:
        return {
            "valid": False,
            "error": "MISSING_SUBNET_ID",
            "message": "Subnet ID is required",
            "field": "subnetId",
        }

    # Validate subnet ID format: subnet- followed by 17 hex chars
    subnet_pattern = re.compile(r"^subnet-[0-9a-f]{17}$")
    if not subnet_pattern.match(subnet_id):
        return {
            "valid": False,
            "error": "INVALID_SUBNET_FORMAT",
            "message": f"Subnet ID '{subnet_id}' has invalid format. " "Format must be subnet-[0-9a-f]{{17}}",
            "field": "subnetId",
        }

    try:
        ec2_client = boto3.client("ec2", region_name=region)

        # Query subnet
        response = ec2_client.describe_subnets(SubnetIds=[subnet_id])

        subnets = response.get("Subnets", [])

        if not subnets:
            return {
                "valid": False,
                "error": "SUBNET_NOT_FOUND",
                "message": f"Subnet {subnet_id} not found in region " f"{region}",
                "field": "subnetId",
            }

        subnet = subnets[0]

        # Extract subnet details
        subnet_details = {
            "subnetId": subnet_id,
            "cidr": subnet.get("CidrBlock"),
            "vpcId": subnet.get("VpcId"),
            "availabilityZone": subnet.get("AvailabilityZone"),
            "availableIpAddressCount": subnet.get("AvailableIpAddressCount", 0),
        }

        return {
            "valid": True,
            "message": f"Subnet {subnet_id} exists in VPC " f"{subnet_details['vpcId']}",
            "details": subnet_details,
        }

    except ClientError as e:
        error_code = e.response["Error"]["Code"]

        if error_code == "InvalidSubnetID.NotFound":
            return {
                "valid": False,
                "error": "SUBNET_NOT_FOUND",
                "message": f"Subnet {subnet_id} not found in region " f"{region}",
                "field": "subnetId",
            }

        return {
            "valid": False,
            "error": "AWS_API_ERROR",
            "message": f"Failed to validate subnet: {str(e)}",
            "field": "subnetId",
        }


def validate_no_duplicate_ips(
    protection_group: Dict[str, Any],
    current_server_id: str,
    new_ip: str,
    new_subnet_id: str,
) -> Dict[str, Any]:
    """
    Validate that no other server in the same subnet has the same static IP.

    This function checks all servers in the protection group to ensure
    no duplicate IP addresses are configured within the same subnet.
    This prevents IP conflicts during recovery operations.

    Args:
        protection_group: Protection group dict containing servers array
        current_server_id: Server ID being updated (excluded from check)
        new_ip: New static private IP being assigned
        new_subnet_id: Subnet ID where the IP will be assigned

    Returns:
        Dict containing validation result:
        {
            "valid": bool,
            "message": str (optional),
            "conflictingServer": dict (optional)
        }

    Example:
        >>> result = validate_no_duplicate_ips(
        ...     protection_group,
        ...     "s-xxx",
        ...     "10.0.1.100",
        ...     "subnet-xxx"
        ... )
        >>> result["valid"]
        True

    Validates: Requirements 12.1, 12.2
    """
    if not new_ip:
        # No IP to check
        return {"valid": True}

    servers = protection_group.get("servers", [])
    group_defaults = protection_group.get("launchConfig", {})

    # Check each server for duplicate IP in same subnet
    for server in servers:
        server_id = server.get("sourceServerId")

        # Skip the current server being updated
        if server_id == current_server_id:
            continue

        # Get server's effective subnet and IP
        server_template = server.get("launchTemplate", {})
        use_defaults = server.get("useGroupDefaults", True)

        # Determine effective subnet for this server
        if use_defaults:
            # Server uses group defaults, may override specific fields
            server_subnet = server_template.get("subnetId") or group_defaults.get("subnetId")
        else:
            # Server has full custom config
            server_subnet = server_template.get("subnetId") or group_defaults.get("subnetId")

        # Determine effective static IP for this server
        server_ip = server_template.get("staticPrivateIp")

        # Check for duplicate: same IP in same subnet
        if server_ip and server_subnet == new_subnet_id and server_ip == new_ip:
            # Found duplicate IP in same subnet
            return {
                "valid": False,
                "error": "DUPLICATE_IP",
                "message": f"IP {new_ip} is already configured for server " f"{server_id} in subnet {new_subnet_id}",
                "field": "staticPrivateIp",
                "conflictingServer": {
                    "sourceServerId": server_id,
                    "instanceId": server.get("instanceId"),
                    "instanceName": server.get("instanceName"),
                    "staticPrivateIp": server_ip,
                    "subnetId": server_subnet,
                },
            }

    # No duplicate found
    return {
        "valid": True,
        "message": f"IP {new_ip} is not used by any other server in " f"subnet {new_subnet_id}",
    }


def validate_subnet_change_ip_revalidation(
    current_config: Dict[str, Any],
    new_config: Dict[str, Any],
    region: str,
) -> Dict[str, Any]:
    """
    Detect subnet changes and revalidate static IP against new subnet.

    When a server's subnet changes, any configured static IP must be
    revalidated to ensure it's still valid in the new subnet's CIDR
    range. This function detects subnet changes and performs full IP
    validation against the new subnet.

    Args:
        current_config: Current server launch configuration
        new_config: New server launch configuration being applied
        region: AWS region for validation

    Returns:
        Dict containing validation result:
        {
            "valid": bool,
            "subnetChanged": bool,
            "message": str (optional),
            "warning": str (optional),
            "details": dict (optional)
        }

    Example:
        >>> result = validate_subnet_change_ip_revalidation(
        ...     {"subnetId": "subnet-old", "staticPrivateIp": "10.0.1.100"},
        ...     {"subnetId": "subnet-new", "staticPrivateIp": "10.0.1.100"},
        ...     "us-east-1"
        ... )
        >>> result["subnetChanged"]
        True

    Validates: Requirements 12.3, 12.4
    """
    # Extract subnet IDs from configs
    current_subnet = current_config.get("subnetId")
    new_subnet = new_config.get("subnetId")

    # Extract static IP from new config
    static_ip = new_config.get("staticPrivateIp")

    # Check if subnet changed
    subnet_changed = current_subnet and new_subnet and current_subnet != new_subnet

    # If no subnet change, no revalidation needed
    if not subnet_changed:
        return {
            "valid": True,
            "subnetChanged": False,
            "message": "No subnet change detected",
        }

    # If no static IP configured, subnet change is safe
    if not static_ip:
        return {
            "valid": True,
            "subnetChanged": True,
            "message": f"Subnet changed from {current_subnet} to " f"{new_subnet}, no static IP to revalidate",
        }

    # Subnet changed and static IP configured - revalidate IP
    validation_result = validate_static_ip(static_ip, new_subnet, region)

    if not validation_result["valid"]:
        # IP is invalid in new subnet
        return {
            "valid": False,
            "subnetChanged": True,
            "error": "SUBNET_CHANGE_IP_INVALID",
            "message": f"Subnet changed from {current_subnet} to "
            f"{new_subnet}. Static IP {static_ip} is no longer valid: "
            f"{validation_result.get('message', 'IP validation failed')}",
            "warning": f"The configured static IP {static_ip} is not "
            f"valid in the new subnet {new_subnet}. Please update the "
            "IP address or remove it to use DHCP.",
            "field": "staticPrivateIp",
            "details": {
                "oldSubnet": current_subnet,
                "newSubnet": new_subnet,
                "staticPrivateIp": static_ip,
                "validationError": validation_result.get("error"),
                "validationMessage": validation_result.get("message"),
            },
        }

    # IP is valid in new subnet
    return {
        "valid": True,
        "subnetChanged": True,
        "message": f"Subnet changed from {current_subnet} to "
        f"{new_subnet}. Static IP {static_ip} is valid in new subnet.",
        "details": {
            "oldSubnet": current_subnet,
            "newSubnet": new_subnet,
            "staticPrivateIp": static_ip,
            "newSubnetCidr": validation_result.get("subnetCidr"),
        },
    }


# Helper functions for testing
def validate_static_ip_format(ip: str) -> Dict[str, Any]:
    """
    Validate IPv4 address format only (no AWS API calls).

    This is a wrapper around _validate_ip_format for testing purposes.
    """
    if ip is None:
        return {"valid": False, "message": "IP address cannot be None"}
    return _validate_ip_format(ip)


def validate_static_ip_cidr(ip: str, cidr: str) -> Dict[str, Any]:
    """
    Validate IP is within CIDR range and not reserved.

    This is a testing helper that combines CIDR and reserved range checks.
    """
    # Validate format first
    format_result = _validate_ip_format(ip)
    if not format_result["valid"]:
        return format_result

    # Validate CIDR range
    cidr_result = _validate_ip_in_cidr(ip, cidr)
    if not cidr_result["valid"]:
        return cidr_result

    # Validate not reserved
    return _validate_ip_not_reserved(ip, cidr)


def is_ip_in_reserved_range(ip: str, cidr: str) -> bool:
    """
    Check if IP is in AWS reserved range (first 4 or last 1 addresses).

    Returns True if IP is reserved, False otherwise.
    """
    result = _validate_ip_not_reserved(ip, cidr)
    return not result["valid"]


def validate_security_group_pattern(sg_id) -> Dict[str, Any]:
    """
    Validate security group ID pattern.

    Args:
        sg_id: Security group ID string or list of IDs

    Returns:
        Dict with validation result
    """
    import re

    # Handle list of security groups
    if isinstance(sg_id, list):
        invalid_groups = []
        for sg in sg_id:
            if not re.match(r"^sg-[0-9a-f]{8,17}$", sg):
                invalid_groups.append(sg)

        if invalid_groups:
            return {
                "valid": False,
                "message": f"Invalid security group IDs: {', '.join(invalid_groups)}",
                "invalidGroups": invalid_groups,
            }
        return {"valid": True}

    # Handle single security group
    if sg_id is None or sg_id == "":
        return {"valid": False, "message": "Security group ID cannot be empty"}

    if not re.match(r"^sg-[0-9a-f]{8,17}$", sg_id):
        return {
            "valid": False,
            "message": f"Invalid security group ID format: {sg_id}",
        }

    return {"valid": True}


def validate_tag_constraints(tags) -> Dict[str, Any]:
    """
    Validate tag key/value length constraints.

    AWS limits:
    - Tag keys: max 128 characters
    - Tag values: max 256 characters

    Args:
        tags: Dictionary of tag key-value pairs

    Returns:
        Dict with validation result
    """
    if tags is None:
        return {"valid": False, "message": "Tags cannot be None"}

    if not isinstance(tags, dict):
        return {"valid": False, "message": "Tags must be a dictionary"}

    if len(tags) == 0:
        return {"valid": True}  # Empty tags are valid

    for key, value in tags.items():
        if len(key) > 128:
            return {
                "valid": False,
                "message": f"Tag key exceeds maximum length of 128 characters: {key[:50]}...",
            }

        if len(str(value)) > 256:
            return {
                "valid": False,
                "message": f"Tag value for key '{key}' exceeds maximum length of 256 characters",
            }

    return {"valid": True}
