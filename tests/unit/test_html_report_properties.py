"""Property-based tests for HTML report generation.

Feature: html-report-generation
Tests correctness properties using hypothesis for property-based testing.
"""
import json
import pytest
from pathlib import Path
from hypothesis import given, strategies as st, settings
from src.reports.html_report import (
    generate_html_report,
    _generate_html_template,
    HTMLGenerationError,
    JSONParseError
)


# Strategy for generating valid organization data
@st.composite
def organization_data_strategy(draw):
    """Generate valid organization data structure."""
    return {
        "organization": {
            "Id": draw(st.text(min_size=1, max_size=50)),
            "Arn": draw(st.text(min_size=1, max_size=100)),
            "MasterAccountId": draw(st.text(min_size=12, max_size=12, alphabet=st.characters(whitelist_categories=('Nd',))))
        },
        "accounts": draw(st.lists(
            st.fixed_dictionaries({
                "Id": st.text(min_size=12, max_size=12, alphabet=st.characters(whitelist_categories=('Nd',))),
                "Name": st.text(min_size=1, max_size=50),
                "Email": st.emails(),
                "Status": st.sampled_from(["ACTIVE", "SUSPENDED"])
            }),
            min_size=0,
            max_size=10
        )),
        "organizational_units": draw(st.lists(
            st.fixed_dictionaries({
                "Id": st.text(min_size=1, max_size=50),
                "Name": st.text(min_size=1, max_size=50)
            }),
            min_size=0,
            max_size=5
        ))
    }


# Strategy for generating valid groups data
@st.composite
def groups_data_strategy(draw):
    """Generate valid groups data structure."""
    return draw(st.lists(
        st.fixed_dictionaries({
            "group_name": st.text(min_size=1, max_size=50),
            "members": st.lists(
                st.fixed_dictionaries({
                    "MemberId": st.fixed_dictionaries({
                        "UserName": st.text(min_size=1, max_size=50)
                    })
                }),
                min_size=0,
                max_size=10
            )
        }),
        min_size=0,
        max_size=10
    ))


# Strategy for generating valid assignments data
@st.composite
def assignments_data_strategy(draw):
    """Generate valid account assignments data structure."""
    account_names = draw(st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=5, unique=True))
    
    result = {}
    for account_name in account_names:
        result[account_name] = draw(st.lists(
            st.fixed_dictionaries({
                "PrincipalType": st.sampled_from(["GROUP", "USER"]),
                "GroupName": st.one_of(st.none(), st.text(min_size=1, max_size=50)),
                "UserName": st.one_of(st.none(), st.text(min_size=1, max_size=50)),
                "PermissionSetName": st.text(min_size=1, max_size=50)
            }),
            min_size=0,
            max_size=5
        ))
    
    return result


@settings(max_examples=100, deadline=None)
@given(org_data=organization_data_strategy())
@pytest.mark.property_test
def test_property_5_html_content_completeness_organizations(org_data, tmp_path):
    """
    Feature: html-report-generation
    Property 5: HTML Content Completeness
    
    For any valid JSON data file (organizations), the generated HTML should include
    all key information from that file, including counts, names, IDs, and hierarchical
    relationships where applicable.
    
    Validates: Requirements 3.1, 3.2, 3.3
    """
    # Generate HTML from organization data
    output_path = tmp_path / "test_report.html"
    html_path = generate_html_report(
        organizations_data=org_data,
        output_path=str(output_path)
    )
    
    # Read generated HTML
    html_content = Path(html_path).read_text()
    
    # Verify organization ID appears in HTML
    if org_data.get("organization", {}).get("Id"):
        assert org_data["organization"]["Id"] in html_content, \
            "Organization ID should appear in HTML"
    
    # Verify account count is displayed
    account_count = len(org_data.get("accounts", []))
    assert str(account_count) in html_content, \
        f"Account count {account_count} should appear in HTML"
    
    # Verify OU count is displayed
    ou_count = len(org_data.get("organizational_units", []))
    assert str(ou_count) in html_content, \
        f"OU count {ou_count} should appear in HTML"
    
    # Verify account names appear in HTML
    for account in org_data.get("accounts", [])[:3]:  # Check first 3 accounts
        if account.get("Name"):
            # Account name should appear somewhere in the HTML
            assert account["Name"] in html_content or \
                   account["Name"].replace(" ", "") in html_content.replace(" ", ""), \
                   f"Account name '{account['Name']}' should appear in HTML"


