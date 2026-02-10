"""Unit tests for the Display Manager.

Feature: interactive-identity-center-explorer
"""

import pytest
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


@pytest.fixture
def display_manager():
    """Create a DisplayManager with a string buffer console."""
    string_buffer = StringIO()
    console = Console(file=string_buffer, force_terminal=True, width=120)
    return DisplayManager(console), string_buffer


def test_display_manager_initialization():
    """Test DisplayManager initialization."""
    dm = DisplayManager()
    assert dm.console is not None
    assert dm.pagination_threshold == 100
    assert dm.get_terminal_width() > 0


def test_format_ou(display_manager):
    """Test OU formatting includes icon and name."""
    dm, buffer = display_manager
    
    ou = OrganizationalUnit(id="ou-123", name="Test OU")
    formatted = dm.format_ou(ou)
    
    assert DisplayManager.ICON_OU in formatted
    assert "Test OU" in formatted


def test_format_account(display_manager):
    """Test account formatting includes name and ID."""
    dm, buffer = display_manager
    
    account = Account(id="123456789012", name="Test Account", email="test@example.com")
    formatted = dm.format_account(account)
    
    assert "Test Account" in formatted
    assert "123456789012" in formatted
    assert "(" in formatted and ")" in formatted


def test_format_permission_set(display_manager):
    """Test permission set formatting includes icon and name."""
    dm, buffer = display_manager
    
    ps = PermissionSet(arn="arn:aws:sso:::permissionSet/test", name="TestPS")
    formatted = dm.format_permission_set(ps)
    
    assert DisplayManager.ICON_PERMISSION_SET in formatted
    assert "TestPS" in formatted


def test_format_group(display_manager):
    """Test group formatting includes icon, name, and member count."""
    dm, buffer = display_manager
    
    users = [
        User(id="u1", username="user1"),
        User(id="u2", username="user2"),
    ]
    group = Group(id="g1", name="TestGroup", members=users)
    formatted = dm.format_group(group)
    
    assert DisplayManager.ICON_GROUP in formatted
    assert "TestGroup" in formatted
    assert "2 members" in formatted


def test_format_user(display_manager):
    """Test user formatting includes icon and display text."""
    dm, buffer = display_manager
    
    user = User(id="u1", username="user1", email="user1@example.com", display_name="User One")
    formatted = dm.format_user(user)
    
    assert DisplayManager.ICON_USER in formatted
    assert "User One" in formatted or "user1@example.com" in formatted


def test_display_error(display_manager):
    """Test error display includes icon and message."""
    dm, buffer = display_manager
    
    dm.display_error("Test error message")
    output = buffer.getvalue()
    
    assert DisplayManager.ICON_ERROR in output
    assert "Test error message" in output


def test_display_warning(display_manager):
    """Test warning display includes icon and message."""
    dm, buffer = display_manager
    
    dm.display_warning("Test warning message")
    output = buffer.getvalue()
    
    assert DisplayManager.ICON_WARNING in output
    assert "Test warning message" in output


def test_display_success(display_manager):
    """Test success display includes icon and message."""
    dm, buffer = display_manager
    
    dm.display_success("Test success message")
    output = buffer.getvalue()
    
    assert DisplayManager.ICON_SUCCESS in output
    assert "Test success message" in output


def test_display_empty_state(display_manager):
    """Test empty state display."""
    dm, buffer = display_manager
    
    dm.display_empty_state("No items found")
    output = buffer.getvalue()
    
    assert "No items found" in output


def test_display_breadcrumb(display_manager):
    """Test breadcrumb display."""
    dm, buffer = display_manager
    
    dm.display_breadcrumb("Root > OU1 > Account1")
    output = buffer.getvalue()
    
    assert "Root > OU1 > Account1" in output


def test_show_welcome_screen(display_manager):
    """Test welcome screen display."""
    dm, buffer = display_manager
    
    dm.show_welcome_screen()
    output = buffer.getvalue()
    
    assert "AWS Organizations Explorer" in output
    assert "Keyboard Shortcuts" in output


def test_display_account_details_empty(display_manager):
    """Test account details display with no assignments."""
    dm, buffer = display_manager
    
    account = Account(id="123456789012", name="Test Account", email="test@example.com")
    dm.display_account_details(account, [], {})
    
    output = buffer.getvalue()
    assert "Test Account" in output
    assert "No IAM Identity Center assignments" in output


def test_display_account_details_with_group_assignment(display_manager):
    """Test account details display with group assignment."""
    dm, buffer = display_manager
    
    account = Account(id="123456789012", name="Test Account", email="test@example.com")
    ps = PermissionSet(arn="arn:aws:sso:::permissionSet/test", name="TestPS")
    assignment = Assignment(
        account_id="123456789012",
        permission_set=ps,
        principal_type="GROUP",
        principal_id="g1",
        principal_name="TestGroup"
    )
    
    user = User(id="u1", username="user1", email="user1@example.com")
    group = Group(id="g1", name="TestGroup", members=[user])
    
    dm.display_account_details(account, [assignment], {"g1": group})
    
    output = buffer.getvalue()
    assert "Test Account" in output
    assert "TestPS" in output
    assert "TestGroup" in output
    assert "user1@example.com" in output
    assert "Group-Based Access" in output


def test_display_account_details_with_direct_user_assignment(display_manager):
    """Test account details display with direct user assignment."""
    dm, buffer = display_manager
    
    account = Account(id="123456789012", name="Test Account", email="test@example.com")
    ps = PermissionSet(arn="arn:aws:sso:::permissionSet/test", name="TestPS")
    assignment = Assignment(
        account_id="123456789012",
        permission_set=ps,
        principal_type="USER",
        principal_id="u1",
        principal_name="user1@example.com"
    )
    
    dm.display_account_details(account, [assignment], {})
    
    output = buffer.getvalue()
    assert "Test Account" in output
    assert "TestPS" in output
    assert "user1@example.com" in output
    assert "direct" in output.lower()
    assert "Direct User Access" in output


def test_display_account_details_summary_statistics(display_manager):
    """Test account details display includes summary statistics."""
    dm, buffer = display_manager
    
    account = Account(id="123456789012", name="Test Account", email="test@example.com")
    ps = PermissionSet(arn="arn:aws:sso:::permissionSet/test", name="TestPS")
    assignment = Assignment(
        account_id="123456789012",
        permission_set=ps,
        principal_type="GROUP",
        principal_id="g1",
        principal_name="TestGroup"
    )
    
    user = User(id="u1", username="user1", email="user1@example.com")
    group = Group(id="g1", name="TestGroup", members=[user])
    
    dm.display_account_details(account, [assignment], {"g1": group})
    
    output = buffer.getvalue()
    assert "Summary" in output
    assert "1 permission sets" in output
    assert "1 groups" in output
    assert "1 unique users" in output


def test_should_paginate():
    """Test pagination threshold logic."""
    dm = DisplayManager()
    
    assert not dm.should_paginate(50)
    assert not dm.should_paginate(100)
    assert dm.should_paginate(101)
    assert dm.should_paginate(500)


def test_get_terminal_width():
    """Test terminal width detection."""
    string_buffer = StringIO()
    console = Console(file=string_buffer, force_terminal=True, width=100)
    dm = DisplayManager(console)
    
    assert dm.get_terminal_width() == 100
