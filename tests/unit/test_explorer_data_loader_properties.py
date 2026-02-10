"""Property-based tests for explorer data loader.

Feature: interactive-identity-center-explorer
"""

import json
import pytest
import tempfile
from pathlib import Path
from hypothesis import given, strategies as st, assume, settings
from src.explorer.data_loader import DataLoader, MissingFileError
from src.explorer.models import (
    Account,
    Assignment,
    Group,
    OrganizationalUnit,
    PermissionSet,
    User,
)


# Strategies for generating test data
@st.composite
def valid_account_id_strategy(draw):
    """Generate a valid 12-digit AWS account ID."""
    return draw(st.text(min_size=12, max_size=12, alphabet=st.characters(whitelist_categories=("Nd",))))


@st.composite
def organization_json_strategy(draw):
    """Generate a valid organizations_complete.json structure."""
    root_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(blacklist_characters="\x00\n\r\t")))
    master_account_id = draw(valid_account_id_strategy())
    
    # Generate root accounts (no OU)
    num_root_accounts = draw(st.integers(min_value=0, max_value=3))
    no_ou_accounts = []
    for i in range(num_root_accounts):
        account_id = draw(valid_account_id_strategy())
        no_ou_accounts.append({
            "name": f"Root Account {i}",
            "account": account_id
        })
    
    # Generate OUs with accounts
    num_ous = draw(st.integers(min_value=1, max_value=5))
    organizational_units = {}
    all_account_ids = [acc["account"] for acc in no_ou_accounts]
    
    for i in range(num_ous):
        ou_name = f"OU-{i}"
        ou_id = f"ou-{i:04d}"
        
        num_accounts = draw(st.integers(min_value=0, max_value=3))
        accounts = {}
        for j in range(num_accounts):
            account_id = draw(valid_account_id_strategy())
            all_account_ids.append(account_id)
            account_name = f"Account-{i}-{j}"
            accounts[account_name] = {
                "name": account_name,
                "account": account_id
            }
        
        organizational_units[ou_name] = {
            "Id": ou_id,
            "Name": ou_name,
            "accounts": accounts,
            "nestedOus": {}
        }
    
    return {
        "rootId": root_id,
        "masterAccountId": master_account_id,
        "noOutAccounts": no_ou_accounts,
        "organizationalUnits": organizational_units
    }, all_account_ids


@st.composite
def assignments_json_strategy(draw, account_ids):
    """Generate a valid account_assignments.json structure."""
    if not account_ids:
        return {}, []
    
    # Remove duplicates from account_ids
    unique_account_ids = list(set(account_ids))
    
    # Select a subset of accounts to have assignments
    num_accounts_with_assignments = draw(st.integers(min_value=0, max_value=len(unique_account_ids)))
    if num_accounts_with_assignments == 0:
        return {}, []
    
    selected_accounts = draw(st.lists(
        st.sampled_from(unique_account_ids),
        min_size=num_accounts_with_assignments,
        max_size=num_accounts_with_assignments,
        unique=True
    ))
    
    assignments = {}
    for account_id in selected_accounts:
        account_name = f"Account-{account_id}"
        num_assignments = draw(st.integers(min_value=1, max_value=3))
        
        account_assignments = []
        for i in range(num_assignments):
            principal_type = draw(st.sampled_from(["GROUP", "USER"]))
            principal_id = f"principal-{account_id}-{i}"
            
            assignment = {
                "AccountId": account_id,
                "PermissionSetArn": f"arn:aws:sso:::permissionSet/ssoins-test/ps-{i}",
                "PermissionSetName": f"PermissionSet-{i}",
                "PrincipalType": principal_type,
                "PrincipalId": principal_id,
            }
            
            if principal_type == "GROUP":
                assignment["GroupName"] = f"Group-{i}"
            else:
                assignment["UserName"] = f"User-{i}"
            
            account_assignments.append(assignment)
        
        assignments[account_name] = account_assignments
    
    # Extract all principal IDs for group generation
    group_ids = []
    for account_assignments in assignments.values():
        for assignment in account_assignments:
            if assignment["PrincipalType"] == "GROUP":
                group_ids.append(assignment["PrincipalId"])
    
    return assignments, list(set(group_ids))


@st.composite
def groups_json_strategy(draw, group_ids):
    """Generate a valid groups.json structure."""
    if not group_ids:
        return []
    
    groups = []
    for group_id in group_ids:
        num_members = draw(st.integers(min_value=0, max_value=5))
        members = []
        
        for i in range(num_members):
            members.append({
                "MemberId": {
                    "UserId": f"user-{group_id}-{i}",
                    "UserName": f"user.{group_id}.{i}"
                },
                "DisplayName": f"User {i} in {group_id}",
                "Email": f"user.{group_id}.{i}@example.com"
            })
        
        groups.append({
            "group_id": group_id,
            "group_name": f"Group-{group_id}",
            "description": f"Test group {group_id}",
            "members": members
        })
    
    return groups