@settings(max_examples=100, deadline=None)
@given(groups_data=groups_data_strategy())
@pytest.mark.property_test
def test_property_5_html_content_completeness_groups(groups_data, tmp_path):
    """
    Feature: html-report-generation
    Property 5: HTML Content Completeness
    
    For any valid groups data, the generated HTML should include all key information
    including group names, member counts, and user details.
    
    Validates: Requirements 3.1, 3.2, 3.3
    """
    # Generate HTML from groups data
    output_path = tmp_path / "test_report.html"
    html_path = generate_html_report(
        groups_data=groups_data,
        output_path=str(output_path)
    )
    
    # Read generated HTML
    html_content = Path(html_path).read_text()
    
    # Verify group count is displayed
    group_count = len(groups_data)
    assert str(group_count) in html_content, \
        f"Group count {group_count} should appear in HTML"
    
    # Verify total member count
    total_members = sum(len(group.get("members", [])) for group in groups_data)
    assert str(total_members) in html_content, \
        f"Total member count {total_members} should appear in HTML"
    
    # Verify group names appear in HTML
    for group in groups_data[:3]:  # Check first 3 groups
        if group.get("group_name"):
            assert group["group_name"] in html_content or \
                   group["group_name"].replace(" ", "") in html_content.replace(" ", ""), \
                   f"Group name '{group['group_name']}' should appear in HTML"


@settings(max_examples=100, deadline=None)
@given(assignments_data=assignments_data_strategy())
@pytest.mark.property_test
def test_property_5_html_content_completeness_assignments(assignments_data, tmp_path):
    """
    Feature: html-report-generation
    Property 5: HTML Content Completeness
    
    For any valid assignments data, the generated HTML should include all key information
    including account names, assignment counts, and permission sets.
    
    Validates: Requirements 3.1, 3.2, 3.3
    """
    # Generate HTML from assignments data
    output_path = tmp_path / "test_report.html"
    html_path = generate_html_report(
        account_assignments_data=assignments_data,
        output_path=str(output_path)
    )
    
    # Read generated HTML
    html_content = Path(html_path).read_text()
    
    # Verify account count with assignments
    account_count = len(assignments_data)
    assert str(account_count) in html_content, \
        f"Account count {account_count} should appear in HTML"
    
    # Verify total assignments count
    total_assignments = sum(len(assignments) for assignments in assignments_data.values())
    assert str(total_assignments) in html_content, \
        f"Total assignments count {total_assignments} should appear in HTML"
    
    # Verify account names appear in HTML
    for account_name in list(assignments_data.keys())[:3]:  # Check first 3 accounts
        assert account_name in html_content or \
               account_name.replace(" ", "") in html_content.replace(" ", ""), \
               f"Account name '{account_name}' should appear in HTML"



