"""Data models with validation for AWS resources."""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
import re


class PrincipalType(Enum):
    """Principal types for account assignments."""
    USER = "USER"
    GROUP = "GROUP"


class AccountStatus(Enum):
    """AWS account status."""
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    PENDING_CLOSURE = "PENDING_CLOSURE"


@dataclass
class AWSAccount:
    """AWS Account model with validation."""
    id: str
    name: str
    email: str
    status: AccountStatus = AccountStatus.ACTIVE
    
    def __post_init__(self):
        """Validate account data after initialization."""
        if not self.id or not self.id.isdigit() or len(self.id) != 12:
            raise ValueError(f"Invalid AWS account ID: {self.id}. Must be 12 digits.")
        
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Account name cannot be empty.")
        
        if not self._is_valid_email(self.email):
            raise ValueError(f"Invalid email format: {self.email}")
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))


@dataclass
class OrganizationalUnit:
    """Organizational Unit model."""
    id: str
    name: str
    parent_id: Optional[str] = None
    accounts: List[AWSAccount] = None
    child_ous: List['OrganizationalUnit'] = None
    
    def __post_init__(self):
        """Initialize collections if None."""
        if self.accounts is None:
            self.accounts = []
        if self.child_ous is None:
            self.child_ous = []
        
        if not self.id or not self.id.startswith('ou-'):
            raise ValueError(f"Invalid OU ID format: {self.id}")
        
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("OU name cannot be empty.")


@dataclass
class AWSOrganization:
    """AWS Organization model."""
    id: str
    master_account_id: str
    feature_set: str
    root_id: str
    organizational_units: List[OrganizationalUnit] = None
    accounts: List[AWSAccount] = None
    
    def __post_init__(self):
        """Initialize collections if None."""
        if self.organizational_units is None:
            self.organizational_units = []
        if self.accounts is None:
            self.accounts = []
        
        if not self.master_account_id.isdigit() or len(self.master_account_id) != 12:
            raise ValueError(f"Invalid master account ID: {self.master_account_id}")


@dataclass
class IdentityStoreUser:
    """Identity Store User model."""
    user_id: str
    username: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    
    def __post_init__(self):
        """Validate user data."""
        if not self.user_id:
            raise ValueError("User ID cannot be empty.")
        
        if not self.username:
            raise ValueError("Username cannot be empty.")
        
        if self.email and not AWSAccount._is_valid_email(self.email):
            raise ValueError(f"Invalid email format: {self.email}")


@dataclass
class IdentityStoreGroup:
    """Identity Store Group model."""
    group_id: str
    display_name: str
    description: Optional[str] = None
    members: List[IdentityStoreUser] = None
    
    def __post_init__(self):
        """Initialize members if None."""
        if self.members is None:
            self.members = []
        
        if not self.group_id:
            raise ValueError("Group ID cannot be empty.")
        
        if not self.display_name:
            raise ValueError("Group display name cannot be empty.")


@dataclass
class PermissionSet:
    """Permission Set model."""
    arn: str
    name: str
    description: Optional[str] = None
    session_duration: Optional[str] = None
    
    def __post_init__(self):
        """Validate permission set data."""
        if not self.arn or not self.arn.startswith('arn:aws:sso:::permissionSet/'):
            raise ValueError(f"Invalid permission set ARN: {self.arn}")
        
        if not self.name:
            raise ValueError("Permission set name cannot be empty.")


@dataclass
class AccountAssignment:
    """Account Assignment model."""
    account_id: str
    permission_set_arn: str
    principal_type: PrincipalType
    principal_id: str
    principal_name: Optional[str] = None
    permission_set_name: Optional[str] = None
    
    def __post_init__(self):
        """Validate assignment data."""
        if not self.account_id.isdigit() or len(self.account_id) != 12:
            raise ValueError(f"Invalid account ID: {self.account_id}")
        
        if not self.permission_set_arn.startswith('arn:aws:sso:::permissionSet/'):
            raise ValueError(f"Invalid permission set ARN: {self.permission_set_arn}")
        
        if not self.principal_id:
            raise ValueError("Principal ID cannot be empty.")


@dataclass
class DiagramConfig:
    """Configuration for diagram generation."""
    title: str
    direction: str = "TB"  # Top to Bottom
    show_labels: bool = True
    output_format: str = "png"
    output_path: Optional[str] = None
    
    def __post_init__(self):
        """Validate diagram configuration."""
        valid_directions = ["TB", "BT", "LR", "RL"]
        if self.direction not in valid_directions:
            raise ValueError(f"Invalid direction: {self.direction}. Must be one of {valid_directions}")
        
        valid_formats = ["png", "svg", "pdf"]
        if self.output_format not in valid_formats:
            raise ValueError(f"Invalid output format: {self.output_format}. Must be one of {valid_formats}")


def validate_aws_response(response: Dict[str, Any], required_keys: List[str]) -> None:
    """
    Validate AWS API response contains required keys.
    
    Args:
        response: AWS API response dictionary
        required_keys: List of required keys
        
    Raises:
        ValueError: If required keys are missing
    """
    missing_keys = [key for key in required_keys if key not in response]
    if missing_keys:
        raise ValueError(f"AWS response missing required keys: {missing_keys}")


def sanitize_name_for_diagram(name: str) -> str:
    """
    Sanitize name for use in diagram generation.
    
    Args:
        name: Original name
        
    Returns:
        Sanitized name safe for diagram use
    """
    if not name:
        return "Unknown"
    
    # Remove special characters and limit length
    sanitized = re.sub(r'[^\w\s-]', '', name)
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    # Limit length and add line breaks for long names
    if len(sanitized) > 20:
        words = sanitized.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line + " " + word) <= 20:
                current_line += " " + word if current_line else word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        sanitized = "\\n".join(lines[:3])  # Max 3 lines
    
    return sanitized