"""Data loader for the Interactive Identity Center Explorer.

This module handles loading and integrating data from multiple JSON sources:
- organizations_complete.json: AWS Organizations structure
- account_assignments.json: IAM Identity Center permission assignments
- groups.json: IAM Identity Center group memberships
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .models import (
    Account,
    Assignment,
    ExplorerData,
    Group,
    OrganizationalUnit,
    OrganizationTree,
    PermissionSet,
    User,
    ValidationWarning,
)

logger = logging.getLogger(__name__)


class DataLoaderError(Exception):
    """Base exception for data loader errors."""
    pass


class MissingFileError(DataLoaderError):
    """Raised when a required JSON file is missing."""
    pass


class InvalidDataError(DataLoaderError):
    """Raised when JSON data is invalid or malformed."""
    pass


class DataLoader:
    """Loads and integrates AWS Organizations and IAM Identity Center data."""
    
    def __init__(self, json_dir: str):
        """
        Initialize the data loader.
        
        Args:
            json_dir: Directory containing JSON data files
        """
        self.json_dir = Path(json_dir)
        self.validation_warnings: List[str] = []
        
        if not self.json_dir.exists():
            raise DataLoaderError(f"JSON directory does not exist: {json_dir}")
        
        if not self.json_dir.is_dir():
            raise DataLoaderError(f"Path is not a directory: {json_dir}")
    
    def load_all_data(self) -> ExplorerData:
        """
        Load and integrate all JSON data sources.
        
        Returns:
            ExplorerData: Unified data model
            
        Raises:
            MissingFileError: If organizations_complete.json is missing
            InvalidDataError: If JSON data is malformed
        """
        logger.info(f"Loading data from {self.json_dir}")
        
        # Load organization structure (required)
        organization = self.load_organizations()
        
        # Load account assignments (optional - graceful degradation)
        assignments_by_account = self.load_account_assignments()
        
        # Load groups (optional - graceful degradation)
        groups_by_id = self.load_groups()
        
        # Create unified data model
        explorer_data = ExplorerData(
            organization=organization,
            assignments_by_account=assignments_by_account,
            groups_by_id=groups_by_id,
            validation_warnings=self.validation_warnings
        )
        
        # Validate data integrity
        self._validate_data_integrity(explorer_data)
        
        logger.info(f"Data loading complete. Loaded {len(organization.all_accounts)} accounts, "
                   f"{len(assignments_by_account)} accounts with assignments, "
                   f"{len(groups_by_id)} groups")
        
        if self.validation_warnings:
            logger.warning(f"Found {len(self.validation_warnings)} validation warnings")
            for warning in self.validation_warnings[:5]:  # Show first 5
                logger.warning(f"  - {warning}")
            if len(self.validation_warnings) > 5:
                logger.warning(f"  ... and {len(self.validation_warnings) - 5} more warnings")
        
        return explorer_data
    
    def load_organizations(self) -> OrganizationTree:
        """
        Load and parse organizations_complete.json.
        
        Returns:
            OrganizationTree: Parsed organization structure
            
        Raises:
            MissingFileError: If file is missing
            InvalidDataError: If JSON is malformed
        """
        org_file = self.json_dir / "organizations_complete.json"
        
        if not org_file.exists():
            raise MissingFileError(
                f"Required file not found: {org_file}\n"
                f"Please run 'reverse_diagrams -o' to generate organization data first."
            )
        
        try:
            with open(org_file, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise InvalidDataError(f"Invalid JSON in {org_file}: {e}")
        except Exception as e:
            raise DataLoaderError(f"Error reading {org_file}: {e}")
        
        return self._parse_organization_structure(data)
    
    def load_account_assignments(self) -> Dict[str, List[Assignment]]:
        """
        Load and parse account_assignments.json.
        
        Returns:
            Dict mapping account IDs to lists of assignments
            
        Note:
            If file is missing, returns empty dict and logs warning
        """
        assignments_file = self.json_dir / "account_assignments.json"
        
        if not assignments_file.exists():
            logger.warning(f"account_assignments.json not found in {self.json_dir}. "
                          f"Accounts will be shown without assignment information.")
            return {}
        
        try:
            with open(assignments_file, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {assignments_file}: {e}")
            self.validation_warnings.append(f"Could not parse account_assignments.json: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error reading {assignments_file}: {e}")
            self.validation_warnings.append(f"Could not read account_assignments.json: {e}")
            return {}
        
        return self._parse_account_assignments(data)
    
    def load_groups(self) -> Dict[str, Group]:
        """
        Load and parse groups.json.
        
        Returns:
            Dict mapping group IDs to Group objects
            
        Note:
            If file is missing, returns empty dict and logs warning
        """
        groups_file = self.json_dir / "groups.json"
        
        if not groups_file.exists():
            logger.warning(f"groups.json not found in {self.json_dir}. "
                          f"Group membership details will not be available.")
            return {}
        
        try:
            with open(groups_file, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {groups_file}: {e}")
            self.validation_warnings.append(f"Could not parse groups.json: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error reading {groups_file}: {e}")
            self.validation_warnings.append(f"Could not read groups.json: {e}")
            return {}
        
        return self._parse_groups(data)
    
    def _parse_organization_structure(self, data: dict) -> OrganizationTree:
        """Parse organizations_complete.json into OrganizationTree."""
        root_id = data.get("rootId", "")
        master_account_id = data.get("masterAccountId")
        
        # Parse root accounts
        root_accounts = []
        no_ou_accounts = data.get("noOutAccounts", [])
        for acc_data in no_ou_accounts:
            account = self._parse_account(acc_data)
            if account:
                root_accounts.append(account)
        
        # Parse organizational units
        root_ous = []
        ou_data = data.get("organizationalUnits", {})
        for ou_name, ou_info in ou_data.items():
            ou = self._parse_ou(ou_name, ou_info)
            if ou:
                root_ous.append(ou)
        
        # Build all_accounts dictionary
        all_accounts = {}
        for account in root_accounts:
            all_accounts[account.id] = account
        
        for ou in root_ous:
            for account in ou.get_all_accounts():
                all_accounts[account.id] = account
        
        return OrganizationTree(
            root_id=root_id,
            master_account_id=master_account_id,
            root_ous=root_ous,
            root_accounts=root_accounts,
            all_accounts=all_accounts
        )
    
    def _parse_ou(self, ou_name: str, ou_data: dict) -> Optional[OrganizationalUnit]:
        """Parse a single organizational unit."""
        try:
            ou_id = ou_data.get("Id", "")
            name = ou_data.get("Name", ou_name)
            
            # Parse accounts in this OU
            accounts = []
            accounts_data = ou_data.get("accounts", {})
            for acc_name, acc_info in accounts_data.items():
                account = Account(
                    id=acc_info.get("account", ""),
                    name=acc_info.get("name", acc_name),
                    email="",  # Not available in organizations_complete.json
                    parent_ou_id=ou_id
                )
                if account.id:
                    accounts.append(account)
            
            # Parse nested OUs
            children_ous = []
            nested_ous_data = ou_data.get("nestedOus", {})
            for nested_name, nested_info in nested_ous_data.items():
                nested_ou = self._parse_ou(nested_name, nested_info)
                if nested_ou:
                    children_ous.append(nested_ou)
            
            return OrganizationalUnit(
                id=ou_id,
                name=name,
                children_ous=children_ous,
                accounts=accounts
            )
        except Exception as e:
            logger.error(f"Error parsing OU {ou_name}: {e}")
            self.validation_warnings.append(f"Could not parse OU {ou_name}: {e}")
            return None
    
    def _parse_account(self, acc_data: dict) -> Optional[Account]:
        """Parse a single account."""
        try:
            return Account(
                id=acc_data.get("account", ""),
                name=acc_data.get("name", ""),
                email=""  # Not available in organizations_complete.json
            )
        except Exception as e:
            logger.error(f"Error parsing account: {e}")
            return None
    
    def _parse_account_assignments(self, data: dict) -> Dict[str, List[Assignment]]:
        """Parse account_assignments.json into assignments by account."""
        assignments_by_account = {}
        
        for account_name, assignments_list in data.items():
            account_id = None
            assignments = []
            
            for assignment_data in assignments_list:
                try:
                    # Extract account ID from first assignment
                    if account_id is None:
                        account_id = assignment_data.get("AccountId", "")
                    
                    permission_set = PermissionSet(
                        arn=assignment_data.get("PermissionSetArn", ""),
                        name=assignment_data.get("PermissionSetName", "")
                    )
                    
                    assignment = Assignment(
                        account_id=account_id,
                        permission_set=permission_set,
                        principal_type=assignment_data.get("PrincipalType", ""),
                        principal_id=assignment_data.get("PrincipalId", ""),
                        principal_name=assignment_data.get("GroupName") or assignment_data.get("UserName", "")
                    )
                    
                    if assignment.validate():
                        assignments.append(assignment)
                    else:
                        self.validation_warnings.append(
                            f"Invalid assignment for account {account_name}: missing required fields"
                        )
                except Exception as e:
                    logger.error(f"Error parsing assignment for {account_name}: {e}")
                    self.validation_warnings.append(f"Could not parse assignment for {account_name}: {e}")
            
            if account_id and assignments:
                assignments_by_account[account_id] = assignments
        
        return assignments_by_account
    
    def _parse_groups(self, data: dict) -> Dict[str, Group]:
        """Parse groups.json into groups by ID."""
        groups_by_id = {}
        
        # Handle both list and dict formats
        if isinstance(data, list):
            # List format: [{"group_id": "...", "group_name": "...", "members": [...]}]
            for group_data in data:
                group = self._parse_single_group(group_data)
                if group:
                    groups_by_id[group.id] = group
        elif isinstance(data, dict):
            # Dict format: {"group_id": {"GroupId": "...", "DisplayName": "...", "Members": [...]}}
            for group_id, group_data in data.items():
                group = self._parse_single_group(group_data, fallback_id=group_id)
                if group:
                    groups_by_id[group.id] = group
        
        return groups_by_id
    
    def _parse_single_group(self, group_data: dict, fallback_id: Optional[str] = None) -> Optional[Group]:
        """Parse a single group."""
        try:
            group_id = group_data.get("group_id") or group_data.get("GroupId") or fallback_id
            group_name = group_data.get("group_name") or group_data.get("DisplayName", "")
            description = group_data.get("description") or group_data.get("Description")
            
            # Parse members
            members = []
            members_data = group_data.get("members", []) or group_data.get("Members", [])
            for member_data in members_data:
                user = self._parse_user(member_data)
                if user:
                    members.append(user)
            
            if not group_id or not group_name:
                self.validation_warnings.append(f"Group missing id or name: {group_data}")
                return None
            
            return Group(
                id=group_id,
                name=group_name,
                description=description,
                members=members
            )
        except Exception as e:
            logger.error(f"Error parsing group: {e}")
            self.validation_warnings.append(f"Could not parse group: {e}")
            return None
    
    def _parse_user(self, user_data: dict) -> Optional[User]:
        """Parse a single user."""
        try:
            # Handle nested MemberId structure
            if "MemberId" in user_data:
                member_id = user_data["MemberId"]
                user_id = member_id.get("UserId", "")
                username = member_id.get("UserName", "")
            else:
                user_id = user_data.get("UserId", "")
                username = user_data.get("UserName", "")
            
            email = user_data.get("Email")
            display_name = user_data.get("DisplayName")
            
            if not user_id or not username:
                return None
            
            return User(
                id=user_id,
                username=username,
                email=email,
                display_name=display_name
            )
        except Exception as e:
            logger.error(f"Error parsing user: {e}")
            return None
    
    def _validate_data_integrity(self, explorer_data: ExplorerData) -> None:
        """Validate cross-references between data sources."""
        # Validate that all account IDs in assignments exist in organization
        for account_id in explorer_data.assignments_by_account.keys():
            if account_id not in explorer_data.organization.all_accounts:
                self.validation_warnings.append(
                    f"Account {account_id} has assignments but is not in organization structure"
                )
        
        # Validate that all group IDs in assignments exist in groups data
        for account_id, assignments in explorer_data.assignments_by_account.items():
            for assignment in assignments:
                if assignment.is_group_assignment():
                    if assignment.principal_id not in explorer_data.groups_by_id:
                        self.validation_warnings.append(
                            f"Group {assignment.principal_name} ({assignment.principal_id}) "
                            f"assigned to account {account_id} but not found in groups data"
                        )
