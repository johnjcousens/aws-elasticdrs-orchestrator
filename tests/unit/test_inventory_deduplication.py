"""
Unit tests for inventory deduplication logic.

Tests that duplicate server entries are properly deduplicated
when querying the inventory database.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add lambda directory to path
lambda_path = Path(__file__).parent.parent.parent / "lambda"
sys.path.insert(0, str(lambda_path))

from shared.inventory_query import query_inventory_by_regions


@pytest.fixture
def mock_inventory_table():
    """Mock DynamoDB inventory table"""
    table = MagicMock()
    return table


@pytest.fixture
def duplicate_servers():
    """Sample servers with duplicates"""
    return [
        {
            "sourceServerID": "s-server1",
            "hostname": "server1.example.com",
            "replicationRegion": "us-east-1",
            "lastUpdatedDateTime": "2024-01-01T10:00:00Z",
        },
        {
            "sourceServerID": "s-server1",  # Duplicate
            "hostname": "server1.example.com",
            "replicationRegion": "us-east-1",
            "lastUpdatedDateTime": "2024-01-01T12:00:00Z",  # Newer
        },
        {
            "sourceServerID": "s-server2",
            "hostname": "server2.example.com",
            "replicationRegion": "us-east-1",
            "lastUpdatedDateTime": "2024-01-01T10:00:00Z",
        },
        {
            "sourceServerID": "s-server1",  # Another duplicate
            "hostname": "server1.example.com",
            "replicationRegion": "us-east-1",
            "lastUpdatedDateTime": "2024-01-01T08:00:00Z",  # Older
        },
    ]


def test_deduplication_keeps_most_recent(mock_inventory_table, duplicate_servers):
    """Test that deduplication keeps the most recent server entry"""
    
    with patch("shared.inventory_query.get_inventory_table", return_value=mock_inventory_table):
        with patch("shared.inventory_query.is_inventory_fresh", return_value=True):
            # Mock scan response
            mock_inventory_table.scan.return_value = {
                "Items": duplicate_servers
            }
            
            # Query inventory
            result = query_inventory_by_regions(regions=["us-east-1"])
            
            # Should have 2 unique servers (s-server1 and s-server2)
            assert len(result) == 2
            
            # Find s-server1 in results
            server1 = next(s for s in result if s["sourceServerID"] == "s-server1")
            
            # Should keep the most recent entry (12:00:00)
            assert server1["lastUpdatedDateTime"] == "2024-01-01T12:00:00Z"


def test_deduplication_with_no_duplicates(mock_inventory_table):
    """Test that deduplication works correctly with no duplicates"""
    
    unique_servers = [
        {
            "sourceServerID": "s-server1",
            "hostname": "server1.example.com",
            "replicationRegion": "us-east-1",
            "lastUpdatedDateTime": "2024-01-01T10:00:00Z",
        },
        {
            "sourceServerID": "s-server2",
            "hostname": "server2.example.com",
            "replicationRegion": "us-east-1",
            "lastUpdatedDateTime": "2024-01-01T10:00:00Z",
        },
    ]
    
    with patch("shared.inventory_query.get_inventory_table", return_value=mock_inventory_table):
        with patch("shared.inventory_query.is_inventory_fresh", return_value=True):
            mock_inventory_table.scan.return_value = {
                "Items": unique_servers
            }
            
            result = query_inventory_by_regions(regions=["us-east-1"])
            
            # Should have 2 servers (no deduplication needed)
            assert len(result) == 2


def test_deduplication_handles_missing_timestamp(mock_inventory_table):
    """Test that deduplication handles servers with missing timestamps"""
    
    servers_with_missing_timestamp = [
        {
            "sourceServerID": "s-server1",
            "hostname": "server1.example.com",
            "replicationRegion": "us-east-1",
            "lastUpdatedDateTime": "2024-01-01T10:00:00Z",
        },
        {
            "sourceServerID": "s-server1",  # Duplicate
            "hostname": "server1.example.com",
            "replicationRegion": "us-east-1",
            # Missing lastUpdatedDateTime
        },
    ]
    
    with patch("shared.inventory_query.get_inventory_table", return_value=mock_inventory_table):
        with patch("shared.inventory_query.is_inventory_fresh", return_value=True):
            mock_inventory_table.scan.return_value = {
                "Items": servers_with_missing_timestamp
            }
            
            result = query_inventory_by_regions(regions=["us-east-1"])
            
            # Should have 1 server (deduplicated)
            assert len(result) == 1
            
            # Should keep the one with timestamp
            assert result[0]["lastUpdatedDateTime"] == "2024-01-01T10:00:00Z"


def test_deduplication_with_many_duplicates(mock_inventory_table):
    """Test deduplication with 448 servers reduced to 300"""
    
    # Simulate the real issue: 448 entries for 300 unique servers
    servers = []
    for i in range(300):
        # Add original server
        servers.append({
            "sourceServerID": f"s-server{i}",
            "hostname": f"server{i}.example.com",
            "replicationRegion": "us-east-1",
            "lastUpdatedDateTime": "2024-01-01T10:00:00Z",
        })
        
        # Add duplicate for first 148 servers (300 + 148 = 448)
        if i < 148:
            servers.append({
                "sourceServerID": f"s-server{i}",
                "hostname": f"server{i}.example.com",
                "replicationRegion": "us-east-1",
                "lastUpdatedDateTime": "2024-01-01T08:00:00Z",  # Older
            })
    
    assert len(servers) == 448
    
    with patch("shared.inventory_query.get_inventory_table", return_value=mock_inventory_table):
        with patch("shared.inventory_query.is_inventory_fresh", return_value=True):
            mock_inventory_table.scan.return_value = {
                "Items": servers
            }
            
            result = query_inventory_by_regions(regions=["us-east-1"])
            
            # Should deduplicate to 300 unique servers
            assert len(result) == 300
