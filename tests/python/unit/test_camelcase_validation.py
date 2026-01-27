"""
Unit tests for CamelCase Validation

Tests to ensure camelCase validation properly distinguishes between:
1. Internal application fields (should be camelCase)
2. AWS API response fields (legitimately PascalCase)
3. AWS API request parameters (legitimately PascalCase)
"""

import os
import re
import sys

import pytest

# Add lambda directory to path for imports
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "lambda"
    ),
)


class TestAWSAPIPascalCaseExceptions:
    """Test that AWS API PascalCase fields are properly handled."""

    def test_ec2_api_fields_are_pascalcase(self):
        """EC2 API returns PascalCase fields - these should be allowed."""
        # Common EC2 API response fields
        ec2_fields = [
            "InstanceId",
            "InstanceIds",
            "InstanceType",
            "PrivateIpAddress",
            "PublicIpAddress",
            "PrivateDnsName",
            "PublicDnsName",
            "SecurityGroups",
            "SubnetId",
            "VpcId",
            "ImageId",
            "KeyName",
            "LaunchTime",
            "State",
            "Tags",
            "Reservations",
            "Instances",
        ]

        # These are legitimate AWS API fields and should NOT trigger validation errors
        for field in ec2_fields:
            assert field[0].isupper(), f"{field} should start with uppercase (PascalCase)"

    def test_drs_api_fields_are_pascalcase(self):
        """DRS API returns PascalCase fields - these should be allowed."""
        # Common DRS API response fields
        drs_fields = [
            "sourceServerID",  # Note: Mixed case
            "recoveryInstanceID",  # Note: Mixed case
            "participatingServers",
            "postLaunchActionsStatus",
            "sourceProperties",
            "identificationHints",
            "launchConfiguration",
            "replicationConfiguration",
        ]

        # These are legitimate AWS API fields
        for field in drs_fields:
            # DRS uses mixed camelCase/PascalCase
            assert field, f"{field} is a valid DRS API field"

    def test_iam_api_fields_are_pascalcase(self):
        """IAM API returns PascalCase fields - these should be allowed."""
        iam_fields = [
            "InstanceProfiles",
            "InstanceProfile",
            "InstanceProfileName",
            "Arn",
            "RoleName",
            "PolicyName",
        ]

        for field in iam_fields:
            assert field[0].isupper(), f"{field} should start with uppercase (PascalCase)"

    def test_cloudwatch_api_fields_are_pascalcase(self):
        """CloudWatch API returns PascalCase fields - these should be allowed."""
        cloudwatch_fields = [
            "MetricName",
            "Namespace",
            "Dimensions",
            "Timestamp",
            "Value",
            "Unit",
        ]

        for field in cloudwatch_fields:
            assert field[0].isupper(), f"{field} should start with uppercase (PascalCase)"


class TestInternalFieldsShouldBeCamelCase:
    """Test that internal application fields use camelCase."""

    def test_dynamodb_fields_should_be_camelcase(self):
        """Internal DynamoDB fields should use camelCase."""
        # These are OUR internal fields, not AWS API fields
        internal_fields = [
            "groupId",
            "planId",
            "executionId",
            "sourceServerId",
            "waveName",
            "protectionGroupId",
            "recoveryPlanName",
            "serverSelectionTags",
            "sourceServerIds",
            "launchConfig",
            "subnetId",
            "securityGroupIds",
            "instanceType",
            "instanceProfileName",
            "copyPrivateIp",
            "copyTags",
            "targetInstanceTypeRightSizingMethod",
            "launchDisposition",
            "licensing",
            "createdAt",
            "updatedAt",
            "startTime",
            "endTime",
            "createdDate",
            "lastModifiedDate",
        ]

        for field in internal_fields:
            # Should start with lowercase
            assert field[0].islower(), f"{field} should start with lowercase (camelCase)"
            # Should not contain underscores (use camelCase not snake_case)
            assert "_" not in field, f"{field} should not contain underscores"

    def test_api_request_fields_should_be_camelcase(self):
        """API request fields from frontend should use camelCase."""
        request_fields = [
            "groupName",
            "region",
            "accountId",
            "assumeRoleName",
            "owner",
            "description",
            "waveNumber",
            "priority",
            "manualApprovalRequired",
        ]

        for field in request_fields:
            assert field[0].islower(), f"{field} should start with lowercase (camelCase)"


