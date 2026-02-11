"""Describe Organizations."""
import logging
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

import emoji
from colorama import Fore

from .client_manager import get_client_manager
from .exceptions import AWSServiceError
from ..dgms.graph_mapper import create_file, create_mapper, find_ou_name
from ..dgms.graph_template import graph_template
from ..reports.save_results import save_results
from ..utils.progress import track_operation, get_progress_tracker
from ..config import get_config
from ..models import AWSAccount, OrganizationalUnit, AWSOrganization, validate_aws_response

logger = logging.getLogger(__name__)


def describe_organization(region: str) -> Dict[str, Any]:
    """
    Describe the organization.

    Args:
        region: AWS Region

    Returns:
        Organization details

    Raises:
        AWSServiceError: If the API call fails
    """
    client_manager = get_client_manager(region=region)
    progress = get_progress_tracker()
    
    progress.show_success("🏢 Getting Organization Info")
    
    try:
        response = client_manager.call_api("organizations", "describe_organization")
        validate_aws_response(response, ["Organization"])
        
        organization = response["Organization"]
        logger.info(f"Retrieved organization: {organization.get('Id', 'Unknown')}")
        return organization
        
    except Exception as e:
        logger.error(f"Failed to describe organization: {e}")
        raise AWSServiceError(f"Failed to describe organization: {e}")


def list_roots(region: str) -> List[Dict[str, Any]]:
    """
    List the organization roots.

    Args:
        region: AWS Region

    Returns:
        List of root objects
    """
    client_manager = get_client_manager(region=region)
    
    try:
        response = client_manager.call_api("organizations", "list_roots")
        validate_aws_response(response, ["Roots"])
        
        roots = response["Roots"]
        logger.info(f"Found {len(roots)} organization roots")
        return roots
        
    except Exception as e:
        logger.error(f"Failed to list roots: {e}")
        raise AWSServiceError(f"Failed to list roots: {e}")


def list_organizational_units(parent_id: str, region: str) -> List[Dict[str, Any]]:
    """
    List organizational units recursively.

    Args:
        parent_id: Parent ID to start from
        region: AWS region

    Returns:
        List of all organizational units
    """
    client_manager = get_client_manager(region=region)
    config = get_config()
    all_ous = []
    
    def _get_ous_recursive(current_parent_id: str, depth: int = 0) -> None:
        """Recursively get all OUs."""
        if depth > 10:  # Prevent infinite recursion
            logger.warning(f"Maximum recursion depth reached for parent {current_parent_id}")
            return
        
        try:
            # Get OUs for current parent
            ous = client_manager.paginate_api_call(
                "organizations",
                "list_organizational_units_for_parent",
                "OrganizationalUnits",
                ParentId=current_parent_id,
                PaginationConfig={
                    'MaxItems': config.pagination.max_items,
                    'PageSize': config.pagination.default_page_size
                }
            )
            
            for ou in ous:
                # Add parent information
                parents_response = client_manager.call_api(
                    "organizations",
                    "list_parents",
                    ChildId=ou["Id"]
                )
                ou["Parents"] = parents_response.get("Parents", [])
                all_ous.append(ou)
                
                # Recursively get child OUs
                _get_ous_recursive(ou["Id"], depth + 1)
                
        except Exception as e:
            logger.warning(f"Failed to get OUs for parent {current_parent_id}: {e}")
    
    with track_operation("Listing organizational units") as task_id:
        _get_ous_recursive(parent_id)
    
    logger.info(f"Found {len(all_ous)} organizational units")
    return all_ous


def list_accounts(region: str) -> List[Dict[str, Any]]:
    """
    List all accounts in the organization.

    Args:
        region: AWS region

    Returns:
        List of account objects with parent information
    """
    client_manager = get_client_manager(region=region)
    config = get_config()
    
    with track_operation("Listing organization accounts") as task_id:
        try:
            # Get all accounts using pagination
            accounts = client_manager.paginate_api_call(
                "organizations",
                "list_accounts",
                "Accounts",
                PaginationConfig={
                    'MaxItems': config.pagination.max_items,
                    'PageSize': config.pagination.default_page_size
                }
            )
            
            logger.info(f"Found {len(accounts)} accounts in organization")
            
            # Add parent information for each account
            indexed_accounts = []
            progress = get_progress_tracker()
            
            with progress.track_operation(f"Getting parent info for {len(accounts)} accounts", total=len(accounts)) as parent_task:
                for i, account in enumerate(accounts):
                    try:
                        parents_response = client_manager.call_api(
                            "organizations",
                            "list_parents",
                            ChildId=account["Id"]
                        )
                        
                        indexed_accounts.append({
                            "account": account["Id"],
                            "name": account["Name"],
                            "email": account.get("Email", ""),
                            "status": account.get("Status", "ACTIVE"),
                            "parents": parents_response.get("Parents", [])
                        })
                        
                        progress.update_progress(parent_task)
                        
                    except Exception as e:
                        logger.warning(f"Failed to get parents for account {account['Id']}: {e}")
                        indexed_accounts.append({
                            "account": account["Id"],
                            "name": account["Name"],
                            "email": account.get("Email", ""),
                            "status": account.get("Status", "ACTIVE"),
                            "parents": []
                        })
            
            return indexed_accounts
            
        except Exception as e:
            logger.error(f"Failed to list accounts: {e}")
            raise AWSServiceError(f"Failed to list accounts: {e}")


