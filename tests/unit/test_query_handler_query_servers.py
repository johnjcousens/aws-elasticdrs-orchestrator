"""
Unit tests for query_drs_servers_by_tags function in query-handler.

Tests tag-based server discovery with DRS API mocking.

**Validates**: Requirements 1.3
- Task 3.6: Test successful server query with matching tags
- Task 3.7: Test no servers match tags
- Task 3.8: Test case-insensitive tag matching
- Task 3.9: Test AND logic (all tags must match)
- Task 3.10: Test cross-account context handling
"""

import os
import sys
from unittest.mock import Mock, patch

import pytest


# Module-level setup to load query-handler index
lambda_dir = os.path.join(os.path.dirname(__file__), "../../lambda")
query_handler_dir = os.path.join(lambda_dir, "query-handler")


@pytest.fixture(scope="function", autouse=True)
def setup_query_handler_import():
    """Ensure query-handler index is imported correctly"""
    original_path = sys.path.copy()
    original_index = sys.modules.get("index")

    if "index" in sys.modules:
        del sys.modules["index"]

    sys.path.insert(0, query_handler_dir)
    sys.path.insert(0, lambda_dir)

    yield

    sys.path = original_path
    if "index" in sys.modules:
        del sys.modules["index"]
    if original_index is not None:
        sys.modules["index"] = original_index


@pytest.fixture
def mock_drs_client():
    """Mock DRS client with paginator support"""
    client = Mock()

    # Mock paginator
    paginator = Mock()
    client.get_paginator = Mock(return_value=paginator)

    return client


@pytest.fixture
def sample_servers():
    """Sample DRS source servers with various tag combinations"""
    return [
        {
            "sourceServerID": "s-001",
            "tags": {
                "Environment": "production",
                "Application": "web",
                "Customer": "acme",
            },
        },
        {
            "sourceServerID": "s-002",
            "tags": {
                "Environment": "production",
                "Application": "database",
                "Customer": "acme",
            },
        },
        {
            "sourceServerID": "s-003",
            "tags": {
                "Environment": "staging",
                "Application": "web",
                "Customer": "acme",
            },
        },
        {
            "sourceServerID": "s-004",
            "tags": {
                "Environment": "production",
                "Application": "web",
                "Customer": "globex",
            },
        },
        {
            "sourceServerID": "s-005",
            "tags": {
                "Environment": "production",
                "Application": "web",
            },
        },
    ]


class TestQueryServersByTagsSuccess:
    """Test successful server query with matching tags (Task 3.6)"""

    def test_single_tag_match(self, mock_drs_client, sample_servers):
        """Test querying servers with single tag"""
        from index import query_drs_servers_by_tags

        # Mock paginator to return all servers
        paginator = mock_drs_client.get_paginator.return_value
        paginator.paginate.return_value = [{"items": sample_servers}]

        with patch("index.create_drs_client", return_value=mock_drs_client):
            result = query_drs_servers_by_tags(region="us-east-1", tags={"Environment": "production"})

        # Verify correct servers returned
        assert len(result) == 4
        assert "s-001" in result
        assert "s-002" in result
        assert "s-004" in result
        assert "s-005" in result
        assert "s-003" not in result  # staging environment

    def test_multiple_tags_match(self, mock_drs_client, sample_servers):
        """Test querying servers with multiple tags (AND logic)"""
        from index import query_drs_servers_by_tags

        # Mock paginator
        paginator = mock_drs_client.get_paginator.return_value
        paginator.paginate.return_value = [{"items": sample_servers}]

        with patch("index.create_drs_client", return_value=mock_drs_client):
            result = query_drs_servers_by_tags(
                region="us-east-1", tags={"Environment": "production", "Application": "web", "Customer": "acme"}
            )

        # Verify only server with ALL tags returned
        assert len(result) == 1
        assert result[0] == "s-001"

    def test_exact_match_required(self, mock_drs_client, sample_servers):
        """Test that all tags must match exactly"""
        from index import query_drs_servers_by_tags

        # Mock paginator
        paginator = mock_drs_client.get_paginator.return_value
        paginator.paginate.return_value = [{"items": sample_servers}]

        with patch("index.create_drs_client", return_value=mock_drs_client):
            result = query_drs_servers_by_tags(
                region="us-east-1",
                tags={
                    "Environment": "production",
                    "Application": "web",
                    "Customer": "acme",
                    "Team": "platform",  # No servers have this tag
                },
            )

        # Verify no servers returned (missing Team tag)
        assert len(result) == 0

    def test_pagination_multiple_pages(self, mock_drs_client):
        """Test handling multiple pages of results"""
        from index import query_drs_servers_by_tags

        # Mock paginator with multiple pages
        paginator = mock_drs_client.get_paginator.return_value
        paginator.paginate.return_value = [
            {
                "items": [
                    {
                        "sourceServerID": "s-001",
                        "tags": {"Environment": "production"},
                    },
                    {
                        "sourceServerID": "s-002",
                        "tags": {"Environment": "production"},
                    },
                ]
            },
            {
                "items": [
                    {
                        "sourceServerID": "s-003",
                        "tags": {"Environment": "staging"},
                    },
                    {
                        "sourceServerID": "s-004",
                        "tags": {"Environment": "production"},
                    },
                ]
            },
        ]

        with patch("index.create_drs_client", return_value=mock_drs_client):
            result = query_drs_servers_by_tags(region="us-east-1", tags={"Environment": "production"})

        # Verify servers from both pages
        assert len(result) == 3
        assert "s-001" in result
        assert "s-002" in result
        assert "s-004" in result
        assert "s-003" not in result


