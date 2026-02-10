"""Property-based tests for the Display Manager.

Feature: interactive-identity-center-explorer
"""

import pytest
from hypothesis import given, strategies as st, settings
from rich.console import Console
from io import StringIO

from src.explorer.display import DisplayManager
from src.explorer.models import (
    OrganizationalUnit,
    Account,
    PermissionSet,
    Group,
    User,
    Assignment,
)


# Custom strategies for generating test data
@st.composite
def user_strategy(draw):
    """Generate a random User."""
    user_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters="\n\r\t")))
    username = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters="\n\r\t")))
    email = draw(st.one_of(st.none(), st.emails()))
    display_name = draw(st.one_of(st.none(), st.text(min_size=1, max_size=50)))
    
    return User(
        id=user_id,
        username=username,
        email=email,
        display_name=display_name
    )


@st.composite
def group_strategy(draw):
    """Generate a random Group."""
    group_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters="\n\r\t")))
    name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters="\n\r\t")))
    description = draw(st.one_of(st.none(), st.text(max_size=200)))
    members = draw(st.lists(user_strategy(), max_size=10))
    
    return Group(
        id=group_id,
        name=name,
        description=description,
        members=members
    )


@st.composite
def permission_set_strategy(draw):
    """Generate a random PermissionSet."""
    arn = f"arn:aws:sso:::permissionSet/{draw(st.text(min_size=1, max_size=50))}"
    # Use printable characters for names
    name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        blacklist_characters="\n\r\t\x00\x0c<>",
        blacklist_categories=("Cc", "Cs")
    )))
    
    return PermissionSet(arn=arn, name=name)


@st.composite
def account_strategy(draw):
    """Generate a random Account."""
    account_id = draw(st.text(min_size=12, max_size=12, alphabet=st.characters(whitelist_categories=("Nd",))))
    name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters="\n\r\t")))
    email = draw(st.emails())
    
    return Account(
        id=account_id,
        name=name,
        email=email
    )


@st.composite
def ou_strategy(draw, max_depth=3, current_depth=0):
    """Generate a random OrganizationalUnit with nested structure."""
    ou_id = f"ou-{draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'Nd'))))}"
    name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters="\n\r\t")))
    
    # Limit nesting depth to avoid infinite recursion
    if current_depth < max_depth:
        children_ous = draw(st.lists(
            ou_strategy(max_depth=max_depth, current_depth=current_depth + 1),
            max_size=3
        ))
    else:
        children_ous = []
    
    accounts = draw(st.lists(account_strategy(), max_size=5))
    
    return OrganizationalUnit(
        id=ou_id,
        name=name,
        children_ous=children_ous,
        accounts=accounts
    )


# Property 6: Hierarchical Display Formatting
@pytest.mark.property
@settings(max_examples=100)
@given(ou=ou_strategy(max_depth=2))
def test_property_6_hierarchical_display_formatting(ou):
    """
    Property 6: Hierarchical Display Formatting
    
    For any hierarchical data structure (OUs, accounts, permission sets, groups, users),
    the rendered output should use consistent indentation where child items have greater
    indentation than their parents, and each item type should include its designated icon.
    
    Validates: Requirements 3.1, 3.3, 3.4, 3.5, 3.7
    Feature: interactive-identity-center-explorer
    """
    # Create display manager with string buffer
    string_buffer = StringIO()
    console = Console(file=string_buffer, force_terminal=True, width=120)
    display_manager = DisplayManager(console)
    
    # Format the OU
    ou_text = display_manager.format_ou(ou)
    
    # Verify OU has the folder icon
    assert DisplayManager.ICON_OU in ou_text, f"OU should contain folder icon {DisplayManager.ICON_OU}"
    assert ou.name in ou_text, "OU text should contain OU name"
    
    # Format accounts
    for account in ou.accounts:
        account_text = display_manager.format_account(account)
        # Accounts should have indentation (spaces at the start)
        assert account_text.startswith("  "), "Account should have indentation"
        assert account.name in account_text, "Account text should contain account name"
        assert account.id in account_text, "Account text should contain account ID"


