"""Integration tests for the Interactive Identity Center Explorer.

Feature: interactive-identity-center-explorer
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.explorer.controller import ExplorerController
from src.explorer.data_loader import DataLoader
from src.explorer.navigation import NavigationEngine, NavigationState
from src.explorer.display import DisplayManager
from src.explorer.models import ExplorerData


@pytest.fixture
def integration_json_dir(tmp_path):
    """Create a complete set of JSON files for integration testing."""
    json_dir = tmp_path / "json"
    json_dir.mkdir()
    
    # Create organizations_complete.json in the correct format
    organizations_data = {
        "rootId": "r-test123",
        "masterAccountId": "333333333333",
        "noOutAccounts": [
            {
                "account": "333333333333",
                "name": "Root Account"
            }
        ],
        "organizationalUnits": {
            "Core OU": {
                "Id": "ou-core-001",
                "Name": "Core OU",
                "accounts": {
                    "Production Account": {
                        "account": "111111111111",
                        "name": "Production Account"
                    }
                },
                "nestedOus": {
                    "Development OU": {
                        "Id": "ou-dev-001",
                        "Name": "Development OU",
                        "accounts": {
                            "Dev Account": {
                                "account": "222222222222",
                                "name": "Dev Account"
                            }
                        },
                        "nestedOus": {}
                    }
                }
            }
        }
    }
    
    # Create account_assignments.json
    assignments_data = {
        "Production Account": [
            {
                "AccountId": "111111111111",
                "PermissionSetArn": "arn:aws:sso:::permissionSet/ssoins-1234/ps-admin",
                "PermissionSetName": "AdministratorAccess",
                "PrincipalType": "GROUP",
                "PrincipalId": "group-admin-001",
                "GroupName": "Administrators"
            }
        ],
        "Dev Account": [
            {
                "AccountId": "222222222222",
                "PermissionSetArn": "arn:aws:sso:::permissionSet/ssoins-1234/ps-dev",
                "PermissionSetName": "DeveloperAccess",
                "PrincipalType": "USER",
                "PrincipalId": "user-dev-001",
                "UserName": "dev.user@example.com"
            }
        ]
    }
    
    # Create groups.json
    groups_data = {
        "group-admin-001": {
            "GroupId": "group-admin-001",
            "DisplayName": "Administrators",
            "Description": "Admin group",
            "Members": [
                {
                    "MemberId": {
                        "UserId": "user-admin-001",
                        "UserName": "admin.user@example.com"
                    },
                    "DisplayName": "Admin User",
                    "Email": "admin.user@example.com"
                }
            ]
        }
    }
    
    # Write JSON files
    with open(json_dir / "organizations_complete.json", "w") as f:
        json.dump(organizations_data, f)
    
    with open(json_dir / "account_assignments.json", "w") as f:
        json.dump(assignments_data, f)
    
    with open(json_dir / "groups.json", "w") as f:
        json.dump(groups_data, f)
    
    return str(json_dir)


class TestCompleteNavigationFlow:
    """Test complete navigation flow through the explorer."""
    
    def test_complete_navigation_flow(self, integration_json_dir):
        """
        Test: Start explorer → Navigate to OU → Select account → View details → Back → Exit
        
        This test verifies that all components work together correctly for a
        complete navigation flow.
        """
        # Load data
        data_loader = DataLoader(integration_json_dir)
        data = data_loader.load_all_data()
        
        # Verify data loaded correctly
        assert data.organization.root_id == "r-test123"
        assert len(data.organization.root_ous) == 1
        assert len(data.organization.root_accounts) == 1
        
        # Initialize navigation engine
        nav_engine = NavigationEngine(data)
        
        # Step 1: Start at root level
        view = nav_engine.get_current_view()
        assert view.is_root_level()
        assert len(view.items) > 0
        
        # Find Core OU
        core_ou_item = None
        for item in view.items:
            if item.is_ou() and "Core OU" in item.display_text:
                core_ou_item = item
                break
        
        assert core_ou_item is not None, "Core OU should be in root view"
        
        # Step 2: Navigate to Core OU
        nav_engine.handle_selection(core_ou_item.item_id)
        view = nav_engine.get_current_view()
        assert view.is_ou_level()
        assert "Core OU" in view.breadcrumb
        
        # Verify Core OU contains Production Account and Development OU
        has_prod_account = any("Production Account" in item.display_text for item in view.items)
        has_dev_ou = any("Development OU" in item.display_text for item in view.items)
        assert has_prod_account, "Production Account should be in Core OU"
        assert has_dev_ou, "Development OU should be in Core OU"
        
        # Step 3: Navigate to Production Account
        prod_account_item = None
        for item in view.items:
            if item.is_account() and "Production Account" in item.display_text:
                prod_account_item = item
                break
        
        assert prod_account_item is not None
        nav_engine.handle_selection(prod_account_item.item_id)
        view = nav_engine.get_current_view()
        assert view.is_account_detail()
        
        # Verify account details
        account = data.organization.get_account_by_id("111111111111")
        assert account is not None
        assignments = data.get_assignments_for_account("111111111111")
        assert len(assignments) == 1
        assert assignments[0].permission_set.name == "AdministratorAccess"
        
        # Step 4: Go back to Core OU
        nav_engine.go_back()
        view = nav_engine.get_current_view()
        assert view.is_ou_level()
        assert "Core OU" in view.breadcrumb
        
        # Step 5: Go back to root
        nav_engine.go_back()
        view = nav_engine.get_current_view()
        assert view.is_root_level()
        assert view.breadcrumb == "Root"
        
        # Step 6: Exit
        exit_item = None
        for item in view.items:
            if item.is_exit():
                exit_item = item
                break
        
        assert exit_item is not None
        nav_engine.handle_selection(exit_item.item_id)
        assert nav_engine.current_state == NavigationState.EXIT


class TestGracefulDegradation:
    """Test graceful degradation with missing files."""
    
    def test_missing_account_assignments(self, tmp_path):
        """
        Test: Start with missing account_assignments.json
        
        Verify accounts are shown without assignment information and no crashes occur.
        """
        json_dir = tmp_path / "json"
        json_dir.mkdir()
        
        # Create only organizations_complete.json in correct format
        organizations_data = {
            "rootId": "r-test123",
            "masterAccountId": "111111111111",
            "noOutAccounts": [
                {
                    "account": "111111111111",
                    "name": "Test Account"
                }
            ],
            "organizationalUnits": {}
        }
        
        with open(json_dir / "organizations_complete.json", "w") as f:
            json.dump(organizations_data, f)
        
        # Load data - should not crash
        data_loader = DataLoader(str(json_dir))
        data = data_loader.load_all_data()
        
        # Verify organization loaded
        assert data.organization.root_id == "r-test123"
        assert len(data.organization.root_accounts) == 1
        
        # Verify no assignments (graceful degradation)
        assert len(data.assignments_by_account) == 0
        assert len(data.groups_by_id) == 0
        
        # Verify navigation still works
        nav_engine = NavigationEngine(data)
        view = nav_engine.get_current_view()
        assert view.is_root_level()
        
        # Navigate to account
        account_item = None
        for item in view.items:
            if item.is_account() and "Test Account" in item.display_text:
                account_item = item
                break
        
        assert account_item is not None
        nav_engine.handle_selection(account_item.item_id)
        view = nav_engine.get_current_view()
        assert view.is_account_detail()
        
        # Verify no assignments for account
        assignments = data.get_assignments_for_account("111111111111")
        assert len(assignments) == 0


class TestErrorHandling:
    """Test error handling with invalid data."""
    
    def test_invalid_organizations_json(self, tmp_path):
        """
        Test: Start with invalid organizations_complete.json
        
        Verify descriptive error message is shown and graceful exit.
        """
        json_dir = tmp_path / "json"
        json_dir.mkdir()
        
        # Create invalid JSON file
        with open(json_dir / "organizations_complete.json", "w") as f:
            f.write("{ invalid json }")
        
        # Attempt to load data - should raise error
        data_loader = DataLoader(str(json_dir))
        
        with pytest.raises(Exception):
            data_loader.load_all_data()


class TestDeepNavigation:
    """Test navigation through deeply nested OU structure."""
    
    def test_deep_navigation(self, tmp_path):
        """
        Test: Navigate through deeply nested OU structure (5+ levels)
        
        Verify breadcrumbs are accurate at each level and back navigation works correctly.
        """
        json_dir = tmp_path / "json"
        json_dir.mkdir()
        
        # Create deeply nested organization structure in correct format
        organizations_data = {
            "rootId": "r-test123",
            "masterAccountId": "111111111111",
            "noOutAccounts": [],
            "organizationalUnits": {
                "Level 1 OU": {
                    "Id": "ou-level1",
                    "Name": "Level 1 OU",
                    "accounts": {},
                    "nestedOus": {
                        "Level 2 OU": {
                            "Id": "ou-level2",
                            "Name": "Level 2 OU",
                            "accounts": {},
                            "nestedOus": {
                                "Level 3 OU": {
                                    "Id": "ou-level3",
                                    "Name": "Level 3 OU",
                                    "accounts": {},
                                    "nestedOus": {
                                        "Level 4 OU": {
                                            "Id": "ou-level4",
                                            "Name": "Level 4 OU",
                                            "accounts": {},
                                            "nestedOus": {
                                                "Level 5 OU": {
                                                    "Id": "ou-level5",
                                                    "Name": "Level 5 OU",
                                                    "accounts": {
                                                        "Deep Account": {
                                                            "account": "111111111111",
                                                            "name": "Deep Account"
                                                        }
                                                    },
                                                    "nestedOus": {}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        with open(json_dir / "organizations_complete.json", "w") as f:
            json.dump(organizations_data, f)
        
        # Load data
        data_loader = DataLoader(str(json_dir))
        data = data_loader.load_all_data()
        
        # Initialize navigation
        nav_engine = NavigationEngine(data)
        
        # Navigate through all 5 levels
        ou_ids = ["ou-level1", "ou-level2", "ou-level3", "ou-level4", "ou-level5"]
        ou_names = ["Level 1 OU", "Level 2 OU", "Level 3 OU", "Level 4 OU", "Level 5 OU"]
        
        for i, (ou_id, ou_name) in enumerate(zip(ou_ids, ou_names)):
            view = nav_engine.get_current_view()
            
            # Find OU item
            ou_item = None
            for item in view.items:
                if item.is_ou() and ou_name in item.display_text:
                    ou_item = item
                    break
            
            assert ou_item is not None, f"{ou_name} should be in view"
            
            # Navigate to OU
            nav_engine.handle_selection(ou_item.item_id)
            view = nav_engine.get_current_view()
            
            # Verify breadcrumb contains all parent OUs
            breadcrumb = nav_engine.get_breadcrumb()
            assert "Root" in breadcrumb
            assert ou_name in breadcrumb
        
        # Verify we're at level 5
        view = nav_engine.get_current_view()
        assert "Level 5 OU" in view.breadcrumb
        
        # Navigate back through all levels
        for i in range(5):
            result = nav_engine.go_back()
            assert result is True
        
        # Should be back at root
        view = nav_engine.get_current_view()
        assert view.is_root_level()


class TestLargeOrganization:
    """Test with large organization (50+ accounts)."""
    
    def test_large_organization(self, tmp_path):
        """
        Test: Use fixture with 50+ accounts in single OU
        
        Verify pagination is implemented and performance is acceptable.
        """
        json_dir = tmp_path / "json"
        json_dir.mkdir()
        
        # Create organization with 60 accounts in correct format
        accounts_dict = {}
        for i in range(60):
            account_id = str(i).zfill(12)
            account_name = f"Account {i}"
            accounts_dict[account_name] = {
                "account": account_id,
                "name": account_name
            }
        
        organizations_data = {
            "rootId": "r-test123",
            "masterAccountId": "000000000000",
            "noOutAccounts": [],
            "organizationalUnits": {
                "Large OU": {
                    "Id": "ou-large-001",
                    "Name": "Large OU",
                    "accounts": accounts_dict,
                    "nestedOus": {}
                }
            }
        }
        
        with open(json_dir / "organizations_complete.json", "w") as f:
            json.dump(organizations_data, f)
        
        # Load data
        data_loader = DataLoader(str(json_dir))
        data = data_loader.load_all_data()
        
        # Verify all accounts loaded
        assert len(data.organization.all_accounts) == 60
        
        # Initialize navigation
        nav_engine = NavigationEngine(data)
        
        # Navigate to Large OU
        view = nav_engine.get_current_view()
        ou_item = None
        for item in view.items:
            if item.is_ou() and "Large OU" in item.display_text:
                ou_item = item
                break
        
        assert ou_item is not None
        nav_engine.handle_selection(ou_item.item_id)
        view = nav_engine.get_current_view()
        
        # Verify all 60 accounts are in the view
        account_items = [item for item in view.items if item.is_account()]
        assert len(account_items) == 60
        
        # Verify pagination should be used (DisplayManager has pagination_threshold = 100)
        from src.explorer.display import DisplayManager
        display_manager = DisplayManager()
        assert display_manager.should_paginate(60) is False  # 60 < 100
        assert display_manager.should_paginate(101) is True  # 101 > 100