class TestQueryServersByTagsNoMatch:
    """Test no servers match tags (Task 3.7)"""

    def test_no_servers_in_region(self, mock_drs_client):
        """Test querying region with no DRS servers"""
        from index import query_drs_servers_by_tags

        # Mock paginator with empty results
        paginator = mock_drs_client.get_paginator.return_value
        paginator.paginate.return_value = [{"items": []}]

        with patch("index.create_drs_client", return_value=mock_drs_client):
            result = query_drs_servers_by_tags(region="us-west-2", tags={"Environment": "production"})

        # Verify empty list returned
        assert result == []

    def test_no_matching_tags(self, mock_drs_client, sample_servers):
        """Test querying with tags that don't match any servers"""
        from index import query_drs_servers_by_tags

        # Mock paginator
        paginator = mock_drs_client.get_paginator.return_value
        paginator.paginate.return_value = [{"items": sample_servers}]

        with patch("index.create_drs_client", return_value=mock_drs_client):
            result = query_drs_servers_by_tags(region="us-east-1", tags={"Environment": "development"})

        # Verify no servers returned
        assert len(result) == 0

    def test_partial_tag_match_excluded(self, mock_drs_client, sample_servers):
        """Test servers with partial tag matches are excluded"""
        from index import query_drs_servers_by_tags

        # Mock paginator
        paginator = mock_drs_client.get_paginator.return_value
        paginator.paginate.return_value = [{"items": sample_servers}]

        with patch("index.create_drs_client", return_value=mock_drs_client):
            result = query_drs_servers_by_tags(
                region="us-east-1",
                tags={
                    "Environment": "production",
                    "Application": "web",
                    "Team": "platform",  # Only s-001 has first 2 tags
                },
            )

        # Verify no servers returned (s-001 missing Team tag)
        assert len(result) == 0

    def test_servers_without_tags(self, mock_drs_client):
        """Test servers without any tags are excluded"""
        from index import query_drs_servers_by_tags

        # Mock paginator with servers without tags
        paginator = mock_drs_client.get_paginator.return_value
        paginator.paginate.return_value = [
            {
                "items": [
                    {
                        "sourceServerID": "s-001",
                        "tags": {},
                    },
                    {
                        "sourceServerID": "s-002",
                        "tags": {"Environment": "production"},
                    },
                ]
            }
        ]

        with patch("index.create_drs_client", return_value=mock_drs_client):
            result = query_drs_servers_by_tags(region="us-east-1", tags={"Environment": "production"})

        # Verify only s-002 returned
        assert len(result) == 1
        assert result[0] == "s-002"


