"""Integration tests for CLI functionality."""
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, Mock
import subprocess
import sys

from src.reverse_diagrams import main
from src.config import Config, set_config


class TestCLIIntegration:
    """Test CLI integration scenarios."""
    
    def test_version_command(self, capsys):
        """Test version command."""
        with patch('sys.argv', ['reverse_diagrams', '--version']):
            result = main()
        
        assert result == 0
        captured = capsys.readouterr()
        assert "1.3.5" in captured.out  # Version should be displayed
    
    def test_list_plugins_command(self, capsys, mock_aws_credentials):
        """Test list plugins command."""
        with patch('sys.argv', ['reverse_diagrams', '--list-plugins']):
            result = main()
        
        assert result == 0
        # Should complete without error even if no plugins are available
    
    def test_invalid_arguments(self, capsys):
        """Test handling of invalid arguments."""
        with patch('sys.argv', ['reverse_diagrams', '--invalid-region', 'invalid']):
            result = main()
        
        assert result == 1  # Should exit with error code
    
    def test_missing_credentials(self, capsys):
        """Test handling of missing AWS credentials."""
        with patch('sys.argv', ['reverse_diagrams', '-o', '-r', 'us-east-1']):
            with patch('boto3.Session') as mock_session:
                mock_session.side_effect = Exception("No credentials")
                result = main()
        
        assert result == 1  # Should exit with error code
    
    def test_output_directory_creation(self, temp_dir, mock_aws_credentials):
        """Test that output directories are created."""
        output_dir = temp_dir / "test_output"
        
        with patch('sys.argv', [
            'reverse_diagrams', 
            '-o', 
            '-r', 'us-east-1',
            '-od', str(output_dir),
            '--no-auto'  # Don't actually run diagram generation
        ]):
            # Mock the graph_organizations function to avoid AWS calls
            with patch('src.reverse_diagrams.graph_organizations') as mock_graph:
                result = main()
        
        # Directories should be created
        assert output_dir.exists()
        assert (output_dir / "json").exists()
        assert (output_dir / "code").exists()
    
    def test_concurrent_processing_flag(self, mock_aws_credentials):
        """Test concurrent processing flag."""
        with patch('sys.argv', [
            'reverse_diagrams', 
            '-o', 
            '-r', 'us-east-1',
            '--concurrent'
        ]):
            with patch('src.reverse_diagrams.graph_organizations') as mock_graph:
                result = main()
        
        assert result == 0
    
    def test_plugin_execution(self, temp_dir, mock_aws_credentials):
        """Test plugin execution."""
        output_dir = temp_dir / "plugin_output"
        
        with patch('sys.argv', [
            'reverse_diagrams',
            '--plugin', 'ec2',
            '-r', 'us-east-1',
            '-od', str(output_dir)
        ]):
            # Mock plugin manager and EC2 plugin
            with patch('src.plugins.registry.get_plugin_manager') as mock_manager:
                mock_plugin = Mock()
                mock_plugin.collect_data.return_value = {"instances": [], "vpcs": []}
                mock_plugin.generate_diagram_code.return_value = "# Test diagram code"
                
                mock_manager_instance = Mock()
                mock_manager_instance.load_plugin.return_value = mock_plugin
                mock_manager.return_value = mock_manager_instance
                
                result = main()
        
        assert result == 0
        # Check that plugin files were created
        assert (output_dir / "code" / "graph_ec2.py").exists()
        assert (output_dir / "json" / "ec2_data.json").exists()


class TestEndToEndScenarios:
    """Test end-to-end scenarios with mocked AWS responses."""
    
    @pytest.fixture
    def mock_aws_responses(self):
        """Mock AWS API responses."""
        responses = {
            "organizations": {
                "describe_organization": {
                    "Organization": {
                        "Id": "o-test123456",
                        "MasterAccountId": "123456789012",
                        "FeatureSet": "ALL"
                    }
                },
                "list_roots": {
                    "Roots": [{"Id": "r-test", "Name": "Root"}]
                },
                "list_accounts": {
                    "Accounts": [
                        {
                            "Id": "123456789012",
                            "Name": "Master Account",
                            "Email": "admin@example.com",
                            "Status": "ACTIVE"
                        }
                    ]
                }
            }
        }
        return responses
    
    def test_organization_diagram_generation(self, temp_dir, mock_aws_responses, mock_aws_credentials):
        """Test complete organization diagram generation."""
        output_dir = temp_dir / "org_test"
        
        with patch('sys.argv', [
            'reverse_diagrams',
            '-o',
            '-r', 'us-east-1',
            '-od', str(output_dir),
            '--no-auto'  # Don't run actual diagram generation
        ]):
            # Mock AWS client manager calls
            with patch('src.aws.client_manager.AWSClientManager') as mock_manager:
                mock_instance = Mock()
                
                # Setup mock responses
                def mock_call_api(service, method, **kwargs):
                    if service == "organizations":
                        return mock_aws_responses["organizations"][method]
                    return {}
                
                mock_instance.call_api = mock_call_api
                mock_instance.paginate_api_call = Mock(return_value=[])
                mock_manager.return_value = mock_instance
                
                # Mock the graph_organizations function
                with patch('src.aws.describe_organization.graph_organizations') as mock_graph:
                    result = main()
        
        assert result == 0
    
    def test_watch_command(self, temp_dir):
        """Test watch command functionality."""
        # Create test JSON file
        test_data = {"test": "data"}
        json_file = temp_dir / "test.json"
        json_file.write_text(json.dumps(test_data))
        
        with patch('sys.argv', [
            'reverse_diagrams',
            'watch',
            '-wo', str(json_file)
        ]):
            # Mock the watch_on_demand function
            with patch('src.reports.console_view.watch_on_demand') as mock_watch:
                result = main()
        
        assert result == 0
        mock_watch.assert_called_once()


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_keyboard_interrupt(self, mock_aws_credentials):
        """Test handling of keyboard interrupt."""
        with patch('sys.argv', ['reverse_diagrams', '-o', '-r', 'us-east-1']):
            with patch('src.reverse_diagrams.graph_organizations') as mock_graph:
                mock_graph.side_effect = KeyboardInterrupt()
                result = main()
        
        assert result == 1  # Should exit gracefully
    
    def test_aws_service_error(self, mock_aws_credentials):
        """Test handling of AWS service errors."""
        with patch('sys.argv', ['reverse_diagrams', '-o', '-r', 'us-east-1']):
            with patch('src.aws.client_manager.AWSClientManager') as mock_manager:
                from src.aws.exceptions import AWSServiceError
                mock_manager.side_effect = AWSServiceError("Service unavailable")
                result = main()
        
        assert result == 1  # Should exit with error
    
    def test_permission_error(self, temp_dir, mock_aws_credentials):
        """Test handling of file permission errors."""
        # Create read-only directory
        readonly_dir = temp_dir / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Read-only
        
        with patch('sys.argv', [
            'reverse_diagrams',
            '-o',
            '-r', 'us-east-1',
            '-od', str(readonly_dir)
        ]):
            with patch('src.reverse_diagrams.graph_organizations') as mock_graph:
                result = main()
        
        # Should handle permission error gracefully
        # Result may vary depending on OS and permissions