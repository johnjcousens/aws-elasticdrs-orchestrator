"""
Unit tests for Recovery Plan delete operation
Tests the critical bug fix for execution history query with GSI fallback
"""

import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError

# Set up environment variables BEFORE importing index
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["PROTECTION_GROUPS_TABLE"] = "protection-groups-test"
os.environ["RECOVERY_PLANS_TABLE"] = "recovery-plans-test"
os.environ["EXECUTION_HISTORY_TABLE"] = "execution-history-test"
os.environ["STATE_MACHINE_ARN"] = "arn:aws:states:us-east-1:123456789012:stateMachine:test"

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lambda'))

from index import delete_recovery_plan


class TestRecoveryPlanDelete:
    """Test delete_recovery_plan function with GSI query and fallback logic"""
    
    @patch('index.execution_history_table')
    @patch('index.recovery_plans_table')
    def test_delete_with_no_executions_gsi_success(self, mock_plans_table, mock_history_table):
        """Test successful delete when no active executions exist (GSI query works)"""
        plan_id = 'plan-123'
        
        # Mock GSI query returning no active executions
        mock_history_table.query.return_value = {'Items': []}
        mock_plans_table.delete_item.return_value = {}
        
        result = delete_recovery_plan(plan_id)
        
        # Verify GSI query was attempted
        mock_history_table.query.assert_called_once()
        call_kwargs = mock_history_table.query.call_args[1]
        assert call_kwargs['IndexName'] == 'PlanIdIndex'
        assert call_kwargs['Limit'] == 1
        
        # Verify delete was called
        mock_plans_table.delete_item.assert_called_once_with(Key={'PlanId': plan_id})
        
        # Verify success response
        assert result['statusCode'] == 200
        body = eval(result['body'])
        assert body['message'] == 'Recovery Plan deleted successfully'
        assert body['planId'] == plan_id
    
    @patch('index.execution_history_table')
    @patch('index.recovery_plans_table')
    def test_delete_with_no_executions_scan_fallback(self, mock_plans_table, mock_history_table):
        """Test successful delete using scan fallback when GSI doesn't exist"""
        plan_id = 'plan-456'
        
        # Mock GSI query failure, then scan success
        mock_history_table.query.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Index not found'}},
            'Query'
        )
        mock_history_table.scan.return_value = {'Items': []}
        mock_plans_table.delete_item.return_value = {}
        
        result = delete_recovery_plan(plan_id)
        
        # Verify GSI query was attempted first
        mock_history_table.query.assert_called_once()
        
        # Verify fallback scan was called
        mock_history_table.scan.assert_called_once()
        scan_kwargs = mock_history_table.scan.call_args[1]
        assert scan_kwargs['Limit'] == 1
        
        # Verify delete was called
        mock_plans_table.delete_item.assert_called_once_with(Key={'PlanId': plan_id})
        
        # Verify success response
        assert result['statusCode'] == 200
        body = eval(result['body'])
        assert body['message'] == 'Recovery Plan deleted successfully'
    
    @patch('index.execution_history_table')
    @patch('index.recovery_plans_table')
    def test_delete_blocked_by_active_execution(self, mock_plans_table, mock_history_table):
        """Test delete fails with 409 when active RUNNING execution exists"""
        plan_id = 'plan-789'
        
        # Mock GSI query returning 1 active execution
        mock_history_table.query.return_value = {
            'Items': [{
                'ExecutionId': 'exec-123',
                'PlanId': plan_id,
                'Status': 'RUNNING'
            }]
        }
        
        result = delete_recovery_plan(plan_id)
        
        # Verify delete was NOT called
        mock_plans_table.delete_item.assert_not_called()
        
        # Verify 409 Conflict response
        assert result['statusCode'] == 409
        body = eval(result['body'])
        assert body['error'] == 'PLAN_HAS_ACTIVE_EXECUTIONS'
        assert 'active execution' in body['message'].lower()
        assert body['activeExecutions'] == 1
        assert body['planId'] == plan_id
    
    @patch('index.execution_history_table')
    @patch('index.recovery_plans_table')
    def test_delete_blocked_by_multiple_active_executions(self, mock_plans_table, mock_history_table):
        """Test delete fails when multiple active executions exist"""
        plan_id = 'plan-multi'
        
        # Mock GSI query returning multiple active executions
        mock_history_table.query.return_value = {
            'Items': [
                {'ExecutionId': 'exec-1', 'Status': 'RUNNING'},
                {'ExecutionId': 'exec-2', 'Status': 'RUNNING'},
                {'ExecutionId': 'exec-3', 'Status': 'RUNNING'}
            ]
        }
        
        result = delete_recovery_plan(plan_id)
        
        # Verify delete was NOT called
        mock_plans_table.delete_item.assert_not_called()
        
        # Verify response includes count
        assert result['statusCode'] == 409
        body = eval(result['body'])
        assert body['activeExecutions'] == 3
    
    @patch('index.execution_history_table')
    @patch('index.recovery_plans_table')
    def test_delete_allowed_with_completed_executions(self, mock_plans_table, mock_history_table):
        """Test delete succeeds when only COMPLETED executions exist"""
        plan_id = 'plan-completed'
        
        # Mock query returning no RUNNING executions (only COMPLETED)
        mock_history_table.query.return_value = {'Items': []}
        mock_plans_table.delete_item.return_value = {}
        
        result = delete_recovery_plan(plan_id)
        
        # Should succeed
        assert result['statusCode'] == 200
        mock_plans_table.delete_item.assert_called_once()
    
    @patch('index.execution_history_table')
    @patch('index.recovery_plans_table')
    def test_delete_error_handling(self, mock_plans_table, mock_history_table):
        """Test error handling when DynamoDB operations fail"""
        plan_id = 'plan-error'
        
        # Mock both query and scan to fail (test complete failure path)
        mock_history_table.query.side_effect = Exception('DynamoDB connection failed')
        mock_history_table.scan.side_effect = Exception('DynamoDB connection failed')
        
        result = delete_recovery_plan(plan_id)
        
        # Verify 500 error response
        assert result['statusCode'] == 500
        body = eval(result['body'])
        assert body['error'] == 'DELETE_FAILED'
        assert 'Failed to delete Recovery Plan' in body['message']
        assert body['planId'] == plan_id
    
    @patch('index.execution_history_table')
    @patch('index.recovery_plans_table')
    def test_gsi_query_parameters_correct(self, mock_plans_table, mock_history_table):
        """Test that GSI query uses correct parameters"""
        plan_id = 'plan-params'
        
        mock_history_table.query.return_value = {'Items': []}
        mock_plans_table.delete_item.return_value = {}
        
        delete_recovery_plan(plan_id)
        
        # Verify query parameters
        mock_history_table.query.assert_called_once()
        call_kwargs = mock_history_table.query.call_args[1]
        
        # Check all required parameters
        assert call_kwargs['IndexName'] == 'PlanIdIndex'
        assert call_kwargs['Limit'] == 1
        # KeyConditionExpression and FilterExpression are boto3 objects
        assert 'KeyConditionExpression' in call_kwargs
        assert 'FilterExpression' in call_kwargs
    
    @patch('index.execution_history_table')
    @patch('index.recovery_plans_table')
    def test_scan_fallback_parameters_correct(self, mock_plans_table, mock_history_table):
        """Test that scan fallback uses correct parameters"""
        plan_id = 'plan-scan'
        
        # Force scan fallback
        mock_history_table.query.side_effect = Exception('GSI error')
        mock_history_table.scan.return_value = {'Items': []}
        mock_plans_table.delete_item.return_value = {}
        
        delete_recovery_plan(plan_id)
        
        # Verify scan parameters
        mock_history_table.scan.assert_called_once()
        scan_kwargs = mock_history_table.scan.call_args[1]
        
        assert scan_kwargs['Limit'] == 1
        assert 'FilterExpression' in scan_kwargs
    
    @patch('index.execution_history_table')
    @patch('index.recovery_plans_table')
    def test_delete_logging_on_success(self, mock_plans_table, mock_history_table, capfd):
        """Test that successful delete logs appropriate messages"""
        plan_id = 'plan-log'
        
        mock_history_table.query.return_value = {'Items': []}
        mock_plans_table.delete_item.return_value = {}
        
        delete_recovery_plan(plan_id)
        
        # Note: In actual implementation, would check logs
        # This test verifies the function completes without errors
        assert mock_plans_table.delete_item.called
    
    @patch('index.execution_history_table')
    @patch('index.recovery_plans_table')
    def test_delete_with_empty_items_list(self, mock_plans_table, mock_history_table):
        """Test delete succeeds when Items list is empty (not missing)"""
        plan_id = 'plan-empty-list'
        
        # Mock query returning empty list
        mock_history_table.query.return_value = {'Items': []}
        mock_plans_table.delete_item.return_value = {}
        
        result = delete_recovery_plan(plan_id)
        
        assert result['statusCode'] == 200
        mock_plans_table.delete_item.assert_called_once()
    
    @patch('index.execution_history_table')
    @patch('index.recovery_plans_table')
    def test_delete_with_no_items_key(self, mock_plans_table, mock_history_table):
        """Test delete succeeds when response has no Items key"""
        plan_id = 'plan-no-key'
        
        # Mock query returning response without Items key
        mock_history_table.query.return_value = {}
        mock_plans_table.delete_item.return_value = {}
        
        result = delete_recovery_plan(plan_id)
        
        # Should still succeed (no active executions found)
        assert result['statusCode'] == 200
        mock_plans_table.delete_item.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