class TestQueryServersByTagsCaseInsensitive:
    """Test case-insensitive tag matching (Task 3.8)"""

    def test_tag_value_case_insensitive(self, mock_drs_client):
        """Test tag values are matched case-insensitively"""
        from index import query_drs_servers_by_tags

        # Mock paginator with mixed case tags
        paginator = mock_drs_client.get_paginator.return_value
        paginator.paginate.return_value = [
            {
                "items": [
                    {
                        "sourceServerID": "s-001",
                        "tags": {"Environment": "Production"},
                    },
                    {
                        "sourceServerID": "s-002",
                        "tags": {"Environment": "PRODUCTION"},
                    },
                    {
                        "sourceServerID": "s-003",
                        "tags": {"Environment": "production"},
                    },
                ]
            }
        ]

        with patch("index.create_drs_client", return_value=mock_drs_client):
            # Query with lowercase
            result = query_drs_servers_by_tags(region="us-east-1", tags={"Environment": "production"})

        # Verify all servers matched regardless of case
        assert len(result) == 3
        assert "s-001" in result
        assert "s-002" in result
        assert "s-003" in result

    def test_query_tag_uppercase(self, mock_drs_client):
        """Test querying with uppercase tag values"""
        from index import query_drs_servers_by_tags

        # Mock paginator
        paginator = mock_drs_client.get_paginator.return_value
        paginator.paginate.return_value = [
            {
                "items": [
                    {
                        "sourceServerID": "s-001",
                        "tags": {"Environment": "production"},
                    },
                ]
            }
        ]

        with patch("index.create_drs_client", return_value=mock_drs_client):
            # Query with uppercase
            result = query_drs_servers_by_tags(region="us-east-1", tags={"Environment": "PRODUCTION"})

        # Verify match found
        assert len(result) == 1
        assert result[0] == "s-001"

    def test_tag_key_case_sensitive(self, mock_drs_client):
        """Test tag keys are case-sensitive (AWS standard)"""
        from index import query_drs_servers_by_tags

        # Mock paginator
        paginator = mock_drs_client.get_paginator.return_value
        paginator.paginate.return_value = [
            {
                "items": [
                    {
                        "sourceServerID": "s-001",
                        "tags": {"Environment": "production"},
                    },
                ]
            }
        ]

        with patch("index.create_drs_client", return_value=mock_drs_client):
            # Query with different case key
            result = query_drs_servers_by_tags(region="us-east-1", tags={"environment": "production"})  # lowercase key

        # Verify no match (key case mismatch)
        assert len(result) == 0

    def test_whitespace_stripped(self, mock_drs_client):
        """Test whitespace is stripped from tag values"""
        from index import query_drs_servers_by_tags

        # Mock paginator with whitespace in tags
        paginator = mock_drs_client.get_paginator.return_value
        paginator.paginate.return_value = [
            {
                "items": [
                    {
                        "sourceServerID": "s-001",
                        "tags": {"Environment": " production "},
                    },
                    {
                        "sourceServerID": "s-002",
                        "tags": {"Environment": "production"},
                    },
                ]
            }
        ]

        with patch("index.create_drs_client", return_value=mock_drs_client):
            result = query_drs_servers_by_tags(region="us-east-1", tags={"Environment": "production"})

        # Verify both servers matched (whitespace stripped)
        assert len(result) == 2
        assert "s-001" in result
        assert "s-002" in result