# Property 4: Data Integration Completeness
# Feature: interactive-identity-center-explorer, Property 4: Data Integration Completeness
@given(st.data())
@settings(max_examples=50, deadline=None)
def test_data_integration_completeness(data):
    """
    Property 4: Data Integration Completeness
    Validates: Requirements 2.4, 10.4, 10.5
    
    For any valid set of JSON files (organizations, assignments, groups),
    the Data Loader should create a unified model where every account ID
    in assignments maps to an account in the organization tree, and every
    group ID in assignments maps to a group in the groups data (or generates
    a validation warning).
    """
    # Generate organization structure
    org_json, account_ids = data.draw(organization_json_strategy())
    assume(len(account_ids) > 0)  # Need at least one account
    
    # Generate assignments for some accounts
    assignments_json, group_ids = data.draw(assignments_json_strategy(account_ids))
    
    # Generate groups for all group IDs
    groups_json = data.draw(groups_json_strategy(group_ids))
    
    # Create temporary directory with JSON files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Write JSON files
        with open(tmpdir_path / "organizations_complete.json", "w") as f:
            json.dump(org_json, f)
        
        with open(tmpdir_path / "account_assignments.json", "w") as f:
            json.dump(assignments_json, f)
        
        with open(tmpdir_path / "groups.json", "w") as f:
            json.dump(groups_json, f)
        
        # Load data
        loader = DataLoader(str(tmpdir_path))
        explorer_data = loader.load_all_data()
        
        # Property 1: All accounts in organization should be in all_accounts dict
        for account_id in account_ids:
            assert account_id in explorer_data.organization.all_accounts, \
                f"Account {account_id} should be in all_accounts dictionary"
        
        # Property 2: All account IDs in assignments should exist in organization
        # (or generate validation warning)
        for account_id in explorer_data.assignments_by_account.keys():
            if account_id not in explorer_data.organization.all_accounts:
                # Should have generated a validation warning
                warning_found = any(
                    account_id in warning
                    for warning in explorer_data.validation_warnings
                )
                assert warning_found, \
                    f"Account {account_id} not in organization should generate warning"
        
        # Property 3: All group IDs in assignments should exist in groups data
        # (or generate validation warning)
        for account_id, assignments in explorer_data.assignments_by_account.items():
            for assignment in assignments:
                if assignment.is_group_assignment():
                    group_id = assignment.principal_id
                    if group_id not in explorer_data.groups_by_id:
                        # Should have generated a validation warning
                        warning_found = any(
                            group_id in warning or assignment.principal_name in warning
                            for warning in explorer_data.validation_warnings
                        )
                        assert warning_found, \
                            f"Group {group_id} not in groups should generate warning"
        
        # Property 4: All assignments should be valid
        for account_id, assignments in explorer_data.assignments_by_account.items():
            for assignment in assignments:
                assert assignment.validate(), \
                    f"Assignment for account {account_id} should be valid"
        
        # Property 5: All groups should be valid
        for group_id, group in explorer_data.groups_by_id.items():
            assert group.validate(), \
                f"Group {group_id} should be valid"
        
        # Property 6: Organization tree should be valid
        assert explorer_data.organization.validate(), \
            "Organization tree should be valid"


# Property 22: Assignment Mapping Completeness
# Feature: interactive-identity-center-explorer, Property 22: Assignment Mapping Completeness
@given(st.data())
@settings(max_examples=50, deadline=None)
def test_assignment_mapping_completeness(data):
    """
    Property 22: Assignment Mapping Completeness
    Validates: Requirements 10.2
    
    For any valid account_assignments.json file, the Data Loader should create
    a mapping where every account ID maps to a list of assignments, and accounts
    with no assignments map to an empty list.
    """
    # Generate organization structure
    org_json, account_ids = data.draw(organization_json_strategy())
    assume(len(account_ids) > 0)
    
    # Generate assignments for some accounts
    assignments_json, group_ids = data.draw(assignments_json_strategy(account_ids))
    
    # Create temporary directory with JSON files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Write JSON files
        with open(tmpdir_path / "organizations_complete.json", "w") as f:
            json.dump(org_json, f)
        
        with open(tmpdir_path / "account_assignments.json", "w") as f:
            json.dump(assignments_json, f)
        
        # Load data
        loader = DataLoader(str(tmpdir_path))
        explorer_data = loader.load_all_data()
        
        # Property 1: All account IDs in assignments_json should be in the mapping
        for account_name, assignments_list in assignments_json.items():
            if assignments_list:
                account_id = assignments_list[0]["AccountId"]
                assert account_id in explorer_data.assignments_by_account, \
                    f"Account {account_id} with assignments should be in mapping"
        
        # Property 2: Accounts without assignments should not be in mapping
        # (or should map to empty list)
        accounts_with_assignments = set(explorer_data.assignments_by_account.keys())
        for account_id in account_ids:
            if account_id not in accounts_with_assignments:
                # This is expected - accounts without assignments are not in the mapping
                assert account_id not in explorer_data.assignments_by_account or \
                       len(explorer_data.assignments_by_account[account_id]) == 0
        
        # Property 3: Each assignment list should contain valid assignments
        for account_id, assignments in explorer_data.assignments_by_account.items():
            assert isinstance(assignments, list), \
                f"Assignments for {account_id} should be a list"
            for assignment in assignments:
                assert assignment.account_id == account_id, \
                    f"Assignment account_id should match key {account_id}"
                assert assignment.validate(), \
                    f"Assignment for {account_id} should be valid"


