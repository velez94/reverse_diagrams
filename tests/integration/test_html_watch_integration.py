"""Integration tests for watch command HTML generation.

Tests end-to-end watch command with HTML generation.
"""
import pytest
import argparse
import shutil
from pathlib import Path
from src.reports.console_view import watch_on_demand


@pytest.fixture
def test_fixtures_dir():
    """Get path to test fixtures directory."""
    return Path(__file__).parent.parent / "fixtures"


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


class TestWatchCommandWithOrganizations:
    """Test watch command with organizations file."""
    
    def test_watch_organizations_generates_html(self, tmp_path, test_fixtures_dir):
        """Test watch command generates HTML from organizations file."""
        # Copy organizations file
        org_file = tmp_path / "organizations.json"
        shutil.copy(test_fixtures_dir / "organizations_valid.json", org_file)
        
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
        assert "Management Account" in html_content
        assert "Production Account" in html_content
        assert "Organizations" in html_content


class TestWatchCommandWithGroups:
    """Test watch command with groups file."""
    
    def test_watch_groups_generates_html(self, tmp_path, test_fixtures_dir):
        """Test watch command generates HTML from groups file."""
        # Copy groups file
        groups_file = tmp_path / "groups.json"
        shutil.copy(test_fixtures_dir / "groups_valid.json", groups_file)
        
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
        assert "Administrators" in html_content
        assert "Developers" in html_content
        assert "admin.user1" in html_content


class TestWatchCommandWithAssignments:
    """Test watch command with assignments file."""
    
    def test_watch_assignments_generates_html(self, tmp_path, test_fixtures_dir):
        """Test watch command generates HTML from assignments file."""
        # Copy assignments file
        assignments_file = tmp_path / "account_assignments.json"
        shutil.copy(test_fixtures_dir / "account_assignments_valid.json", assignments_file)
        
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
        assert "Production Account" in html_content
        assert "AdministratorAccess" in html_content
        assert "Administrators" in html_content


class TestWatchCommandOutputPath:
    """Test watch command output path handling."""
    
    def test_watch_with_custom_output_path(self, tmp_path, test_fixtures_dir):
        """Test watch command with custom output path."""
        groups_file = tmp_path / "groups.json"
        shutil.copy(test_fixtures_dir / "groups_valid.json", groups_file)
        
        custom_output = tmp_path / "custom" / "my_report.html"
        
        args = create_watch_args(
            watch_graph_identity=str(groups_file),
            html=True,
            html_output=str(custom_output)
        )
        
        watch_on_demand(args)
        
        # Verify HTML was created at custom path
        assert custom_output.exists()
        assert custom_output.parent.name == "custom"
    
    def test_watch_creates_output_directory(self, tmp_path, test_fixtures_dir):
        """Test that watch command creates output directory if needed."""
        groups_file = tmp_path / "groups.json"
        shutil.copy(test_fixtures_dir / "groups_valid.json", groups_file)
        
        output_path = tmp_path / "new_dir" / "report.html"
        
        # Verify directory doesn't exist
        assert not output_path.parent.exists()
        
        args = create_watch_args(
            watch_graph_identity=str(groups_file),
            html=True,
            html_output=str(output_path)
        )
        
        watch_on_demand(args)
        
        # Verify directory was created
        assert output_path.parent.exists()
        assert output_path.exists()
