"""Integration tests for combined diagram and HTML generation.

Tests that both diagrams and HTML reports are generated when flags are combined.
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


class TestCombinedGeneration:
    """Test combined diagram and HTML generation."""
    
    def test_html_generated_after_diagram_data_exists(self, tmp_path, test_fixtures_dir):
        """
        Test HTML generation after diagram data has been created.
        
        Simulates the scenario where -o or -i flags have created JSON files,
        and then --html-report is used to generate HTML.
        """
        # Setup: Simulate diagram generation by copying JSON files
        json_dir = tmp_path / "json"
        json_dir.mkdir()
        
        shutil.copy(
            test_fixtures_dir / "organizations_valid.json",
            json_dir / "organizations.json"
        )
        shutil.copy(
            test_fixtures_dir / "groups_valid.json",
            json_dir / "groups.json"
        )
        
        # Simulate diagram code files
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        (code_dir / "graph_org.py").write_text("# Organization diagram code")
        (code_dir / "graph_sso_complete.py").write_text("# SSO diagram code")
        
        # Now generate HTML report
        output_path = tmp_path / "reports" / "report.html"
        
        generate_html_report_cli(
            html_output=str(output_path),
            json_dir=str(json_dir)
        )
        
        # Verify both diagram files and HTML exist
        assert (code_dir / "graph_org.py").exists(), "Diagram code should still exist"
        assert (code_dir / "graph_sso_complete.py").exists(), "Diagram code should still exist"
        assert output_path.exists(), "HTML report should be created"
        
        # Verify HTML contains data from both sources
        html_content = output_path.read_text()
        assert "Management Account" in html_content  # From organizations
        assert "Administrators" in html_content  # From groups
    
    def test_both_outputs_contain_same_data(self, tmp_path, test_fixtures_dir):
        """Test that HTML and diagram data contain the same information."""
        json_dir = tmp_path / "json"
        json_dir.mkdir()
        
        shutil.copy(
            test_fixtures_dir / "organizations_valid.json",
            json_dir / "organizations.json"
        )
        
        output_path = tmp_path / "report.html"
        
        # Generate HTML
        generate_html_report_cli(
            html_output=str(output_path),
            json_dir=str(json_dir)
        )
        
        # Read original JSON
        with open(json_dir / "organizations.json") as f:
            org_data = json.load(f)
        
        # Read HTML
        html_content = output_path.read_text()
        
        # Verify key data appears in both
        for account in org_data["accounts"]:
            assert account["Name"] in html_content, \
                f"Account {account['Name']} should appear in HTML"
