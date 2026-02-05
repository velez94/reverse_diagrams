"""Unit tests for HTML report error handling.

Tests specific error scenarios and error messages.
"""
import pytest
import json
from pathlib import Path
from unittest.mock import patch
from src.reports.html_report import (
    generate_html_report,
    generate_report_from_files,
    JSONFileNotFoundError,
    JSONParseError,
    InvalidOutputPathError,
    HTMLWriteError
)
from src.reverse_diagrams import generate_html_report_cli


class TestUnreadableJSONFiles:
    """Test handling of unreadable JSON files."""
    
    def test_unreadable_organizations_file(self, tmp_path):
        """Test error when organizations file cannot be read."""
        json_file = tmp_path / "organizations.json"
        json_file.write_text('{"organization": {"Id": "test"}, "accounts": [], "organizational_units": []}')
        
        # Mock open to raise PermissionError
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with pytest.raises(JSONParseError) as exc_info:
                generate_report_from_files(
                    organizations_file=str(json_file),
                    output_path=str(tmp_path / "report.html")
                )
            
            assert "organizations.json" in str(exc_info.value) or str(json_file) in str(exc_info.value)
    
    def test_unreadable_groups_file(self, tmp_path):
        """Test error when groups file cannot be read."""
        json_file = tmp_path / "groups.json"
        json_file.write_text('[{"group_name": "test", "members": []}]')
        
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with pytest.raises(JSONParseError) as exc_info:
                generate_report_from_files(
                    groups_file=str(json_file),
                    output_path=str(tmp_path / "report.html")
                )
            
            assert "groups.json" in str(exc_info.value) or str(json_file) in str(exc_info.value)


class TestMalformedJSON:
    """Test handling of malformed JSON files."""
    
    def test_malformed_organizations_json(self, tmp_path):
        """Test error when organizations JSON is malformed."""
        json_file = tmp_path / "organizations.json"
        json_file.write_text('{"invalid": json syntax}')
        
        with pytest.raises(JSONParseError) as exc_info:
            generate_report_from_files(
                organizations_file=str(json_file),
                output_path=str(tmp_path / "report.html")
            )
        
        error_message = str(exc_info.value)
        assert "organizations.json" in error_message or str(json_file) in error_message
        assert "invalid" in error_message.lower() or "json" in error_message.lower()
    
    def test_malformed_groups_json(self, tmp_path):
        """Test error when groups JSON is malformed."""
        json_file = tmp_path / "groups.json"
        json_file.write_text('[{invalid json}]')
        
        with pytest.raises(JSONParseError) as exc_info:
            generate_report_from_files(
                groups_file=str(json_file),
                output_path=str(tmp_path / "report.html")
            )
        
        error_message = str(exc_info.value)
        assert "groups.json" in error_message or str(json_file) in error_message
    
    def test_malformed_assignments_json(self, tmp_path):
        """Test error when assignments JSON is malformed."""
        json_file = tmp_path / "account_assignments.json"
        json_file.write_text('{"invalid": json}')
        
        with pytest.raises(JSONParseError) as exc_info:
            generate_report_from_files(
                assignments_file=str(json_file),
                output_path=str(tmp_path / "report.html")
            )
        
        error_message = str(exc_info.value)
        assert "account_assignments.json" in error_message or str(json_file) in error_message


class TestPermissionErrors:
    """Test handling of permission errors."""
    
    def test_output_directory_not_writable(self, tmp_path):
        """Test error when output directory is not writable."""
        # Create valid JSON
        json_dir = tmp_path / "json"
        json_dir.mkdir()
        (json_dir / "organizations.json").write_text(json.dumps({
            "organization": {"Id": "test"},
            "accounts": [],
            "organizational_units": []
        }))
        
        # Create non-writable directory
        if hasattr(tmp_path, 'chmod'):
            output_dir = tmp_path / "readonly"
            output_dir.mkdir()
            output_dir.chmod(0o444)  # Read-only
            
            try:
                with pytest.raises((InvalidOutputPathError, PermissionError)):
                    generate_html_report_cli(
                        html_output=str(output_dir / "report.html"),
                        json_dir=str(json_dir)
                    )
            finally:
                output_dir.chmod(0o755)  # Restore for cleanup


class TestMissingFilesWithHelpfulSuggestions:
    """Test that missing files produce helpful error messages."""
    
    def test_no_json_files_suggests_generating_data(self, tmp_path):
        """Test error message suggests generating data when no JSON files exist."""
        json_dir = tmp_path / "json"
        json_dir.mkdir()
        
        with pytest.raises(JSONFileNotFoundError) as exc_info:
            generate_html_report_cli(
                html_output=str(tmp_path / "report.html"),
                json_dir=str(json_dir)
            )
        
        error_message = str(exc_info.value)
        # Should suggest running with -o or -i flags
        assert "-o" in error_message or "-i" in error_message or "generate" in error_message.lower()
    
    def test_missing_organizations_file_suggests_flag(self, tmp_path):
        """Test error message suggests -o flag when organizations file is missing."""
        json_file = tmp_path / "organizations.json"
        
        with pytest.raises(JSONFileNotFoundError) as exc_info:
            generate_report_from_files(
                organizations_file=str(json_file),
                output_path=str(tmp_path / "report.html")
            )
        
        error_message = str(exc_info.value)
        assert "-o" in error_message or "organizations" in error_message.lower()
    
    def test_missing_groups_file_suggests_flag(self, tmp_path):
        """Test error message suggests -i flag when groups file is missing."""
        json_file = tmp_path / "groups.json"
        
        with pytest.raises(JSONFileNotFoundError) as exc_info:
            generate_report_from_files(
                groups_file=str(json_file),
                output_path=str(tmp_path / "report.html")
            )
        
        error_message = str(exc_info.value)
        assert "-i" in error_message or "groups" in error_message.lower()
    
    def test_missing_assignments_file_suggests_flag(self, tmp_path):
        """Test error message suggests -i flag when assignments file is missing."""
        json_file = tmp_path / "account_assignments.json"
        
        with pytest.raises(JSONFileNotFoundError) as exc_info:
            generate_report_from_files(
                assignments_file=str(json_file),
                output_path=str(tmp_path / "report.html")
            )
        
        error_message = str(exc_info.value)
        assert "-i" in error_message or "assignments" in error_message.lower()


class TestInvalidJSONStructure:
    """Test handling of invalid JSON structure."""
    
    def test_organizations_wrong_type(self, tmp_path):
        """Test error when organizations data is wrong type."""
        with pytest.raises(JSONParseError) as exc_info:
            generate_html_report(
                organizations_data="should be dict not string",
                output_path=str(tmp_path / "report.html")
            )
        
        assert "dictionary" in str(exc_info.value).lower()
    
    def test_groups_wrong_type(self, tmp_path):
        """Test error when groups data is wrong type."""
        with pytest.raises(JSONParseError) as exc_info:
            generate_html_report(
                groups_data={"should": "be list not dict"},
                output_path=str(tmp_path / "report.html")
            )
        
        assert "list" in str(exc_info.value).lower()
    
    def test_assignments_wrong_type(self, tmp_path):
        """Test error when assignments data is wrong type."""
        with pytest.raises(JSONParseError) as exc_info:
            generate_html_report(
                account_assignments_data=["should", "be", "dict"],
                output_path=str(tmp_path / "report.html")
            )
        
        assert "dictionary" in str(exc_info.value).lower()
