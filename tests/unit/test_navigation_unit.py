"""Unit tests for Navigation Engine.

Feature: interactive-identity-center-explorer
"""

import pytest
from src.explorer.models import (
    Account,
    OrganizationalUnit,
    OrganizationTree,
    ExplorerData,
)
from src.explorer.navigation import NavigationEngine, NavigationState


@pytest.fixture
def simple_org_data():
    """Create a simple organization structure for testing."""
    # Create accounts
    account1 = Account(id="111111111111", name="Account 1", email="acc1@example.com")
    account2 = Account(id="222222222222", name="Account 2", email="acc2@example.com")
    account3 = Account(id="333333333333", name="Account 3", email="acc3@example.com")
    
    # Create OUs
    child_ou = OrganizationalUnit(
        id="ou-child",
        name="Child OU",
        accounts=[account2]
    )
    
    root_ou = OrganizationalUnit(
        id="ou-root",
        name="Root OU",
        children_ous=[child_ou],
        accounts=[account1]
    )
    
    # Create organization tree
    organization = OrganizationTree(
        root_id="r-root",
        root_ous=[root_ou],
        root_accounts=[account3],
        all_accounts={
            account1.id: account1,
            account2.id: account2,
            account3.id: account3,
        }
    )
    
    return ExplorerData(
        organization=organization,
        assignments_by_account={},
        groups_by_id={}
    )


class TestNavigationEngineInitialization:
    """Test navigation engine initialization."""
    
    def test_initial_state_is_root(self, simple_org_data):
        """Test that navigation engine starts at root level."""
        nav_engine = NavigationEngine(simple_org_data)
        
        assert nav_engine.current_state == NavigationState.ROOT_LEVEL
        assert nav_engine.current_item_id is None
        assert len(nav_engine.history) == 1
    
    def test_initial_view_shows_root_items(self, simple_org_data):
        """Test that initial view shows root OUs and accounts."""
        nav_engine = NavigationEngine(simple_org_data)
        view = nav_engine.get_current_view()
        
        assert view.is_root_level()
        assert view.title == "AWS Organizations Explorer"
        
        # Should have: 1 root OU + 1 root account + 1 exit option
        assert len(view.items) == 3
        
        # Check for root OU
        ou_items = [item for item in view.items if item.is_ou()]
        assert len(ou_items) == 1
        assert ou_items[0].item_id == "ou-root"
        
        # Check for root account
        account_items = [item for item in view.items if item.is_account()]
        assert len(account_items) == 1
        assert account_items[0].item_id == "333333333333"
        
        # Check for exit option
        exit_items = [item for item in view.items if item.is_exit()]
        assert len(exit_items) == 1


class TestNavigationToOU:
    """Test navigation to organizational units."""
    
    def test_navigate_to_root_ou(self, simple_org_data):
        """Test navigating to a root-level OU."""
        nav_engine = NavigationEngine(simple_org_data)
        
        # Navigate to root OU
        nav_engine.handle_selection("ou-root")
        
        assert nav_engine.current_state == NavigationState.OU_LEVEL
        assert nav_engine.current_item_id == "ou-root"
        assert len(nav_engine.history) == 2
    
    def test_ou_view_shows_children(self, simple_org_data):
        """Test that OU view shows child OUs and accounts."""
        nav_engine = NavigationEngine(simple_org_data)
        nav_engine.handle_selection("ou-root")
        
        view = nav_engine.get_current_view()
        
        assert view.is_ou_level()
        assert "Root OU" in view.title
        
        # Should have: 1 child OU + 1 account + back + exit
        assert len(view.items) == 4
        
        # Check for child OU
        ou_items = [item for item in view.items if item.is_ou()]
        assert len(ou_items) == 1
        assert ou_items[0].item_id == "ou-child"
        
        # Check for account
        account_items = [item for item in view.items if item.is_account()]
        assert len(account_items) == 1
        assert account_items[0].item_id == "111111111111"
    
    def test_navigate_to_nested_ou(self, simple_org_data):
        """Test navigating to a nested OU."""
        nav_engine = NavigationEngine(simple_org_data)
        
        # Navigate to root OU
        nav_engine.handle_selection("ou-root")
        
        # Navigate to child OU
        nav_engine.handle_selection("ou-child")
        
        assert nav_engine.current_state == NavigationState.OU_LEVEL
        assert nav_engine.current_item_id == "ou-child"
        assert len(nav_engine.history) == 3
        
        view = nav_engine.get_current_view()
        assert "Child OU" in view.title