@settings(max_examples=100, deadline=None)
@given(
    org_data=st.one_of(st.none(), organization_data_strategy()),
    groups_data=st.one_of(st.none(), groups_data_strategy()),
    assignments_data=st.one_of(st.none(), assignments_data_strategy())
)
@pytest.mark.property_test
def test_property_6_html_self_containment(org_data, groups_data, assignments_data, tmp_path):
    """
    Feature: html-report-generation
    Property 6: HTML Self-Containment
    
    For any generated HTML report, the file should contain no external resource references
    (no external CSS links, no external JavaScript, no external images), and should be
    viewable in a browser without network access.
    
    Validates: Requirements 4.5
    """
    # Skip if all data is None
    if org_data is None and groups_data is None and assignments_data is None:
        pytest.skip("At least one data source required")
    
    # Generate HTML
    output_path = tmp_path / "test_report.html"
    html_path = generate_html_report(
        organizations_data=org_data,
        groups_data=groups_data,
        account_assignments_data=assignments_data,
        output_path=str(output_path)
    )
    
    # Read generated HTML
    html_content = Path(html_path).read_text()
    
    # Verify no external CSS links
    assert '<link' not in html_content.lower() or 'rel="stylesheet"' not in html_content.lower(), \
        "HTML should not contain external CSS links"
    
    # Verify no external JavaScript
    assert '<script src=' not in html_content.lower(), \
        "HTML should not contain external JavaScript references"
    
    # Verify no external images (except data URIs)
    if '<img' in html_content.lower():
        # If images exist, they should use data URIs
        assert 'src="data:' in html_content or 'src=\'data:' in html_content, \
            "Images should use data URIs, not external URLs"
    
    # Verify no http:// or https:// in src attributes (except in href for links)
    import re
    src_pattern = re.compile(r'src=["\']https?://', re.IGNORECASE)
    src_matches = src_pattern.findall(html_content)
    assert len(src_matches) == 0, \
        f"HTML should not contain external resources in src attributes: {src_matches}"
    
    # Verify CSS is embedded
    assert '<style>' in html_content and '</style>' in html_content, \
        "HTML should contain embedded CSS in <style> tags"
    
    # Verify HTML is complete and self-contained
    assert '<!DOCTYPE html>' in html_content, "HTML should have DOCTYPE declaration"
    assert '<html' in html_content.lower() and '</html>' in html_content.lower(), \
        "HTML should have complete html tags"
    assert '<head>' in html_content.lower() and '</head>' in html_content.lower(), \
        "HTML should have complete head section"
    assert '<body>' in html_content.lower() and '</body>' in html_content.lower(), \
        "HTML should have complete body section"



@settings(max_examples=100, deadline=None)
@given(
    org_data=st.one_of(st.none(), organization_data_strategy()),
    groups_data=st.one_of(st.none(), groups_data_strategy()),
    assignments_data=st.one_of(st.none(), assignments_data_strategy())
)
@pytest.mark.property_test
def test_property_7_html_structure_validity(org_data, groups_data, assignments_data, tmp_path):
    """
    Feature: html-report-generation
    Property 7: HTML Structure Validity
    
    For any generated HTML report, the file should contain a header with timestamp,
    modern CSS styling (including gradients and card layouts), color-coded badges
    for resource types, and responsive design elements.
    
    Validates: Requirements 4.1, 4.2, 4.3, 4.4
    """
    # Skip if all data is None
    if org_data is None and groups_data is None and assignments_data is None:
        pytest.skip("At least one data source required")
    
    # Generate HTML
    output_path = tmp_path / "test_report.html"
    html_path = generate_html_report(
        organizations_data=org_data,
        groups_data=groups_data,
        account_assignments_data=assignments_data,
        output_path=str(output_path)
    )
    
    # Read generated HTML
    html_content = Path(html_path).read_text()
    
    # Verify header with timestamp exists
    assert 'Generated:' in html_content or 'generated' in html_content.lower(), \
        "HTML should contain generation timestamp in header"
    
    # Verify modern CSS styling with gradients
    assert 'linear-gradient' in html_content, \
        "HTML should contain gradient styling"
    
    # Verify card layouts
    assert 'card' in html_content.lower(), \
        "HTML should contain card layout elements"
    
    # Verify color-coded badges
    assert 'badge' in html_content.lower(), \
        "HTML should contain badge elements for resource types"
    
    # Verify multiple badge types exist
    badge_types = ['badge-primary', 'badge-success', 'badge-info', 'badge-warning']
    badge_count = sum(1 for badge_type in badge_types if badge_type in html_content)
    # At least one badge type should be present
    assert badge_count > 0, \
        "HTML should contain at least one type of color-coded badge"
    
    # Verify responsive design elements
    assert '@media' in html_content, \
        "HTML should contain media queries for responsive design"
    
    # Verify viewport meta tag for mobile responsiveness
    assert 'viewport' in html_content.lower(), \
        "HTML should contain viewport meta tag for responsive design"
    
    # Verify modern CSS properties
    modern_css_properties = ['border-radius', 'box-shadow', 'flex', 'grid']
    css_property_count = sum(1 for prop in modern_css_properties if prop in html_content)
    assert css_property_count >= 2, \
        f"HTML should contain modern CSS properties (found {css_property_count} of {len(modern_css_properties)})"
    
    # Verify header structure
    assert '<h1' in html_content.lower(), \
        "HTML should contain main heading"
    
    # Verify sections are properly structured
    assert 'section' in html_content.lower() or 'class=' in html_content, \
        "HTML should have structured sections"



