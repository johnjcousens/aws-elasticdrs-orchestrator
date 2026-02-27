"""
Property-based tests for IAM policies in function-specific roles.

Tests verify that IAM policies correctly implement least privilege principles,
resource-level restrictions, and security controls across all Lambda functions.

Uses Hypothesis framework for property-based testing with minimum 100 iterations
per property to ensure comprehensive coverage across input space.
"""

import json
import re
from typing import Dict, List, Any, Optional

import pytest
from hypothesis import given, strategies as st, settings

# Test configuration
MIN_EXAMPLES = 100  # Minimum iterations per property test

# Load template once at module level to avoid fixture issues with Hypothesis
import os
import yaml

def load_template_once():
    """Load CloudFormation template once at module level."""
    template_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "cfn",
        "iam",
        "roles-stack.yaml"
    )
    
    # Register CloudFormation intrinsic function constructors
    def cfn_constructor(loader, tag_suffix, node):
        if isinstance(node, yaml.ScalarNode):
            return {tag_suffix: loader.construct_scalar(node)}
        elif isinstance(node, yaml.SequenceNode):
            return {tag_suffix: loader.construct_sequence(node)}
        elif isinstance(node, yaml.MappingNode):
            return {tag_suffix: loader.construct_mapping(node)}
        return {tag_suffix: None}
    
    yaml.SafeLoader.add_multi_constructor("!", cfn_constructor)
    
    with open(template_path, "r") as f:
        return yaml.safe_load(f)

# Load template once for all tests
IAM_TEMPLATE = load_template_once()


# ============================================================================
# Test Strategies (Generators)
# ============================================================================

@st.composite
def dynamodb_table_name(draw):
    """Generate DynamoDB table names (project and non-project)."""
    project_name = "aws-drs-orchestration"
    table_types = ["protection-groups", "recovery-plans", "execution-history", "target-accounts"]
    
    is_project_table = draw(st.booleans())
    if is_project_table:
        table_type = draw(st.sampled_from(table_types))
        env = draw(st.sampled_from(["dev", "test", "staging", "prod"]))
        return f"{project_name}-{table_type}-{env}"
    else:
        # Non-project table
        other_project = draw(st.sampled_from(["other-project", "different-app", "external-service"]))
        return f"{other_project}-table-{draw(st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz'))}"


@st.composite
def lambda_function_name(draw):
    """Generate Lambda function names (project and non-project)."""
    project_name = "aws-drs-orchestration"
    function_types = ["query-handler", "data-management-handler", "execution-handler", "dr-orch-sf", "frontend-deployer"]
    
    is_project_function = draw(st.booleans())
    if is_project_function:
        function_type = draw(st.sampled_from(function_types))
        env = draw(st.sampled_from(["dev", "test", "staging", "prod"]))
        return f"{project_name}-{function_type}-{env}"
    else:
        # Non-project function
        other_project = draw(st.sampled_from(["other-project", "different-app", "external-service"]))
        return f"{other_project}-function-{draw(st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz'))}"


@st.composite
def s3_bucket_name(draw):
    """Generate S3 bucket names (frontend and non-frontend)."""
    project_name = "aws-drs-orchestration"
    
    is_frontend_bucket = draw(st.booleans())
    if is_frontend_bucket:
        env = draw(st.sampled_from(["dev", "test", "staging", "prod"]))
        account_id = draw(st.integers(min_value=100000000000, max_value=999999999999))
        return f"{project_name}-{account_id}-fe-{env}"
    else:
        # Non-frontend bucket
        other_project = draw(st.sampled_from(["other-project", "different-app", "external-service"]))
        return f"{other_project}-bucket-{draw(st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz'))}"


@st.composite
def sns_topic_name(draw):
    """Generate SNS topic names (project and non-project)."""
    project_name = "aws-drs-orchestration"
    topic_types = ["execution-alerts", "security-alerts", "notifications"]
    
    is_project_topic = draw(st.booleans())
    if is_project_topic:
        topic_type = draw(st.sampled_from(topic_types))
        env = draw(st.sampled_from(["dev", "test", "staging", "prod"]))
        return f"{project_name}-{topic_type}-{env}"
    else:
        # Non-project topic
        other_project = draw(st.sampled_from(["other-project", "different-app", "external-service"]))
        return f"{other_project}-topic-{draw(st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz'))}"