def create_organization_complete_map(
    root_id: str,
    organization: Dict[str, Any],
    organizational_units: List[Dict[str, Any]],
    accounts: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Create a complete organization map with nested structure.

    Args:
        root_id: Organization root ID
        organization: Organization details
        organizational_units: List of OUs
        accounts: List of accounts

    Returns:
        Complete organization structure with properly nested OUs
    """
    # Create lookup dictionaries for efficient access
    ou_by_id = {ou["Id"]: ou for ou in organizational_units}
    accounts_by_parent = {}
    
    # Group accounts by their parent OU
    for account in accounts:
        for parent in account.get("parents", []):
            parent_id = parent["Id"]
            if parent_id not in accounts_by_parent:
                accounts_by_parent[parent_id] = []
            accounts_by_parent[parent_id].append(account)
    
    def build_ou_structure(ou_id: str) -> Dict[str, Any]:
        """Recursively build OU structure with nested OUs and accounts."""
        ou = ou_by_id.get(ou_id)
        if not ou:
            return {}
        
        ou_structure = {
            "Id": ou["Id"],
            "Name": ou["Name"],
            "accounts": {},
            "nestedOus": {},
        }
        
        # Add accounts directly under this OU
        if ou_id in accounts_by_parent:
            for account in accounts_by_parent[ou_id]:
                ou_structure["accounts"][account["name"]] = {
                    "account": account["account"],
                    "name": account["name"]
                }
        
        # Find and add nested OUs
        for child_ou in organizational_units:
            for parent in child_ou.get("Parents", []):
                if parent["Type"] == "ORGANIZATIONAL_UNIT" and parent["Id"] == ou_id:
                    # This is a child OU - recursively build its structure
                    child_structure = build_ou_structure(child_ou["Id"])
                    if child_structure:
                        ou_structure["nestedOus"][child_ou["Name"]] = child_structure
        
        return ou_structure
    
    organizations_complete = {
        "rootId": root_id,
        "masterAccountId": organization["MasterAccountId"],
        "noOutAccounts": [],
        "organizationalUnits": {},
    }
    
    # Add accounts directly under root
    if root_id in accounts_by_parent:
        for account in accounts_by_parent[root_id]:
            organizations_complete["noOutAccounts"].append({
                "account": account["account"],
                "name": account["name"]
            })
    
    # Build root-level OUs with their nested structures
    for ou in organizational_units:
        for parent in ou.get("Parents", []):
            if parent["Type"] == "ROOT":
                ou_structure = build_ou_structure(ou["Id"])
                if ou_structure:
                    organizations_complete["organizationalUnits"][ou["Name"]] = ou_structure
    
    return organizations_complete


def graph_organizations(diagrams_path: str, region: str, auto: bool) -> None:
    """
    Create organizations graph with improved error handling and progress tracking.

    Args:
        diagrams_path: Output directory path
        region: AWS region
        auto: Whether to automatically create diagrams
    """
    template_file = "graph_org.py"
    code_path = Path(diagrams_path) / "code"
    json_path = Path(diagrams_path) / "json"
    
    # Ensure directories exist
    code_path.mkdir(parents=True, exist_ok=True)
    json_path.mkdir(parents=True, exist_ok=True)
    
    progress = get_progress_tracker()
    
    try:
        # Create template file
        create_file(
            template_content=graph_template,
            file_name=template_file,
            directory_path=str(code_path),
        )
        
        # Get organization data
        organization = describe_organization(region=region)
        roots = list_roots(region=region)
        
        if not roots:
            raise AWSServiceError("No organization roots found")
        
        root_id = roots[0]["Id"]
        
        # Get organizational units
        progress.show_success("📋 Listing Organizational Units")
        organizational_units = list_organizational_units(parent_id=root_id, region=region)
        
        # Get accounts
        progress.show_success("👥 Getting Account Information")
        accounts = list_accounts(region=region)
        
        progress.show_summary(
            "Organization Summary",
            [
                f"Organization ID: {organization.get('Id', 'Unknown')}",
                f"Master Account: {organization.get('MasterAccountId', 'Unknown')}",
                f"Organizational Units: {len(organizational_units)}",
                f"Accounts: {len(accounts)}"
            ]
        )
        
        # Save basic accounts data
        save_results(
            results=accounts,
            filename="organizations.json",
            directory_path=str(json_path)
        )
        
        # Create diagram mapper
        create_mapper(
            template_file=str(code_path / template_file),
            org=organization,
            root_id=root_id,
            list_ous=organizational_units,
            list_accounts=accounts,
        )
        
        # Create complete organization map
        organizations_complete = create_organization_complete_map(
            root_id=root_id,
            organization=organization,
            organizational_units=organizational_units,
            accounts=accounts
        )
        
        save_results(
            results=organizations_complete,
            filename="organizations_complete.json",
            directory_path=str(json_path)
        )
        
        if auto:
            progress.show_success(f"🎨 Creating diagrams in {code_path}")
            command = os.system(f"cd {code_path} && python3 {template_file}")
            if command != 0:
                progress.show_error("Failed to create diagrams", f"Command exit code: {command}")
            else:
                progress.show_success("Diagrams created successfully")
        else:
            progress.show_success(
                "Ready to create diagrams",
                f"Run: python3 {code_path / template_file}"
            )
            
    except Exception as e:
        logger.error(f"Failed to create organization graph: {e}")
        progress.show_error("Organization diagram generation failed", str(e))
        raise