class TestNavigationToAccount:
    """Test navigation to accounts."""
    
    def test_navigate_to_root_account(self, simple_org_data):
        """Test navigating to a root-level account."""
        nav_engine = NavigationEngine(simple_org_data)
        
        # Navigate to root account
        nav_engine.handle_selection("333333333333")
        
        assert nav_engine.current_state == NavigationState.ACCOUNT_DETAIL
        assert nav_engine.current_item_id == "333333333333"
        assert len(nav_engine.history) == 2
    
    def test_navigate_to_account_in_ou(self, simple_org_data):
        """Test navigating to an account within an OU."""
        nav_engine = NavigationEngine(simple_org_data)
        
        # Navigate to root OU
        nav_engine.handle_selection("ou-root")
        
        # Navigate to account
        nav_engine.handle_selection("111111111111")
        
        assert nav_engine.current_state == NavigationState.ACCOUNT_DETAIL
        assert nav_engine.current_item_id == "111111111111"
        assert len(nav_engine.history) == 3
    
    def test_account_view_has_back_and_exit(self, simple_org_data):
        """Test that account detail view has back and exit options."""
        nav_engine = NavigationEngine(simple_org_data)
        nav_engine.handle_selection("333333333333")
        
        view = nav_engine.get_current_view()
        
        assert view.is_account_detail()
        
        # Should have back and exit options
        back_items = [item for item in view.items if item.is_back()]
        assert len(back_items) == 1
        
        exit_items = [item for item in view.items if item.is_exit()]
        assert len(exit_items) == 1


class TestBackNavigation:
    """Test back navigation functionality."""
    
    def test_go_back_from_ou(self, simple_org_data):
        """Test going back from OU to root."""
        nav_engine = NavigationEngine(simple_org_data)
        
        # Navigate to OU
        nav_engine.handle_selection("ou-root")
        assert nav_engine.current_state == NavigationState.OU_LEVEL
        
        # Go back
        result = nav_engine.go_back()
        
        assert result is True
        assert nav_engine.current_state == NavigationState.ROOT_LEVEL
        assert nav_engine.current_item_id is None
        assert len(nav_engine.history) == 1
    
    def test_go_back_from_account(self, simple_org_data):
        """Test going back from account to root."""
        nav_engine = NavigationEngine(simple_org_data)
        
        # Navigate to account
        nav_engine.handle_selection("333333333333")
        assert nav_engine.current_state == NavigationState.ACCOUNT_DETAIL
        
        # Go back
        result = nav_engine.go_back()
        
        assert result is True
        assert nav_engine.current_state == NavigationState.ROOT_LEVEL
    
    def test_go_back_from_nested_ou(self, simple_org_data):
        """Test going back from nested OU to parent OU."""
        nav_engine = NavigationEngine(simple_org_data)
        
        # Navigate to root OU then child OU
        nav_engine.handle_selection("ou-root")
        nav_engine.handle_selection("ou-child")
        
        # Go back to parent OU
        result = nav_engine.go_back()
        
        assert result is True
        assert nav_engine.current_state == NavigationState.OU_LEVEL
        assert nav_engine.current_item_id == "ou-root"
    
    def test_cannot_go_back_from_root(self, simple_org_data):
        """Test that going back from root returns False."""
        nav_engine = NavigationEngine(simple_org_data)
        
        result = nav_engine.go_back()
        
        assert result is False
        assert nav_engine.current_state == NavigationState.ROOT_LEVEL
    
    def test_back_via_handle_selection(self, simple_org_data):
        """Test back navigation via handle_selection with back item."""
        nav_engine = NavigationEngine(simple_org_data)
        
        # Navigate to OU
        nav_engine.handle_selection("ou-root")
        
        # Select back option
        nav_engine.handle_selection("back")
        
        assert nav_engine.current_state == NavigationState.ROOT_LEVEL