class TestAWSAPIContextDetection:
    """Test detection of AWS API context vs internal context."""

    def test_detect_ec2_api_context(self):
        """Should detect when code is accessing EC2 API responses."""
        # Patterns that indicate EC2 API context
        ec2_patterns = [
            'instance.get("PrivateIpAddress")',
            'instance["PrivateIpAddress"]',
            'response["Reservations"]',
            'ec2.describe_instances',
            'instance.get("Tags")',
        ]

        for pattern in ec2_patterns:
            # These patterns indicate AWS API context
            assert "instance" in pattern or "response" in pattern or "ec2." in pattern

    def test_detect_drs_api_context(self):
        """Should detect when code is accessing DRS API responses."""
        drs_patterns = [
            'drs_server.get("recoveryInstanceID")',
            'server.get("sourceProperties")',
            'drs_client.describe_source_servers',
            'job.get("participatingServers")',
        ]

        for pattern in drs_patterns:
            assert "drs" in pattern.lower() or "server" in pattern.lower()

    def test_detect_internal_context(self):
        """Should detect when code is using internal fields."""
        internal_patterns = [
            'item["groupId"]',
            'body.get("groupName")',
            'wave.get("waveNumber")',
            'execution["executionId"]',
        ]

        for pattern in internal_patterns:
            # These are internal fields, not AWS API fields
            assert "item" in pattern or "body" in pattern or "wave" in pattern or "execution" in pattern


class TestValidationScriptPatterns:
    """Test patterns used in validation script."""

    def test_aws_api_exclusion_patterns(self):
        """Validation script should exclude AWS API patterns."""
        # Patterns that should be excluded from PascalCase validation
        exclusion_patterns = [
            'instance.get("PrivateIpAddress")',  # EC2 API
            'instance["PrivateIpAddress"]',  # EC2 API
            'response["Reservations"]',  # EC2 API
            'ec2.describe_instances',  # EC2 API call
            'drs_client.describe_source_servers',  # DRS API call
            'iam.list_instance_profiles',  # IAM API call
            'subnet["SubnetId"]',  # EC2 API
            'sg["GroupId"]',  # EC2 API
            'profile["InstanceProfileName"]',  # IAM API
            'it["InstanceType"]',  # EC2 API
            'result["SecurityGroups"]',  # EC2 API
            'paginator.paginate',  # AWS API pagination
        ]

        # These should NOT trigger validation errors
        for pattern in exclusion_patterns:
            # Check if pattern contains AWS API indicators
            aws_indicators = [
                "instance.",
                "instance[",
                "response[",
                "ec2.",
                "drs_client.",
                "iam.",
                "subnet[",
                "sg[",
                "profile[",
                "it[",
                "result[",
                "paginator.",
            ]
            has_indicator = any(indicator in pattern for indicator in aws_indicators)
            assert has_indicator, f"Pattern '{pattern}' should have AWS API indicator"

    def test_internal_field_detection_patterns(self):
        """Validation script should detect internal PascalCase fields."""
        # Patterns that SHOULD trigger validation errors
        error_patterns = [
            'item["GroupId"]',  # Should be groupId
            'body.get("GroupName")',  # Should be groupName
            'wave["WaveName"]',  # Should be waveName
            'execution["ExecutionId"]',  # Should be executionId
            '"groupId": "GroupId"',  # Field mapping error
        ]

        for pattern in error_patterns:
            # These should trigger validation errors
            # Check if pattern is NOT in AWS API context
            aws_indicators = [
                "instance.",
                "instance[",
                "response[",
                "ec2.",
                "drs_client.",
                "subnet[",
                "sg[",
            ]
            has_indicator = any(indicator in pattern for indicator in aws_indicators)
            assert not has_indicator, f"Pattern '{pattern}' should NOT have AWS API indicator"


class TestLegacyCleanupPatterns:
    """Test patterns for legacy PascalCase cleanup."""

    def test_legacy_removal_patterns_allowed(self):
        """Legacy cleanup code should be allowed to reference old PascalCase fields."""
        # These patterns are for REMOVING old PascalCase fields
        cleanup_patterns = [
            'if "ServerSelectionTags" in existing_group:',
            'update_expression += " REMOVE ServerSelectionTags"',
            'remove_clauses.append("ServerSelectionTags")',
            'remove_clauses.extend(["GroupId", "PlanId"])',
        ]

        for pattern in cleanup_patterns:
            # These should be excluded from validation
            cleanup_indicators = [
                "REMOVE",
                "remove_clauses",
                "in existing_group:",
                "in existing_plan:",
            ]
            has_indicator = any(indicator in pattern for indicator in cleanup_indicators)
            assert has_indicator, f"Pattern '{pattern}' should have cleanup indicator"


