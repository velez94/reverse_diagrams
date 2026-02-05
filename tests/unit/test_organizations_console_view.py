"""Unit tests for organizations console view.

Tests the -wo watch command functionality.
"""
import pytest
import json
import argparse
from pathlib import Path
from unittest.mock import patch, Mock
from src.reports.console_view import (
    create_organizations_console_view,
    watch_on_demand
)


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


class TestOrganizationsConsoleView:
    """Test organizations console view functionality."""
    
    def test_create_organizations_console_view_with_complete_data(self, tmp_path):
        """Test console view with complete organizations data."""
        org_data = {
            "organization": {
                "Id": "o-test123",
                "MasterAccountId": "123456789012"
            },
            "accounts": [
                {"Id": "123456789012", "Name": "Management", "Status": "ACTIVE"},
                {"Id": "123456789013", "Name": "Production", "Status": "ACTIVE"}
            ],
            "organizational_units": [
                {"Id": "ou-test1", "Name": "Production"}
            ],
            "organizations_complete": {
                "noOutAccounts": [
                    {"name": "Management", "id": "123456789012"}
                ],
                "organizationalUnits": {
                    "Production": {
                        "accounts": {
                            "Production": {"id": "123456789013"}
                        }
                    }
                }
            }
        }
        
        # Mock console to capture output
        with patch('src.reports.console_view.Console') as mock_console:
            mock_console_instance = Mock()
            mock_console.return_value = mock_console_instance
            
            # Should not raise exception
            create_organizations_console_view(org_data)
            
            # Verify console.print was called
            assert mock_console_instance.print.called
    
    def test_create_organizations_console_view_minimal_data(self, tmp_path):
        """Test console view with minimal organizations data."""
        org_data = {
            "organization": {"Id": "o-test123"},
            "accounts": [],
            "organizational_units": []
        }
        
        # Should not raise exception
        with patch('src.reports.console_view.Console'):
            create_organizations_console_view(org_data)
    
    def test_watch_organizations_command(self, tmp_path):
        """Test watch command with organizations file."""
        # Create organizations JSON file
        org_file = tmp_path / "organizations.json"
        org_data = {
            "organization": {
                "Id": "o-test123",
                "MasterAccountId": "123456789012"
            },
            "accounts": [
                {"Id": "123456789012", "Name": "TestAccount", "Status": "ACTIVE"}
            ],
            "organizational_units": [],
            "organizations_complete": {
                "noOutAccounts": [
                    {"name": "TestAccount", "id": "123456789012"}
                ]
            }
        }
        org_file.write_text(json.dumps(org_data))
        
        args = create_watch_args(
            watch_graph_organization=str(org_file)
        )
        
        # Mock console
        with patch('src.reports.console_view.Console') as mock_console:
            mock_console_instance = Mock()
            mock_console.return_value = mock_console_instance
            
            # Execute watch command
            watch_on_demand(args)
            
            # Verify console view was displayed
            assert mock_console_instance.print.called
    
    def test_watch_organizations_with_html_flag(self, tmp_path):
        """Test watch command with organizations file and HTML flag."""
        # Create organizations JSON file
        org_file = tmp_path / "organizations.json"
        org_data = {
            "organization": {"Id": "o-test123"},
            "accounts": [],
            "organizational_units": []
        }
        org_file.write_text(json.dumps(org_data))
        
        output_path = tmp_path / "report.html"
        
        args = create_watch_args(
            watch_graph_organization=str(org_file),
            html=True,
            html_output=str(output_path)
        )
        
        # Execute watch command
        watch_on_demand(args)
        
        # Verify HTML was created instead of console view
        assert output_path.exists()
        html_content = output_path.read_text()
        assert "<!DOCTYPE html>" in html_content


class TestOrganizationsViewWithDifferentDataFormats:
    """Test organizations view handles different data formats."""
    
    def test_with_organizations_complete(self, tmp_path):
        """Test with organizations_complete structure."""
        org_data = {
            "organization": {"Id": "o-test"},
            "accounts": [],
            "organizational_units": [],
            "organizations_complete": {
                "noOutAccounts": [],
                "organizationalUnits": {
                    "TestOU": {
                        "accounts": {
                            "TestAccount": {"id": "123456789012"}
                        }
                    }
                }
            }
        }
        
        with patch('src.reports.console_view.Console'):
            # Should not raise exception
            create_organizations_console_view(org_data)
    
    def test_without_organizations_complete(self, tmp_path):
        """Test without organizations_complete structure (fallback)."""
        org_data = {
            "organization": {"Id": "o-test"},
            "accounts": [
                {"Id": "123456789012", "Name": "TestAccount", "Status": "ACTIVE"}
            ],
            "organizational_units": []
        }
        
        with patch('src.reports.console_view.Console'):
            # Should not raise exception and use fallback
            create_organizations_console_view(org_data)
    
    def test_with_many_accounts(self, tmp_path):
        """Test with many accounts (should limit display)."""
        org_data = {
            "organization": {"Id": "o-test"},
            "accounts": [
                {"Id": f"12345678901{i}", "Name": f"Account{i}", "Status": "ACTIVE"}
                for i in range(20)
            ],
            "organizational_units": []
        }
        
        with patch('src.reports.console_view.Console'):
            # Should not raise exception
            create_organizations_console_view(org_data)