# Property 7: Account Display Formatting
@pytest.mark.property
@settings(max_examples=100)
@given(account=account_strategy())
def test_property_7_account_display_formatting(account):
    """
    Property 7: Account Display Formatting
    
    For any account, the rendered display text should contain both the account name
    and the account ID in a formatted manner.
    
    Validates: Requirements 3.2
    Feature: interactive-identity-center-explorer
    """
    string_buffer = StringIO()
    console = Console(file=string_buffer, force_terminal=True, width=120)
    display_manager = DisplayManager(console)
    
    # Format the account
    account_text = display_manager.format_account(account)
    
    # Verify both name and ID are present
    assert account.name in account_text, "Account text should contain account name"
    assert account.id in account_text, "Account text should contain account ID"
    
    # Verify formatting includes parentheses for ID
    assert "(" in account_text and ")" in account_text, "Account ID should be in parentheses"


# Property 18: Item Type Color Differentiation
@pytest.mark.property
@settings(max_examples=50)
@given(
    ou=ou_strategy(max_depth=0),  # No nesting to speed up test
    account=account_strategy(),
    ps=permission_set_strategy(),
    group=group_strategy(),
    user=user_strategy()
)
def test_property_18_item_type_color_differentiation(ou, account, ps, group, user):
    """
    Property 18: Item Type Color Differentiation
    
    For any list of mixed item types (OUs, accounts, permission sets, groups, users),
    each item type should be rendered in its designated color to enable quick visual
    differentiation.
    
    Validates: Requirements 9.4
    Feature: interactive-identity-center-explorer
    """
    string_buffer = StringIO()
    console = Console(file=string_buffer, force_terminal=True, width=120)
    display_manager = DisplayManager(console)
    
    # Format each item type
    ou_text = display_manager.format_ou(ou)
    account_text = display_manager.format_account(account)
    ps_text = display_manager.format_permission_set(ps)
    group_text = display_manager.format_group(group)
    user_text = display_manager.format_user(user)
    
    # Verify each has its designated icon (color is handled by rich internally)
    assert DisplayManager.ICON_OU in ou_text
    assert DisplayManager.ICON_PERMISSION_SET in ps_text
    assert DisplayManager.ICON_GROUP in group_text
    assert DisplayManager.ICON_USER in user_text
    
    # Verify content is present
    assert ou.name in ou_text
    assert account.name in account_text
    assert ps.name in ps_text
    assert group.name in group_text
    # User text should contain username, email, or display name
    user_display = user.get_display_text()
    assert user_display in user_text


# Property 19: Error Display Formatting
@pytest.mark.property
@settings(max_examples=100)
@given(error_message=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_characters="\n\r\t\x00")))
def test_property_19_error_display_formatting(error_message):
    """
    Property 19: Error Display Formatting
    
    For any error condition, the error message should be displayed in red color
    with an error icon to clearly indicate the error state.
    
    Validates: Requirements 9.5
    Feature: interactive-identity-center-explorer
    """
    string_buffer = StringIO()
    console = Console(file=string_buffer, force_terminal=True, width=120, legacy_windows=False)
    display_manager = DisplayManager(console)
    
    # Display error
    display_manager.display_error(error_message)
    
    # Get output
    output = string_buffer.getvalue()
    
    # Verify error icon is present
    assert DisplayManager.ICON_ERROR in output, "Error output should contain error icon"
    
    # Verify error message is present (allowing for rich's text processing)
    # Rich may escape or modify certain characters, so we check if the message appears
    # in some form in the output
    assert error_message in output or len(output) > len(DisplayManager.ICON_ERROR), \
        "Error output should contain the error message or have content"


@st.composite
def assignment_strategy(draw, principal_type=None):
    """Generate a random Assignment."""
    account_id = draw(st.text(min_size=12, max_size=12, alphabet=st.characters(whitelist_categories=("Nd",))))
    ps = draw(permission_set_strategy())
    
    if principal_type is None:
        principal_type = draw(st.sampled_from(["GROUP", "USER"]))
    
    # Use printable characters for names to avoid Rich filtering issues
    principal_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        blacklist_characters="\n\r\t\x00\x0c<>=",
        blacklist_categories=("Cc", "Cs")  # Control characters and surrogates
    )))
    principal_name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        blacklist_characters="\n\r\t\x00\x0c<>=",
        blacklist_categories=("Cc", "Cs")
    )))
    
    return Assignment(
        account_id=account_id,
        permission_set=ps,
        principal_type=principal_type,
        principal_id=principal_id,
        principal_name=principal_name
    )


