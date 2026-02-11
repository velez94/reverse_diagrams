"""Test nested OU generation in organizations_complete.json.

This test verifies that the create_organization_complete_map function
properly handles nested OUs at multiple levels.
"""

import pytest
from src.aws.describe_organization import create_organization_complete_map


def test_nested_ou_structure():
    """Test that nested OUs are properly structured in the output."""
    # Mock data with nested OUs
    root_id = "r-test123"
    organization = {"MasterAccountId": "123456789012"}
    
    organizational_units = [
        {
            "Id": "ou-root-1",
            "Name": "Root OU",
            "Parents": [{"Type": "ROOT", "Id": root_id}]
        },
        {
            "Id": "ou-level1-1",
            "Name": "Level 1 OU",
            "Parents": [{"Type": "ORGANIZATIONAL_UNIT", "Id": "ou-root-1"}]
        },
        {
            "Id": "ou-level2-1",
            "Name": "Level 2 OU",
            "Parents": [{"Type": "ORGANIZATIONAL_UNIT", "Id": "ou-level1-1"}]
        },
        {
            "Id": "ou-level3-1",
            "Name": "Level 3 OU",
            "Parents": [{"Type": "ORGANIZATIONAL_UNIT", "Id": "ou-level2-1"}]
        }
    ]
    
    accounts = [
        {
            "account": "111111111111",
            "name": "Root Account",
            "parents": [{"Type": "ROOT", "Id": root_id}]
        },
        {
            "account": "222222222222",
            "name": "Root OU Account",
            "parents": [{"Type": "ORGANIZATIONAL_UNIT", "Id": "ou-root-1"}]
        },
        {
            "account": "333333333333",
            "name": "Level 1 Account",
            "parents": [{"Type": "ORGANIZATIONAL_UNIT", "Id": "ou-level1-1"}]
        },
        {
            "account": "444444444444",
            "name": "Level 2 Account",
            "parents": [{"Type": "ORGANIZATIONAL_UNIT", "Id": "ou-level2-1"}]
        },
        {
            "account": "555555555555",
            "name": "Level 3 Account",
            "parents": [{"Type": "ORGANIZATIONAL_UNIT", "Id": "ou-level3-1"}]
        }
    ]
    
    # Create the organization map
    result = create_organization_complete_map(
        root_id=root_id,
        organization=organization,
        organizational_units=organizational_units,
        accounts=accounts
    )
    
    # Verify root structure
    assert result["rootId"] == root_id
    assert result["masterAccountId"] == "123456789012"
    
    # Verify root account
    assert len(result["noOutAccounts"]) == 1
    assert result["noOutAccounts"][0]["account"] == "111111111111"
    
    # Verify Root OU exists at top level
    assert "Root OU" in result["organizationalUnits"]
    root_ou = result["organizationalUnits"]["Root OU"]
    
    # Verify Root OU has its account
    assert "Root OU Account" in root_ou["accounts"]
    assert root_ou["accounts"]["Root OU Account"]["account"] == "222222222222"
    
    # Verify Level 1 OU is nested under Root OU
    assert "Level 1 OU" in root_ou["nestedOus"]
    level1_ou = root_ou["nestedOus"]["Level 1 OU"]
    
    # Verify Level 1 OU has its account
    assert "Level 1 Account" in level1_ou["accounts"]
    assert level1_ou["accounts"]["Level 1 Account"]["account"] == "333333333333"
    
    # Verify Level 2 OU is nested under Level 1 OU
    assert "Level 2 OU" in level1_ou["nestedOus"]
    level2_ou = level1_ou["nestedOus"]["Level 2 OU"]
    
    # Verify Level 2 OU has its account
    assert "Level 2 Account" in level2_ou["accounts"]
    assert level2_ou["accounts"]["Level 2 Account"]["account"] == "444444444444"
    
    # Verify Level 3 OU is nested under Level 2 OU
    assert "Level 3 OU" in level2_ou["nestedOus"]
    level3_ou = level2_ou["nestedOus"]["Level 3 OU"]
    
    # Verify Level 3 OU has its account
    assert "Level 3 Account" in level3_ou["accounts"]
    assert level3_ou["accounts"]["Level 3 Account"]["account"] == "555555555555"
    
    # Verify Level 3 OU has no nested OUs
    assert len(level3_ou["nestedOus"]) == 0


def test_multiple_nested_branches():
    """Test that multiple nested branches are handled correctly."""
    root_id = "r-test123"
    organization = {"MasterAccountId": "123456789012"}
    
    organizational_units = [
        # Branch 1
        {
            "Id": "ou-branch1",
            "Name": "Branch 1",
            "Parents": [{"Type": "ROOT", "Id": root_id}]
        },
        {
            "Id": "ou-branch1-child",
            "Name": "Branch 1 Child",
            "Parents": [{"Type": "ORGANIZATIONAL_UNIT", "Id": "ou-branch1"}]
        },
        # Branch 2
        {
            "Id": "ou-branch2",
            "Name": "Branch 2",
            "Parents": [{"Type": "ROOT", "Id": root_id}]
        },
        {
            "Id": "ou-branch2-child",
            "Name": "Branch 2 Child",
            "Parents": [{"Type": "ORGANIZATIONAL_UNIT", "Id": "ou-branch2"}]
        }
    ]
    
    accounts = [
        {
            "account": "111111111111",
            "name": "Branch 1 Account",
            "parents": [{"Type": "ORGANIZATIONAL_UNIT", "Id": "ou-branch1-child"}]
        },
        {
            "account": "222222222222",
            "name": "Branch 2 Account",
            "parents": [{"Type": "ORGANIZATIONAL_UNIT", "Id": "ou-branch2-child"}]
        }
    ]
    
    result = create_organization_complete_map(
        root_id=root_id,
        organization=organization,
        organizational_units=organizational_units,
        accounts=accounts
    )
    
    # Verify both branches exist at root level
    assert "Branch 1" in result["organizationalUnits"]
    assert "Branch 2" in result["organizationalUnits"]
    
    # Verify Branch 1 structure
    branch1 = result["organizationalUnits"]["Branch 1"]
    assert "Branch 1 Child" in branch1["nestedOus"]
    assert "Branch 1 Account" in branch1["nestedOus"]["Branch 1 Child"]["accounts"]
    
    # Verify Branch 2 structure
    branch2 = result["organizationalUnits"]["Branch 2"]
    assert "Branch 2 Child" in branch2["nestedOus"]
    assert "Branch 2 Account" in branch2["nestedOus"]["Branch 2 Child"]["accounts"]


def test_empty_nested_ous():
    """Test that OUs with no children have empty nestedOus dict."""
    root_id = "r-test123"
    organization = {"MasterAccountId": "123456789012"}
    
    organizational_units = [
        {
            "Id": "ou-empty",
            "Name": "Empty OU",
            "Parents": [{"Type": "ROOT", "Id": root_id}]
        }
    ]
    
    accounts = []
    
    result = create_organization_complete_map(
        root_id=root_id,
        organization=organization,
        organizational_units=organizational_units,
        accounts=accounts
    )
    
    # Verify empty OU has empty nestedOus
    assert "Empty OU" in result["organizationalUnits"]
    empty_ou = result["organizationalUnits"]["Empty OU"]
    assert len(empty_ou["nestedOus"]) == 0
    assert len(empty_ou["accounts"]) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
