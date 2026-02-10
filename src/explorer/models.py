"""Data models for the Interactive Identity Center Explorer."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class User:
    """Represents an IAM Identity Center user."""
    
    id: str
    username: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    
    def validate(self) -> bool:
        """Validate user data integrity."""
        return bool(self.id and self.username)
    
    def get_display_text(self) -> str:
        """Get formatted display text for the user."""
        if self.display_name:
            return f"{self.display_name} ({self.email or self.username})"
        return self.email or self.username


@dataclass
class Group:
    """Represents an IAM Identity Center group."""
    
    id: str
    name: str
    description: Optional[str] = None
    members: List[User] = field(default_factory=list)
    
    def validate(self) -> bool:
        """Validate group data integrity."""
        if not (self.id and self.name):
            return False
        return all(member.validate() for member in self.members)
    
    def get_member_count(self) -> int:
        """Get the number of members in the group."""
        return len(self.members)


@dataclass
class PermissionSet:
    """Represents an IAM Identity Center permission set."""
    
    arn: str
    name: str
    
    def validate(self) -> bool:
        """Validate permission set data integrity."""
        return bool(self.arn and self.name)


@dataclass
class Assignment:
    """Represents an account assignment (permission set + principal)."""
    
    account_id: str
    permission_set: PermissionSet
    principal_type: str  # "GROUP" or "USER"
    principal_id: str
    principal_name: str
    
    def validate(self) -> bool:
        """Validate assignment data integrity."""
        if not (self.account_id and self.principal_id and self.principal_name):
            return False
        if self.principal_type not in ["GROUP", "USER"]:
            return False
        return self.permission_set.validate()
    
    def is_group_assignment(self) -> bool:
        """Check if this is a group-based assignment."""
        return self.principal_type == "GROUP"
    
    def is_user_assignment(self) -> bool:
        """Check if this is a direct user assignment."""
        return self.principal_type == "USER"


@dataclass
class Account:
    """Represents an AWS account."""
    
    id: str
    name: str
    email: str = ""
    status: str = "ACTIVE"
    parent_ou_id: Optional[str] = None
    
    def validate(self) -> bool:
        """Validate account data integrity."""
        # Email is optional since organizations_complete.json doesn't include it
        return bool(self.id and self.name)
    
    def get_display_text(self) -> str:
        """Get formatted display text for the account."""
        return f"{self.name} ({self.id})"


@dataclass
class OrganizationalUnit:
    """Represents an AWS Organizational Unit."""
    
    id: str
    name: str
    parent_id: Optional[str] = None
    children_ous: List['OrganizationalUnit'] = field(default_factory=list)
    accounts: List[Account] = field(default_factory=list)
    
    def validate(self) -> bool:
        """Validate OU data integrity."""
        if not (self.id and self.name):
            return False
        # Validate all children
        for child_ou in self.children_ous:
            if not child_ou.validate():
                return False
        for account in self.accounts:
            if not account.validate():
                return False
        return True
    
    def get_all_accounts(self) -> List[Account]:
        """Get all accounts in this OU and its children recursively."""
        accounts = list(self.accounts)
        for child_ou in self.children_ous:
            accounts.extend(child_ou.get_all_accounts())
        return accounts
    
    def get_child_count(self) -> int:
        """Get total count of child OUs and accounts."""
        return len(self.children_ous) + len(self.accounts)
    
    def is_empty(self) -> bool:
        """Check if this OU has no children or accounts."""
        return self.get_child_count() == 0


@dataclass
class OrganizationTree:
    """Represents the complete AWS Organizations structure."""
    
    root_id: str
    master_account_id: Optional[str] = None
    root_ous: List[OrganizationalUnit] = field(default_factory=list)
    root_accounts: List[Account] = field(default_factory=list)
    all_accounts: Dict[str, Account] = field(default_factory=dict)
    
    def validate(self) -> bool:
        """Validate organization tree data integrity."""
        if not self.root_id:
            return False
        # Validate all root OUs
        for ou in self.root_ous:
            if not ou.validate():
                return False
        # Validate all root accounts
        for account in self.root_accounts:
            if not account.validate():
                return False
        return True
    
    def get_account_by_id(self, account_id: str) -> Optional[Account]:
        """Get an account by its ID."""
        return self.all_accounts.get(account_id)
    
    def get_total_account_count(self) -> int:
        """Get total number of accounts in the organization."""
        return len(self.all_accounts)
    
    def get_total_ou_count(self) -> int:
        """Get total number of OUs in the organization."""
        count = len(self.root_ous)
        for ou in self.root_ous:
            count += self._count_nested_ous(ou)
        return count
    
    def _count_nested_ous(self, ou: OrganizationalUnit) -> int:
        """Recursively count nested OUs."""
        count = len(ou.children_ous)
        for child_ou in ou.children_ous:
            count += self._count_nested_ous(child_ou)
        return count


@dataclass
class ExplorerData:
    """Unified data model combining all explorer data sources."""
    
    organization: OrganizationTree
    assignments_by_account: Dict[str, List[Assignment]] = field(default_factory=dict)
    groups_by_id: Dict[str, Group] = field(default_factory=dict)
    validation_warnings: List[str] = field(default_factory=list)
    
    def validate(self) -> bool:
        """Validate explorer data integrity."""
        return self.organization.validate()
    
    def get_assignments_for_account(self, account_id: str) -> List[Assignment]:
        """Get all assignments for a specific account."""
        return self.assignments_by_account.get(account_id, [])
    
    def get_group_by_id(self, group_id: str) -> Optional[Group]:
        """Get a group by its ID."""
        return self.groups_by_id.get(group_id)
    
    def has_assignments(self, account_id: str) -> bool:
        """Check if an account has any assignments."""
        return len(self.get_assignments_for_account(account_id)) > 0
    
    def get_assignment_summary(self, account_id: str) -> Dict[str, int]:
        """Get summary statistics for an account's assignments."""
        assignments = self.get_assignments_for_account(account_id)
        
        permission_sets = set()
        groups = set()
        users = set()
        
        for assignment in assignments:
            permission_sets.add(assignment.permission_set.name)
            if assignment.is_group_assignment():
                groups.add(assignment.principal_id)
                # Count users in the group
                group = self.get_group_by_id(assignment.principal_id)
                if group:
                    users.update(user.id for user in group.members)
            else:
                users.add(assignment.principal_id)
        
        return {
            "permission_sets": len(permission_sets),
            "groups": len(groups),
            "users": len(users),
        }