class TestQueryServersByTagsAndLogic:
    """Test AND logic (all tags must match) (Task 3.9)"""

    def test_and_logic_two_tags(self, mock_drs_client):
        """Test AND logic with two tags"""
        from index import query_drs_servers_by_tags

        # Mock paginator
        paginator = mock_drs_client.get_paginator.return_value
        paginator.paginate.return_value = [
            {
                "items": [
                    {
                        "sourceServerID": "s-001",
                        "tags": {
                            "Environment": "production",
                            "Application": "web",
                        },
                    },
                    {
                        "sourceServerID": "s-002",
                        "tags": {
                            "Environment": "production",
                        },
                    },
                    {
                        "sourceServerID": "s-003",
                        "tags": {
                            "Application": "web",
                        },
                    },
                ]
            }
        ]

        with patch("index.create_drs_client", return_value=mock_drs_client):
            result = query_drs_servers_by_tags(
                region="us-east-1", tags={"Environment": "production", "Application": "web"}
            )

        # Verify only server with BOTH tags returned
        assert len(result) == 1
        assert result[0] == "s-001"

    def test_and_logic_three_tags(self, mock_drs_client):
        """Test AND logic with three tags"""
        from index import query_drs_servers_by_tags

        # Mock paginator
        paginator = mock_drs_client.get_paginator.return_value
        paginator.paginate.return_value = [
            {
                "items": [
                    {
                        "sourceServerID": "s-001",
                        "tags": {
                            "Environment": "production",
                            "Application": "web",
                            "Customer": "acme",
                        },
                    },
                    {
                        "sourceServerID": "s-002",
                        "tags": {
                            "Environment": "production",
                            "Application": "web",
                        },
                    },
                    {
                        "sourceServerID": "s-003",
                        "tags": {
                            "Environment": "production",
                            "Customer": "acme",
                        },
                    },
                ]
            }
        ]

        with patch("index.create_drs_client", return_value=mock_drs_client):
            result = query_drs_servers_by_tags(
                region="us-east-1", tags={"Environment": "production", "Application": "web", "Customer": "acme"}
            )

        # Verify only server with ALL THREE tags returned
        assert len(result) == 1
        assert result[0] == "s-001"

    def test_and_logic_multiple_matches(self, mock_drs_client):
        """Test AND logic returns multiple servers when all match"""
        from index import query_drs_servers_by_tags

        # Mock paginator
        paginator = mock_drs_client.get_paginator.return_value
        paginator.paginate.return_value = [
            {
                "items": [
                    {
                        "sourceServerID": "s-001",
                        "tags": {
                            "Environment": "production",
                            "Application": "web",
                        },
                    },
                    {
                        "sourceServerID": "s-002",
                        "tags": {
                            "Environment": "production",
                            "Application": "web",
                        },
                    },
                    {
                        "sourceServerID": "s-003",
                        "tags": {
                            "Environment": "staging",
                            "Application": "web",
                        },
                    },
                ]
            }
        ]

        with patch("index.create_drs_client", return_value=mock_drs_client):
            result = query_drs_servers_by_tags(
                region="us-east-1", tags={"Environment": "production", "Application": "web"}
            )

        # Verify both production web servers returned
        assert len(result) == 2
        assert "s-001" in result
        assert "s-002" in result
        assert "s-003" not in result

    def test_and_logic_one_missing_tag(self, mock_drs_client):
        """Test server excluded if missing one required tag"""
        from index import query_drs_servers_by_tags

        # Mock paginator
        paginator = mock_drs_client.get_paginator.return_value
        paginator.paginate.return_value = [
            {
                "items": [
                    {
                        "sourceServerID": "s-001",
                        "tags": {
                            "Environment": "production",
                            "Application": "web",
                            "Customer": "acme",
                            "Team": "platform",
                        },
                    },
                ]
            }
        ]

        with patch("index.create_drs_client", return_value=mock_drs_client):
            result = query_drs_servers_by_tags(
                region="us-east-1",
                tags={
                    "Environment": "production",
                    "Application": "web",
                    "Customer": "acme",
                    "Team": "platform",
                    "Region": "us-east",  # Missing this tag
                },
            )

        # Verify no servers returned (missing Region tag)
        assert len(result) == 0


class TestQueryServersByTagsCrossAccount:
    """Test cross-account context handling (Task 3.10)"""

    def test_cross_account_context_passed(self, mock_drs_client, sample_servers):
        """Test cross-account context is passed to create_drs_client"""
        from index import query_drs_servers_by_tags

        # Mock paginator
        paginator = mock_drs_client.get_paginator.return_value
        paginator.paginate.return_value = [{"items": sample_servers}]

        account_context = {
            "accountId": "123456789012",
            "assumeRoleName": "DRSOrchestrationRole",
            "isCurrentAccount": False,
        }

        with patch("index.create_drs_client", return_value=mock_drs_client) as mock_create:
            result = query_drs_servers_by_tags(
                region="us-east-1", tags={"Environment": "production"}, account_context=account_context
            )

        # Verify create_drs_client called with account context
        mock_create.assert_called_once_with("us-east-1", account_context)

        # Verify results returned correctly
        assert len(result) == 4

    def test_no_account_context(self, mock_drs_client, sample_servers):
        """Test querying without account context (current account)"""
        from index import query_drs_servers_by_tags

        # Mock paginator
        paginator = mock_drs_client.get_paginator.return_value
        paginator.paginate.return_value = [{"items": sample_servers}]

        with patch("index.create_drs_client", return_value=mock_drs_client) as mock_create:
            result = query_drs_servers_by_tags(region="us-east-1", tags={"Environment": "production"})

        # Verify create_drs_client called with None context
        mock_create.assert_called_once_with("us-east-1", None)

        # Verify results returned correctly
        assert len(result) == 4

    def test_current_account_context(self, mock_drs_client, sample_servers):
        """Test querying with current account context"""
        from index import query_drs_servers_by_tags

        # Mock paginator
        paginator = mock_drs_client.get_paginator.return_value
        paginator.paginate.return_value = [{"items": sample_servers}]

        account_context = {
            "accountId": "999888777666",
            "isCurrentAccount": True,
        }

        with patch("index.create_drs_client", return_value=mock_drs_client) as mock_create:
            result = query_drs_servers_by_tags(
                region="us-east-1", tags={"Environment": "production"}, account_context=account_context
            )

        # Verify create_drs_client called with account context
        mock_create.assert_called_once_with("us-east-1", account_context)

        # Verify results returned correctly
        assert len(result) == 4