@settings(max_examples=100, deadline=None)
@given(
    org_data=st.one_of(st.none(), organization_data_strategy()),
    # Generate valid relative paths
    path_parts=st.lists(
        st.text(min_size=1, max_size=20, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            min_codepoint=ord('a'), max_codepoint=ord('z')
        )),
        min_size=1,
        max_size=3
    ),
    filename=st.text(min_size=1, max_size=20, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        min_codepoint=ord('a'), max_codepoint=ord('z')
    ))
)
@pytest.mark.property_test
def test_property_4_custom_output_path_handling(org_data, path_parts, filename, tmp_path):
    """
    Feature: html-report-generation
    Property 4: Custom Output Path Handling
    
    For any valid file system path provided via --html-output, the HTML report should
    be saved to exactly that path, creating any necessary parent directories, and the
    file should be readable and contain valid HTML.
    
    Validates: Requirements 2.1, 2.2
    """
    # Skip if no data
    if org_data is None:
        org_data = {"organization": {"Id": "test-org"}, "accounts": [], "organizational_units": []}
    
    # Create a valid custom path within tmp_path
    custom_dir = tmp_path
    for part in path_parts:
        custom_dir = custom_dir / part
    
    output_path = custom_dir / f"{filename}.html"
    
    # Generate HTML with custom output path
    html_path = generate_html_report(
        organizations_data=org_data,
        output_path=str(output_path)
    )
    
    # Verify file was created at exact path
    assert Path(html_path).exists(), \
        f"HTML file should exist at {html_path}"
    
    assert Path(html_path).resolve() == output_path.resolve(), \
        f"HTML file should be at exact path {output_path}, got {html_path}"
    
    # Verify parent directories were created
    assert output_path.parent.exists(), \
        f"Parent directory {output_path.parent} should be created"
    
    # Verify file is readable
    try:
        content = Path(html_path).read_text()
    except Exception as e:
        pytest.fail(f"HTML file should be readable: {e}")
    
    # Verify content is valid HTML
    assert '<!DOCTYPE html>' in content, \
        "File should contain valid HTML with DOCTYPE"
    assert '<html' in content.lower() and '</html>' in content.lower(), \
        "File should contain complete HTML tags"



