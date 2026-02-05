"""Integration tests for standalone HTML generation.

Tests end-to-end HTML generation without diagram generation.
"""
import pytest
import json
import shutil
from pathlib import Path
from src.reverse_diagrams import generate_html_report_cli


@pytest.fixture
def test_fixtures_dir():
    """Get path to test fixtures directory."""
    return Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def setup_json_files(tmp_path, test_fixtures_dir):
    """Setup JSON files for testing."""
    json_dir = tmp_path / "json"
    json_dir.mkdir()
    
    # Copy fixture files
    shutil.copy(
        test_fixtures_dir / "organizations_valid.json",
        json_dir / "organizations.json"
    )
    shutil.copy(
        test_fixtures_dir / "groups_valid.json",
        json_dir / "groups.json"
    )
    shutil.copy(
        test_fixtures_dir / "account_assignments_valid.json",
        json_dir / "account_assignments.json"
    )
    
    return json_dir


class TestStandaloneHTMLGeneration:
    """Test standalone HTML generation (--html-report only)."""
    
    def test_html_generation_with_all_files(self, tmp_path, setup_json_files):
        """Test HTML generation with all JSON files present."""
        json_dir = setup_json_files
        output_path = tmp_path / "reports" / "test_report.html"
        
        # Generate HTML report
        generate_html_report_cli(
            html_output=str(output_path),
            json_dir=str(json_dir)
        )
        
        # Verify HTML file was created
        assert output_path.exists(), "HTML file should be created"
        
        # Read and verify HTML content
        html_content = output_path.read_text()
        
        # Verify HTML structure
        assert '<!DOCTYPE html>' in html_content
        assert '<html' in html_content.lower()
        assert '</html>' in html_content.lower()
        
        # Verify organizations content
        assert "Management Account" in html_content
        assert "Production Account" in html_content
        assert "Development Account" in html_content
        assert "Organizations" in html_content
        
        # Verify groups content
        assert "Administrators" in html_content
        assert "Developers" in html_content
        assert "ReadOnly" in html_content
        assert "admin.user1" in html_content
        assert "dev.user1" in html_content
        
        # Verify assignments content
        assert "AdministratorAccess" in html_content
        assert "PowerUserAccess" in html_content
        assert "ReadOnlyAccess" in html_content
        assert "Account Assignments" in html_content
    
    def test_html_generation_organizations_only(self, tmp_path, test_fixtures_dir):
        """Test HTML generation with only organizations file."""
        json_dir = tmp_path / "json"
        json_dir.mkdir()
        
        shutil.copy(
            test_fixtures_dir / "organizations_valid.json",
            json_dir / "organizations.json"
        )
        
        output_path = tmp_path / "report.html"
        
        # Generate HTML report
        generate_html_report_cli(
            html_output=str(output_path),
            json_dir=str(json_dir)
        )
        
        # Verify HTML was created
        assert output_path.exists()
        
        html_content = output_path.read_text()
        
        # Should contain organizations content
        assert "Management Account" in html_content
        assert "Organizations" in html_content
        
        # Should not contain groups/assignments sections (or should be empty)
        # The HTML generator gracefully handles missing data
        assert '<!DOCTYPE html>' in html_content
    
    def test_html_generation_groups_only(self, tmp_path, test_fixtures_dir):
        """Test HTML generation with only groups file."""
        json_dir = tmp_path / "json"
        json_dir.mkdir()
        
        shutil.copy(
            test_fixtures_dir / "groups_valid.json",
            json_dir / "groups.json"
        )
        
        output_path = tmp_path / "report.html"
        
        # Generate HTML report
        generate_html_report_cli(
            html_output=str(output_path),
            json_dir=str(json_dir)
        )
        
        # Verify HTML was created
        assert output_path.exists()
        
        html_content = output_path.read_text()
        
        # Should contain groups content
        assert "Administrators" in html_content
        assert "Developers" in html_content
        assert "admin.user1" in html_content
    
    def test_html_generation_assignments_only(self, tmp_path, test_fixtures_dir):
        """Test HTML generation with only assignments file."""
        json_dir = tmp_path / "json"
        json_dir.mkdir()
        
        shutil.copy(
            test_fixtures_dir / "account_assignments_valid.json",
            json_dir / "account_assignments.json"
        )
        
        output_path = tmp_path / "report.html"
        
        # Generate HTML report
        generate_html_report_cli(
            html_output=str(output_path),
            json_dir=str(json_dir)
        )
        
        # Verify HTML was created
        assert output_path.exists()
        
        html_content = output_path.read_text()
        
        # Should contain assignments content
        assert "Production Account" in html_content
        assert "AdministratorAccess" in html_content
        assert "Administrators" in html_content


class TestHTMLFileCreationAndContent:
    """Test that HTML file is created with correct content."""
    
    def test_html_file_is_readable(self, tmp_path, setup_json_files):
        """Test that generated HTML file is readable."""
        json_dir = setup_json_files
        output_path = tmp_path / "report.html"
        
        generate_html_report_cli(
            html_output=str(output_path),
            json_dir=str(json_dir)
        )
        
        # Should be able to read the file
        content = output_path.read_text()
        assert len(content) > 0
    
    def test_html_contains_timestamp(self, tmp_path, setup_json_files):
        """Test that HTML contains generation timestamp."""
        json_dir = setup_json_files
        output_path = tmp_path / "report.html"
        
        generate_html_report_cli(
            html_output=str(output_path),
            json_dir=str(json_dir)
        )
        
        html_content = output_path.read_text()
        
        # Should contain timestamp
        assert "Generated:" in html_content or "generated" in html_content.lower()
    
    def test_html_is_self_contained(self, tmp_path, setup_json_files):
        """Test that HTML is self-contained with no external dependencies."""
        json_dir = setup_json_files
        output_path = tmp_path / "report.html"
        
        generate_html_report_cli(
            html_output=str(output_path),
            json_dir=str(json_dir)
        )
        
        html_content = output_path.read_text()
        
        # Should have embedded CSS
        assert '<style>' in html_content
        assert '</style>' in html_content
        
        # Should not have external CSS links
        assert '<link' not in html_content or 'rel="stylesheet"' not in html_content
        
        # Should not have external JavaScript
        assert '<script src=' not in html_content.lower()


class TestNoDiagramFilesCreated:
    """Test that no diagram files are created during HTML-only generation."""
    
    def test_no_diagram_code_files_created(self, tmp_path, setup_json_files):
        """Test that no diagram code files are created."""
        json_dir = setup_json_files
        output_path = tmp_path / "reports" / "report.html"
        
        # Create code directory to verify it stays empty
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        
        # Generate HTML only
        generate_html_report_cli(
            html_output=str(output_path),
            json_dir=str(json_dir)
        )
        
        # Verify code directory is still empty
        assert len(list(code_dir.iterdir())) == 0, \
            "No diagram code files should be created"
    
    def test_no_diagram_image_files_created(self, tmp_path, setup_json_files):
        """Test that no diagram image files are created."""
        json_dir = setup_json_files
        output_path = tmp_path / "reports" / "report.html"
        
        # Create images directory to verify it stays empty
        images_dir = tmp_path / "images"
        images_dir.mkdir()
        
        # Generate HTML only
        generate_html_report_cli(
            html_output=str(output_path),
            json_dir=str(json_dir)
        )
        
        # Verify images directory is still empty
        assert len(list(images_dir.iterdir())) == 0, \
            "No diagram image files should be created"
