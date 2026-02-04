"""Pytest configuration and fixtures."""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import json

from src.config import Config, set_config
from src.aws.client_manager import AWSClientManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def test_config(temp_dir):
    """Create a test configuration."""
    config = Config()
    config.output.default_output_dir = str(temp_dir / "diagrams")
    config.logging.level = "DEBUG"
    config.enable_caching = True
    config.cache_ttl_hours = 1
    set_config(config)
    return config


@pytest.fixture
def mock_aws_credentials():
    """Mock AWS credentials."""
    with patch('boto3.Session') as mock_session:
        mock_sts = Mock()
        mock_sts.get_caller_identity.return_value = {
            'Account': '123456789012',
            'UserId': 'test-user',
            'Arn': 'arn:aws:iam::123456789012:user/test-user'
        }
        mock_session.return_value.client.return_value = mock_sts
        yield mock_session


@pytest.fixture
def sample_organization():
    """Sample organization data."""
    return {
        "Id": "o-example123456",
        "Arn": "arn:aws:organizations::123456789012:organization/o-example123456",
        "FeatureSet": "ALL",
        "MasterAccountArn": "arn:aws:organizations::123456789012:account/o-example123456/123456789012",
        "MasterAccountId": "123456789012",
        "MasterAccountEmail": "admin@example.com"
    }


@pytest.fixture
def sample_accounts():
    """Sample accounts data."""
    return [
        {
            "Id": "123456789012",
            "Arn": "arn:aws:organizations::123456789012:account/o-example123456/123456789012",
            "Email": "admin@example.com",
            "Name": "Master Account",
            "Status": "ACTIVE",
            "JoinedMethod": "INVITED",
            "JoinedTimestamp": "2020-01-01T00:00:00Z"
        },
        {
            "Id": "123456789013",
            "Arn": "arn:aws:organizations::123456789012:account/o-example123456/123456789013",
            "Email": "dev@example.com",
            "Name": "Development Account",
            "Status": "ACTIVE",
            "JoinedMethod": "CREATED",
            "JoinedTimestamp": "2020-01-02T00:00:00Z"
        }
    ]


@pytest.fixture
def sample_organizational_units():
    """Sample organizational units data."""
    return [
        {
            "Id": "ou-root-example123",
            "Arn": "arn:aws:organizations::123456789012:ou/o-example123456/ou-root-example123",
            "Name": "Development",
            "Parents": [{"Id": "r-example", "Type": "ROOT"}]
        },
        {
            "Id": "ou-root-example456",
            "Arn": "arn:aws:organizations::123456789012:ou/o-example123456/ou-root-example456",
            "Name": "Production",
            "Parents": [{"Id": "r-example", "Type": "ROOT"}]
        }
    ]


@pytest.fixture
def sample_sso_instances():
    """Sample SSO instances data."""
    return [
        {
            "InstanceArn": "arn:aws:sso:::instance/ssoins-example123456",
            "IdentityStoreId": "d-example123456"
        }
    ]


@pytest.fixture
def sample_groups():
    """Sample identity store groups."""
    return [
        {
            "GroupId": "group-123456789012",
            "DisplayName": "Administrators",
            "Description": "Administrator group"
        },
        {
            "GroupId": "group-123456789013",
            "DisplayName": "Developers",
            "Description": "Developer group"
        }
    ]


@pytest.fixture
def sample_users():
    """Sample identity store users."""
    return [
        {
            "UserId": "user-123456789012",
            "UserName": "admin@example.com",
            "DisplayName": "Administrator",
            "Emails": [{"Value": "admin@example.com", "Type": "work", "Primary": True}]
        },
        {
            "UserId": "user-123456789013",
            "UserName": "dev@example.com",
            "DisplayName": "Developer",
            "Emails": [{"Value": "dev@example.com", "Type": "work", "Primary": True}]
        }
    ]


@pytest.fixture
def mock_client_manager(mock_aws_credentials):
    """Mock AWS client manager."""
    with patch('src.aws.client_manager.AWSClientManager') as mock_manager:
        manager_instance = Mock()
        mock_manager.return_value = manager_instance
        yield manager_instance