@settings(max_examples=50, deadline=None)
@given(
    invalid_type=st.sampled_from(["string", "number", "list_for_dict", "dict_for_list"])
)
@pytest.mark.property_test
def test_property_9_json_validation_before_processing(invalid_type, tmp_path):
    """
    Feature: html-report-generation
    Property 9: JSON Validation Before Processing
    
    For any JSON file provided to the HTML generator, the file structure should be
    validated before any HTML generation begins, and invalid structures should result
    in descriptive error messages that identify the problematic file.
    
    Validates: Requirements 5.5, 8.5
    """
    # Create invalid data based on type
    if invalid_type == "string":
        # Organizations should be dict, not string
        invalid_org_data = "invalid string data"
        expected_error = JSONParseError
        error_message_contains = "must be a dictionary"
    elif invalid_type == "number":
        # Organizations should be dict, not number
        invalid_org_data = 12345
        expected_error = JSONParseError
        error_message_contains = "must be a dictionary"
    elif invalid_type == "list_for_dict":
        # Organizations should be dict, not list
        invalid_org_data = ["item1", "item2"]
        expected_error = JSONParseError
        error_message_contains = "must be a dictionary"
    else:  # dict_for_list
        # Groups should be list, not dict
        invalid_groups_data = {"key": "value"}
        expected_error = JSONParseError
        error_message_contains = "must be a list"
    
    output_path = tmp_path / "report.html"
    
    # Test with invalid organizations data
    if invalid_type != "dict_for_list":
        with pytest.raises(expected_error) as exc_info:
            generate_html_report(
                organizations_data=invalid_org_data,
                output_path=str(output_path)
            )
        
        assert error_message_contains in str(exc_info.value), \
            f"Error message should contain '{error_message_contains}'"
    
    # Test with invalid groups data
    if invalid_type == "dict_for_list":
        with pytest.raises(expected_error) as exc_info:
            generate_html_report(
                groups_data=invalid_groups_data,
                output_path=str(output_path)
            )
        
        assert error_message_contains in str(exc_info.value), \
            f"Error message should contain '{error_message_contains}'"


@settings(max_examples=50, deadline=None)
@given(
    file_type=st.sampled_from(["organizations", "groups", "assignments"]),
    corruption_type=st.sampled_from(["malformed_json", "wrong_structure"])
)
@pytest.mark.property_test
def test_property_9_malformed_json_detection(file_type, corruption_type, tmp_path):
    """
    Feature: html-report-generation
    Property 9: JSON Validation Before Processing
    
    Malformed JSON files should be detected and reported with descriptive error messages.
    
    Validates: Requirements 5.5, 8.5
    """
    # Create JSON directory
    json_dir = tmp_path / "json"
    json_dir.mkdir()
    
    json_file = json_dir / f"{file_type}.json"
    
    if corruption_type == "malformed_json":
        # Create malformed JSON (invalid syntax)
        json_file.write_text('{"invalid": json syntax}')
        expected_error = JSONParseError
        error_should_mention_file = True
    else:  # wrong_structure
        # Create valid JSON but wrong structure
        if file_type == "organizations":
            # Should be dict, provide list
            json_file.write_text('["wrong", "structure"]')
        elif file_type == "groups":
            # Should be list, provide dict
            json_file.write_text('{"wrong": "structure"}')
        else:  # assignments
            # Should be dict, provide list
            json_file.write_text('["wrong", "structure"]')
        
        expected_error = JSONParseError
        error_should_mention_file = True
    
    output_path = tmp_path / "report.html"
    
    # Attempt to generate HTML from malformed file
    with pytest.raises(expected_error) as exc_info:
        generate_html_report_cli(
            html_output=str(output_path),
            json_dir=str(json_dir)
        )
    
    error_message = str(exc_info.value)
    
    # Verify error message is descriptive
    if error_should_mention_file:
        assert file_type in error_message or f"{file_type}.json" in error_message, \
            f"Error message should identify the problematic file ({file_type})"
    
    # Verify error message suggests action
    assert any(keyword in error_message.lower() for keyword in ["regenerate", "corrupted", "invalid"]), \
        "Error message should suggest corrective action"



