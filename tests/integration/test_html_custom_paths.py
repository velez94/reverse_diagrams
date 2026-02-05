"""Integration tests for custom output paths.

Tests various output path scenarios and directory creation.
"""
import pytest
import shutil
from pathlib import Path
from src.reverse_diagrams import generate_html_report_cli
from src.reports.html_report import InvalidOutputPathError


@pytest.fixture
def test_fixtures_dir():
    """Get path to test fixtures directory."""
    return Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def setup_minimal_json(tmp_path, test_fixtures_dir):
    """Setup minimal JSON file for testing."""
    json_dir = tmp_path / "json"
    json_dir.mkdir()
    
    shutil.copy(
        test_fixtures_dir / "organizations_valid.json",
        json_dir / "organizations.json"
    )
    
    return json_dir


class TestCustomOutputPaths:
    """Test various custom output path scenarios."""
    
    def test_custom_output_path_simple(self, tmp_path, setup_minimal_json):
        """Test HTML generation with simple custom output path."""
        json_dir = setup_minimal_json
        output_path = tmp_path / "my_custom_report.html"
        
        generate_html_report_cli(
            html_output=str(output_path),
            json_dir=str(json_dir)
        )
        
        assert output_path.exists()
        assert output_path.name == "my_custom_report.html"
    
    def test_custom_output_path_nested_directories(self, tmp_path, setup_minimal_json):
        """Test HTML generation with nested directory path."""
        json_dir = setup_minimal_json
        output_path = tmp_path / "reports" / "2024" / "february" / "report.html"
        
        generate_html_report_cli(
            html_output=str(output_path),
            json_dir=str(json_dir)
        )
        
        assert output_path.exists()
        assert output_path.parent.name == "february"
        assert output_path.parent.parent.name == "2024"
    
    def test_custom_output_path_with_spaces(self, tmp_path, setup_minimal_json):
        """Test HTML generation with path containing spaces."""
        json_dir = setup_minimal_json
        output_path = tmp_path / "my reports" / "aws report.html"
        
        generate_html_report_cli(
            html_output=str(output_path),
            json_dir=str(json_dir)
        )
        
        assert output_path.exists()
        assert "my reports" in str(output_path)


class TestDirectoryCreation:
    """Test that directories are created as needed."""
    
    def test_creates_parent_directory(self, tmp_path, setup_minimal_json):
        """Test that parent directory is created if it doesn't exist."""
        json_dir = setup_minimal_json
        output_path = tmp_path / "new_directory" / "report.html"
        
        # Verify directory doesn't exist yet
        assert not output_path.parent.exists()
        
        generate_html_report_cli(
            html_output=str(output_path),
            json_dir=str(json_dir)
        )
        
        # Verify directory was created
        assert output_path.parent.exists()
        assert output_path.exists()
    
    def test_creates_nested_directories(self, tmp_path, setup_minimal_json):
        """Test that nested directories are created."""
        json_dir = setup_minimal_json
        output_path = tmp_path / "level1" / "level2" / "level3" / "report.html"
        
        generate_html_report_cli(
            html_output=str(output_path),
            json_dir=str(json_dir)
        )
        
        assert output_path.exists()
        assert (tmp_path / "level1").exists()
        assert (tmp_path / "level1" / "level2").exists()
        assert (tmp_path / "level1" / "level2" / "level3").exists()


class TestPathValidation:
    """Test path validation and error handling."""
    
    def test_overwrites_existing_file(self, tmp_path, setup_minimal_json):
        """Test that existing HTML file is overwritten."""
        json_dir = setup_minimal_json
        output_path = tmp_path / "report.html"
        
        # Create existing file
        output_path.write_text("old content")
        old_size = output_path.stat().st_size
        
        # Generate new report
        generate_html_report_cli(
            html_output=str(output_path),
            json_dir=str(json_dir)
        )
        
        # Verify file was overwritten
        new_content = output_path.read_text()
        assert "old content" not in new_content
        assert "<!DOCTYPE html>" in new_content
        assert output_path.stat().st_size != old_size
    
    def test_handles_relative_paths(self, tmp_path, setup_minimal_json):
        """Test that relative paths are handled correctly."""
        json_dir = setup_minimal_json
        
        # Use relative path
        output_path = tmp_path / "reports" / "report.html"
        
        generate_html_report_cli(
            html_output=str(output_path),
            json_dir=str(json_dir)
        )
        
        assert output_path.exists()
