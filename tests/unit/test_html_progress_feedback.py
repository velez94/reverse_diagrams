"""Property-based tests for HTML report progress feedback.

Feature: html-report-generation
Property 11: Progress Feedback Completeness
"""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, call
from hypothesis import given, strategies as st, settings
from src.reverse_diagrams import generate_html_report_cli
from src.reports.html_report import JSONFileNotFoundError


@settings(max_examples=50, deadline=None)
@given(
    has_org=st.booleans(),
    has_groups=st.booleans(),
    has_assignments=st.booleans()
)
@pytest.mark.property_test
def test_property_11_progress_feedback_completeness(has_org, has_groups, has_assignments, tmp_path):
    """
    Feature: html-report-generation
    Property 11: Progress Feedback Completeness
    
    For any HTML report generation operation, the CLI should display progress indicators
    during generation, display the output file path upon success, display the number of
    sections included, and list which JSON files were processed.
    
    Validates: Requirements 6.5, 7.1, 7.2, 7.4, 7.5
    """
    # Skip if no data files
    if not (has_org or has_groups or has_assignments):
        pytest.skip("At least one data file required")
    
    # Create JSON directory
    json_dir = tmp_path / "json"
    json_dir.mkdir()
    
    # Create JSON files based on flags
    files_created = []
    
    if has_org:
        org_file = json_dir / "organizations.json"
        org_file.write_text(json.dumps({
            "organization": {"Id": "o-test123"},
            "accounts": [{"Id": "123456789012", "Name": "TestAccount"}],
            "organizational_units": []
        }))
        files_created.append("organizations.json")
    
    if has_groups:
        groups_file = json_dir / "groups.json"
        groups_file.write_text(json.dumps([
            {"group_name": "TestGroup", "members": []}
        ]))
        files_created.append("groups.json")
    
    if has_assignments:
        assignments_file = json_dir / "account_assignments.json"
        assignments_file.write_text(json.dumps({
            "TestAccount": [{"PrincipalType": "GROUP", "GroupName": "TestGroup", "PermissionSetName": "Admin"}]
        }))
        files_created.append("account_assignments.json")
    
    # Mock progress tracker to capture calls
    with patch('src.reverse_diagrams.get_progress_tracker') as mock_progress:
        mock_tracker = Mock()
        mock_progress.return_value = mock_tracker
        
        # Generate HTML report
        output_path = tmp_path / "report.html"
        try:
            generate_html_report_cli(
                html_output=str(output_path),
                json_dir=str(json_dir)
            )
        except Exception as e:
            pytest.fail(f"HTML generation should succeed: {e}")
        
        # Verify progress indicators were displayed
        assert mock_tracker.show_info.called or mock_tracker.show_success.called, \
            "Progress indicators should be displayed during generation"
        
        # Verify success message was shown
        assert mock_tracker.show_success.called, \
            "Success message should be displayed upon completion"
        
        # Get the success message
        success_calls = [call for call in mock_tracker.show_success.call_args_list]
        assert len(success_calls) > 0, "At least one success message should be shown"
        
        # Verify output path is in success message
        success_message = str(success_calls[0])
        assert str(output_path) in success_message or "report.html" in success_message, \
            "Output file path should be displayed in success message"
        
        # Verify number of sections is mentioned
        section_count = len(files_created)
        assert str(section_count) in success_message, \
            f"Number of sections ({section_count}) should be displayed"
        
        # Verify processed files are listed
        for filename in files_created:
            assert filename in success_message, \
                f"Processed file '{filename}' should be listed in success message"


@settings(max_examples=50, deadline=None)
@given(
    custom_output=st.booleans()
)
@pytest.mark.property_test
def test_property_11_output_path_display(custom_output, tmp_path):
    """
    Feature: html-report-generation
    Property 11: Progress Feedback Completeness
    
    The output file path should always be displayed in the success message,
    whether using default or custom output path.
    
    Validates: Requirements 7.2
    """
    # Create JSON directory with at least one file
    json_dir = tmp_path / "json"
    json_dir.mkdir()
    
    org_file = json_dir / "organizations.json"
    org_file.write_text(json.dumps({
        "organization": {"Id": "o-test123"},
        "accounts": [],
        "organizational_units": []
    }))
    
    # Determine output path
    if custom_output:
        output_path = tmp_path / "custom" / "my_report.html"
    else:
        output_path = None  # Use default
    
    # Mock progress tracker
    with patch('src.reverse_diagrams.get_progress_tracker') as mock_progress:
        mock_tracker = Mock()
        mock_progress.return_value = mock_tracker
        
        # Generate HTML report
        try:
            generate_html_report_cli(
                html_output=str(output_path) if output_path else None,
                json_dir=str(json_dir)
            )
        except Exception as e:
            pytest.fail(f"HTML generation should succeed: {e}")
        
        # Verify success message contains output path
        assert mock_tracker.show_success.called, \
            "Success message should be displayed"
        
        success_message = str(mock_tracker.show_success.call_args_list[0])
        
        if custom_output:
            assert "my_report.html" in success_message or str(output_path) in success_message, \
                "Custom output path should be displayed in success message"
        else:
            assert "aws_report.html" in success_message or "reports" in success_message, \
                "Default output path should be displayed in success message"