@settings(max_examples=50, deadline=None)
@given(
    error_scenario=st.sampled_from([
        "missing_file",
        "unreadable_file",
        "malformed_json",
        "invalid_output_path"
    ])
)
@pytest.mark.property_test
def test_property_12_error_message_descriptiveness(error_scenario, tmp_path):
    """
    Feature: html-report-generation
    Property 12: Error Message Descriptiveness
    
    For any error condition during HTML generation (unreadable files, permission errors,
    malformed JSON, missing files), the error message should include the specific file
    path or resource involved, the nature of the error, and a suggested action for
    resolution.
    
    Validates: Requirements 7.3, 8.1, 8.2, 8.3
    """
    json_dir = tmp_path / "json"
    json_dir.mkdir()
    
    output_path = tmp_path / "report.html"
    
    if error_scenario == "missing_file":
        # No JSON files exist
        expected_error = JSONFileNotFoundError
        
        with pytest.raises(expected_error) as exc_info:
            generate_html_report_cli(
                html_output=str(output_path),
                json_dir=str(json_dir)
            )
        
        error_message = str(exc_info.value)
        
        # Verify error message includes file path
        assert str(json_dir) in error_message or "json" in error_message.lower(), \
            "Error message should include directory path"
        
        # Verify error message suggests action
        assert any(keyword in error_message.lower() for keyword in ["-o", "-i", "generate", "run"]), \
            "Error message should suggest running with -o or -i flags"
    
    elif error_scenario == "unreadable_file":
        # Create file but make it unreadable (simulate permission error)
        json_file = json_dir / "organizations.json"
        json_file.write_text('{"organization": {"Id": "test"}, "accounts": [], "organizational_units": []}')
        
        # Mock file read to raise PermissionError
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with pytest.raises(JSONParseError) as exc_info:
                generate_html_report_cli(
                    html_output=str(output_path),
                    json_dir=str(json_dir)
                )
            
            error_message = str(exc_info.value)
            
            # Verify error message includes file path
            assert "organizations.json" in error_message or str(json_file) in error_message, \
                "Error message should include file path"
    
    elif error_scenario == "malformed_json":
        # Create malformed JSON file
        json_file = json_dir / "organizations.json"
        json_file.write_text('{"invalid": json}')
        
        with pytest.raises(JSONParseError) as exc_info:
            generate_html_report_cli(
                html_output=str(output_path),
                json_dir=str(json_dir)
            )
        
        error_message = str(exc_info.value)
        
        # Verify error message includes file path
        assert "organizations.json" in error_message or str(json_file) in error_message, \
            "Error message should include file path"
        
        # Verify error message describes the problem
        assert any(keyword in error_message.lower() for keyword in ["invalid", "json", "corrupted"]), \
            "Error message should describe the nature of the error"
        
        # Verify error message suggests action
        assert any(keyword in error_message.lower() for keyword in ["regenerate", "flag"]), \
            "Error message should suggest regenerating the file"
    
    elif error_scenario == "invalid_output_path":
        # Create valid JSON file
        json_file = json_dir / "organizations.json"
        json_file.write_text('{"organization": {"Id": "test"}, "accounts": [], "organizational_units": []}')
        
        # Use invalid output path (e.g., path with invalid characters or non-writable)
        if hasattr(tmp_path, 'chmod'):
            # Make directory non-writable
            output_dir = tmp_path / "readonly"
            output_dir.mkdir()
            output_dir.chmod(0o444)  # Read-only
            invalid_output = output_dir / "report.html"
            
            try:
                with pytest.raises((InvalidOutputPathError, HTMLWriteError, PermissionError)) as exc_info:
                    generate_html_report_cli(
                        html_output=str(invalid_output),
                        json_dir=str(json_dir)
                    )
                
                error_message = str(exc_info.value)
                
                # Verify error message includes path
                assert str(output_dir) in error_message or "readonly" in error_message, \
                    "Error message should include output path"
                
                # Verify error message suggests action
                assert any(keyword in error_message.lower() for keyword in ["permission", "writable", "check"]), \
                    "Error message should suggest checking permissions"
            finally:
                # Restore permissions for cleanup
                output_dir.chmod(0o755)
