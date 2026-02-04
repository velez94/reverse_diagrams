"""Describe SSO."""
import logging
from typing import List, Dict, Any, Optional

from .client_manager import get_client_manager
from .exceptions import AWSServiceError
from ..utils.progress import track_operation
from ..config import get_config

logger = logging.getLogger(__name__)


def list_instances(region: str) -> List[Dict[str, Any]]:
    """
    List all SSO instances in the region.

    Args:
        region: AWS region name

    Returns:
        List of SSO instances

    Raises:
        AWSServiceError: If the API call fails
    """
    client_manager = get_client_manager(region=region)
    
    with track_operation("Listing SSO instances") as task_id:
        response = client_manager.call_api("sso-admin", "list_instances")
        instances = response.get("Instances", [])
        logger.info(f"Found {len(instances)} SSO instances")
        return instances


def list_account_assignments(
    instance_arn: str, 
    account_id: str, 
    permission_set_arn: str, 
    region: str
) -> List[Dict[str, Any]]:
    """
    List all account assignments for a permission set.

    Args:
        instance_arn: SSO instance ARN
        account_id: AWS account ID
        permission_set_arn: Permission set ARN
        region: AWS region name

    Returns:
        List of account assignments
    """
    client_manager = get_client_manager(region=region)
    config = get_config()
    
    try:
        # Use paginated API call for better handling of large result sets
        assignments = client_manager.paginate_api_call(
            "sso-admin",
            "list_account_assignments",
            "AccountAssignments",
            InstanceArn=instance_arn,
            AccountId=account_id,
            PermissionSetArn=permission_set_arn,
            PaginationConfig={
                'MaxItems': config.pagination.max_items,
                'PageSize': config.pagination.default_page_size
            }
        )
        
        logger.debug(f"Retrieved {len(assignments)} account assignments for account {account_id}")
        return assignments
        
    except Exception as e:
        logger.error(f"Failed to list account assignments for account {account_id}: {e}")
        raise AWSServiceError(f"Failed to list account assignments: {e}")


def list_permissions_set(instance_arn: str, region: str) -> List[str]:
    """
    List all permission sets in an SSO instance.

    Args:
        instance_arn: SSO instance ARN
        region: AWS region name

    Returns:
        List of permission set ARNs
    """
    client_manager = get_client_manager(region=region)
    config = get_config()
    
    with track_operation("Listing permission sets") as task_id:
        try:
            permission_sets = client_manager.paginate_api_call(
                "sso-admin",
                "list_permission_sets",
                "PermissionSets",
                InstanceArn=instance_arn,
                PaginationConfig={
                    'MaxItems': config.pagination.max_items,
                    'PageSize': config.pagination.default_page_size
                }
            )
            
            logger.info(f"Found {len(permission_sets)} permission sets")
            return permission_sets
            
        except Exception as e:
            logger.error(f"Failed to list permission sets: {e}")
            raise AWSServiceError(f"Failed to list permission sets: {e}")


def list_permission_provisioned(account_id: str, instance_arn: str, region: str) -> List[str]:
    """
    List permission sets provisioned to an account.

    Args:
        account_id: AWS account ID
        instance_arn: SSO instance ARN
        region: AWS region name

    Returns:
        List of provisioned permission set ARNs
    """
    client_manager = get_client_manager(region=region)
    
    try:
        response = client_manager.call_api(
            "sso-admin",
            "list_permission_sets_provisioned_to_account",
            InstanceArn=instance_arn,
            AccountId=account_id
        )
        
        permission_sets = response.get("PermissionSets", [])
        logger.debug(f"Found {len(permission_sets)} provisioned permission sets for account {account_id}")
        return permission_sets
        
    except Exception as e:
        logger.error(f"Failed to list provisioned permission sets for account {account_id}: {e}")
        raise AWSServiceError(f"Failed to list provisioned permission sets: {e}")


def extends_permissions_set(
    permissions_sets: List[str], 
    store_arn: str, 
    region: str
) -> Dict[str, str]:
    """
    Get detailed information for permission sets.

    Args:
        permissions_sets: List of permission set ARNs
        store_arn: SSO instance ARN
        region: AWS region name

    Returns:
        Dictionary mapping permission set ARN to name
    """
    client_manager = get_client_manager(region=region)
    permissions_map = {}
    
    with track_operation(f"Getting details for {len(permissions_sets)} permission sets") as task_id:
        for i, permission_set_arn in enumerate(permissions_sets):
            try:
                response = client_manager.call_api(
                    "sso-admin",
                    "describe_permission_set",
                    InstanceArn=store_arn,
                    PermissionSetArn=permission_set_arn
                )
                
                permission_set = response.get("PermissionSet", {})
                permissions_map[permission_set_arn] = permission_set.get("Name", "Unknown")
                
                # Update progress
                if i % 5 == 0:  # Update every 5 items to avoid too frequent updates
                    client_manager._progress_tracker.update_progress(task_id, advance=5)
                
            except Exception as e:
                logger.warning(f"Failed to describe permission set {permission_set_arn}: {e}")
                permissions_map[permission_set_arn] = "Unknown"
    
    logger.info(f"Retrieved details for {len(permissions_map)} permission sets")
    return permissions_map


# Backward compatibility function
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
    from .client_manager import client as new_client
    return new_client(service_name, region_name, profile)
