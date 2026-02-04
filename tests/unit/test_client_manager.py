"""Tests for AWS client manager."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

from src.aws.client_manager import AWSClientManager, get_client_manager, retry_with_backoff
from src.aws.exceptions import AWSCredentialsError, AWSPermissionError, AWSServiceError


class TestAWSClientManager:
    """Test AWS client manager functionality."""
    
    def test_credential_validation_success(self, mock_aws_credentials):
        """Test successful credential validation."""
        manager = AWSClientManager(region="us-east-1")
        assert manager.region == "us-east-1"
        assert manager.profile is None
    
    def test_credential_validation_with_profile(self, mock_aws_credentials):
        """Test credential validation with profile."""
        manager = AWSClientManager(region="us-east-1", profile="test-profile")
        assert manager.region == "us-east-1"
        assert manager.profile == "test-profile"
    
    def test_no_credentials_error(self):
        """Test handling of missing credentials."""
        with patch('boto3.Session') as mock_session:
            mock_sts = Mock()
            mock_sts.get_caller_identity.side_effect = NoCredentialsError()
            mock_session.return_value.client.return_value = mock_sts
            
            with pytest.raises(AWSCredentialsError, match="No AWS credentials found"):
                AWSClientManager(region="us-east-1")
    
    def test_partial_credentials_error(self):
        """Test handling of incomplete credentials."""
        with patch('boto3.Session') as mock_session:
            mock_sts = Mock()
            mock_sts.get_caller_identity.side_effect = PartialCredentialsError(
                provider="test", cred_var="AWS_ACCESS_KEY_ID"
            )
            mock_session.return_value.client.return_value = mock_sts
            
            with pytest.raises(AWSCredentialsError, match="Incomplete AWS credentials"):
                AWSClientManager(region="us-east-1")
    
    def test_access_denied_error(self):
        """Test handling of access denied errors."""
        with patch('boto3.Session') as mock_session:
            mock_sts = Mock()
            mock_sts.get_caller_identity.side_effect = ClientError(
                {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
                'GetCallerIdentity'
            )
            mock_session.return_value.client.return_value = mock_sts
            
            with pytest.raises(AWSPermissionError, match="Insufficient AWS permissions"):
                AWSClientManager(region="us-east-1")
    
    def test_get_client_caching(self, mock_aws_credentials):
        """Test client caching functionality."""
        manager = AWSClientManager(region="us-east-1")
        
        # First call should create client
        client1 = manager.get_client("organizations")
        
        # Second call should return cached client
        client2 = manager.get_client("organizations")
        
        assert client1 is client2
    
    def test_call_api_success(self, mock_aws_credentials):
        """Test successful API call."""
        manager = AWSClientManager(region="us-east-1")
        
        # Mock the client and method
        mock_client = Mock()
        mock_method = Mock(return_value={"Organization": {"Id": "test"}})
        mock_client.describe_organization = mock_method
        
        manager._clients["organizations_us-east-1"] = mock_client
        
        result = manager.call_api("organizations", "describe_organization")
        
        assert result == {"Organization": {"Id": "test"}}
        mock_method.assert_called_once()
    
    def test_call_api_with_parameters(self, mock_aws_credentials):
        """Test API call with parameters."""
        manager = AWSClientManager(region="us-east-1")
        
        mock_client = Mock()
        mock_method = Mock(return_value={"Accounts": []})
        mock_client.list_accounts = mock_method
        
        manager._clients["organizations_us-east-1"] = mock_client
        
        result = manager.call_api("organizations", "list_accounts", MaxResults=20)
        
        assert result == {"Accounts": []}
        mock_method.assert_called_once_with(MaxResults=20)
    
    def test_call_api_method_not_found(self, mock_aws_credentials):
        """Test API call with non-existent method."""
        manager = AWSClientManager(region="us-east-1")
        
        mock_client = Mock()
        del mock_client.nonexistent_method  # Ensure method doesn't exist
        manager._clients["organizations_us-east-1"] = mock_client
        
        with pytest.raises(AWSServiceError, match="Method nonexistent_method not found"):
            manager.call_api("organizations", "nonexistent_method")
    
    def test_paginate_api_call(self, mock_aws_credentials):
        """Test paginated API call."""
        manager = AWSClientManager(region="us-east-1")
        
        # Mock paginator
        mock_paginator = Mock()
        mock_page1 = {"Accounts": [{"Id": "1"}, {"Id": "2"}]}
        mock_page2 = {"Accounts": [{"Id": "3"}]}
        mock_paginator.paginate.return_value = [mock_page1, mock_page2]
        
        mock_client = Mock()
        mock_client.get_paginator.return_value = mock_paginator
        
        manager._clients["organizations_us-east-1"] = mock_client
        
        result = manager.paginate_api_call("organizations", "list_accounts", "Accounts")
        
        expected = [{"Id": "1"}, {"Id": "2"}, {"Id": "3"}]
        assert result == expected


class TestRetryLogic:
    """Test retry logic functionality."""
    
    def test_retry_on_throttling(self):
        """Test retry on throttling errors."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3, backoff_factor=0.1)
        def mock_api_call():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ClientError(
                    {'Error': {'Code': 'Throttling', 'Message': 'Rate exceeded'}},
                    'TestOperation'
                )
            return {"success": True}
        
        result = mock_api_call()
        
        assert result == {"success": True}
        assert call_count == 3
    
    def test_retry_exhausted(self):
        """Test retry exhaustion."""
        @retry_with_backoff(max_retries=2, backoff_factor=0.1)
        def mock_api_call():
            raise ClientError(
                {'Error': {'Code': 'Throttling', 'Message': 'Rate exceeded'}},
                'TestOperation'
            )
        
        with pytest.raises(AWSServiceError, match="AWS API error"):
            mock_api_call()
    
    def test_no_retry_on_other_errors(self):
        """Test that non-throttling errors are not retried."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3, backoff_factor=0.1)
        def mock_api_call():
            nonlocal call_count
            call_count += 1
            raise ClientError(
                {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
                'TestOperation'
            )
        
        with pytest.raises(AWSServiceError):
            mock_api_call()
        
        assert call_count == 1  # Should not retry


class TestGlobalClientManager:
    """Test global client manager functionality."""
    
    def test_get_client_manager_singleton(self, mock_aws_credentials):
        """Test that get_client_manager returns singleton."""
        manager1 = get_client_manager(region="us-east-1")
        manager2 = get_client_manager(region="us-east-1")
        
        assert manager1 is manager2
    
    def test_get_client_manager_different_regions(self, mock_aws_credentials):
        """Test that different regions create different managers."""
        manager1 = get_client_manager(region="us-east-1")
        manager2 = get_client_manager(region="us-west-2")
        
        assert manager1 is not manager2
        assert manager1.region == "us-east-1"
        assert manager2.region == "us-west-2"