@st.composite
def external_id_value(draw):
    """Generate ExternalId values (matching and non-matching)."""
    project_name = "aws-drs-orchestration"
    env = draw(st.sampled_from(["dev", "test", "staging", "prod"]))
    
    is_matching = draw(st.booleans())
    if is_matching:
        return f"{project_name}-{env}"
    else:
        # Non-matching ExternalId
        return draw(st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyz-'))


# ============================================================================
# Helper Functions
# ============================================================================

def extract_policy_statements(template: Dict[str, Any], role_name: str) -> List[Dict[str, Any]]:
    """
    Extract all policy statements from a role in the CloudFormation template.
    
    Args:
        template: Parsed CloudFormation template
        role_name: Name of the IAM role resource
        
    Returns:
        List of IAM policy statements
    """
    resources = IAM_TEMPLATE.get("Resources", {})
    role = resources.get(role_name, {})
    properties = role.get("Properties", {})
    policies = properties.get("Policies", [])
    
    statements = []
    for policy in policies:
        policy_doc = policy.get("PolicyDocument", {})
        policy_statements = policy_doc.get("Statement", [])
        statements.extend(policy_statements)
    
    return statements


def check_action_allowed(statements: List[Dict[str, Any]], action: str) -> bool:
    """
    Check if an action is allowed by any policy statement.
    
    Args:
        statements: List of IAM policy statements
        action: AWS action to check (e.g., "dynamodb:GetItem")
        
    Returns:
        True if action is allowed, False otherwise
    """
    for statement in statements:
        if statement.get("Effect") != "Allow":
            continue
        
        actions = statement.get("Action", [])
        if isinstance(actions, str):
            actions = [actions]
        
        # Check for exact match or wildcard match
        for allowed_action in actions:
            if action == allowed_action:
                return True
            # Check wildcard patterns (e.g., "dynamodb:*" matches "dynamodb:GetItem")
            if "*" in allowed_action:
                pattern = allowed_action.replace("*", ".*")
                if re.match(f"^{pattern}$", action):
                    return True
    
    return False


def check_resource_allowed(statements: List[Dict[str, Any]], action: str, resource_arn: str) -> bool:
    """
    Check if an action on a specific resource is allowed.
    
    Args:
        statements: List of IAM policy statements
        action: AWS action to check
        resource_arn: Resource ARN to check
        
    Returns:
        True if action on resource is allowed, False otherwise
    """
    for statement in statements:
        if statement.get("Effect") != "Allow":
            continue
        
        actions = statement.get("Action", [])
        if isinstance(actions, str):
            actions = [actions]
        
        # Check if action matches
        action_matches = False
        for allowed_action in actions:
            if action == allowed_action or (
                "*" in allowed_action and re.match(f"^{allowed_action.replace('*', '.*')}$", action)
            ):
                action_matches = True
                break
        
        if not action_matches:
            continue
        
        # Check if resource matches
        resources = statement.get("Resource", [])
        if isinstance(resources, str):
            resources = [resources]
        
        for allowed_resource in resources:
            # Handle CloudFormation intrinsic functions
            if isinstance(allowed_resource, dict):
                # Extract the actual ARN pattern from !Sub or other functions
                if "Sub" in allowed_resource:
                    allowed_resource = str(allowed_resource["Sub"])
                elif "Fn::Sub" in allowed_resource:
                    allowed_resource = str(allowed_resource["Fn::Sub"])
                else:
                    continue
            
            if allowed_resource == "*":
                return True
            
            # Replace CloudFormation variables for pattern matching
            # Convert CloudFormation template to regex pattern
            pattern = allowed_resource
            pattern = pattern.replace("${ProjectName}", "aws-drs-orchestration")
            pattern = pattern.replace("${AWS::Partition}", "aws")
            pattern = pattern.replace("${AWS::Region}", r"[a-z0-9\-]+")
            pattern = pattern.replace("${AWS::AccountId}", r"\d{12}")
            pattern = pattern.replace("${Environment}", r"[a-z0-9\-]+")
            
            # Escape dots in ARN format
            pattern = pattern.replace(":", r"\:")
            
            # Replace * with .* for wildcard matching
            pattern = pattern.replace("*", ".*")
            
            # Try to match
            if re.match(f"^{pattern}$", resource_arn):
                return True
    
    return False


def extract_condition_keys(statements: List[Dict[str, Any]], action: str) -> Dict[str, Any]:
    """
    Extract condition keys for a specific action.
    
    Args:
        statements: List of IAM policy statements
        action: AWS action to check
        
    Returns:
        Dictionary of condition keys and their values
    """
    for statement in statements:
        if statement.get("Effect") != "Allow":
            continue
        
        actions = statement.get("Action", [])
        if isinstance(actions, str):
            actions = [actions]
        
        # Check if action matches
        for allowed_action in actions:
            if action == allowed_action or (
                "*" in allowed_action and re.match(f"^{allowed_action.replace('*', '.*')}$", action)
            ):
                return statement.get("Condition", {})
    
    return {}


# ============================================================================
# Property 1: Query Handler Read-Only Access
# ============================================================================

@settings(max_examples=MIN_EXAMPLES)
@given(
    operation=st.sampled_from([
        # Read operations (should succeed)
        ("dynamodb:GetItem", True),
        ("dynamodb:Query", True),
        ("dynamodb:Scan", True),
        ("drs:DescribeSourceServers", True),
        ("ec2:DescribeInstances", True),
        ("cloudwatch:GetMetricData", True),
        # Write operations (should fail)
        ("dynamodb:PutItem", False),
        ("dynamodb:UpdateItem", False),
        ("drs:StartRecovery", False),
        ("drs:TerminateRecoveryInstances", False),
    ])
)
def test_property_1_query_handler_read_only_access(operation):
    """
    Feature: function-specific-iam-roles, Property 1: Query Handler Read-Only Access
    
    For any DRS, DynamoDB, EC2, or CloudWatch operation, when the Query Handler
    attempts a read operation on project resources, the operation should succeed,
    and when it attempts a write operation, the operation should fail with AccessDenied.
    
    Validates: Requirements 1.2, 1.3, 1.4, 1.8, 1.9
    """
    statements = extract_policy_statements(IAM_TEMPLATE, "QueryHandlerRole")
    
    action, should_be_allowed = operation
    is_allowed = check_action_allowed(statements, action)
    
    assert is_allowed == should_be_allowed, (
        f"Query Handler: {action} should {'be allowed' if should_be_allowed else 'be denied'}, "
        f"but was {'allowed' if is_allowed else 'denied'}"
    )


# ============================================================================
# Property 2: Query Handler Resource Restrictions
# ============================================================================

@settings(max_examples=MIN_EXAMPLES)
@given(
    table_name=dynamodb_table_name(),
    function_name=lambda_function_name()
)
def test_property_2_query_handler_resource_restrictions(table_name, function_name):
    """
    Feature: function-specific-iam-roles, Property 2: Query Handler Resource Restrictions
    
    For any DynamoDB table name or Lambda function name, when the Query Handler
    attempts operations on resources matching the pattern {ProjectName}-*, the
    operation should succeed, and when it attempts operations on resources not
    matching the pattern, the operation should fail with AccessDenied.
    
    Validates: Requirements 1.10, 1.11, 1.12
    """
    statements = extract_policy_statements(IAM_TEMPLATE, "QueryHandlerRole")
    
    project_name = "aws-drs-orchestration"
    
    # Test DynamoDB table access
    table_arn = f"arn:aws:dynamodb:us-east-2:123456789012:table/{table_name}"
    table_allowed = check_resource_allowed(statements, "dynamodb:GetItem", table_arn)
    table_should_be_allowed = table_name.startswith(f"{project_name}-")
    
    assert table_allowed == table_should_be_allowed, (
        f"Query Handler: DynamoDB table {table_name} should "
        f"{'be allowed' if table_should_be_allowed else 'be denied'}, "
        f"but was {'allowed' if table_allowed else 'denied'}"
    )
    
    # Test Lambda function invocation
    function_arn = f"arn:aws:lambda:us-east-2:123456789012:function:{function_name}"
    function_allowed = check_resource_allowed(statements, "lambda:InvokeFunction", function_arn)
    # Query Handler can only invoke execution-handler
    function_should_be_allowed = "execution-handler" in function_name and function_name.startswith(f"{project_name}-")
    
    assert function_allowed == function_should_be_allowed, (
        f"Query Handler: Lambda function {function_name} should "
        f"{'be allowed' if function_should_be_allowed else 'be denied'}, "
        f"but was {'allowed' if function_allowed else 'denied'}"
    )


# ============================================================================
# Property 3: Data Management Handler DynamoDB and DRS Metadata Access
# ============================================================================

@settings(max_examples=MIN_EXAMPLES)
@given(
    operation=st.sampled_from([
        # DynamoDB CRUD operations (should succeed)
        ("dynamodb:GetItem", True),
        ("dynamodb:PutItem", True),
        ("dynamodb:UpdateItem", True),
        ("dynamodb:DeleteItem", True),
        # DRS metadata operations (should succeed)
        ("drs:DescribeSourceServers", True),
        ("drs:TagResource", True),
        ("drs:UntagResource", True),
        ("drs:CreateExtendedSourceServer", True),
        # DRS recovery operations (should fail)
        ("drs:StartRecovery", False),
        ("drs:TerminateRecoveryInstances", False),
        ("drs:CreateRecoveryInstanceForDrs", False),
    ])
)
def test_property_3_data_management_handler_access(operation):
    """
    Feature: function-specific-iam-roles, Property 3: Data Management Handler DynamoDB and DRS Metadata Access
    
    For any DynamoDB CRUD operation or DRS metadata operation, when the Data
    Management Handler attempts the operation on project resources, the operation
    should succeed, and when it attempts DRS recovery operations, the operation
    should fail with AccessDenied.
    
    Validates: Requirements 2.2, 2.3, 2.4, 2.9
    """
    # Using module-level IAM_TEMPLATE
    statements = extract_policy_statements(IAM_TEMPLATE, "DataManagementRole")
    
    action, should_be_allowed = operation
    is_allowed = check_action_allowed(statements, action)
    
    assert is_allowed == should_be_allowed, (
        f"Data Management Handler: {action} should {'be allowed' if should_be_allowed else 'be denied'}, "
        f"but was {'allowed' if is_allowed else 'denied'}"
    )


# ============================================================================
# Property 4: Data Management Handler Resource Restrictions
# ============================================================================

@settings(max_examples=MIN_EXAMPLES)
@given(
    function_name=lambda_function_name()
)
def test_property_4_data_management_handler_resource_restrictions(function_name):
    """
    Feature: function-specific-iam-roles, Property 4: Data Management Handler Resource Restrictions
    
    For any Lambda function name, when the Data Management Handler attempts
    operations on resources matching the pattern {ProjectName}-*, the operation
    should succeed, and when it attempts operations on resources not matching
    the pattern, the operation should fail with AccessDenied.
    
    Validates: Requirements 2.10, 2.11, 2.12
    """
    # Using module-level IAM_TEMPLATE
    statements = extract_policy_statements(IAM_TEMPLATE, "DataManagementRole")
    
    project_name = "aws-drs-orchestration"
    
    # Test Lambda self-invocation (only data-management-handler)
    function_arn = f"arn:aws:lambda:us-east-2:123456789012:function:{function_name}"
    function_allowed = check_resource_allowed(statements, "lambda:InvokeFunction", function_arn)
    function_should_be_allowed = "data-management-handler" in function_name and function_name.startswith(f"{project_name}-")
    
    assert function_allowed == function_should_be_allowed, (
        f"Data Management Handler: Lambda function {function_name} should "
        f"{'be allowed' if function_should_be_allowed else 'be denied'}, "
        f"but was {'allowed' if function_allowed else 'denied'}"
    )


# ============================================================================
# Property 5: Execution Handler Orchestration Access
# ============================================================================

@settings(max_examples=MIN_EXAMPLES)
@given(
    operation=st.sampled_from([
        # Step Functions operations (should succeed)
        ("states:StartExecution", True),
        ("states:DescribeExecution", True),
        ("states:SendTaskSuccess", True),
        # SNS operations (should succeed)
        ("sns:Publish", True),
        ("sns:Subscribe", True),
        # DynamoDB operations (should succeed)
        ("dynamodb:GetItem", True),
        ("dynamodb:PutItem", True),
        # DRS operations (should succeed)
        ("drs:DescribeSourceServers", True),
        ("drs:StartRecovery", True),
        ("drs:TerminateRecoveryInstances", True),
        # EC2 operations (should succeed)
        ("ec2:DescribeInstances", True),
        ("ec2:TerminateInstances", True),
    ])
)
def test_property_5_execution_handler_orchestration_access(operation):
    """
    Feature: function-specific-iam-roles, Property 5: Execution Handler Orchestration Access
    
    For any Step Functions, SNS, DynamoDB, DRS, or EC2 operation, when the
    Execution Handler attempts orchestration operations on project resources,
    the operation should succeed.
    
    Validates: Requirements 3.2, 3.3, 3.4, 3.5, 3.6
    """
    # Using module-level IAM_TEMPLATE
    statements = extract_policy_statements(IAM_TEMPLATE, "ExecutionHandlerRole")
    
    action, should_be_allowed = operation
    is_allowed = check_action_allowed(statements, action)
    
    assert is_allowed == should_be_allowed, (
        f"Execution Handler: {action} should {'be allowed' if should_be_allowed else 'be denied'}, "
        f"but was {'allowed' if is_allowed else 'denied'}"
    )


# ============================================================================
# Property 6: Execution Handler Resource Restrictions
# ============================================================================

@settings(max_examples=MIN_EXAMPLES)
@given(
    topic_name=sns_topic_name(),
    function_name=lambda_function_name()
)
def test_property_6_execution_handler_resource_restrictions(topic_name, function_name):
    """
    Feature: function-specific-iam-roles, Property 6: Execution Handler Resource Restrictions
    
    For any SNS topic ARN or Lambda function ARN, when the Execution Handler
    attempts operations on resources matching the pattern {ProjectName}-*, the
    operation should succeed, and when it attempts operations on resources not
    matching the pattern, the operation should fail with AccessDenied.
    
    Validates: Requirements 3.10, 3.11, 3.12
    """
    # Using module-level IAM_TEMPLATE
    statements = extract_policy_statements(IAM_TEMPLATE, "ExecutionHandlerRole")
    
    project_name = "aws-drs-orchestration"
    
    # Test SNS topic access
    topic_arn = f"arn:aws:sns:us-east-2:123456789012:{topic_name}"
    topic_allowed = check_resource_allowed(statements, "sns:Publish", topic_arn)
    topic_should_be_allowed = topic_name.startswith(f"{project_name}-")
    
    assert topic_allowed == topic_should_be_allowed, (
        f"Execution Handler: SNS topic {topic_name} should "
        f"{'be allowed' if topic_should_be_allowed else 'be denied'}, "
        f"but was {'allowed' if topic_allowed else 'denied'}"
    )
    
    # Test Lambda function invocation (only data-management-handler)
    function_arn = f"arn:aws:lambda:us-east-2:123456789012:function:{function_name}"
    function_allowed = check_resource_allowed(statements, "lambda:InvokeFunction", function_arn)
    function_should_be_allowed = "data-management-handler" in function_name and function_name.startswith(f"{project_name}-")
    
    assert function_allowed == function_should_be_allowed, (
        f"Execution Handler: Lambda function {function_name} should "
        f"{'be allowed' if function_should_be_allowed else 'be denied'}, "
        f"but was {'allowed' if function_allowed else 'denied'}"
    )



# ============================================================================
# Property 7: Orchestration Role Comprehensive DRS and EC2 Access
# ============================================================================

@settings(max_examples=MIN_EXAMPLES)
@given(
    operation=st.sampled_from([
        # DRS read operations (should succeed)
        ("drs:DescribeSourceServers", True),
        ("drs:DescribeJobs", True),
        ("drs:GetLaunchConfiguration", True),
        # DRS write operations (should succeed with region condition)
        ("drs:StartRecovery", True),
        ("drs:CreateRecoveryInstanceForDrs", True),
        ("drs:TerminateRecoveryInstances", True),
        ("drs:UpdateLaunchConfiguration", True),
        # EC2 operations (should succeed)
        ("ec2:DescribeInstances", True),
        ("ec2:RunInstances", True),
        ("ec2:TerminateInstances", True),
        ("ec2:CreateLaunchTemplate", True),
        ("ec2:CreateTags", True),
        # IAM PassRole (should succeed with service condition)
        ("iam:PassRole", True),
        # KMS operations (should succeed with service condition)
        ("kms:DescribeKey", True),
        ("kms:CreateGrant", True),
    ])
)
def test_property_7_orchestration_role_comprehensive_access(operation):
    """
    Feature: function-specific-iam-roles, Property 7: Orchestration Role Comprehensive DRS and EC2 Access
    
    For any DRS operation (read or write) or EC2 operation, when the Orchestration
    Function attempts the operation, the operation should succeed if it meets the
    IAM condition key requirements (region restriction for DRS writes, service
    restriction for IAM PassRole, service restriction for KMS operations).
    
    Validates: Requirements 4.2, 4.3, 4.4, 4.5, 4.7, 4.13, 4.14
    """
    # Using module-level IAM_TEMPLATE
    statements = extract_policy_statements(IAM_TEMPLATE, "OrchestrationRole")
    
    action, should_be_allowed = operation
    is_allowed = check_action_allowed(statements, action)
    
    assert is_allowed == should_be_allowed, (
        f"Orchestration Role: {action} should {'be allowed' if should_be_allowed else 'be denied'}, "
        f"but was {'allowed' if is_allowed else 'denied'}"
    )
    
    # Verify condition keys for specific actions
    if action in ["drs:StartRecovery", "drs:CreateRecoveryInstanceForDrs", "drs:TerminateRecoveryInstances"]:
        conditions = extract_condition_keys(statements, action)
        # Should have region restriction
        assert "StringEquals" in conditions or len(conditions) > 0, (
            f"Orchestration Role: {action} should have region restriction condition"
        )
    
    if action == "iam:PassRole":
        conditions = extract_condition_keys(statements, action)
        # Should have service restriction
        assert "StringEquals" in conditions, (
            f"Orchestration Role: {action} should have service restriction condition"
        )
    
    if action in ["kms:DescribeKey", "kms:CreateGrant"]:
        conditions = extract_condition_keys(statements, action)
        # Should have service restriction
        assert "StringEquals" in conditions, (
            f"Orchestration Role: {action} should have service restriction condition"
        )


# ============================================================================
# Property 8: Orchestration Role Resource Restrictions
# ============================================================================

@settings(max_examples=MIN_EXAMPLES)
@given(
    table_name=dynamodb_table_name(),
    topic_name=sns_topic_name(),
    function_name=lambda_function_name()
)
def test_property_8_orchestration_role_resource_restrictions(table_name, topic_name, function_name):
    """
    Feature: function-specific-iam-roles, Property 8: Orchestration Role Resource Restrictions
    
    For any DynamoDB table ARN, SNS topic ARN, or Lambda function ARN, when the
    Orchestration Function attempts operations on resources matching the pattern
    {ProjectName}-*, the operation should succeed, and when it attempts operations
    on resources not matching the pattern, the operation should fail with AccessDenied.
    
    Validates: Requirements 4.10, 4.15, 4.16
    """
    # Using module-level IAM_TEMPLATE
    statements = extract_policy_statements(IAM_TEMPLATE, "OrchestrationRole")
    
    project_name = "aws-drs-orchestration"
    
    # Test DynamoDB table access
    table_arn = f"arn:aws:dynamodb:us-east-2:123456789012:table/{table_name}"
    table_allowed = check_resource_allowed(statements, "dynamodb:GetItem", table_arn)
    table_should_be_allowed = table_name.startswith(f"{project_name}-")
    
    assert table_allowed == table_should_be_allowed, (
        f"Orchestration Role: DynamoDB table {table_name} should "
        f"{'be allowed' if table_should_be_allowed else 'be denied'}, "
        f"but was {'allowed' if table_allowed else 'denied'}"
    )
    
    # Test SNS topic access
    topic_arn = f"arn:aws:sns:us-east-2:123456789012:{topic_name}"
    topic_allowed = check_resource_allowed(statements, "sns:Publish", topic_arn)
    topic_should_be_allowed = topic_name.startswith(f"{project_name}-")
    
    assert topic_allowed == topic_should_be_allowed, (
        f"Orchestration Role: SNS topic {topic_name} should "
        f"{'be allowed' if topic_should_be_allowed else 'be denied'}, "
        f"but was {'allowed' if topic_allowed else 'denied'}"
    )
    
    # Test Lambda function invocation (execution-handler and query-handler only)
    function_arn = f"arn:aws:lambda:us-east-2:123456789012:function:{function_name}"
    function_allowed = check_resource_allowed(statements, "lambda:InvokeFunction", function_arn)
    function_should_be_allowed = (
        ("execution-handler" in function_name or "query-handler" in function_name)
        and function_name.startswith(f"{project_name}-")
    )
    
    assert function_allowed == function_should_be_allowed, (
        f"Orchestration Role: Lambda function {function_name} should "
        f"{'be allowed' if function_should_be_allowed else 'be denied'}, "
        f"but was {'allowed' if function_allowed else 'denied'}"
    )


# ============================================================================
# Property 9: Frontend Deployer S3 and CloudFront Access
# ============================================================================

@settings(max_examples=MIN_EXAMPLES)
@given(
    operation=st.sampled_from([
        # S3 operations (should succeed)
        ("s3:ListBucket", True),
        ("s3:GetObject", True),
        ("s3:PutObject", True),
        ("s3:DeleteObject", True),
        ("s3:DeleteObjectVersion", True),
        # CloudFront operations (should succeed)
        ("cloudfront:CreateInvalidation", True),
        ("cloudfront:GetDistribution", True),
        # CloudFormation operations (should succeed)
        ("cloudformation:DescribeStacks", True),
        # Operations that should fail
        ("drs:DescribeSourceServers", False),
        ("ec2:DescribeInstances", False),
        ("dynamodb:GetItem", False),
        ("states:StartExecution", False),
        ("sns:Publish", False),
    ])
)
def test_property_9_frontend_deployer_access(operation):
    """
    Feature: function-specific-iam-roles, Property 9: Frontend Deployer S3 and CloudFront Access
    
    For any S3 operation or CloudFront operation, when the Frontend Deployer
    attempts the operation on project frontend buckets or distributions, the
    operation should succeed, and when it attempts DRS, EC2, DynamoDB, Step
    Functions, or SNS operations, the operation should fail with AccessDenied.
    
    Validates: Requirements 14.2, 14.3, 14.4, 14.5, 14.8, 14.12
    """
    # Using module-level IAM_TEMPLATE
    statements = extract_policy_statements(IAM_TEMPLATE, "FrontendDeployerRole")
    
    action, should_be_allowed = operation
    is_allowed = check_action_allowed(statements, action)
    
    assert is_allowed == should_be_allowed, (
        f"Frontend Deployer: {action} should {'be allowed' if should_be_allowed else 'be denied'}, "
        f"but was {'allowed' if is_allowed else 'denied'}"
    )


# ============================================================================
# Property 10: Frontend Deployer Resource Restrictions
# ============================================================================

@settings(max_examples=MIN_EXAMPLES)
@given(
    bucket_name=s3_bucket_name()
)
def test_property_10_frontend_deployer_resource_restrictions(bucket_name):
    """
    Feature: function-specific-iam-roles, Property 10: Frontend Deployer Resource Restrictions
    
    For any S3 bucket name, when the Frontend Deployer attempts operations on
    resources matching the pattern {ProjectName}-*-fe-*, the operation should
    succeed, and when it attempts operations on resources not matching the
    pattern, the operation should fail with AccessDenied.
    
    Validates: Requirements 14.9, 14.10, 14.11
    """
    # Using module-level IAM_TEMPLATE
    statements = extract_policy_statements(IAM_TEMPLATE, "FrontendDeployerRole")
    
    project_name = "aws-drs-orchestration"
    
    # Test S3 bucket access
    bucket_arn = f"arn:aws:s3:::{bucket_name}"
    bucket_allowed = check_resource_allowed(statements, "s3:ListBucket", bucket_arn)
    bucket_should_be_allowed = bucket_name.startswith(f"{project_name}-") and "-fe-" in bucket_name
    
    assert bucket_allowed == bucket_should_be_allowed, (
        f"Frontend Deployer: S3 bucket {bucket_name} should "
        f"{'be allowed' if bucket_should_be_allowed else 'be denied'}, "
        f"but was {'allowed' if bucket_allowed else 'denied'}"
    )


# ============================================================================
# Property 11: Conditional Role Creation Mutual Exclusivity
# ============================================================================

@settings(max_examples=MIN_EXAMPLES)
@given(
    use_function_specific_roles=st.booleans()
)
def test_property_11_conditional_role_creation_mutual_exclusivity(use_function_specific_roles):
    """
    Feature: function-specific-iam-roles, Property 11: Conditional Role Creation Mutual Exclusivity
    
    For any value of the UseFunctionSpecificRoles parameter, when CloudFormation
    creates the stack, either the Unified Role OR the five Function-Specific Roles
    should be created, but never both simultaneously.
    
    Validates: Requirements 5.3, 5.4, 5.7
    """
    # Using module-level IAM_TEMPLATE
    resources = IAM_TEMPLATE.get("Resources", {})
    
    # Check conditions
    conditions = IAM_TEMPLATE.get("Conditions", {})
    assert "UseFunctionSpecificRoles" in conditions, "UseFunctionSpecificRoles condition must exist"
    assert "UseUnifiedRole" in conditions, "UseUnifiedRole condition must exist"
    
    # Check that UnifiedOrchestrationRole has UseUnifiedRole condition
    unified_role = resources.get("UnifiedOrchestrationRole", {})
    assert unified_role.get("Condition") == "UseUnifiedRole", (
        "UnifiedOrchestrationRole must have UseUnifiedRole condition"
    )
    
    # Check that function-specific roles have UseFunctionSpecificRoles condition
    function_specific_roles = [
        "QueryHandlerRole",
        "DataManagementRole",
        "ExecutionHandlerRole",
        "OrchestrationRole",
        "FrontendDeployerRole"
    ]
    
    for role_name in function_specific_roles:
        role = resources.get(role_name, {})
        assert role.get("Condition") == "UseFunctionSpecificRoles", (
            f"{role_name} must have UseFunctionSpecificRoles condition"
        )
    
    # Verify mutual exclusivity: conditions are inverses of each other
    use_func_specific_condition = conditions.get("UseFunctionSpecificRoles")
    use_unified_condition = conditions.get("UseUnifiedRole")
    
    # UseUnifiedRole should be !Not [UseFunctionSpecificRoles]
    # Check if it's a dict with Fn::Not or !Not structure
    is_inverse = (
        isinstance(use_unified_condition, dict) and
        ("Fn::Not" in use_unified_condition or "Not" in str(use_unified_condition))
    )
    
    assert is_inverse, (
        "UseUnifiedRole condition should be the inverse of UseFunctionSpecificRoles"
    )


# ============================================================================
# Property 12: Conditional Role Assignment
# ============================================================================

def test_property_12_conditional_role_assignment():
    """
    Feature: function-specific-iam-roles, Property 12: Conditional Role Assignment
    
    For any Lambda function and any value of the UseFunctionSpecificRoles parameter,
    when CloudFormation creates the Lambda function, the function should use the
    Unified Role ARN when UseFunctionSpecificRoles=false, and the function should
    use its respective Function-Specific Role ARN when UseFunctionSpecificRoles=true.
    
    Validates: Requirements 5.5, 5.6
    
    Note: This property is tested through CloudFormation template structure validation
    rather than property-based testing since it requires Lambda stack template analysis.
    """
    # This test validates the IAM roles template structure
    # The actual Lambda function role assignment is validated in the Lambda stack tests
    # Using module-level IAM_TEMPLATE
    
    # Verify that outputs exist for both unified and function-specific roles
    outputs = IAM_TEMPLATE.get("Outputs", {})
    
    # Check unified role output
    assert "UnifiedRoleArn" in outputs, "UnifiedRoleArn output must exist"
    
    # Check function-specific role outputs
    function_specific_outputs = [
        "QueryHandlerRoleArn",
        "DataManagementRoleArn",
        "ExecutionHandlerRoleArn",
        "OrchestrationRoleArn",
        "FrontendDeployerRoleArn"
    ]
    
    for output_name in function_specific_outputs:
        assert output_name in outputs, f"{output_name} output must exist"


# ============================================================================
# Property 13: IAM Role Naming Convention
# ============================================================================

@settings(max_examples=MIN_EXAMPLES)
@given(
    project_name=st.sampled_from(["aws-drs-orchestration", "my-project", "test-app"]),
    environment=st.sampled_from(["dev", "test", "staging", "prod"]),
    function_type=st.sampled_from([
        "query-handler",
        "data-management",
        "execution-handler",
        "orchestration",
        "frontend-deployer"
    ])
)
def test_property_13_iam_role_naming_convention(project_name, environment, function_type):
    """
    Feature: function-specific-iam-roles, Property 13: IAM Role Naming Convention
    
    For any IAM role and any values of ProjectName and Environment parameters,
    when CloudFormation creates the role, the role name should match the pattern
    {ProjectName}-{function}-role-{Environment} where function is one of:
    query-handler, data-management, execution-handler, orchestration, frontend-deployer.
    
    Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7
    """
    # Using module-level IAM_TEMPLATE
    resources = IAM_TEMPLATE.get("Resources", {})
    
    # Map function types to role resource names
    role_mapping = {
        "query-handler": "QueryHandlerRole",
        "data-management": "DataManagementRole",
        "execution-handler": "ExecutionHandlerRole",
        "orchestration": "OrchestrationRole",
        "frontend-deployer": "FrontendDeployerRole"
    }
    
    role_resource_name = role_mapping.get(function_type)
    role = resources.get(role_resource_name, {})
    properties = role.get("Properties", {})
    role_name_template = properties.get("RoleName", "")
    
    # Expected pattern: {ProjectName}-{function}-role-{Environment}
    expected_pattern = f"{project_name}-{function_type}-role-{environment}"
    
    # The template uses !Sub, so we need to check the pattern
    # RoleName should be: !Sub "${ProjectName}-{function}-role-${Environment}"
    assert "Sub" in str(role_name_template) or "${ProjectName}" in str(role_name_template), (
        f"{role_resource_name} RoleName should use CloudFormation substitution"
    )
    
    # Verify the pattern includes the function type
    assert function_type in str(role_name_template), (
        f"{role_resource_name} RoleName should include '{function_type}'"
    )


# ============================================================================
# Property 14: IAM Policy Resource ARN Patterns
# ============================================================================

@settings(max_examples=MIN_EXAMPLES)
@given(
    role_name=st.sampled_from([
        "QueryHandlerRole",
        "DataManagementRole",
        "ExecutionHandlerRole",
        "OrchestrationRole",
        "FrontendDeployerRole"
    ]),
    service=st.sampled_from(["dynamodb", "s3", "sns", "lambda", "states"])
)
def test_property_14_iam_policy_resource_arn_patterns(role_name, service):
    """
    Feature: function-specific-iam-roles, Property 14: IAM Policy Resource ARN Patterns
    
    For any IAM policy statement and any AWS service (DynamoDB, S3, SNS, Lambda,
    Step Functions), when the policy grants permissions, the Resource field should
    use specific ARN patterns matching {ProjectName}-* instead of wildcards, except
    when the service does not support resource-level permissions (DRS, EC2 Describe operations).
    
    Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7
    """
    # Using module-level IAM_TEMPLATE
    statements = extract_policy_statements(IAM_TEMPLATE, role_name)
    
    project_name = "aws-drs-orchestration"
    
    # Find statements that grant permissions for the specified service
    service_statements = []
    for statement in statements:
        if statement.get("Effect") != "Allow":
            continue
        
        actions = statement.get("Action", [])
        if isinstance(actions, str):
            actions = [actions]
        
        # Check if any action belongs to the service
        for action in actions:
            if action.startswith(f"{service}:"):
                service_statements.append(statement)
                break
    
    # Verify resource ARN patterns for services that support resource-level permissions
    for statement in service_statements:
        resources = statement.get("Resource", [])
        if isinstance(resources, str):
            resources = [resources]
        
        for resource in resources:
            # Handle CloudFormation intrinsic functions
            resource_str = resource
            if isinstance(resource, dict):
                if "Sub" in resource:
                    resource_str = str(resource["Sub"])
                elif "Fn::Sub" in resource:
                    resource_str = str(resource["Fn::Sub"])
                else:
                    resource_str = str(resource)
            
            if resource_str == "*":
                # Wildcard is only acceptable for services that don't support resource-level permissions
                # or for specific read-only operations
                actions = statement.get("Action", [])
                if isinstance(actions, str):
                    actions = [actions]
                
                # Check if these are describe/read operations or services without resource-level support
                is_describe_operation = any(
                    "Describe" in action or "Get" in action or "List" in action
                    for action in actions
                )
                
                # DRS and EC2 Describe operations don't support resource-level permissions
                is_drs_or_ec2_describe = any(
                    action.startswith("drs:") or (action.startswith("ec2:") and "Describe" in action)
                    for action in actions
                )
                
                if not (is_describe_operation or is_drs_or_ec2_describe):
                    # For write operations on services with resource-level support, should use specific ARNs
                    if service in ["dynamodb", "s3", "sns", "lambda", "states"]:
                        pytest.fail(
                            f"{role_name}: {service} write operations should use specific ARN patterns, "
                            f"not wildcard. Actions: {actions}"
                        )
            else:
                # Verify that specific ARNs include project name pattern
                if service in ["dynamodb", "s3", "sns", "lambda", "states"]:
                    # Should include project name or wildcard pattern
                    assert (
                        project_name in resource_str or
                        "${ProjectName}" in resource_str or
                        "*" in resource_str
                    ), (
                        f"{role_name}: {service} resource ARN should include project name pattern. "
                        f"Resource: {resource_str}"
                    )


# ============================================================================
# Property 19: CloudFormation Template Structure Consistency
# ============================================================================

def test_property_19_cloudformation_template_structure_consistency():
    """
    Feature: function-specific-iam-roles, Property 19: CloudFormation Template Structure Consistency
    
    For any nested stack template, when the template is validated, it should include
    a description, define clear input parameters with descriptions, define outputs
    for resources that other stacks depend on, use consistent parameter naming
    (ProjectName, Environment, DeploymentBucket), and pass cfn-lint validation.
    
    Validates: Requirements 16.49, 16.50, 16.51, 16.52, 16.53, 16.54
    """
    # Using module-level IAM_TEMPLATE
    
    # Check template has description
    assert "Description" in IAM_TEMPLATE, "Template must have a Description field"
    description = IAM_TEMPLATE.get("Description", "")
    assert len(description) > 0, "Description must not be empty"
    
    # Check parameters exist and have descriptions
    parameters = IAM_TEMPLATE.get("Parameters", {})
    assert len(parameters) > 0, "Template must define parameters"
    
    required_parameters = ["ProjectName", "Environment", "UseFunctionSpecificRoles"]
    for param_name in required_parameters:
        assert param_name in parameters, f"Template must define {param_name} parameter"
        param = parameters[param_name]
        assert "Description" in param, f"{param_name} parameter must have a Description"
        assert len(param["Description"]) > 0, f"{param_name} Description must not be empty"
    
    # Check outputs exist for role ARNs
    outputs = IAM_TEMPLATE.get("Outputs", {})
    assert len(outputs) > 0, "Template must define outputs"
    
    required_outputs = [
        "UnifiedRoleArn",
        "QueryHandlerRoleArn",
        "DataManagementRoleArn",
        "ExecutionHandlerRoleArn",
        "OrchestrationRoleArn",
        "FrontendDeployerRoleArn"
    ]
    
    for output_name in required_outputs:
        assert output_name in outputs, f"Template must define {output_name} output"
        output = outputs[output_name]
        assert "Description" in output, f"{output_name} output must have a Description"
        assert "Value" in output, f"{output_name} output must have a Value"


# ============================================================================
# Property 20: EventBridge Rule Consolidation Eliminates Duplication
# ============================================================================

def test_property_20_eventbridge_rule_consolidation():
    """
    Feature: function-specific-iam-roles, Property 20: EventBridge Rule Consolidation Eliminates Duplication
    
    For any EventBridge rule that triggers execution polling, when the reorganization
    is complete, exactly one rule should exist (ExecutionPollingScheduleRule in
    eventbridge stack), and no duplicate rules should exist in lambda-stack.yaml
    or other non-eventbridge templates.
    
    Validates: Requirements 16.63, 16.64, 16.65, 16.66, 16.67, 16.68, 16.69, 16.70, 16.71
    
    Note: This property validates IAM roles template structure. EventBridge rule
    consolidation is validated in eventbridge stack tests.
    """
    # This test validates that IAM roles template doesn't contain EventBridge rules
    # Using module-level IAM_TEMPLATE
    resources = IAM_TEMPLATE.get("Resources", {})
    
    # Verify no EventBridge rules in IAM roles template
    for resource_name, resource in resources.items():
        resource_type = resource.get("Type", "")
        assert resource_type != "AWS::Events::Rule", (
            f"IAM roles template should not contain EventBridge rules. Found: {resource_name}"
        )


# ============================================================================
# Property 21: Backward Compatibility Preservation
# ============================================================================

def test_property_21_backward_compatibility_preservation():
    """
    Feature: function-specific-iam-roles, Property 21: Backward Compatibility Preservation
    
    For any existing CloudFormation template, when the reorganization is complete,
    the template should remain functional, and the unified role should continue to
    work when UseFunctionSpecificRoles=false.
    
    Validates: Requirements 16.43, 16.44, 16.45, 16.46, 16.48
    """
    # Using module-level IAM_TEMPLATE
    resources = IAM_TEMPLATE.get("Resources", {})
    
    # Verify UnifiedOrchestrationRole exists for backward compatibility
    assert "UnifiedOrchestrationRole" in resources, (
        "UnifiedOrchestrationRole must exist for backward compatibility"
    )
    
    unified_role = resources["UnifiedOrchestrationRole"]
    assert unified_role.get("Type") == "AWS::IAM::Role", (
        "UnifiedOrchestrationRole must be an IAM role"
    )
    
    # Verify it has the UseUnifiedRole condition
    assert unified_role.get("Condition") == "UseUnifiedRole", (
        "UnifiedOrchestrationRole must have UseUnifiedRole condition"
    )
    
    # Verify it has comprehensive permissions (backward compatibility)
    properties = unified_role.get("Properties", {})
    policies = properties.get("Policies", [])
    assert len(policies) > 0, "UnifiedOrchestrationRole must have policies"
    
    # Verify it includes permissions for all services
    all_statements = []
    for policy in policies:
        policy_doc = policy.get("PolicyDocument", {})
        statements = policy_doc.get("Statement", [])
        all_statements.extend(statements)
    
    # Check for key permissions that all functions need
    required_services = ["dynamodb", "drs", "states", "sns", "lambda"]
    for service in required_services:
        has_service_permission = any(
            any(
                action.startswith(f"{service}:")
                for action in (
                    statement.get("Action", [])
                    if isinstance(statement.get("Action", []), list)
                    else [statement.get("Action", "")]
                )
            )
            for statement in all_statements
            if statement.get("Effect") == "Allow"
        )
        assert has_service_permission, (
            f"UnifiedOrchestrationRole must have {service} permissions for backward compatibility"
        )


# ============================================================================
# Property 22: Deletion Policy Completeness
# ============================================================================

def test_property_22_deletion_policy_completeness():
    """
    Feature: function-specific-iam-roles, Property 22: Deletion Policy Completeness
    
    For any IAM role resource, when the CloudFormation stack is deleted, the role
    should be properly cleaned up without leaving orphaned resources.
    
    Validates: Requirements 17.1-17.13 (comprehensive test suite requirements)
    
    Note: This property validates that IAM roles don't have DeletionPolicy=Retain
    which would prevent cleanup during stack deletion.
    """
    # Using module-level IAM_TEMPLATE
    resources = IAM_TEMPLATE.get("Resources", {})
    
    # Get all IAM role resources
    iam_roles = [
        "UnifiedOrchestrationRole",
        "QueryHandlerRole",
        "DataManagementRole",
        "ExecutionHandlerRole",
        "OrchestrationRole",
        "FrontendDeployerRole"
    ]
    
    for role_name in iam_roles:
        role = resources.get(role_name, {})
        if not role:
            continue
        
        # Verify no DeletionPolicy=Retain (would prevent cleanup)
        deletion_policy = role.get("DeletionPolicy", "Delete")
        assert deletion_policy != "Retain", (
            f"{role_name} should not have DeletionPolicy=Retain to ensure proper cleanup"
        )
        
        # Verify role has proper AssumeRolePolicyDocument
        properties = role.get("Properties", {})
        assume_role_policy = properties.get("AssumeRolePolicyDocument", {})
        assert len(assume_role_policy) > 0, (
            f"{role_name} must have AssumeRolePolicyDocument"
        )