class TestBreadcrumbGeneration:
    """Test breadcrumb generation at various levels."""
    
    def test_breadcrumb_at_root(self, simple_org_data):
        """Test breadcrumb at root level."""
        nav_engine = NavigationEngine(simple_org_data)
        
        breadcrumb = nav_engine.get_breadcrumb()
        
        assert breadcrumb == "Root"
    
    def test_breadcrumb_at_ou(self, simple_org_data):
        """Test breadcrumb at OU level."""
        nav_engine = NavigationEngine(simple_org_data)
        nav_engine.handle_selection("ou-root")
        
        breadcrumb = nav_engine.get_breadcrumb()
        
        assert breadcrumb == "Root > Root OU"
    
    def test_breadcrumb_at_nested_ou(self, simple_org_data):
        """Test breadcrumb at nested OU level."""
        nav_engine = NavigationEngine(simple_org_data)
        nav_engine.handle_selection("ou-root")
        nav_engine.handle_selection("ou-child")
        
        breadcrumb = nav_engine.get_breadcrumb()
        
        assert breadcrumb == "Root > Root OU > Child OU"
    
    def test_breadcrumb_at_account(self, simple_org_data):
        """Test breadcrumb at account level."""
        nav_engine = NavigationEngine(simple_org_data)
        nav_engine.handle_selection("333333333333")
        
        breadcrumb = nav_engine.get_breadcrumb()
        
        assert breadcrumb == "Root > Account 3"
    
    def test_breadcrumb_updates_after_back(self, simple_org_data):
        """Test that breadcrumb updates correctly after going back."""
        nav_engine = NavigationEngine(simple_org_data)
        
        # Navigate forward
        nav_engine.handle_selection("ou-root")
        nav_engine.handle_selection("ou-child")
        
        # Go back
        nav_engine.go_back()
        
        breadcrumb = nav_engine.get_breadcrumb()
        assert breadcrumb == "Root > Root OU"


class TestExitNavigation:
    """Test exit navigation functionality."""
    
    def test_exit_from_root(self, simple_org_data):
        """Test exiting from root level."""
        nav_engine = NavigationEngine(simple_org_data)
        
        nav_engine.handle_selection("exit")
        
        assert nav_engine.current_state == NavigationState.EXIT
    
    def test_exit_from_ou(self, simple_org_data):
        """Test exiting from OU level."""
        nav_engine = NavigationEngine(simple_org_data)
        nav_engine.handle_selection("ou-root")
        
        nav_engine.handle_selection("exit")
        
        assert nav_engine.current_state == NavigationState.EXIT
    
    def test_exit_view(self, simple_org_data):
        """Test that exit state returns appropriate view."""
        nav_engine = NavigationEngine(simple_org_data)
        nav_engine.handle_selection("exit")
        
        view = nav_engine.get_current_view()
        
        assert view.level == "EXIT"
        assert view.title == "Exiting..."
        assert len(view.items) == 0


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_navigate_to_nonexistent_item(self, simple_org_data):
        """Test navigating to a non-existent item ID."""
        nav_engine = NavigationEngine(simple_org_data)
        
        # Try to navigate to non-existent item
        nav_engine.handle_selection("nonexistent-id")
        
        # Should remain at root level
        assert nav_engine.current_state == NavigationState.ROOT_LEVEL
    
    def test_empty_ou(self):
        """Test navigation to an empty OU."""
        # Create an empty OU
        empty_ou = OrganizationalUnit(
            id="ou-empty",
            name="Empty OU",
            children_ous=[],
            accounts=[]
        )
        
        organization = OrganizationTree(
            root_id="r-root",
            root_ous=[empty_ou],
            root_accounts=[],
            all_accounts={}
        )
        
        explorer_data = ExplorerData(
            organization=organization,
            assignments_by_account={},
            groups_by_id={}
        )
        
        nav_engine = NavigationEngine(explorer_data)
        nav_engine.handle_selection("ou-empty")
        
        view = nav_engine.get_current_view()
        
        # Should have only back and exit options
        assert len(view.items) == 2
        assert any(item.is_back() for item in view.items)
        assert any(item.is_exit() for item in view.items)
    
    def test_get_selectable_items(self, simple_org_data):
        """Test get_selectable_items returns current view items."""
        nav_engine = NavigationEngine(simple_org_data)
        
        items = nav_engine.get_selectable_items()
        view = nav_engine.get_current_view()
        
        assert items == view.items
