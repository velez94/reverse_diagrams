"""Tests for data models."""
import pytest

from src.models import (
    AWSAccount, OrganizationalUnit, AWSOrganization, IdentityStoreUser,
    IdentityStoreGroup, PermissionSet, AccountAssignment, DiagramConfig,
    PrincipalType, AccountStatus, validate_aws_response, sanitize_name_for_diagram
)


class TestAWSAccount:
    """Test AWS Account model."""
    
    def test_valid_account(self):
        """Test creating a valid AWS account."""
        account = AWSAccount(
            id="123456789012",
            name="Test Account",
            email="test@example.com"
        )
        
        assert account.id == "123456789012"
        assert account.name == "Test Account"
        assert account.email == "test@example.com"
        assert account.status == AccountStatus.ACTIVE
    
    def test_invalid_account_id_non_numeric(self):
        """Test invalid account ID with non-numeric characters."""
        with pytest.raises(ValueError, match="Invalid AWS account ID"):
            AWSAccount(
                id="invalid-id",
                name="Test Account",
                email="test@example.com"
            )
    
    def test_invalid_account_id_wrong_length(self):
        """Test invalid account ID with wrong length."""
        with pytest.raises(ValueError, match="Invalid AWS account ID"):
            AWSAccount(
                id="12345",  # Too short
                name="Test Account",
                email="test@example.com"
            )
    
    def test_empty_account_name(self):
        """Test empty account name."""
        with pytest.raises(ValueError, match="Account name cannot be empty"):
            AWSAccount(
                id="123456789012",
                name="",
                email="test@example.com"
            )
    
    def test_invalid_email_format(self):
        """Test invalid email format."""
        with pytest.raises(ValueError, match="Invalid email format"):
            AWSAccount(
                id="123456789012",
                name="Test Account",
                email="invalid-email"
            )
    
    def test_valid_email_formats(self):
        """Test various valid email formats."""
        valid_emails = [
            "test@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "123@example.org"
        ]
        
        for email in valid_emails:
            account = AWSAccount(
                id="123456789012",
                name="Test Account",
                email=email
            )
            assert account.email == email


class TestOrganizationalUnit:
    """Test Organizational Unit model."""
    
    def test_valid_ou(self):
        """Test creating a valid OU."""
        ou = OrganizationalUnit(
            id="ou-root-123456789",
            name="Development",
            parent_id="r-example"
        )
        
        assert ou.id == "ou-root-123456789"
        assert ou.name == "Development"
        assert ou.parent_id == "r-example"
        assert ou.accounts == []
        assert ou.child_ous == []
    
    def test_invalid_ou_id_format(self):
        """Test invalid OU ID format."""
        with pytest.raises(ValueError, match="Invalid OU ID format"):
            OrganizationalUnit(
                id="invalid-id",
                name="Development"
            )
    
    def test_empty_ou_name(self):
        """Test empty OU name."""
        with pytest.raises(ValueError, match="OU name cannot be empty"):
            OrganizationalUnit(
                id="ou-root-123456789",
                name=""
            )
    
    def test_ou_with_accounts_and_child_ous(self):
        """Test OU with accounts and child OUs."""
        account = AWSAccount(
            id="123456789012",
            name="Test Account",
            email="test@example.com"
        )
        
        child_ou = OrganizationalUnit(
            id="ou-child-123456789",
            name="Child OU"
        )
        
        ou = OrganizationalUnit(
            id="ou-root-123456789",
            name="Parent OU",
            accounts=[account],
            child_ous=[child_ou]
        )
        
        assert len(ou.accounts) == 1
        assert len(ou.child_ous) == 1
        assert ou.accounts[0].name == "Test Account"
        assert ou.child_ous[0].name == "Child OU"


class TestIdentityStoreUser:
    """Test Identity Store User model."""
    
    def test_valid_user(self):
        """Test creating a valid user."""
        user = IdentityStoreUser(
            user_id="user-123456789",
            username="testuser",
            display_name="Test User",
            email="test@example.com"
        )
        
        assert user.user_id == "user-123456789"
        assert user.username == "testuser"
        assert user.display_name == "Test User"
        assert user.email == "test@example.com"
    
    def test_empty_user_id(self):
        """Test empty user ID."""
        with pytest.raises(ValueError, match="User ID cannot be empty"):
            IdentityStoreUser(
                user_id="",
                username="testuser"
            )
    
    def test_empty_username(self):
        """Test empty username."""
        with pytest.raises(ValueError, match="Username cannot be empty"):
            IdentityStoreUser(
                user_id="user-123456789",
                username=""
            )
    
    def test_invalid_email(self):
        """Test invalid email format."""
        with pytest.raises(ValueError, match="Invalid email format"):
            IdentityStoreUser(
                user_id="user-123456789",
                username="testuser",
                email="invalid-email"
            )


class TestIdentityStoreGroup:
    """Test Identity Store Group model."""
    
    def test_valid_group(self):
        """Test creating a valid group."""
        user = IdentityStoreUser(
            user_id="user-123456789",
            username="testuser"
        )
        
        group = IdentityStoreGroup(
            group_id="group-123456789",
            display_name="Test Group",
            description="A test group",
            members=[user]
        )
        
        assert group.group_id == "group-123456789"
        assert group.display_name == "Test Group"
        assert group.description == "A test group"
        assert len(group.members) == 1
        assert group.members[0].username == "testuser"
    
    def test_empty_group_id(self):
        """Test empty group ID."""
        with pytest.raises(ValueError, match="Group ID cannot be empty"):
            IdentityStoreGroup(
                group_id="",
                display_name="Test Group"
            )
    
    def test_empty_display_name(self):
        """Test empty display name."""
        with pytest.raises(ValueError, match="Group display name cannot be empty"):
            IdentityStoreGroup(
                group_id="group-123456789",
                display_name=""
            )