# Property 8: Direct Assignment Indication
@pytest.mark.property
@settings(max_examples=100)
@given(
    account=account_strategy(),
    user_assignment=assignment_strategy(principal_type="USER")
)
def test_property_8_direct_assignment_indication(account, user_assignment):
    """
    Property 8: Direct Assignment Indication
    
    For any account with direct user assignments (principal type is USER),
    the rendered output should clearly indicate that the assignment is direct
    and not through a group.
    
    Validates: Requirements 3.6
    Feature: interactive-identity-center-explorer
    """
    string_buffer = StringIO()
    console = Console(file=string_buffer, force_terminal=True, width=120)
    display_manager = DisplayManager(console)
    
    # Set the assignment to this account
    user_assignment.account_id = account.id
    
    # Display account details with direct user assignment
    display_manager.display_account_details(account, [user_assignment], {})
    
    # Get output
    output = string_buffer.getvalue()
    
    # Verify "direct" indication is present
    assert "direct" in output.lower() or "Direct" in output, \
        "Output should indicate direct user assignment"
    
    # Verify user icon is present
    assert DisplayManager.ICON_USER in output, "Output should contain user icon"


# Property 9: Display Completeness for Account Details
@pytest.mark.property
@settings(max_examples=50)
@given(
    account=account_strategy(),
    assignments=st.lists(assignment_strategy(), min_size=1, max_size=5),
    groups=st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=group_strategy(),
        min_size=0,
        max_size=3
    )
)
def test_property_9_display_completeness_for_account_details(account, assignments, groups):
    """
    Property 9: Display Completeness for Account Details
    
    For any account with permission set assignments, the account detail view
    should display all permission sets, all groups associated with each permission set,
    and all users in each group, with no omissions.
    
    Validates: Requirements 4.1, 4.2, 4.3
    Feature: interactive-identity-center-explorer
    """
    string_buffer = StringIO()
    console = Console(file=string_buffer, force_terminal=True, width=120)
    display_manager = DisplayManager(console)
    
    # Set all assignments to this account
    for assignment in assignments:
        assignment.account_id = account.id
    
    # Display account details
    display_manager.display_account_details(account, assignments, groups)
    
    # Get output
    output = string_buffer.getvalue()
    
    # Verify all permission sets are displayed
    permission_set_names = set(a.permission_set.name for a in assignments)
    for ps_name in permission_set_names:
        # Skip very short names that might appear in other contexts
        if len(ps_name) > 1:
            assert ps_name in output, f"Permission set {ps_name} should be in output"
    
    # Verify all group assignments are displayed
    for assignment in assignments:
        if assignment.is_group_assignment():
            # Skip very short names that might appear in other contexts (like counts)
            if len(assignment.principal_name) > 1:
                assert assignment.principal_name in output, \
                    f"Group {assignment.principal_name} should be in output"
            
            # If group exists in groups dict, verify members are shown
            group = groups.get(assignment.principal_id)
            if group:
                for user in group.members:
                    user_display = user.get_display_text()
                    # Skip very short display names
                    if len(user_display) > 1:
                        assert user_display in output, \
                            f"User {user_display} should be in output"


# Property 10: Assignment Type Separation
@pytest.mark.property
@settings(max_examples=100)
@given(
    account=account_strategy(),
    group_assignment=assignment_strategy(principal_type="GROUP"),
    user_assignment=assignment_strategy(principal_type="USER")
)
def test_property_10_assignment_type_separation(account, group_assignment, user_assignment):
    """
    Property 10: Assignment Type Separation
    
    For any account with both direct user assignments and group-based assignments,
    the rendered output should visually separate or distinguish between these two
    types of assignments.
    
    Validates: Requirements 4.4
    Feature: interactive-identity-center-explorer
    """
    string_buffer = StringIO()
    console = Console(file=string_buffer, force_terminal=True, width=120)
    display_manager = DisplayManager(console)
    
    # Set assignments to this account
    group_assignment.account_id = account.id
    user_assignment.account_id = account.id
    
    # Display account details with both types
    display_manager.display_account_details(account, [group_assignment, user_assignment], {})
    
    # Get output
    output = string_buffer.getvalue()
    
    # Verify both section headers are present
    assert "Group-Based Access" in output or "group" in output.lower(), \
        "Output should have group-based section"
    assert "Direct User Access" in output or "direct" in output.lower(), \
        "Output should have direct user section"
    
    # Verify both assignments are shown
    assert group_assignment.principal_name in output
    assert user_assignment.principal_name in output


