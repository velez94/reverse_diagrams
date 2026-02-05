"""Property-based tests for watch command HTML generation.

Feature: html-report-generation
Property 10: Watch Command HTML Generation
"""
import pytest
import json
import argparse
from pathlib import Path
from hypothesis import given, strategies as st, settings
from src.reports.console_view import watch_on_demand


def create_watch_args(json_file, file_type, html=False, html_output=None):
    """Helper to create watch command arguments."""
    args = argparse.Namespace(
        watch_graph_organization=json_file if file_type == "organizations" else None,
        watch_graph_identity=json_file if file_type == "groups" else None,
        watch_graph_accounts_assignments=json_file if file_type == "assignments" else None,
        html=html,
        html_output=html_output
    )
    return args


@settings(max_examples=50, deadline=None)
@given(
    file_type=st.sampled_from(["organizations", "groups", "assignments"]),
    use_custom_output=st.booleans()
)
@pytest.mark.property_test
def test_property_10_watch_command_html_generation(file_type, use_custom_output, tmp_path):
    """
    Feature: html-report-generation
    Property 10: Watch Command HTML Generation
    
    For any valid JSON file path provided to the watch command with the --html flag,
    an HTML report should be generated with content appropriate to the JSON file type
    (organizations, groups, or assignments), and saved to the specified or default
    output path.
    
    Validates: Requirements 6.1, 6.2, 6.4
    """
    # Create JSON file based on type
    json_file = tmp_path / f"{file_type}.json"
    
    if file_type == "organizations":
        data = {
            "organization": {"Id": "o-test123", "Arn": "arn:aws:organizations::123456789012:organization/o-test123"},
            "accounts": [
                {"Id": "123456789012", "Name": "TestAccount", "Email": "test@example.com", "Status": "ACTIVE"}
            ],
            "organizational_units": [
                {"Id": "ou-test1", "Name": "TestOU"}
            ]
        }
        expected_content = ["TestAccount", "TestOU", "Organizations"]
    elif file_type == "groups":
        data = [
            {
                "group_name": "AdminGroup",
                "members": [
                    {"MemberId": {"UserName": "admin_user"}}
                ]
            }
        ]
        expected_content = ["AdminGroup", "admin_user", "Identity Center"]
    else:  # assignments
        data = {
            "TestAccount": [
                {
                    "PrincipalType": "GROUP",
                    "GroupName": "AdminGroup",
                    "PermissionSetName": "AdministratorAccess"
                }
            ]
        }
        expected_content = ["TestAccount", "AdminGroup", "AdministratorAccess", "Account Assignments"]
    
    json_file.write_text(json.dumps(data))
    
    # Determine output path
    if use_custom_output:
        output_path = tmp_path / "custom_reports" / "my_report.html"
    else:
        output_path = tmp_path / "reports" / "aws_report.html"
    
    # Create watch command args
    args = create_watch_args(
        json_file=str(json_file),
        file_type=file_type,
        html=True,
        html_output=str(output_path) if use_custom_output else None
    )
    
    # If not using custom output, set default
    if not use_custom_output:
        args.html_output = str(output_path)
    
    # Execute watch command with HTML generation
    try:
        watch_on_demand(args)
    except Exception as e:
        pytest.fail(f"Watch command HTML generation should succeed: {e}")
    
    # Verify HTML file was created
    assert output_path.exists(), \
        f"HTML file should be created at {output_path}"
    
    # Read HTML content
    html_content = output_path.read_text()
    
    # Verify HTML is valid
    assert '<!DOCTYPE html>' in html_content, \
        "HTML should have DOCTYPE declaration"
    
    assert '<html' in html_content.lower() and '</html>' in html_content.lower(), \
        "HTML should have complete html tags"
    
    # Verify content appropriate to file type
    for expected in expected_content:
        assert expected in html_content or expected.replace(" ", "") in html_content.replace(" ", ""), \
            f"HTML should contain '{expected}' for {file_type} report"
    
    # Verify HTML has substantial content
    assert len(html_content) > 1000, \
        "HTML should have substantial content"


@settings(max_examples=30, deadline=None)
@given(
    file_type=st.sampled_from(["organizations", "groups", "assignments"])
)
@pytest.mark.property_test
def test_property_10_watch_command_determines_report_type(file_type, tmp_path):
    """
    Feature: html-report-generation
    Property 10: Watch Command HTML Generation
    
    The watch command should correctly determine the report type based on which
    flag is used (-wo, -wi, or -wa) and generate appropriate HTML content.
    
    Validates: Requirements 6.2
    """
    # Create JSON file
    json_file = tmp_path / f"{file_type}.json"
    
    if file_type == "organizations":
        data = {"organization": {"Id": "o-test"}, "accounts": [], "organizational_units": []}
        section_marker = "Organizations"
    elif file_type == "groups":
        data = [{"group_name": "TestGroup", "members": []}]
        section_marker = "Identity Center"
    else:  # assignments
        data = {"TestAccount": []}
        section_marker = "Account Assignments"
    
    json_file.write_text(json.dumps(data))
    
    # Create output path
    output_path = tmp_path / "report.html"
    
    # Create watch command args
    args = create_watch_args(
        json_file=str(json_file),
        file_type=file_type,
        html=True,
        html_output=str(output_path)
    )
    
    # Execute watch command
    try:
        watch_on_demand(args)
    except Exception as e:
        pytest.fail(f"Watch command should succeed: {e}")
    
    # Verify HTML was created
    assert output_path.exists(), "HTML should be created"
    
    # Verify correct section is present
    html_content = output_path.read_text()
    assert section_marker in html_content or section_marker.replace(" ", "") in html_content.replace(" ", ""), \
        f"HTML should contain {file_type} section marker '{section_marker}'"


@settings(max_examples=30, deadline=None)
@given(
    file_type=st.sampled_from(["organizations", "groups", "assignments"]),
    output_filename=st.text(min_size=1, max_size=20, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        min_codepoint=ord('a'), max_codepoint=ord('z')
    ))
)
@pytest.mark.property_test
def test_property_10_watch_command_custom_output_path(file_type, output_filename, tmp_path):
    """
    Feature: html-report-generation
    Property 10: Watch Command HTML Generation
    
    The watch command should save HTML to the specified output path when provided.
    
    Validates: Requirements 6.4
    """
    # Create JSON file
    json_file = tmp_path / f"{file_type}.json"
    
    if file_type == "organizations":
        data = {"organization": {"Id": "o-test"}, "accounts": [], "organizational_units": []}
    elif file_type == "groups":
        data = [{"group_name": "TestGroup", "members": []}]
    else:  # assignments
        data = {}
    
    json_file.write_text(json.dumps(data))
    
    # Create custom output path
    custom_output = tmp_path / "custom" / f"{output_filename}.html"
    
    # Create watch command args
    args = create_watch_args(
        json_file=str(json_file),
        file_type=file_type,
        html=True,
        html_output=str(custom_output)
    )
    
    # Execute watch command
    try:
        watch_on_demand(args)
    except Exception as e:
        pytest.fail(f"Watch command with custom output should succeed: {e}")
    
    # Verify HTML was created at custom path
    assert custom_output.exists(), \
        f"HTML should be created at custom path {custom_output}"
    
    # Verify it's valid HTML
    html_content = custom_output.read_text()
    assert '<!DOCTYPE html>' in html_content, \
        "HTML should be valid"
