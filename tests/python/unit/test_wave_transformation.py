"""
Unit tests for wave data transformation logic
Tests the critical bug fix for ServerIds type handling
"""

import pytest
import sys
import os

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

from index import transform_rp_to_camelcase


class TestWaveTransformation:
    """Test wave data transformation logic with defensive ServerIds handling"""
    
    def test_transform_with_valid_server_ids_list(self):
        """Test transformation with properly formatted ServerIds as list"""
        rp = {
            'PlanId': 'plan-123',
            'PlanName': 'Test Plan',
            'Description': 'Test Description',
            'AccountId': '123456789012',
            'Region': 'us-east-1',
            'Owner': 'testuser',
            'RPO': 60,
            'RTO': 120,
            'Waves': [{
                'WaveId': 'wave-0',
                'WaveName': 'Wave 1',
                'WaveDescription': 'First wave',
                'ServerIds': ['s-123', 's-456'],  # List format - correct
                'ProtectionGroupId': 'pg-789',
                'ExecutionType': 'sequential',
                'Dependencies': []
            }],
            'CreatedDate': 1700000000,
            'LastModifiedDate': 1700000000
        }
        
        result = transform_rp_to_camelcase(rp)
        
        assert result['id'] == 'plan-123'
        assert result['name'] == 'Test Plan'
        assert len(result['waves']) == 1
        assert result['waves'][0]['serverIds'] == ['s-123', 's-456']
        assert isinstance(result['waves'][0]['serverIds'], list)
        assert result['waves'][0]['protectionGroupId'] == 'pg-789'
    
    def test_transform_with_string_server_ids(self):
        """Test recovery from string ServerIds (boto3 deserialization edge case)"""
        rp = {
            'PlanId': 'plan-456',
            'PlanName': 'Edge Case Plan',
            'Description': 'Test',
            'AccountId': '123456789012',
            'Region': 'us-east-1',
            'Owner': 'testuser',
            'RPO': 60,
            'RTO': 120,
            'Waves': [{
                'WaveId': 'wave-0',
                'WaveName': 'Wave 1',
                'ServerIds': 's-123',  # STRING instead of list - bug scenario
                'ProtectionGroupId': 'pg-789',
                'ExecutionType': 'sequential',
                'Dependencies': []
            }],
            'CreatedDate': 1700000000,
            'LastModifiedDate': 1700000000
        }
        
        result = transform_rp_to_camelcase(rp)
        
        # Should recover by wrapping string in list
        assert isinstance(result['waves'][0]['serverIds'], list)
        assert result['waves'][0]['serverIds'] == ['s-123']
    
    def test_transform_with_missing_server_ids(self):
        """Test handling of missing ServerIds field"""
        rp = {
            'PlanId': 'plan-789',
            'PlanName': 'Empty Wave Plan',
            'Description': 'Test',
            'AccountId': '123456789012',
            'Region': 'us-east-1',
            'Owner': 'testuser',
            'RPO': 60,
            'RTO': 120,
            'Waves': [{
                'WaveId': 'wave-0',
                'WaveName': 'Wave 1',
                # ServerIds missing entirely
                'ProtectionGroupId': 'pg-789',
                'ExecutionType': 'sequential',
                'Dependencies': []
            }],
            'CreatedDate': 1700000000,
            'LastModifiedDate': 1700000000
        }
        
        result = transform_rp_to_camelcase(rp)
        
        # Should default to empty list
        assert result['waves'][0]['serverIds'] == []
        assert isinstance(result['waves'][0]['serverIds'], list)
    
    def test_transform_with_invalid_server_ids_type(self):
        """Test handling of invalid ServerIds type (number, dict, etc.)"""
        rp = {
            'PlanId': 'plan-999',
            'PlanName': 'Invalid Type Plan',
            'Description': 'Test',
            'AccountId': '123456789012',
            'Region': 'us-east-1',
            'Owner': 'testuser',
            'RPO': 60,
            'RTO': 120,
            'Waves': [{
                'WaveId': 'wave-0',
                'WaveName': 'Wave 1',
                'ServerIds': {'invalid': 'dict'},  # Invalid type
                'ProtectionGroupId': 'pg-789',
                'ExecutionType': 'sequential',
                'Dependencies': []
            }],
            'CreatedDate': 1700000000,
            'LastModifiedDate': 1700000000
        }
        
        result = transform_rp_to_camelcase(rp)
        
        # Should recover with empty list
        assert result['waves'][0]['serverIds'] == []
        assert isinstance(result['waves'][0]['serverIds'], list)
    
    def test_transform_with_empty_waves(self):
        """Test handling of empty Waves array"""
        rp = {
            'PlanId': 'plan-empty',
            'PlanName': 'No Waves Plan',
            'Description': 'Test',
            'AccountId': '123456789012',
            'Region': 'us-east-1',
            'Owner': 'testuser',
            'RPO': 60,
            'RTO': 120,
            'Waves': [],  # No waves
            'CreatedDate': 1700000000,
            'LastModifiedDate': 1700000000
        }
        
        result = transform_rp_to_camelcase(rp)
        
        assert result['waves'] == []
        assert result['waveCount'] == 0
    
    def test_transform_with_dependencies(self):
        """Test extraction of dependency wave numbers from WaveId format"""
        rp = {
            'PlanId': 'plan-deps',
            'PlanName': 'Dependencies Plan',
            'Description': 'Test',
            'AccountId': '123456789012',
            'Region': 'us-east-1',
            'Owner': 'testuser',
            'RPO': 60,
            'RTO': 120,
            'Waves': [
                {
                    'WaveId': 'wave-0',
                    'WaveName': 'Wave 1',
                    'ServerIds': ['s-123'],
                    'ProtectionGroupId': 'pg-789',
                    'ExecutionType': 'sequential',
                    'Dependencies': []
                },
                {
                    'WaveId': 'wave-1',
                    'WaveName': 'Wave 2',
                    'ServerIds': ['s-456'],
                    'ProtectionGroupId': 'pg-789',
                    'ExecutionType': 'sequential',
                    'Dependencies': [
                        {'DependsOnWaveId': 'wave-0'}
                    ]
                },
                {
                    'WaveId': 'wave-2',
                    'WaveName': 'Wave 3',
                    'ServerIds': ['s-789'],
                    'ProtectionGroupId': 'pg-789',
                    'ExecutionType': 'sequential',
                    'Dependencies': [
                        {'DependsOnWaveId': 'wave-0'},
                        {'DependsOnWaveId': 'wave-1'}
                    ]
                }
            ],
            'CreatedDate': 1700000000,
            'LastModifiedDate': 1700000000
        }
        
        result = transform_rp_to_camelcase(rp)
        
        # Wave 0: no dependencies
        assert result['waves'][0]['dependsOnWaves'] == []
        
        # Wave 1: depends on wave 0
        assert result['waves'][1]['dependsOnWaves'] == [0]
        
        # Wave 2: depends on waves 0 and 1
        assert result['waves'][2]['dependsOnWaves'] == [0, 1]
    
    def test_transform_with_malformed_dependencies(self):
        """Test handling of malformed dependency WaveIds"""
        rp = {
            'PlanId': 'plan-bad-deps',
            'PlanName': 'Bad Dependencies Plan',
            'Description': 'Test',
            'AccountId': '123456789012',
            'Region': 'us-east-1',
            'Owner': 'testuser',
            'RPO': 60,
            'RTO': 120,
            'Waves': [{
                'WaveId': 'wave-0',
                'WaveName': 'Wave 1',
                'ServerIds': ['s-123'],
                'ProtectionGroupId': 'pg-789',
                'ExecutionType': 'sequential',
                'Dependencies': [
                    {'DependsOnWaveId': 'invalid-format'},  # No hyphen-number
                    {'DependsOnWaveId': 'wave-abc'},  # Non-numeric
                    {'DependsOnWaveId': ''},  # Empty
                ]
            }],
            'CreatedDate': 1700000000,
            'LastModifiedDate': 1700000000
        }
        
        result = transform_rp_to_camelcase(rp)
        
        # Should skip malformed dependencies gracefully
        assert result['waves'][0]['dependsOnWaves'] == []
    
    def test_transform_multiple_waves_with_various_server_id_formats(self):
        """Test transformation with mixed ServerIds formats across waves"""
        rp = {
            'PlanId': 'plan-mixed',
            'PlanName': 'Mixed Format Plan',
            'Description': 'Test',
            'AccountId': '123456789012',
            'Region': 'us-east-1',
            'Owner': 'testuser',
            'RPO': 60,
            'RTO': 120,
            'Waves': [
                {
                    'WaveId': 'wave-0',
                    'WaveName': 'Correct Wave',
                    'ServerIds': ['s-111', 's-222'],  # Correct list
                    'ProtectionGroupId': 'pg-789',
                    'ExecutionType': 'sequential',
                    'Dependencies': []
                },
                {
                    'WaveId': 'wave-1',
                    'WaveName': 'String Wave',
                    'ServerIds': 's-333',  # String (bug scenario)
                    'ProtectionGroupId': 'pg-789',
                    'ExecutionType': 'sequential',
                    'Dependencies': []
                },
                {
                    'WaveId': 'wave-2',
                    'WaveName': 'Missing Wave',
                    # ServerIds missing
                    'ProtectionGroupId': 'pg-789',
                    'ExecutionType': 'sequential',
                    'Dependencies': []
                }
            ],
            'CreatedDate': 1700000000,
            'LastModifiedDate': 1700000000
        }
        
        result = transform_rp_to_camelcase(rp)
        
        # Wave 0: should have correct list
        assert result['waves'][0]['serverIds'] == ['s-111', 's-222']
        
        # Wave 1: should recover string to list
        assert result['waves'][1]['serverIds'] == ['s-333']
        
        # Wave 2: should default to empty list
        assert result['waves'][2]['serverIds'] == []
        
        # All should be lists
        for wave in result['waves']:
            assert isinstance(wave['serverIds'], list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