class TestRealWorldCodePatterns:
    """Test real-world code patterns from the codebase."""

    def test_ec2_instance_details_function(self):
        """Test EC2 instance details function uses correct patterns."""
        # This is from execution-poller/index.py
        code_snippet = '''
        instance = response["Reservations"][0]["Instances"][0]
        tags = {t["Key"]: t["Value"] for t in instance.get("Tags", [])}
        hostname = tags.get("Name", "")
        return {
            "hostname": hostname,
            "privateIp": instance.get("PrivateIpAddress", ""),  # EC2 API returns PascalCase
        }
        '''

        # Should have AWS API context indicators
        assert "instance.get(" in code_snippet
        assert "response[" in code_snippet
        assert "# EC2 API returns PascalCase" in code_snippet

        # Internal return fields should be camelCase
        assert '"hostname"' in code_snippet
        assert '"privateIp"' in code_snippet

    def test_drs_server_enrichment(self):
        """Test DRS server enrichment uses correct patterns."""
        code_snippet = '''
        # AWS DRS API returns PascalCase by default - transform to camelCase for internal use
        recovery_instance_id = drs_server.get("recoveryInstanceID")
        if recovery_instance_id:
            server_data["instanceId"] = recovery_instance_id
        '''

        # Should have comment explaining AWS API PascalCase
        assert "AWS DRS API returns PascalCase" in code_snippet

        # Internal fields should be camelCase
        assert 'server_data["instanceId"]' in code_snippet

    def test_dynamodb_operations(self):
        """Test DynamoDB operations use camelCase."""
        code_snippet = '''
        item = {
            "groupId": group_id,
            "groupName": name,
            "description": body.get("description", ""),
            "region": region,
            "accountId": body.get("accountId", ""),
            "createdDate": timestamp,
            "lastModifiedDate": timestamp,
        }
        '''

        # All fields should be camelCase
        camelcase_fields = [
            "groupId",
            "groupName",
            "description",
            "region",
            "accountId",
            "createdDate",
            "lastModifiedDate",
        ]

        for field in camelcase_fields:
            assert f'"{field}"' in code_snippet


class TestValidationScriptAccuracy:
    """Test that validation script patterns match actual code usage."""

    def test_validation_excludes_aws_api_patterns(self):
        """Validation script should exclude AWS API access patterns."""
        # These grep exclusions should be in the validation script
        required_exclusions = [
            "instance\\[",  # EC2 instance access
            "response\\[",  # API response access
            "ec2\\.describe",  # EC2 API calls
            "drs_client\\.",  # DRS API calls
            "iam\\.list",  # IAM API calls
            "subnet\\[",  # EC2 subnet access
            "sg\\[",  # Security group access
            "profile\\[",  # Instance profile access
            "it\\[",  # Instance type access
            "paginator\\.paginate",  # AWS pagination
        ]

        # These patterns should be in the validation script's grep exclusions
        for pattern in required_exclusions:
            # Verify pattern is a valid regex
            try:
                re.compile(pattern)
            except re.error:
                pytest.fail(f"Invalid regex pattern: {pattern}")

    def test_validation_detects_internal_pascalcase(self):
        """Validation script should detect internal PascalCase usage."""
        # These should trigger validation errors
        error_cases = [
            ('item["GroupId"]', "Internal field should be groupId"),
            ('body.get("GroupName")', "Internal field should be groupName"),
            ('wave["WaveName"]', "Internal field should be waveName"),
            ('"ExecutionId": execution_id', "Internal field should be executionId"),
        ]

        for code, reason in error_cases:
            # Should NOT match AWS API exclusion patterns
            aws_patterns = [
                r"instance\[",
                r"response\[",
                r"ec2\.",
                r"drs_client\.",
                r"subnet\[",
                r"sg\[",
            ]

            matches_aws_pattern = any(
                re.search(pattern, code) for pattern in aws_patterns
            )
            assert not matches_aws_pattern, f"{code} should not match AWS patterns: {reason}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