class TestQueryServersByTagsErrorHandling:
    """Test error handling and edge cases"""

    def test_drs_api_error_raises_exception(self, mock_drs_client):
        """Test DRS API errors are raised"""
        from index import query_drs_servers_by_tags
        from botocore.exceptions import ClientError

        # Mock paginator to raise error
        paginator = mock_drs_client.get_paginator.return_value
        paginator.paginate.side_effect = ClientError(
            {
                "Error": {
                    "Code": "AccessDeniedException",
                    "Message": "Not authorized",
                }
            },
            "DescribeSourceServers",
        )

        with patch("index.create_drs_client", return_value=mock_drs_client):
            with pytest.raises(ClientError):
                query_drs_servers_by_tags(region="us-east-1", tags={"Environment": "production"})

    def test_empty_tags_dict(self, mock_drs_client, sample_servers):
        """Test querying with empty tags dict returns all servers"""
        from index import query_drs_servers_by_tags

        # Mock paginator
        paginator = mock_drs_client.get_paginator.return_value
        paginator.paginate.return_value = [{"items": sample_servers}]

        with patch("index.create_drs_client", return_value=mock_drs_client):
            result = query_drs_servers_by_tags(region="us-east-1", tags={})

        # Verify all servers returned (no filtering)
        assert len(result) == 5

    def test_server_missing_tags_field(self, mock_drs_client):
        """Test handling servers without tags field"""
        from index import query_drs_servers_by_tags

        # Mock paginator with server missing tags field
        paginator = mock_drs_client.get_paginator.return_value
        paginator.paginate.return_value = [
            {
                "items": [
                    {
                        "sourceServerID": "s-001",
                        # No tags field
                    },
                    {
                        "sourceServerID": "s-002",
                        "tags": {"Environment": "production"},
                    },
                ]
            }
        ]

        with patch("index.create_drs_client", return_value=mock_drs_client):
            result = query_drs_servers_by_tags(region="us-east-1", tags={"Environment": "production"})

        # Verify only s-002 returned (s-001 has no tags)
        assert len(result) == 1
        assert result[0] == "s-002"

    def test_server_missing_source_server_id(self, mock_drs_client):
        """Test handling servers without sourceServerID field"""
        from index import query_drs_servers_by_tags

        # Mock paginator with server missing sourceServerID
        paginator = mock_drs_client.get_paginator.return_value
        paginator.paginate.return_value = [
            {
                "items": [
                    {
                        # No sourceServerID field
                        "tags": {"Environment": "production"},
                    },
                    {
                        "sourceServerID": "s-002",
                        "tags": {"Environment": "production"},
                    },
                ]
            }
        ]

        with patch("index.create_drs_client", return_value=mock_drs_client):
            result = query_drs_servers_by_tags(region="us-east-1", tags={"Environment": "production"})

        # Verify both servers processed (empty string for missing ID)
        assert len(result) == 2
        assert "" in result  # Empty string for missing ID
        assert "s-002" in result

    def test_tag_value_numeric(self, mock_drs_client):
        """Test handling numeric tag values"""
        from index import query_drs_servers_by_tags

        # Mock paginator with numeric tag values
        paginator = mock_drs_client.get_paginator.return_value
        paginator.paginate.return_value = [
            {
                "items": [
                    {
                        "sourceServerID": "s-001",
                        "tags": {"Port": 8080},  # Numeric value
                    },
                    {
                        "sourceServerID": "s-002",
                        "tags": {"Port": "8080"},  # String value
                    },
                ]
            }
        ]

        with patch("index.create_drs_client", return_value=mock_drs_client):
            result = query_drs_servers_by_tags(region="us-east-1", tags={"Port": "8080"})

        # Verify both servers matched (numeric converted to string)
        assert len(result) == 2
        assert "s-001" in result
        assert "s-002" in result
