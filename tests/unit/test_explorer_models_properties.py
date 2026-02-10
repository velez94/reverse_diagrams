"""Property-based tests for explorer data models.

Feature: interactive-identity-center-explorer
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from src.explorer.models import (
    User,
    Group,
    PermissionSet,
    Assignment,
    Account,
    OrganizationalUnit,
    OrganizationTree,
)


# Strategies for generating test data
@st.composite
def user_strategy(draw):
    """Generate a random User."""
    user_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters="\x00")))
    username = draw(st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_characters="\x00")))
    email = draw(st.one_of(st.none(), st.emails()))
    display_name = draw(st.one_of(st.none(), st.text(min_size=1, max_size=100)))
    
    return User(
        id=user_id,
        username=username,
        email=email,
        display_name=display_name
    )


@st.composite
def group_strategy(draw, min_members=0, max_members=10):
    """Generate a random Group."""
    group_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters="\x00")))
    name = draw(st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_characters="\x00")))
    description = draw(st.one_of(st.none(), st.text(max_size=200)))
    members = draw(st.lists(user_strategy(), min_size=min_members, max_size=max_members))
    
    return Group(
        id=group_id,
        name=name,
        description=description,
        members=members
    )


@st.composite
def account_strategy(draw):
    """Generate a random Account."""
    account_id = draw(st.text(min_size=12, max_size=12, alphabet=st.characters(whitelist_categories=("Nd",))))
    name = draw(st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_characters="\x00")))
    email = draw(st.emails())
    status = draw(st.sampled_from(["ACTIVE", "SUSPENDED", "PENDING_CLOSURE"]))
    parent_ou_id = draw(st.one_of(st.none(), st.text(min_size=1, max_size=50)))
    
    return Account(
        id=account_id,
        name=name,
        email=email,
        status=status,
        parent_ou_id=parent_ou_id
    )


@st.composite
def ou_strategy(draw, max_depth=3, current_depth=0):
    """Generate a random OrganizationalUnit with nested structure."""
    ou_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters="\x00")))
    name = draw(st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_characters="\x00")))
    parent_id = draw(st.one_of(st.none(), st.text(min_size=1, max_size=50)))
    
    # Limit recursion depth
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
        parent_id=parent_id,
        children_ous=children_ous,
        accounts=accounts
    )


# Property 21: Organization Tree Structure Integrity
# Feature: interactive-identity-center-explorer, Property 21: Organization Tree Structure Integrity
@settings(suppress_health_check=[HealthCheck.too_slow])
@given(
    root_id=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters="\x00")),
    root_ous=st.lists(ou_strategy(max_depth=2), max_size=3),
    root_accounts=st.lists(account_strategy(), max_size=3, unique_by=lambda acc: acc.id)
)
def test_organization_tree_structure_integrity(root_id, root_ous, root_accounts):
    """
    Property 21: Organization Tree Structure Integrity
    Validates: Requirements 10.1
    
    For any valid organizations_complete.json file, the Data Loader should create
    a tree structure where every OU has a valid parent reference (or is a root OU),
    and every account belongs to exactly one OU or the root.
    """
    # Build all_accounts dictionary
    all_accounts = {}
    for account in root_accounts:
        all_accounts[account.id] = account
    
    for ou in root_ous:
        for account in ou.get_all_accounts():
            # Skip if account ID already exists (can happen with nested OUs)
            if account.id not in all_accounts:
                all_accounts[account.id] = account
    
    # Create organization tree
    org_tree = OrganizationTree(
        root_id=root_id,
        root_ous=root_ous,
        root_accounts=root_accounts,
        all_accounts=all_accounts
    )
    
    # Property: Tree should be valid
    assert org_tree.validate(), "Organization tree should be valid"
    
    # Property: All accounts should be in all_accounts dictionary
    for account in root_accounts:
        assert account.id in org_tree.all_accounts, f"Root account {account.id} should be in all_accounts"
    
    for ou in root_ous:
        for account in ou.get_all_accounts():
            assert account.id in org_tree.all_accounts, f"OU account {account.id} should be in all_accounts"
    
    # Property: Total account count should match unique accounts
    expected_count = len(all_accounts)
    actual_count = org_tree.get_total_account_count()
    assert actual_count == expected_count, f"Total account count should be {expected_count}, got {actual_count}"


# Additional property tests for individual models
@given(user_strategy())
def test_user_validation_property(user):
    """Valid users should pass validation."""
    # Property: A user with id and username should be valid
    if user.id and user.username:
        assert user.validate(), "User with id and username should be valid"


@given(group_strategy())
def test_group_validation_property(group):
    """Valid groups should pass validation."""
    # Property: A group with id and name should be valid if all members are valid
    if group.id and group.name:
        all_members_valid = all(member.validate() for member in group.members)
        assert group.validate() == all_members_valid, "Group validation should match member validation"


@given(account_strategy())
def test_account_validation_property(account):
    """Valid accounts should pass validation."""
    # Property: An account with id, name, and email should be valid
    if account.id and account.name and account.email:
        assert account.validate(), "Account with id, name, and email should be valid"


@given(ou_strategy(max_depth=2))
def test_ou_validation_property(ou):
    """Valid OUs should pass validation."""
    # Property: An OU with id and name should be valid if all children are valid
    if ou.id and ou.name:
        all_children_valid = all(child.validate() for child in ou.children_ous)
        all_accounts_valid = all(account.validate() for account in ou.accounts)
        expected_valid = all_children_valid and all_accounts_valid
        assert ou.validate() == expected_valid, "OU validation should match children validation"


@given(ou_strategy(max_depth=2))
def test_ou_get_all_accounts_property(ou):
    """get_all_accounts should return all accounts recursively."""
    # Property: get_all_accounts should include direct accounts and all nested accounts
    all_accounts = ou.get_all_accounts()
    
    # Direct accounts should be included
    for account in ou.accounts:
        assert account in all_accounts, "Direct accounts should be in get_all_accounts result"
    
    # Nested accounts should be included
    for child_ou in ou.children_ous:
        for account in child_ou.get_all_accounts():
            assert account in all_accounts, "Nested accounts should be in get_all_accounts result"


@given(ou_strategy(max_depth=1))
def test_ou_child_count_property(ou):
    """Child count should equal number of child OUs plus accounts."""
    # Property: get_child_count should equal len(children_ous) + len(accounts)
    expected_count = len(ou.children_ous) + len(ou.accounts)
    actual_count = ou.get_child_count()
    assert actual_count == expected_count, f"Child count should be {expected_count}, got {actual_count}"


@given(ou_strategy(max_depth=1))
def test_ou_is_empty_property(ou):
    """is_empty should be true only when no children or accounts."""
    # Property: is_empty should be True iff get_child_count() == 0
    is_empty = ou.is_empty()
    has_no_children = ou.get_child_count() == 0
    assert is_empty == has_no_children, "is_empty should match having no children"