class TestPermissionSet:
    """Test Permission Set model."""
    
    def test_valid_permission_set(self):
        """Test creating a valid permission set."""
        ps = PermissionSet(
            arn="arn:aws:sso:::permissionSet/ssoins-123456789/ps-123456789",
            name="AdministratorAccess",
            description="Full administrator access"
        )
        
        assert ps.arn == "arn:aws:sso:::permissionSet/ssoins-123456789/ps-123456789"
        assert ps.name == "AdministratorAccess"
        assert ps.description == "Full administrator access"
    
    def test_invalid_permission_set_arn(self):
        """Test invalid permission set ARN."""
        with pytest.raises(ValueError, match="Invalid permission set ARN"):
            PermissionSet(
                arn="invalid-arn",
                name="AdministratorAccess"
            )
    
    def test_empty_permission_set_name(self):
        """Test empty permission set name."""
        with pytest.raises(ValueError, match="Permission set name cannot be empty"):
            PermissionSet(
                arn="arn:aws:sso:::permissionSet/ssoins-123456789/ps-123456789",
                name=""
            )


class TestAccountAssignment:
    """Test Account Assignment model."""
    
    def test_valid_account_assignment(self):
        """Test creating a valid account assignment."""
        assignment = AccountAssignment(
            account_id="123456789012",
            permission_set_arn="arn:aws:sso:::permissionSet/ssoins-123456789/ps-123456789",
            principal_type=PrincipalType.GROUP,
            principal_id="group-123456789",
            principal_name="Administrators",
            permission_set_name="AdministratorAccess"
        )
        
        assert assignment.account_id == "123456789012"
        assert assignment.principal_type == PrincipalType.GROUP
        assert assignment.principal_name == "Administrators"
    
    def test_invalid_account_id(self):
        """Test invalid account ID."""
        with pytest.raises(ValueError, match="Invalid account ID"):
            AccountAssignment(
                account_id="invalid",
                permission_set_arn="arn:aws:sso:::permissionSet/ssoins-123456789/ps-123456789",
                principal_type=PrincipalType.GROUP,
                principal_id="group-123456789"
            )
    
    def test_invalid_permission_set_arn(self):
        """Test invalid permission set ARN."""
        with pytest.raises(ValueError, match="Invalid permission set ARN"):
            AccountAssignment(
                account_id="123456789012",
                permission_set_arn="invalid-arn",
                principal_type=PrincipalType.GROUP,
                principal_id="group-123456789"
            )


class TestDiagramConfig:
    """Test Diagram Configuration model."""
    
    def test_valid_diagram_config(self):
        """Test creating a valid diagram config."""
        config = DiagramConfig(
            title="Test Diagram",
            direction="LR",
            output_format="svg"
        )
        
        assert config.title == "Test Diagram"
        assert config.direction == "LR"
        assert config.output_format == "svg"
    
    def test_invalid_direction(self):
        """Test invalid direction."""
        with pytest.raises(ValueError, match="Invalid direction"):
            DiagramConfig(
                title="Test Diagram",
                direction="INVALID"
            )
    
    def test_invalid_output_format(self):
        """Test invalid output format."""
        with pytest.raises(ValueError, match="Invalid output format"):
            DiagramConfig(
                title="Test Diagram",
                output_format="invalid"
            )


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_validate_aws_response_success(self):
        """Test successful AWS response validation."""
        response = {
            "Organization": {"Id": "test"},
            "Accounts": []
        }
        
        # Should not raise an exception
        validate_aws_response(response, ["Organization", "Accounts"])
    
    def test_validate_aws_response_missing_keys(self):
        """Test AWS response validation with missing keys."""
        response = {
            "Organization": {"Id": "test"}
        }
        
        with pytest.raises(ValueError, match="AWS response missing required keys"):
            validate_aws_response(response, ["Organization", "Accounts"])
    
    def test_sanitize_name_for_diagram_short_name(self):
        """Test sanitizing short names."""
        result = sanitize_name_for_diagram("Test Name")
        assert result == "Test Name"
    
    def test_sanitize_name_for_diagram_long_name(self):
        """Test sanitizing long names."""
        long_name = "This is a very long name that should be split into multiple lines"
        result = sanitize_name_for_diagram(long_name)
        
        # Should contain line breaks
        assert "\\n" in result
        # Should not exceed 3 lines
        assert result.count("\\n") <= 2
    
    def test_sanitize_name_for_diagram_special_characters(self):
        """Test sanitizing names with special characters."""
        name_with_special = "Test@Name#With$Special%Characters"
        result = sanitize_name_for_diagram(name_with_special)
        
        # Special characters should be removed
        assert "@" not in result
        assert "#" not in result
        assert "$" not in result
        assert "%" not in result
    
    def test_sanitize_name_for_diagram_empty_name(self):
        """Test sanitizing empty name."""
        result = sanitize_name_for_diagram("")
        assert result == "Unknown"
    
    def test_sanitize_name_for_diagram_none_name(self):
        """Test sanitizing None name."""
        result = sanitize_name_for_diagram(None)
        assert result == "Unknown"