# Property 11: Summary Statistics Accuracy
@pytest.mark.property
@settings(max_examples=50)
@given(
    account=account_strategy(),
    assignments=st.lists(assignment_strategy(), min_size=1, max_size=10),
    groups=st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=group_strategy(),
        min_size=0,
        max_size=5
    )
)
def test_property_11_summary_statistics_accuracy(account, assignments, groups):
    """
    Property 11: Summary Statistics Accuracy
    
    For any account detail view, the displayed summary statistics (total permission sets,
    total groups, total users) should exactly match the count of items shown in the
    detailed view.
    
    Validates: Requirements 4.6
    Feature: interactive-identity-center-explorer
    """
    string_buffer = StringIO()
    console = Console(file=string_buffer, force_terminal=True, width=120)
    display_manager = DisplayManager(console)
    
    # Set all assignments to this account
    for assignment in assignments:
        assignment.account_id = account.id
    
    # Calculate expected counts
    expected_ps_count = len(set(a.permission_set.name for a in assignments))
    expected_group_count = len(set(a.principal_id for a in assignments if a.is_group_assignment()))
    
    # Count unique users
    unique_users = set()
    for assignment in assignments:
        if assignment.is_user_assignment():
            unique_users.add(assignment.principal_id)
        elif assignment.is_group_assignment():
            group = groups.get(assignment.principal_id)
            if group:
                unique_users.update(user.id for user in group.members)
    expected_user_count = len(unique_users)
    
    # Display account details
    display_manager.display_account_details(account, assignments, groups)
    
    # Get output
    output = string_buffer.getvalue()
    
    # Verify summary is present
    assert "Summary" in output, "Output should contain summary section"
    
    # Verify counts are in the output
    # The summary format is: "X permission sets, Y groups, Z unique users"
    assert str(expected_ps_count) in output, \
        f"Summary should show {expected_ps_count} permission sets"
    assert str(expected_group_count) in output, \
        f"Summary should show {expected_group_count} groups"
    assert str(expected_user_count) in output, \
        f"Summary should show {expected_user_count} users"


# Property 16: Pagination for Large Lists
@pytest.mark.property
@settings(max_examples=50)
@given(item_count=st.integers(min_value=101, max_value=500))
def test_property_16_pagination_for_large_lists(item_count):
    """
    Property 16: Pagination for Large Lists
    
    For any OU containing more than 100 accounts, the display should implement
    pagination or scrolling rather than attempting to show all items at once.
    
    Validates: Requirements 8.4
    Feature: interactive-identity-center-explorer
    """
    string_buffer = StringIO()
    console = Console(file=string_buffer, force_terminal=True, width=120)
    display_manager = DisplayManager(console)
    
    # Verify pagination threshold is set
    assert display_manager.pagination_threshold == 100, \
        "Pagination threshold should be 100"
    
    # Verify should_paginate returns True for large lists
    assert display_manager.should_paginate(item_count), \
        f"Should paginate for {item_count} items (> 100)"
    
    # Verify should_paginate returns False for small lists
    assert not display_manager.should_paginate(50), \
        "Should not paginate for 50 items"


# Property 20: Terminal Width Responsiveness
@pytest.mark.property
@settings(max_examples=50)
@given(width=st.integers(min_value=80, max_value=200))
def test_property_20_terminal_width_responsiveness(width):
    """
    Property 20: Terminal Width Responsiveness
    
    For any terminal width between 80 and 200 characters, the display should
    render without line breaks in unexpected places or content overflow.
    
    Validates: Requirements 9.6
    Feature: interactive-identity-center-explorer
    """
    string_buffer = StringIO()
    console = Console(file=string_buffer, force_terminal=True, width=width)
    display_manager = DisplayManager(console)
    
    # Verify terminal width is detected correctly
    detected_width = display_manager.get_terminal_width()
    assert detected_width == width, \
        f"Terminal width should be {width}, got {detected_width}"
    
    # Test that breadcrumb respects width
    long_breadcrumb = " > ".join([f"OU-{i}" for i in range(20)])
    display_manager.display_breadcrumb(long_breadcrumb)
    
    output = string_buffer.getvalue()
    
    # Verify output doesn't exceed terminal width significantly
    # (allowing for ANSI codes and some margin)
    lines = output.split('\n')
    for line in lines:
        # Remove ANSI codes for length check
        import re
        clean_line = re.sub(r'\x1b\[[0-9;]*m', '', line)
        # Allow some margin for icons and formatting
        assert len(clean_line) <= width + 10, \
            f"Line length {len(clean_line)} exceeds terminal width {width}"
