"""AWS Client Manager with proper error handling and validation."""
import logging
from functools import wraps
from typing import Optional, Dict, Any
import time

import boto3
from botocore.exceptions import (
    ClientError, 
    NoCredentialsError, 
    PartialCredentialsError,
    BotoCoreError
)

from .exceptions import (
    AWSCredentialsError,
    AWSPermissionError,
    AWSServiceError,
    AWSResourceNotFoundError
)

logger = logging.getLogger(__name__)


def retry_with_backoff(max_retries: int = 3, backoff_factor: float = 2.0):
    """Decorator to retry AWS API calls with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except ClientError as e:
                    error_code = e.response.get('Error', {}).get('Code', '')
                    
                    # Retry on throttling errors
                    if error_code in ['Throttling', 'TooManyRequestsException', 'RequestLimitExceeded']:
                        if attempt < max_retries - 1:
                            sleep_time = backoff_factor ** attempt
                            logger.warning(f"AWS API throttled, retrying in {sleep_time}s (attempt {attempt + 1}/{max_retries})")
                            time.sleep(sleep_time)
                            continue
                    
                    # Don't retry on other errors
                    raise AWSServiceError(f"AWS API error: {e}")
                except BotoCoreError as e:
                    raise AWSServiceError(f"AWS service error: {e}")
            
            # Final attempt without retry
            return func(*args, **kwargs)
        return wrapper
    return decorator


class AWSClientManager:
    """Manages AWS clients with proper error handling and validation."""
    
    def __init__(self, region: str, profile: Optional[str] = None):
        """
        Initialize AWS client manager.
        
        Args:
            region: AWS region name
            profile: AWS CLI profile name (optional)
        """
        self.region = region
        self.profile = profile
        self._session = None
        self._clients: Dict[str, Any] = {}
        
        self._setup_session()
        self._validate_credentials()
    
    def _setup_session(self):
        """Setup boto3 session with profile if provided."""
        try:
            if self.profile:
                self._session = boto3.Session(profile_name=self.profile)
                logger.info(f"Using AWS profile: {self.profile}")
            else:
                self._session = boto3.Session()
                logger.info("Using default AWS credentials")
        except Exception as e:
            raise AWSCredentialsError(f"Failed to setup AWS session: {e}")
    
    def _validate_credentials(self):
        """Validate AWS credentials by making a test call."""
        try:
            sts_client = self.get_client('sts')
            identity = sts_client.get_caller_identity()
            logger.info(f"AWS credentials validated for account: {identity.get('Account')}")
        except NoCredentialsError:
            raise AWSCredentialsError("No AWS credentials found. Please configure AWS CLI or set environment variables.")
        except PartialCredentialsError:
            raise AWSCredentialsError("Incomplete AWS credentials. Please check your configuration.")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code in ['AccessDenied', 'UnauthorizedOperation']:
                raise AWSPermissionError(f"Insufficient AWS permissions: {e}")
            raise AWSCredentialsError(f"AWS credential validation failed: {e}")
    
    def get_client(self, service_name: str, **kwargs):
        """
        Get AWS client for specified service with caching.
        
        Args:
            service_name: AWS service name (e.g., 'organizations', 'sso-admin')
            **kwargs: Additional client configuration
            
        Returns:
            Boto3 client instance
        """
        client_key = f"{service_name}_{self.region}"
        
        if client_key not in self._clients:
            try:
                self._clients[client_key] = self._session.client(
                    service_name,
                    region_name=self.region,
                    **kwargs
                )
                logger.debug(f"Created {service_name} client for region {self.region}")
            except Exception as e:
                raise AWSServiceError(f"Failed to create {service_name} client: {e}")
        
        return self._clients[client_key]
    
    @retry_with_backoff()
    def call_api(self, service_name: str, method_name: str, **kwargs):
        """
        Make AWS API call with error handling and retry logic.
        
        Args:
            service_name: AWS service name
            method_name: API method name
            **kwargs: Method parameters
            
        Returns:
            API response
        """
        try:
            client = self.get_client(service_name)
            method = getattr(client, method_name)
            response = method(**kwargs)
            logger.debug(f"Successfully called {service_name}.{method_name}")
            return response
        except AttributeError:
            raise AWSServiceError(f"Method {method_name} not found for service {service_name}")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            
            if error_code in ['ResourceNotFoundException', 'NoSuchEntity']:
                raise AWSResourceNotFoundError(f"AWS resource not found: {e}")
            elif error_code in ['AccessDenied', 'UnauthorizedOperation']:
                raise AWSPermissionError(f"Insufficient permissions for {service_name}.{method_name}: {e}")
            else:
                raise AWSServiceError(f"AWS API call failed {service_name}.{method_name}: {e}")
    
    def paginate_api_call(self, service_name: str, method_name: str, result_key: str, **kwargs):
        """
        Handle paginated AWS API calls.
        
        Args:
            service_name: AWS service name
            method_name: API method name
            result_key: Key in response containing the results
            **kwargs: Method parameters
            
        Returns:
            List of all results from paginated calls
        """
        try:
            client = self.get_client(service_name)
            paginator = client.get_paginator(method_name)
            
            all_results = []
            for page in paginator.paginate(**kwargs):
                if result_key in page:
                    all_results.extend(page[result_key])
            
            logger.debug(f"Retrieved {len(all_results)} items from paginated {service_name}.{method_name}")
            return all_results
            
        except ClientError as e:
            raise AWSServiceError(f"Paginated API call failed {service_name}.{method_name}: {e}")
        except Exception as e:
            raise AWSServiceError(f"Pagination error for {service_name}.{method_name}: {e}")


# Global client manager instance
_client_manager: Optional[AWSClientManager] = None


def get_client_manager(region: str, profile: Optional[str] = None) -> AWSClientManager:
    """Get or create global client manager instance."""
    global _client_manager
    
    if _client_manager is None or _client_manager.region != region or _client_manager.profile != profile:
        _client_manager = AWSClientManager(region=region, profile=profile)
    
    return _client_manager


def client(service_name: str, region_name: str, profile: Optional[str] = None):
    """
    Backward compatibility function for existing code.
    
    Args:
        service_name: AWS service name
        region_name: AWS region
        profile: AWS profile (optional)
        
    Returns:
        Boto3 client instance
    """
    manager = get_client_manager(region=region_name, profile=profile)
    return manager.get_client(service_name)