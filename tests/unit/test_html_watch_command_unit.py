"""Unit tests for watch command HTML integration.

Tests specific scenarios for watch command HTML generation.
"""
import pytest
import json
import argparse
from pathlib import Path
from unittest.mock import patch, Mock
from src.reports.console_view import watch_on_demand


def create_watch_args(**kwargs):
    """Helper to create watch command arguments."""
    defaults = {
        'watch_graph_organization': None,
        'watch_graph_identity': None,
        'watch_graph_accounts_assignments': None,
        'html': False,
        'html_output': None
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestWatchCommandHTMLFlagForEachFileType:
    """Test watch command with --html flag for each JSON file type."""
    
    def test_watch_organizations_with_html_flag(self, tmp_path):
        """Test watch command with organizations file and --html flag."""
        # Create organizations JSON file
        org_file = tmp_path / "organizations.json"
        org_file.write_text(json.dumps({
            "organization": {"Id": "o-test123"},
            "accounts": [{"Id": "123456789012", "Name": "TestAccount"}],
            "organizational_units": []
        }))
        
        output_path = tmp_path / "report.html"
        
        args = create_watch_args(
            watch_graph_organization=str(org_file),
            html=True,
            html_output=str(output_path)
        )
        
        # Execute watch command
        watch_on_demand(args)
        
        # Verify HTML was created
        assert output_path.exists()
        html_content = output_path.read_text()
        assert "TestAccount" in html_content
        assert "Organizations" in html_content
    
    def test_watch_groups_with_html_flag(self, tmp_path):
        """Test watch command with groups file and --html flag."""
        # Create groups JSON file
        groups_file = tmp_path / "groups.json"
        groups_file.write_text(json.dumps([
            {
                "group_name": "AdminGroup",
                "members": [{"MemberId": {"UserName": "admin_user"}}]
            }
        ]))
        
        output_path = tmp_path / "report.html"
        
        args = create_watch_args(
            watch_graph_identity=str(groups_file),
            html=True,
            html_output=str(output_path)
        )
        
        # Execute watch command
        watch_on_demand(args)
        
        # Verify HTML was created
        assert output_path.exists()
        html_content = output_path.read_text()
        assert "AdminGroup" in html_content
        assert "admin_user" in html_content
    
    def test_watch_assignments_with_html_flag(self, tmp_path):
        """Test watch command with assignments file and --html flag."""
        # Create assignments JSON file
        assignments_file = tmp_path / "account_assignments.json"
        assignments_file.write_text(json.dumps({
            "TestAccount": [
                {
                    "PrincipalType": "GROUP",
                    "GroupName": "AdminGroup",
                    "PermissionSetName": "AdministratorAccess"
                }
            ]
        }))
        
        output_path = tmp_path / "report.html"
        
        args = create_watch_args(
            watch_graph_accounts_assignments=str(assignments_file),
            html=True,
            html_output=str(output_path)
        )
        
        # Execute watch command
        watch_on_demand(args)
        
        # Verify HTML was created
        assert output_path.exists()
        html_content = output_path.read_text()
        assert "TestAccount" in html_content
        assert "AdminGroup" in html_content
        assert "AdministratorAccess" in html_content


class TestWatchCommandOutputPathHandling:
    """Test output path handling in watch mode."""
    
    def test_watch_with_custom_output_path(self, tmp_path):
        """Test watch command with custom output path."""
        # Create JSON file
        json_file = tmp_path / "groups.json"
        json_file.write_text(json.dumps([{"group_name": "TestGroup", "members": []}]))
        
        # Custom output path
        custom_output = tmp_path / "custom" / "my_report.html"
        
        args = create_watch_args(
            watch_graph_identity=str(json_file),
            html=True,
            html_output=str(custom_output)
        )
        
        # Execute watch command
        watch_on_demand(args)
        
        # Verify HTML was created at custom path
        assert custom_output.exists()
        assert custom_output.parent.name == "custom"
    
    def test_watch_with_default_output_path(self, tmp_path):
        """Test watch command with default output path."""
        # Create JSON file
        json_file = tmp_path / "groups.json"
        json_file.write_text(json.dumps([{"group_name": "TestGroup", "members": []}]))
        
        # Use default output path
        default_output = tmp_path / "diagrams" / "reports" / "aws_report.html"
        
        args = create_watch_args(
            watch_graph_identity=str(json_file),
            html=True,
            html_output=None  # Will use default
        )
        
        # Mock to use tmp_path as default
        with patch('src.reports.console_view.generate_report_from_files') as mock_gen:
            mock_gen.return_value = str(default_output)
            default_output.parent.mkdir(parents=True, exist_ok=True)
            default_output.write_text("<!DOCTYPE html><html></html>")
            
            watch_on_demand(args)
            
            # Verify generate_report_from_files was called
            assert mock_gen.called


class TestWatchCommandProgressIndicators:
    """Test progress indicators in watch mode."""
    
    def test_watch_displays_progress_indicators(self, tmp_path):
        """Test that watch command displays progress indicators."""
        # Create JSON file
        json_file = tmp_path / "groups.json"
        json_file.write_text(json.dumps([{"group_name": "TestGroup", "members": []}]))
        
        output_path = tmp_path / "report.html"
        
        args = create_watch_args(
            watch_graph_identity=str(json_file),
            html=True,
            html_output=str(output_path)
        )
        
        # Mock progress tracker
        with patch('src.reports.console_view.get_progress_tracker') as mock_progress:
            mock_tracker = Mock()
            mock_progress.return_value = mock_tracker
            
            # Execute watch command
            watch_on_demand(args)
            
            # Verify progress methods were called
            assert mock_tracker.show_info.called or mock_tracker.show_success.called, \
                "Progress indicators should be displayed"
    
    def test_watch_displays_success_message(self, tmp_path):
        """Test that watch command displays success message."""
        # Create JSON file
        json_file = tmp_path / "groups.json"
        json_file.write_text(json.dumps([{"group_name": "TestGroup", "members": []}]))
        
        output_path = tmp_path / "report.html"
        
        args = create_watch_args(
            watch_graph_identity=str(json_file),
            html=True,
            html_output=str(output_path)
        )
        
        # Mock progress tracker
        with patch('src.reports.console_view.get_progress_tracker') as mock_progress:
            mock_tracker = Mock()
            mock_progress.return_value = mock_tracker
            
            # Execute watch command
            watch_on_demand(args)
            
            # Verify success message was shown
            assert mock_tracker.show_success.called, \
                "Success message should be displayed"
            
            # Verify success message contains output path
            success_call = mock_tracker.show_success.call_args
            success_message = str(success_call)
            assert str(output_path) in success_message or "report.html" in success_message, \
                "Success message should contain output path"


class TestWatchCommandWithoutHTMLFlag:
    """Test that watch command without --html flag works normally."""
    
    def test_watch_without_html_flag_shows_console_view(self, tmp_path):
        """Test watch command without --html flag uses console view."""
        # Create JSON file
        json_file = tmp_path / "groups.json"
        json_file.write_text(json.dumps([
            {"group_name": "TestGroup", "members": [{"MemberId": {"UserName": "user1"}}]}
        ]))
        
        args = create_watch_args(
            watch_graph_identity=str(json_file),
            html=False  # No HTML generation
        )
        
        # Mock console output
        with patch('src.reports.console_view.Console') as mock_console:
            mock_console_instance = Mock()
            mock_console.return_value = mock_console_instance
            
            # Execute watch command
            watch_on_demand(args)
            
            # Verify console view was used (not HTML generation)
            assert mock_console_instance.print.called, \
                "Console view should be used when --html flag is not set"