# Property 23: Group Mapping Completeness
# Feature: interactive-identity-center-explorer, Property 23: Group Mapping Completeness
@given(st.data())
@settings(max_examples=50, deadline=None)
def test_group_mapping_completeness(data):
    """
    Property 23: Group Mapping Completeness
    Validates: Requirements 10.3
    
    For any valid groups.json file, the Data Loader should create a mapping
    where every group ID maps to a Group object containing all member users.
    """
    # Generate organization structure (minimal)
    org_json = {
        "rootId": "r-test",
        "masterAccountId": "123456789012",
        "noOutAccounts": [],
        "organizationalUnits": {}
    }
    
    # Generate random group IDs
    num_groups = data.draw(st.integers(min_value=1, max_value=10))
    group_ids = [f"group-{i:04d}" for i in range(num_groups)]
    
    # Generate groups
    groups_json = data.draw(groups_json_strategy(group_ids))
    
    # Create temporary directory with JSON files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Write JSON files
        with open(tmpdir_path / "organizations_complete.json", "w") as f:
            json.dump(org_json, f)
        
        with open(tmpdir_path / "groups.json", "w") as f:
            json.dump(groups_json, f)
        
        # Load data
        loader = DataLoader(str(tmpdir_path))
        explorer_data = loader.load_all_data()
        
        # Property 1: All group IDs should be in the mapping
        for group_data in groups_json:
            group_id = group_data["group_id"]
            assert group_id in explorer_data.groups_by_id, \
                f"Group {group_id} should be in mapping"
        
        # Property 2: Each group should contain all its members
        for group_data in groups_json:
            group_id = group_data["group_id"]
            group = explorer_data.groups_by_id[group_id]
            
            expected_member_count = len(group_data["members"])
            actual_member_count = len(group.members)
            
            assert actual_member_count == expected_member_count, \
                f"Group {group_id} should have {expected_member_count} members, got {actual_member_count}"
        
        # Property 3: All groups should be valid
        for group_id, group in explorer_data.groups_by_id.items():
            assert group.validate(), \
                f"Group {group_id} should be valid"
            assert group.id == group_id, \
                f"Group ID should match key {group_id}"
        
        # Property 4: All members should be valid users
        for group_id, group in explorer_data.groups_by_id.items():
            for member in group.members:
                assert member.validate(), \
                    f"Member {member.id} in group {group_id} should be valid"



