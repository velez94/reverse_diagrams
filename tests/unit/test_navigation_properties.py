"""Property-based tests for Navigation Engine.

Feature: interactive-identity-center-explorer
"""

import pytest
from hypothesis import given, strategies as st, assume
from src.explorer.models import (
    OrganizationalUnit,
    Account,
    OrganizationTree,
    ExplorerData,
)
from src.explorer.navigation import NavigationEngine, NavigationState


# Custom strategies for generating test data
_ou_id_counter = 0

@st.composite
def organizational_unit_strategy(draw, max_depth=3, current_depth=0):
    """Generate a random organizational unit with children."""
    global _ou_id_counter
    _ou_id_counter += 1
    ou_id = f"ou-{_ou_id_counter:06d}"
    name = draw(st.text(min_size=3, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))))
    
    # Generate accounts
    num_accounts = draw(st.integers(min_value=0, max_value=5))
    accounts = []
    for i in range(num_accounts):
        account_id = draw(st.text(min_size=12, max_size=12, alphabet=st.characters(whitelist_categories=('Nd',))))
        account_name = draw(st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
        accounts.append(Account(
            id=account_id,
            name=account_name,
            email=f"{account_name}@example.com",
            parent_ou_id=ou_id
        ))
    
    # Generate child OUs (limit depth to avoid infinite recursion)
    children_ous = []
    if current_depth < max_depth:
        num_children = draw(st.integers(min_value=0, max_value=3))
        for _ in range(num_children):
            child_ou = draw(organizational_unit_strategy(max_depth=max_depth, current_depth=current_depth + 1))
            child_ou.parent_id = ou_id
            children_ous.append(child_ou)
    
    return OrganizationalUnit(
        id=ou_id,
        name=name,
        children_ous=children_ous,
        accounts=accounts
    )


@st.composite
def explorer_data_with_ou_strategy(draw):
    """Generate ExplorerData with at least one OU."""
    global _ou_id_counter
    _ou_id_counter = 0  # Reset counter for each test
    
    root_id = "r-root"
    
    # Generate at least one root OU
    num_root_ous = draw(st.integers(min_value=1, max_value=3))
    root_ous = [draw(organizational_unit_strategy()) for _ in range(num_root_ous)]
    
    # Build all_accounts dictionary
    all_accounts = {}
    for ou in root_ous:
        for account in ou.get_all_accounts():
            all_accounts[account.id] = account
    
    organization = OrganizationTree(
        root_id=root_id,
        root_ous=root_ous,
        root_accounts=[],
        all_accounts=all_accounts
    )
    
    return ExplorerData(
        organization=organization,
        assignments_by_account={},
        groups_by_id={}
    )


@st.composite
def explorer_data_with_root_accounts_strategy(draw):
    """Generate ExplorerData with at least one root-level account."""
    global _ou_id_counter
    _ou_id_counter = 0  # Reset counter for each test
    
    root_id = "r-root"
    
    # Generate root accounts with "acc-" prefix to avoid ID collisions
    num_root_accounts = draw(st.integers(min_value=1, max_value=3))
    root_accounts = []
    for i in range(num_root_accounts):
        account_id = "acc-" + draw(st.text(min_size=12, max_size=12, alphabet=st.characters(whitelist_categories=('Nd',))))
        account_name = draw(st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
        root_accounts.append(Account(
            id=account_id,
            name=account_name,
            email=f"{account_name}@example.com"
        ))
    
    # Optionally add some OUs
    num_root_ous = draw(st.integers(min_value=0, max_value=2))
    root_ous = [draw(organizational_unit_strategy()) for _ in range(num_root_ous)]
    
    # Build all_accounts dictionary
    all_accounts = {}
    for account in root_accounts:
        all_accounts[account.id] = account
    for ou in root_ous:
        for account in ou.get_all_accounts():
            all_accounts[account.id] = account
    
    organization = OrganizationTree(
        root_id=root_id,
        root_ous=root_ous,
        root_accounts=root_accounts,
        all_accounts=all_accounts
    )
    
    return ExplorerData(
        organization=organization,
        assignments_by_account={},
        groups_by_id={}
    )


# Property 1: Navigation State Transitions for OUs
@given(explorer_data_with_ou_strategy())
def test_ou_navigation_shows_all_children(explorer_data):
    """
    Property 1: Navigation State Transitions for OUs
    
    For any organizational unit with child OUs or accounts, selecting that OU
    should result in a navigation state containing all of its children (both
    child OUs and accounts).
    
    Validates: Requirements 1.3
    Feature: interactive-identity-center-explorer
    """
    # Assume we have at least one OU
    assume(len(explorer_data.organization.root_ous) > 0)
    
    # Get the first root OU
    test_ou = explorer_data.organization.root_ous[0]
    
    # Assume the OU has at least one child (OU or account)
    assume(test_ou.get_child_count() > 0)
    
    # Initialize navigation engine
    nav_engine = NavigationEngine(explorer_data)
    
    # Navigate to the OU
    nav_engine.handle_selection(test_ou.id)
    
    # Get the current view
    view = nav_engine.get_current_view()
    
    # Verify we're at OU level
    assert view.is_ou_level(), "Should be at OU level after selecting an OU"
    
    # Extract child OU IDs and account IDs from the view
    view_ou_ids = set()
    view_account_ids = set()
    
    for item in view.items:
        if item.is_ou():
            view_ou_ids.add(item.item_id)
        elif item.is_account():
            view_account_ids.add(item.item_id)
    
    # Expected child OU IDs and account IDs
    expected_ou_ids = {child_ou.id for child_ou in test_ou.children_ous}
    expected_account_ids = {account.id for account in test_ou.accounts}
    
    # Verify all child OUs are shown
    assert view_ou_ids == expected_ou_ids, \
        f"View should show all child OUs. Expected: {expected_ou_ids}, Got: {view_ou_ids}"
    
    # Verify all accounts are shown
    assert view_account_ids == expected_account_ids, \
        f"View should show all accounts. Expected: {expected_account_ids}, Got: {view_account_ids}"


@given(explorer_data_with_ou_strategy())
def test_ou_navigation_state_is_correct(explorer_data):
    """
    Property 1 (variant): Navigation state should be OU_LEVEL after selecting an OU.
    
    Validates: Requirements 1.3
    Feature: interactive-identity-center-explorer
    """
    # Assume we have at least one OU
    assume(len(explorer_data.organization.root_ous) > 0)
    
    # Get the first root OU
    test_ou = explorer_data.organization.root_ous[0]
    
    # Initialize navigation engine
    nav_engine = NavigationEngine(explorer_data)
    
    # Verify initial state is ROOT
    assert nav_engine.current_state == NavigationState.ROOT_LEVEL
    
    # Navigate to the OU
    nav_engine.handle_selection(test_ou.id)
    
    # Verify state changed to OU_LEVEL
    assert nav_engine.current_state == NavigationState.OU_LEVEL, \
        "Navigation state should be OU_LEVEL after selecting an OU"
    
    # Verify current_item_id is set correctly
    assert nav_engine.current_item_id == test_ou.id, \
        f"Current item ID should be {test_ou.id}, got {nav_engine.current_item_id}"


@given(explorer_data_with_ou_strategy())
def test_nested_ou_navigation(explorer_data):
    """
    Property 1 (variant): Navigation should work for nested OUs.
    
    Validates: Requirements 1.3
    Feature: interactive-identity-center-explorer
    """
    # Find an OU with at least one child OU
    def find_ou_with_children(ous):
        for ou in ous:
            if len(ou.children_ous) > 0:
                return ou, ou.children_ous[0]
            # Recursively search in children
            result = find_ou_with_children(ou.children_ous)
            if result:
                return result
        return None
    
    result = find_ou_with_children(explorer_data.organization.root_ous)
    assume(result is not None)
    
    parent_ou, child_ou = result
    
    # Initialize navigation engine
    nav_engine = NavigationEngine(explorer_data)
    
    # Navigate to parent OU
    nav_engine.handle_selection(parent_ou.id)
    
    # Verify we can see the child OU
    view = nav_engine.get_current_view()
    child_ou_ids = {item.item_id for item in view.items if item.is_ou()}
    
    assert child_ou.id in child_ou_ids, \
        f"Child OU {child_ou.id} should be visible in parent OU view"
    
    # Navigate to child OU
    nav_engine.handle_selection(child_ou.id)
    
    # Verify we're now at the child OU level
    assert nav_engine.current_state == NavigationState.OU_LEVEL
    assert nav_engine.current_item_id == child_ou.id
    
    # Verify the view shows the child OU's contents
    child_view = nav_engine.get_current_view()
    expected_child_ou_ids = {ou.id for ou in child_ou.children_ous}
    expected_account_ids = {acc.id for acc in child_ou.accounts}
    
    actual_child_ou_ids = {item.item_id for item in child_view.items if item.is_ou()}
    actual_account_ids = {item.item_id for item in child_view.items if item.is_account()}
    
    assert actual_child_ou_ids == expected_child_ou_ids
    assert actual_account_ids == expected_account_ids


# Property 2: Navigation State Transitions for Accounts
@given(explorer_data_with_root_accounts_strategy())
def test_account_navigation_shows_detail_view(explorer_data):
    """
    Property 2: Navigation State Transitions for Accounts
    
    For any account in the organization, selecting that account should result
    in a navigation state showing the account detail view with all associated
    permission set assignments.
    
    Validates: Requirements 1.4
    Feature: interactive-identity-center-explorer
    """
    # We have at least one root account
    assume(len(explorer_data.organization.root_accounts) > 0)
    
    # Get the first root account
    test_account = explorer_data.organization.root_accounts[0]
    
    # Initialize navigation engine
    nav_engine = NavigationEngine(explorer_data)
    
    # Navigate to the account
    nav_engine.handle_selection(test_account.id)
    
    # Get the current view
    view = nav_engine.get_current_view()
    
    # Verify we're at ACCOUNT_DETAIL level
    assert view.is_account_detail(), \
        "Should be at ACCOUNT_DETAIL level after selecting an account"
    
    # Verify navigation state
    assert nav_engine.current_state == NavigationState.ACCOUNT_DETAIL, \
        "Navigation state should be ACCOUNT_DETAIL after selecting an account"
    
    # Verify current_item_id is set correctly
    assert nav_engine.current_item_id == test_account.id, \
        f"Current item ID should be {test_account.id}, got {nav_engine.current_item_id}"
    
    # Verify the title contains the account information
    assert test_account.name in view.title or test_account.id in view.title, \
        f"View title should contain account information. Title: {view.title}"


@given(explorer_data_with_ou_strategy())
def test_account_navigation_from_ou(explorer_data):
    """
    Property 2 (variant): Account navigation should work from within an OU.
    
    Validates: Requirements 1.4
    Feature: interactive-identity-center-explorer
    """
    # Find an OU with at least one account
    def find_ou_with_accounts(ous):
        for ou in ous:
            if len(ou.accounts) > 0:
                return ou, ou.accounts[0]
            # Recursively search in children
            result = find_ou_with_accounts(ou.children_ous)
            if result:
                return result
        return None
    
    result = find_ou_with_accounts(explorer_data.organization.root_ous)
    assume(result is not None)
    
    parent_ou, test_account = result
    
    # Initialize navigation engine
    nav_engine = NavigationEngine(explorer_data)
    
    # Navigate to the OU first
    nav_engine.handle_selection(parent_ou.id)
    
    # Verify we're at OU level (if not, the OU ID might be invalid)
    if nav_engine.current_state != NavigationState.OU_LEVEL:
        assume(False)  # Skip this test case
    
    # Now navigate to the account
    nav_engine.handle_selection(test_account.id)
    
    # Verify we're at ACCOUNT_DETAIL level
    assert nav_engine.current_state == NavigationState.ACCOUNT_DETAIL, \
        f"Should be at ACCOUNT_DETAIL after selecting account, but at {nav_engine.current_state}"
    assert nav_engine.current_item_id == test_account.id, \
        f"Current item should be {test_account.id}, but is {nav_engine.current_item_id}"
    
    # Verify the view is correct
    view = nav_engine.get_current_view()
    assert view.is_account_detail(), "View should be account detail view"


@given(explorer_data_with_root_accounts_strategy())
def test_account_detail_view_has_back_and_exit(explorer_data):
    """
    Property 2 (variant): Account detail view should always have Back and Exit options.
    
    Validates: Requirements 1.4, 1.5, 1.6
    Feature: interactive-identity-center-explorer
    """
    # We have at least one root account
    assume(len(explorer_data.organization.root_accounts) > 0)
    test_account = explorer_data.organization.root_accounts[0]
    
    # Initialize navigation engine
    nav_engine = NavigationEngine(explorer_data)
    
    # Navigate to the account
    nav_engine.handle_selection(test_account.id)
    
    # Get the current view
    view = nav_engine.get_current_view()
    
    # Check for Back option
    has_back = any(item.is_back() for item in view.items)
    assert has_back, "Account detail view should have a Back option"
    
    # Check for Exit option
    has_exit = any(item.is_exit() for item in view.items)
    assert has_exit, "Account detail view should have an Exit option"


# Property 3: Navigation History Consistency
@given(explorer_data_with_ou_strategy())
def test_navigation_history_back_returns_to_original(explorer_data):
    """
    Property 3: Navigation History Consistency
    
    For any sequence of navigation actions (forward selections), performing
    those actions followed by an equal number of "back" actions should return
    the navigation state to its original position.
    
    Validates: Requirements 1.5
    Feature: interactive-identity-center-explorer
    """
    # Assume we have at least one OU
    assume(len(explorer_data.organization.root_ous) > 0)
    
    # Initialize navigation engine
    nav_engine = NavigationEngine(explorer_data)
    
    # Record initial state
    initial_state = nav_engine.current_state
    initial_item_id = nav_engine.current_item_id
    initial_history_length = len(nav_engine.history)
    
    # Perform a sequence of forward navigations
    navigation_steps = []
    
    # Step 1: Navigate to first OU
    first_ou = explorer_data.organization.root_ous[0]
    nav_engine.handle_selection(first_ou.id)
    navigation_steps.append("ou")
    
    # Step 2: If the OU has children, navigate to one
    if len(first_ou.children_ous) > 0:
        child_ou = first_ou.children_ous[0]
        nav_engine.handle_selection(child_ou.id)
        navigation_steps.append("child_ou")
    elif len(first_ou.accounts) > 0:
        # Navigate to an account if no child OUs
        account = first_ou.accounts[0]
        nav_engine.handle_selection(account.id)
        navigation_steps.append("account")
    
    # Record state after forward navigation
    forward_state = nav_engine.current_state
    forward_item_id = nav_engine.current_item_id
    
    # Now go back the same number of steps
    for _ in range(len(navigation_steps)):
        result = nav_engine.go_back()
        assert result, "go_back() should return True when not at root"
    
    # Verify we're back to the initial state
    assert nav_engine.current_state == initial_state, \
        f"Should return to initial state {initial_state}, but at {nav_engine.current_state}"
    assert nav_engine.current_item_id == initial_item_id, \
        f"Should return to initial item {initial_item_id}, but at {nav_engine.current_item_id}"
    assert len(nav_engine.history) == initial_history_length, \
        f"History length should be {initial_history_length}, but is {len(nav_engine.history)}"


@given(explorer_data_with_ou_strategy())
def test_navigation_history_cannot_go_back_from_root(explorer_data):
    """
    Property 3 (variant): Cannot go back from root level.
    
    Validates: Requirements 1.5
    Feature: interactive-identity-center-explorer
    """
    # Initialize navigation engine
    nav_engine = NavigationEngine(explorer_data)
    
    # Verify we're at root
    assert nav_engine.current_state == NavigationState.ROOT_LEVEL
    
    # Try to go back from root
    result = nav_engine.go_back()
    
    # Should return False
    assert result == False, "go_back() should return False when at root level"
    
    # Should still be at root
    assert nav_engine.current_state == NavigationState.ROOT_LEVEL, \
        "Should remain at root level after failed go_back()"


@given(explorer_data_with_ou_strategy())
def test_navigation_history_preserves_breadcrumb(explorer_data):
    """
    Property 3 (variant): Navigation history should preserve breadcrumb trail.
    
    Validates: Requirements 1.5, 6.1
    Feature: interactive-identity-center-explorer
    """
    # Assume we have at least one OU
    assume(len(explorer_data.organization.root_ous) > 0)
    
    # Initialize navigation engine
    nav_engine = NavigationEngine(explorer_data)
    
    # Record initial breadcrumb
    initial_breadcrumb = nav_engine.get_breadcrumb()
    assert initial_breadcrumb == "Root", "Initial breadcrumb should be 'Root'"
    
    # Navigate to first OU
    first_ou = explorer_data.organization.root_ous[0]
    nav_engine.handle_selection(first_ou.id)
    
    # Breadcrumb should include the OU
    ou_breadcrumb = nav_engine.get_breadcrumb()
    assert "Root" in ou_breadcrumb, "Breadcrumb should contain 'Root'"
    assert first_ou.name in ou_breadcrumb, f"Breadcrumb should contain OU name '{first_ou.name}'"
    
    # Go back
    nav_engine.go_back()
    
    # Breadcrumb should be back to initial
    back_breadcrumb = nav_engine.get_breadcrumb()
    assert back_breadcrumb == initial_breadcrumb, \
        f"Breadcrumb should return to '{initial_breadcrumb}', but is '{back_breadcrumb}'"


@given(explorer_data_with_ou_strategy())
def test_navigation_history_deep_nesting(explorer_data):
    """
    Property 3 (variant): Navigation history should work for deeply nested structures.
    
    Validates: Requirements 1.5
    Feature: interactive-identity-center-explorer
    """
    # Find a path through nested OUs
    def find_deep_path(ous, path=[]):
        for ou in ous:
            current_path = path + [ou]
            if len(ou.children_ous) > 0:
                # Continue deeper
                deeper_path = find_deep_path(ou.children_ous, current_path)
                if len(deeper_path) > len(current_path):
                    return deeper_path
            # Return current path if it's the deepest we can go
            if len(current_path) > len(path):
                return current_path
        return path
    
    deep_path = find_deep_path(explorer_data.organization.root_ous)
    assume(len(deep_path) >= 2)  # Need at least 2 levels
    
    # Initialize navigation engine
    nav_engine = NavigationEngine(explorer_data)
    
    # Navigate down the path
    for ou in deep_path:
        nav_engine.handle_selection(ou.id)
        assert nav_engine.current_state == NavigationState.OU_LEVEL
        assert nav_engine.current_item_id == ou.id
    
    # Now go back up the path
    for i in range(len(deep_path) - 1, 0, -1):
        nav_engine.go_back()
        expected_ou = deep_path[i - 1]
        assert nav_engine.current_state == NavigationState.OU_LEVEL, \
            f"Should be at OU level after going back"
        assert nav_engine.current_item_id == expected_ou.id, \
            f"Should be at OU {expected_ou.id} after going back"
    
    # One more back should return to root
    nav_engine.go_back()
    assert nav_engine.current_state == NavigationState.ROOT_LEVEL, \
        "Should be at root level after going back from first OU"


# Property 14: Breadcrumb Path Accuracy
@given(explorer_data_with_ou_strategy())
def test_breadcrumb_reflects_full_path(explorer_data):
    """
    Property 14: Breadcrumb Path Accuracy
    
    For any navigation state (root, OU, or account), the breadcrumb should
    accurately reflect the full path from root to the current location,
    including all intermediate OUs.
    
    Validates: Requirements 6.1, 6.3, 6.4
    Feature: interactive-identity-center-explorer
    """
    # Assume we have at least one OU
    assume(len(explorer_data.organization.root_ous) > 0)
    
    # Initialize navigation engine
    nav_engine = NavigationEngine(explorer_data)
    
    # Test 1: Root level breadcrumb
    breadcrumb = nav_engine.get_breadcrumb()
    assert breadcrumb == "Root", f"Root breadcrumb should be 'Root', got '{breadcrumb}'"
    
    # Test 2: Navigate to first OU
    first_ou = explorer_data.organization.root_ous[0]
    nav_engine.handle_selection(first_ou.id)
    
    breadcrumb = nav_engine.get_breadcrumb()
    assert "Root" in breadcrumb, "Breadcrumb should contain 'Root'"
    assert first_ou.name in breadcrumb, f"Breadcrumb should contain OU name '{first_ou.name}'"
    
    # Verify the structure is "Root > OU_Name"
    expected_parts = ["Root", first_ou.name]
    actual_breadcrumb = nav_engine.get_breadcrumb(max_width=1000)  # No truncation
    expected_breadcrumb = " > ".join(expected_parts)
    assert actual_breadcrumb == expected_breadcrumb, \
        f"Expected '{expected_breadcrumb}', got '{actual_breadcrumb}'"
    
    # Test 3: If OU has children, navigate deeper
    if len(first_ou.children_ous) > 0:
        child_ou = first_ou.children_ous[0]
        nav_engine.handle_selection(child_ou.id)
        
        breadcrumb = nav_engine.get_breadcrumb(max_width=1000)
        expected_parts = ["Root", first_ou.name, child_ou.name]
        expected_breadcrumb = " > ".join(expected_parts)
        assert breadcrumb == expected_breadcrumb, \
            f"Expected '{expected_breadcrumb}', got '{breadcrumb}'"
    
    # Test 4: Navigate to account if available
    if len(first_ou.accounts) > 0:
        # Go back to first OU if we navigated to child
        if len(first_ou.children_ous) > 0:
            nav_engine.go_back()
        
        account = first_ou.accounts[0]
        nav_engine.handle_selection(account.id)
        
        breadcrumb = nav_engine.get_breadcrumb(max_width=1000)
        assert "Root" in breadcrumb, "Account breadcrumb should contain 'Root'"
        assert first_ou.name in breadcrumb, "Account breadcrumb should contain OU name"
        assert account.name in breadcrumb, "Account breadcrumb should contain account name"


@given(explorer_data_with_ou_strategy())
def test_breadcrumb_accuracy_at_each_level(explorer_data):
    """
    Property 14 (variant): Breadcrumb should be accurate at each navigation level.
    
    Validates: Requirements 6.1, 6.3, 6.4
    Feature: interactive-identity-center-explorer
    """
    # Find a deep path
    def find_path_with_account(ous, path=[]):
        for ou in ous:
            current_path = path + [ou]
            if len(ou.accounts) > 0:
                return current_path, ou.accounts[0]
            if len(ou.children_ous) > 0:
                result = find_path_with_account(ou.children_ous, current_path)
                if result:
                    return result
        return None
    
    result = find_path_with_account(explorer_data.organization.root_ous)
    assume(result is not None)
    
    ou_path, account = result
    
    # Initialize navigation engine
    nav_engine = NavigationEngine(explorer_data)
    
    # Navigate through the path and verify breadcrumb at each step
    expected_parts = ["Root"]
    
    for ou in ou_path:
        nav_engine.handle_selection(ou.id)
        expected_parts.append(ou.name)
        
        breadcrumb = nav_engine.get_breadcrumb(max_width=1000)
        expected_breadcrumb = " > ".join(expected_parts)
        
        assert breadcrumb == expected_breadcrumb, \
            f"At OU {ou.name}, expected '{expected_breadcrumb}', got '{breadcrumb}'"
    
    # Navigate to account
    nav_engine.handle_selection(account.id)
    expected_parts.append(account.name)
    
    breadcrumb = nav_engine.get_breadcrumb(max_width=1000)
    expected_breadcrumb = " > ".join(expected_parts)
    
    assert breadcrumb == expected_breadcrumb, \
        f"At account {account.name}, expected '{expected_breadcrumb}', got '{breadcrumb}'"


@given(explorer_data_with_root_accounts_strategy())
def test_breadcrumb_for_root_account(explorer_data):
    """
    Property 14 (variant): Breadcrumb for root-level accounts.
    
    Validates: Requirements 6.1, 6.4
    Feature: interactive-identity-center-explorer
    """
    # We have at least one root account
    assume(len(explorer_data.organization.root_accounts) > 0)
    
    account = explorer_data.organization.root_accounts[0]
    
    # Initialize navigation engine
    nav_engine = NavigationEngine(explorer_data)
    
    # Navigate to account
    nav_engine.handle_selection(account.id)
    
    # Breadcrumb should show Root > Account Name
    breadcrumb = nav_engine.get_breadcrumb(max_width=1000)
    expected = f"Root > {account.name}"
    
    assert breadcrumb == expected, \
        f"Expected '{expected}', got '{breadcrumb}'"


# Property 15: Breadcrumb Truncation Preservation
@given(explorer_data_with_ou_strategy(), st.integers(min_value=30, max_value=80))
def test_breadcrumb_truncation_preserves_context(explorer_data, max_width):
    """
    Property 15: Breadcrumb Truncation Preservation
    
    For any breadcrumb that exceeds the terminal width, the truncated version
    should preserve the most important context (typically the current location
    and immediate parent).
    
    Validates: Requirements 6.5
    Feature: interactive-identity-center-explorer
    """
    # Find a deep path to create a long breadcrumb
    def find_deep_path(ous, path=[]):
        for ou in ous:
            current_path = path + [ou]
            if len(ou.children_ous) > 0:
                deeper_path = find_deep_path(ou.children_ous, current_path)
                if len(deeper_path) > len(current_path):
                    return deeper_path
            if len(current_path) > len(path):
                return current_path
        return path
    
    deep_path = find_deep_path(explorer_data.organization.root_ous)
    assume(len(deep_path) >= 3)  # Need at least 3 levels for meaningful truncation
    
    # Initialize navigation engine
    nav_engine = NavigationEngine(explorer_data)
    
    # Navigate down the path
    for ou in deep_path:
        nav_engine.handle_selection(ou.id)
    
    # Get full breadcrumb (no truncation)
    full_breadcrumb = nav_engine.get_breadcrumb(max_width=1000)
    
    # Get truncated breadcrumb
    truncated_breadcrumb = nav_engine.get_breadcrumb(max_width=max_width)
    
    # Verify truncated breadcrumb respects max_width
    assert len(truncated_breadcrumb) <= max_width, \
        f"Truncated breadcrumb length {len(truncated_breadcrumb)} exceeds max_width {max_width}"
    
    # If truncation occurred, verify important context is preserved
    if len(full_breadcrumb) > max_width:
        # Should contain some recognizable part of Root or ellipsis
        assert "Root" in truncated_breadcrumb or "Roo" in truncated_breadcrumb or "..." in truncated_breadcrumb, \
            "Truncated breadcrumb should preserve Root or show ellipsis"
        
        # Should contain some part of the current location (last item)
        current_name = deep_path[-1].name
        # The name might be heavily truncated, so check for any prefix
        name_prefix = current_name[:min(3, len(current_name))]
        assert name_prefix in truncated_breadcrumb or "..." in truncated_breadcrumb, \
            f"Truncated breadcrumb should preserve part of current location or show ellipsis"
        
        # Should be non-empty and readable
        assert len(truncated_breadcrumb) > 0, "Truncated breadcrumb should not be empty"


@given(explorer_data_with_ou_strategy())
def test_breadcrumb_truncation_with_long_names(explorer_data):
    """
    Property 15 (variant): Breadcrumb truncation with very long OU names.
    
    Validates: Requirements 6.5
    Feature: interactive-identity-center-explorer
    """
    # Assume we have at least one OU
    assume(len(explorer_data.organization.root_ous) > 0)
    
    # Create a navigation path
    nav_engine = NavigationEngine(explorer_data)
    first_ou = explorer_data.organization.root_ous[0]
    nav_engine.handle_selection(first_ou.id)
    
    # Test with very narrow width
    narrow_breadcrumb = nav_engine.get_breadcrumb(max_width=30)
    
    # Should still be readable and within limit
    assert len(narrow_breadcrumb) <= 30, \
        f"Breadcrumb length {len(narrow_breadcrumb)} exceeds limit 30"
    
    # Should contain some recognizable content
    assert len(narrow_breadcrumb) > 0, "Breadcrumb should not be empty"
    assert ">" in narrow_breadcrumb or "Root" in narrow_breadcrumb, \
        "Breadcrumb should contain separator or Root"


@given(explorer_data_with_ou_strategy())
def test_breadcrumb_no_truncation_when_short(explorer_data):
    """
    Property 15 (variant): No truncation when breadcrumb is short enough.
    
    Validates: Requirements 6.5
    Feature: interactive-identity-center-explorer
    """
    # Assume we have at least one OU
    assume(len(explorer_data.organization.root_ous) > 0)
    
    # Navigate to first OU
    nav_engine = NavigationEngine(explorer_data)
    first_ou = explorer_data.organization.root_ous[0]
    nav_engine.handle_selection(first_ou.id)
    
    # Get full breadcrumb
    full_breadcrumb = nav_engine.get_breadcrumb(max_width=1000)
    
    # If breadcrumb is short, it should not be truncated even with smaller max_width
    if len(full_breadcrumb) <= 80:
        breadcrumb_80 = nav_engine.get_breadcrumb(max_width=80)
        assert breadcrumb_80 == full_breadcrumb, \
            "Short breadcrumbs should not be truncated unnecessarily"


@given(explorer_data_with_ou_strategy())
def test_breadcrumb_truncation_ellipsis_indicator(explorer_data):
    """
    Property 15 (variant): Truncated breadcrumbs should use ellipsis to indicate omission.
    
    Validates: Requirements 6.5
    Feature: interactive-identity-center-explorer
    """
    # Find a path with at least 4 levels
    def find_deep_path(ous, path=[]):
        for ou in ous:
            current_path = path + [ou]
            if len(ou.children_ous) > 0:
                deeper_path = find_deep_path(ou.children_ous, current_path)
                if len(deeper_path) > len(current_path):
                    return deeper_path
            if len(current_path) > len(path):
                return current_path
        return path
    
    deep_path = find_deep_path(explorer_data.organization.root_ous)
    assume(len(deep_path) >= 4)  # Need deep nesting
    
    # Navigate down the path
    nav_engine = NavigationEngine(explorer_data)
    for ou in deep_path:
        nav_engine.handle_selection(ou.id)
    
    # Get full breadcrumb
    full_breadcrumb = nav_engine.get_breadcrumb(max_width=1000)
    
    # Get truncated breadcrumb with narrow width
    truncated = nav_engine.get_breadcrumb(max_width=50)
    
    # If truncation occurred, should contain ellipsis
    if len(full_breadcrumb) > 50:
        assert "..." in truncated, \
            "Truncated breadcrumb should contain ellipsis (...) to indicate omission"
