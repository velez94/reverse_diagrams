"""Unit tests for explorer data loader.

Feature: interactive-identity-center-explorer
"""

import json
import pytest
import tempfile
from pathlib import Path
from src.explorer.data_loader import DataLoader, MissingFileError, DataLoaderError


def test_missing_organizations_file_raises_error():
    """Test that missing organizations_complete.json raises MissingFileError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Don't create organizations_complete.json
        
        loader = DataLoader(tmpdir)
        
        with pytest.raises(MissingFileError) as exc_info:
            loader.load_all_data()
        
        # Verify error message is descriptive
        assert "organizations_complete.json" in str(exc_info.value)
        assert "reverse_diagrams -o" in str(exc_info.value)


def test_missing_assignments_file_graceful_degradation():
    """Test that missing account_assignments.json is handled gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create minimal organizations file
        org_json = {
            "rootId": "r-test",
            "masterAccountId": "123456789012",
            "noOutAccounts": [{
                "name": "Test Account",
                "account": "123456789012"
            }],
            "organizationalUnits": {}
        }
        
        with open(tmpdir_path / "organizations_complete.json", "w") as f:
            json.dump(org_json, f)
        
        # Don't create account_assignments.json
        
        loader = DataLoader(str(tmpdir))
        explorer_data = loader.load_all_data()
        
        # Should load successfully with empty assignments
        assert explorer_data is not None
        assert len(explorer_data.assignments_by_account) == 0
        assert len(explorer_data.organization.all_accounts) == 1


def test_missing_groups_file_graceful_degradation():
    """Test that missing groups.json is handled gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create minimal organizations file
        org_json = {
            "rootId": "r-test",
            "masterAccountId": "123456789012",
            "noOutAccounts": [{
                "name": "Test Account",
                "account": "123456789012"
            }],
            "organizationalUnits": {}
        }
        
        with open(tmpdir_path / "organizations_complete.json", "w") as f:
            json.dump(org_json, f)
        
        # Create assignments file
        assignments_json = {
            "Test Account": [{
                "AccountId": "123456789012",
                "PermissionSetArn": "arn:aws:sso:::permissionSet/test/ps-1",
                "PermissionSetName": "TestPermissionSet",
                "PrincipalType": "GROUP",
                "PrincipalId": "group-test",
                "GroupName": "TestGroup"
            }]
        }
        
        with open(tmpdir_path / "account_assignments.json", "w") as f:
            json.dump(assignments_json, f)
        
        # Don't create groups.json
        
        loader = DataLoader(str(tmpdir))
        explorer_data = loader.load_all_data()
        
        # Should load successfully with empty groups
        assert explorer_data is not None
        assert len(explorer_data.groups_by_id) == 0
        assert len(explorer_data.assignments_by_account) == 1


def test_invalid_json_directory():
    """Test that invalid directory path raises DataLoaderError."""
    with pytest.raises(DataLoaderError) as exc_info:
        DataLoader("/nonexistent/directory")
    
    assert "does not exist" in str(exc_info.value)


def test_json_directory_is_file():
    """Test that providing a file path instead of directory raises error."""
    with tempfile.NamedTemporaryFile() as tmpfile:
        with pytest.raises(DataLoaderError) as exc_info:
            DataLoader(tmpfile.name)
        
        assert "not a directory" in str(exc_info.value)


def test_malformed_json_syntax_in_assignments():
    """Test that malformed JSON in assignments file is handled gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create valid organizations file
        org_json = {
            "rootId": "r-test",
            "masterAccountId": "123456789012",
            "noOutAccounts": [],
            "organizationalUnits": {}
        }
        
        with open(tmpdir_path / "organizations_complete.json", "w") as f:
            json.dump(org_json, f)
        
        # Create invalid JSON file
        with open(tmpdir_path / "account_assignments.json", "w") as f:
            f.write('{"invalid": json}')  # Invalid JSON syntax
        
        loader = DataLoader(str(tmpdir))
        explorer_data = loader.load_all_data()
        
        # Should load successfully with empty assignments
        assert explorer_data is not None
        assert len(explorer_data.assignments_by_account) == 0
        # Should have validation warning
        assert len(explorer_data.validation_warnings) > 0


def test_malformed_json_syntax_in_groups():
    """Test that malformed JSON in groups file is handled gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create valid organizations file
        org_json = {
            "rootId": "r-test",
            "masterAccountId": "123456789012",
            "noOutAccounts": [],
            "organizationalUnits": {}
        }
        
        with open(tmpdir_path / "organizations_complete.json", "w") as f:
            json.dump(org_json, f)
        
        # Create invalid JSON file
        with open(tmpdir_path / "groups.json", "w") as f:
            f.write('[{"group_id": "test",]')  # Invalid JSON syntax
        
        loader = DataLoader(str(tmpdir))
        explorer_data = loader.load_all_data()
        
        # Should load successfully with empty groups
        assert explorer_data is not None
        assert len(explorer_data.groups_by_id) == 0
        # Should have validation warning
        assert len(explorer_data.validation_warnings) > 0


def test_valid_data_loading():
    """Test that valid data is loaded correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create valid organizations file
        org_json = {
            "rootId": "r-test",
            "masterAccountId": "123456789012",
            "noOutAccounts": [{
                "name": "Test Account",
                "account": "123456789012"
            }],
            "organizationalUnits": {
                "Production": {
                    "Id": "ou-prod",
                    "Name": "Production",
                    "accounts": {
                        "Prod Account": {
                            "name": "Prod Account",
                            "account": "123456789013"
                        }
                    },
                    "nestedOus": {}
                }
            }
        }
        
        with open(tmpdir_path / "organizations_complete.json", "w") as f:
            json.dump(org_json, f)
        
        # Create valid assignments file
        assignments_json = {
            "Test Account": [{
                "AccountId": "123456789012",
                "PermissionSetArn": "arn:aws:sso:::permissionSet/test/ps-1",
                "PermissionSetName": "AdminAccess",
                "PrincipalType": "GROUP",
                "PrincipalId": "group-admin",
                "GroupName": "Administrators"
            }]
        }
        
        with open(tmpdir_path / "account_assignments.json", "w") as f:
            json.dump(assignments_json, f)
        
        # Create valid groups file
        groups_json = [{
            "group_id": "group-admin",
            "group_name": "Administrators",
            "description": "Admin group",
            "members": [{
                "MemberId": {
                    "UserId": "user-1",
                    "UserName": "admin.user"
                },
                "DisplayName": "Admin User",
                "Email": "admin@example.com"
            }]
        }]
        
        with open(tmpdir_path / "groups.json", "w") as f:
            json.dump(groups_json, f)
        
        loader = DataLoader(str(tmpdir))
        explorer_data = loader.load_all_data()
        
        # Verify data is loaded correctly
        assert explorer_data is not None
        assert len(explorer_data.organization.all_accounts) == 2
        assert "123456789012" in explorer_data.organization.all_accounts
        assert "123456789013" in explorer_data.organization.all_accounts
        assert len(explorer_data.assignments_by_account) == 1
        assert "123456789012" in explorer_data.assignments_by_account
        assert len(explorer_data.groups_by_id) == 1
        assert "group-admin" in explorer_data.groups_by_id
        assert len(explorer_data.groups_by_id["group-admin"].members) == 1