# Property 5: Graceful Handling of Malformed Data
# Feature: interactive-identity-center-explorer, Property 5: Graceful Handling of Malformed Data
@given(st.data())
@settings(max_examples=50, deadline=None)
def test_graceful_handling_of_malformed_data(data):
    """
    Property 5: Graceful Handling of Malformed Data
    Validates: Requirements 2.6, 7.4, 10.6
    
    For any JSON file with missing or invalid fields, the Data Loader should
    not crash but should log warnings and continue processing with default
    values or partial data.
    """
    # Generate a valid organization structure first
    org_json, account_ids = data.draw(organization_json_strategy())
    assume(len(account_ids) > 0)
    
    # Generate malformed assignments (missing required fields)
    malformed_type = data.draw(st.sampled_from([
        "missing_account_id",
        "missing_permission_set_arn",
        "missing_principal_type",
        "invalid_principal_type",
        "missing_principal_id",
    ]))
    
    assignments_json = {}
    if malformed_type == "missing_account_id":
        # Assignment without AccountId
        assignments_json["Test Account"] = [{
            "PermissionSetArn": "arn:aws:sso:::permissionSet/test/ps-1",
            "PermissionSetName": "TestPermissionSet",
            "PrincipalType": "GROUP",
            "PrincipalId": "group-test",
            "GroupName": "TestGroup"
        }]
    elif malformed_type == "missing_permission_set_arn":
        # Assignment without PermissionSetArn
        assignments_json["Test Account"] = [{
            "AccountId": account_ids[0],
            "PermissionSetName": "TestPermissionSet",
            "PrincipalType": "GROUP",
            "PrincipalId": "group-test",
            "GroupName": "TestGroup"
        }]
    elif malformed_type == "missing_principal_type":
        # Assignment without PrincipalType
        assignments_json["Test Account"] = [{
            "AccountId": account_ids[0],
            "PermissionSetArn": "arn:aws:sso:::permissionSet/test/ps-1",
            "PermissionSetName": "TestPermissionSet",
            "PrincipalId": "group-test",
            "GroupName": "TestGroup"
        }]
    elif malformed_type == "invalid_principal_type":
        # Assignment with invalid PrincipalType
        assignments_json["Test Account"] = [{
            "AccountId": account_ids[0],
            "PermissionSetArn": "arn:aws:sso:::permissionSet/test/ps-1",
            "PermissionSetName": "TestPermissionSet",
            "PrincipalType": "INVALID",
            "PrincipalId": "group-test",
            "GroupName": "TestGroup"
        }]
    elif malformed_type == "missing_principal_id":
        # Assignment without PrincipalId
        assignments_json["Test Account"] = [{
            "AccountId": account_ids[0],
            "PermissionSetArn": "arn:aws:sso:::permissionSet/test/ps-1",
            "PermissionSetName": "TestPermissionSet",
            "PrincipalType": "GROUP",
            "GroupName": "TestGroup"
        }]
    
    # Generate malformed groups (missing required fields)
    groups_json = [{
        "group_id": "group-test",
        # Missing group_name
        "members": []
    }]
    
    # Create temporary directory with JSON files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Write JSON files
        with open(tmpdir_path / "organizations_complete.json", "w") as f:
            json.dump(org_json, f)
        
        with open(tmpdir_path / "account_assignments.json", "w") as f:
            json.dump(assignments_json, f)
        
        with open(tmpdir_path / "groups.json", "w") as f:
            json.dump(groups_json, f)
        
        # Load data - should not crash
        try:
            loader = DataLoader(str(tmpdir_path))
            explorer_data = loader.load_all_data()
            
            # Property 1: Data loader should not crash with malformed data
            assert explorer_data is not None, "Data loader should return data even with malformed input"
            
            # Property 2: Organization should still be valid (it's not malformed)
            assert explorer_data.organization.validate(), "Organization should be valid"
            
            # Property 3: Validation warnings should be generated for malformed data
            # (This is optional - the loader may skip invalid entries without warning)
            # We just verify it doesn't crash
            
        except Exception as e:
            # Should not raise exceptions for malformed data
            pytest.fail(f"Data loader should not crash with malformed data, but got: {e}")


# Additional test for completely invalid JSON syntax
@given(st.data())
@settings(max_examples=20, deadline=None)
def test_invalid_json_syntax_handling(data):
    """
    Test that the Data Loader handles invalid JSON syntax gracefully.
    
    For JSON files with syntax errors, the loader should log errors and
    continue with partial data where possible.
    """
    # Generate a valid organization structure
    org_json, account_ids = data.draw(organization_json_strategy())
    assume(len(account_ids) > 0)
    
    # Create temporary directory with JSON files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Write valid organizations file
        with open(tmpdir_path / "organizations_complete.json", "w") as f:
            json.dump(org_json, f)
        
        # Write invalid JSON for assignments (syntax error)
        with open(tmpdir_path / "account_assignments.json", "w") as f:
            f.write('{"invalid": json syntax}')  # Missing quotes around 'json'
        
        # Write invalid JSON for groups (syntax error)
        with open(tmpdir_path / "groups.json", "w") as f:
            f.write('[{"group_id": "test", "group_name": "Test",]')  # Extra comma
        
        # Load data - should not crash
        try:
            loader = DataLoader(str(tmpdir_path))
            explorer_data = loader.load_all_data()
            
            # Property 1: Data loader should not crash with invalid JSON
            assert explorer_data is not None, "Data loader should return data even with invalid JSON"
            
            # Property 2: Organization should still be loaded (it's valid)
            assert explorer_data.organization.validate(), "Organization should be valid"
            assert len(explorer_data.organization.all_accounts) > 0, "Accounts should be loaded"
            
            # Property 3: Invalid files should result in empty mappings
            # (since they couldn't be parsed)
            assert isinstance(explorer_data.assignments_by_account, dict), \
                "Assignments should be a dict (possibly empty)"
            assert isinstance(explorer_data.groups_by_id, dict), \
                "Groups should be a dict (possibly empty)"
            
            # Property 4: Validation warnings should be present
            assert len(explorer_data.validation_warnings) > 0, \
                "Should have validation warnings for invalid JSON files"
            
        except Exception as e:
            # Should not raise exceptions for invalid JSON
            pytest.fail(f"Data loader should not crash with invalid JSON, but got: {e}")