@dataclass
class SelectableItem:
    """Represents an item that can be selected in the navigation."""
    
    display_text: str
    item_type: str  # "OU", "ACCOUNT", "BACK", "EXIT"
    item_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_ou(self) -> bool:
        """Check if this is an OU item."""
        return self.item_type == "OU"
    
    def is_account(self) -> bool:
        """Check if this is an account item."""
        return self.item_type == "ACCOUNT"
    
    def is_back(self) -> bool:
        """Check if this is a back navigation item."""
        return self.item_type == "BACK"
    
    def is_exit(self) -> bool:
        """Check if this is an exit item."""
        return self.item_type == "EXIT"


@dataclass
class NavigationView:
    """Represents the current navigation view state."""
    
    level: str  # "ROOT", "OU", "ACCOUNT_DETAIL"
    items: List[SelectableItem] = field(default_factory=list)
    breadcrumb: str = "Root"
    title: str = "AWS Organizations Explorer"
    
    def is_root_level(self) -> bool:
        """Check if at root level."""
        return self.level == "ROOT"
    
    def is_ou_level(self) -> bool:
        """Check if at OU level."""
        return self.level == "OU"
    
    def is_account_detail(self) -> bool:
        """Check if showing account details."""
        return self.level == "ACCOUNT_DETAIL"
    
    def has_items(self) -> bool:
        """Check if there are any selectable items."""
        return len(self.items) > 0


@dataclass
class ValidationWarning:
    """Represents a data validation warning."""
    
    message: str
    severity: str = "WARNING"  # "WARNING", "ERROR"
    context: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        """Get string representation of the warning."""
        return f"[{self.severity}] {self.message}"
