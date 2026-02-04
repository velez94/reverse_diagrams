"""AWS Organizations plugin for generating organizational structure diagrams."""
import logging
from typing import Dict, Any, List
from pathlib import Path

from src.plugins.base import AWSServicePlugin, PluginMetadata
from src.aws.client_manager import AWSClientManager
from src.models import DiagramConfig
from src.utils.concurrent import get_concurrent_processor
from src.utils.progress import get_progress_tracker
from src.dgms.graph_mapper import create_mapper, find_ou_name

logger = logging.getLogger(__name__)


class OrganizationsPlugin(AWSServicePlugin):
    """Plugin for AWS Organizations service diagram generation."""
    
    @property
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name="organizations",
            version="1.0.0",
            description="Generate diagrams for AWS Organizations structure, accounts, and OUs",
            author="Reverse Diagrams Team",
            aws_services=["organizations"],
            dependencies=[]
        )
    
    def collect_data(self, client_manager: AWSClientManager, region: str, **kwargs) -> Dict[str, Any]:
        """
        Collect AWS Organizations data.
        
        Args:
            client_manager: AWS client manager
            region: AWS region
            **kwargs: Additional parameters
            
        Returns:
            Dictionary containing Organizations data
        """
        logger.debug(f"Collecting AWS Organizations data from region {region}")
        progress = get_progress_tracker()
        
        data = {
            "region": region,
            "organization": {},
            "roots": [],
            "organizational_units": [],
            "accounts": [],
            "organizations_complete": {}
        }
        
        try:
            # Get organization details
            progress.show_success("🏢 Getting Organization Info")
            org_response = client_manager.call_api("organizations", "describe_organization")
            data["organization"] = org_response.get("Organization", {})
            logger.debug(f"Retrieved organization: {data['organization'].get('Id', 'Unknown')}")
            
            # Get roots
            roots_response = client_manager.call_api("organizations", "list_roots")
            data["roots"] = roots_response.get("Roots", [])
            logger.debug(f"Found {len(data['roots'])} organization roots")
            
            if not data["roots"]:
                raise ValueError("No organization roots found")
            
            root_id = data["roots"][0]["Id"]
            
            # Get organizational units recursively
            progress.show_success("📋 Listing Organizational Units")
            data["organizational_units"] = self._list_organizational_units_recursive(
                client_manager, root_id, region
            )
            logger.debug(f"Found {len(data['organizational_units'])} organizational units")
            
            # Get accounts with parent information
            progress.show_success("👥 Getting Account Information")
            data["accounts"] = self._list_accounts_with_parents(client_manager, region)
            logger.debug(f"Found {len(data['accounts'])} accounts")
            
            # Create complete organization map
            data["organizations_complete"] = self._create_organization_complete_map(
                root_id,
                data["organization"],
                data["organizational_units"],
                data["accounts"]
            )
            
            progress.show_summary(
                "Organization Summary",
                [
                    f"Organization ID: {data['organization'].get('Id', 'Unknown')}",
                    f"Master Account: {data['organization'].get('MasterAccountId', 'Unknown')}",
                    f"Organizational Units: {len(data['organizational_units'])}",
                    f"Accounts: {len(data['accounts'])}"
                ]
            )
            
        except Exception as e:
            logger.error(f"Failed to collect Organizations data: {e}")
            raise
        
        return data
    
    def _list_organizational_units_recursive(
        self, 
        client_manager: AWSClientManager, 
        parent_id: str, 
        region: str,
        depth: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List organizational units recursively.
        
        Args:
            client_manager: AWS client manager
            parent_id: Parent ID to start from
            region: AWS region
            depth: Current recursion depth
            
        Returns:
            List of all organizational units
        """
        if depth > 10:  # Prevent infinite recursion
            logger.warning(f"Maximum recursion depth reached for parent {parent_id}")
            return []
        
        all_ous = []
        
        try:
            # Get OUs for current parent using pagination
            ous = client_manager.paginate_api_call(
                "organizations",
                "list_organizational_units_for_parent",
                "OrganizationalUnits",
                ParentId=parent_id
            )
            
            for ou in ous:
                # Add parent information
                try:
                    parents_response = client_manager.call_api(
                        "organizations",
                        "list_parents",
                        ChildId=ou["Id"]
                    )
                    ou["Parents"] = parents_response.get("Parents", [])
                except Exception as e:
                    logger.warning(f"Failed to get parents for OU {ou['Id']}: {e}")
                    ou["Parents"] = []
                
                all_ous.append(ou)
                
                # Recursively get child OUs
                child_ous = self._list_organizational_units_recursive(
                    client_manager, ou["Id"], region, depth + 1
                )
                all_ous.extend(child_ous)
                
        except Exception as e:
            logger.warning(f"Failed to get OUs for parent {parent_id}: {e}")
        
        return all_ous
    
    def _list_accounts_with_parents(
        self, 
        client_manager: AWSClientManager, 
        region: str
    ) -> List[Dict[str, Any]]:
        """
        List all accounts with parent information.
        
        Args:
            client_manager: AWS client manager
            region: AWS region
            
        Returns:
            List of accounts with parent information
        """
        progress = get_progress_tracker()
        
        # Get all accounts using pagination
        accounts = client_manager.paginate_api_call(
            "organizations",
            "list_accounts",
            "Accounts"
        )
        
        logger.debug(f"Found {len(accounts)} accounts in organization")
        
        # Add parent information for each account
        indexed_accounts = []
        
        with progress.track_operation(f"Getting parent info for {len(accounts)} accounts", total=len(accounts)) as task_id:
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
                    
                    progress.update_progress(task_id)
                    
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
    
    def _create_organization_complete_map(
        self,
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
            Complete organization structure
        """
        organizations_complete = {
            "rootId": root_id,
            "masterAccountId": organization.get("MasterAccountId", ""),
            "noOutAccounts": [],
            "organizationalUnits": {},
        }
        
        # Build OU hierarchy
        for ou in organizational_units:
            for parent in ou.get("Parents", []):
                if parent["Type"] == "ROOT":
                    organizations_complete["organizationalUnits"][ou["Name"]] = {
                        "Id": ou["Id"],
                        "Name": ou["Name"],
                        "accounts": {},
                        "nestedOus": {},
                    }
        
        # Add accounts to appropriate OUs or root
        for account in accounts:
            for parent in account.get("parents", []):
                if parent["Type"] == "ROOT":
                    organizations_complete["noOutAccounts"].append({
                        "account": account["account"],
                        "name": account["name"]
                    })
                elif parent["Type"] == "ORGANIZATIONAL_UNIT":
                    # Find the OU name
                    ou_name = find_ou_name(organizational_units, parent["Id"])
                    if ou_name and ou_name in organizations_complete["organizationalUnits"]:
                        organizations_complete["organizationalUnits"][ou_name]["accounts"][account["name"]] = {
                            "account": account["account"],
                            "name": account["name"]
                        }
        
        return organizations_complete
    
    def generate_diagram_code(self, data: Dict[str, Any], config: DiagramConfig) -> str:
        """
        Generate diagram code for AWS Organizations.
        
        Args:
            data: Organizations data collected from AWS
            config: Diagram configuration
            
        Returns:
            Python code for generating Organizations diagram
        """
        logger.debug("Generating AWS Organizations diagram code")
        
        from src.dgms.graph_template import graph_template
        
        # Start with the template
        code_lines = [
            "from diagrams import Diagram, Cluster",
            "from diagrams.aws.management import Organizations, OrganizationsAccount, OrganizationsOrganizationalUnit",
            "",
            f'with Diagram("{config.title}", show=False, direction="{config.direction}"):'
        ]
        
        # Add organization root
        organization = data.get("organization", {})
        roots = data.get("roots", [])
        organizational_units = data.get("organizational_units", [])
        accounts = data.get("accounts", [])
        
        if roots:
            root_id = roots[0]["Id"]
            code_lines.extend([
                "    with Cluster('Organizations'):",
                f"        oo = Organizations('{organization.get('Id', 'Unknown')}\\n{organization.get('MasterAccountId', 'Unknown')}\\n{root_id}')"
            ])
            
            # Add organizational units
            for ou in organizational_units:
                ou_name_safe = self._format_name_for_code(ou["Name"])
                code_lines.append(
                    f"        ou_{ou_name_safe} = OrganizationsOrganizationalUnit(\"{ou['Id']}\\n{ou['Name']}\")"
                )
                
                # Add relationships
                for parent in ou.get("Parents", []):
                    if parent["Type"] == "ROOT":
                        code_lines.append(f"        oo >> ou_{ou_name_safe}")
                    elif parent["Type"] == "ORGANIZATIONAL_UNIT":
                        parent_name = find_ou_name(organizational_units, parent["Id"])
                        if parent_name:
                            parent_name_safe = self._format_name_for_code(parent_name)
                            code_lines.append(f"        ou_{parent_name_safe} >> ou_{ou_name_safe}")
            
            # Add accounts
            for account in accounts:
                account_name_safe = self._format_name_for_code(account["name"])
                for parent in account.get("parents", []):
                    if parent["Type"] == "ROOT":
                        code_lines.append(
                            f"        oo >> OrganizationsAccount(\"{account['account']}\\n{self._split_long_name(account['name'])}\")"
                        )
                    elif parent["Type"] == "ORGANIZATIONAL_UNIT":
                        ou_name = find_ou_name(organizational_units, parent["Id"])
                        if ou_name:
                            ou_name_safe = self._format_name_for_code(ou_name)
                            code_lines.append(
                                f"        ou_{ou_name_safe} >> OrganizationsAccount(\"{account['account']}\\n{self._split_long_name(account['name'])}\")"
                            )
        
        return "\n".join(code_lines)
    
    def _format_name_for_code(self, name: str) -> str:
        """Format name for use in Python code."""
        import re
        # Remove special characters and spaces
        formatted = re.sub(r'[^\w]', '', name)
        return formatted if formatted else "Unknown"
    
    def _split_long_name(self, name: str) -> str:
        """Split long names for better display."""
        if len(name) > 17:
            return name[:16] + "\\n" + name[16:]
        return name
    
    def get_required_permissions(self) -> List[str]:
        """Get required AWS permissions for Organizations plugin."""
        return [
            "organizations:DescribeOrganization",
            "organizations:ListRoots",
            "organizations:ListOrganizationalUnitsForParent",
            "organizations:ListAccounts",
            "organizations:ListParents"
        ]