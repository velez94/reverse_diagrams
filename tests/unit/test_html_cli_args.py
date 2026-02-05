"""Unit tests for HTML report CLI argument parsing.

Tests CLI argument parsing for HTML report generation flags.
"""
import pytest
import argparse
from src.reverse_diagrams import validate_arguments


def create_test_args(**kwargs):
    """Helper to create argument namespace for testing."""
    defaults = {
        'profile': None,
        'output_dir_path': 'diagrams',
        'region': 'us-east-1',
        'graph_organization': False,
        'graph_identity': False,
        'auto_create': True,
        'plugins': None,
        'list_plugins': False,
        'concurrent': True,
        'html_report': False,
        'html_output': None,
        'commands': None,
        'version': False,
        'debug': False
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestHTMLReportFlagRecognition:
    """Test that --html-report flag is recognized."""
    
    def test_html_report_flag_recognized(self):
        """Test --html-report flag is recognized and sets attribute."""
        args = create_test_args(html_report=True)
        assert args.html_report is True
    
    def test_html_report_flag_default_false(self):
        """Test --html-report flag defaults to False."""
        args = create_test_args()
        assert args.html_report is False


class TestHTMLOutputPathValidation:
    """Test --html-output flag with valid and invalid paths."""
    
    def test_html_output_with_valid_path(self):
        """Test --html-output with valid path."""
        args = create_test_args(html_report=True, html_output='reports/custom.html')
        # Should not raise exception
        validate_arguments(args)
    
    def test_html_output_without_html_report_raises_error(self):
        """Test --html-output without --html-report raises ValueError."""
        args = create_test_args(html_output='reports/custom.html')
        with pytest.raises(ValueError, match="--html-output flag requires --html-report"):
            validate_arguments(args)
    
    def test_html_output_none_is_valid(self):
        """Test that html_output=None is valid (uses default)."""
        args = create_test_args(html_report=True, html_output=None)
        # Should not raise exception
        validate_arguments(args)


class TestInvalidFlagCombinations:
    """Test invalid flag combinations."""
    
    def test_html_output_requires_html_report(self):
        """Test that --html-output requires --html-report."""
        args = create_test_args(html_output='custom.html', html_report=False)
        with pytest.raises(ValueError, match="--html-output flag requires --html-report"):
            validate_arguments(args)
    
    def test_no_operation_specified_raises_error(self):
        """Test that at least one operation must be specified."""
        args = create_test_args()
        with pytest.raises(ValueError, match="Please specify at least one operation"):
            validate_arguments(args)
    
    def test_html_report_alone_is_valid_operation(self):
        """Test that --html-report alone is a valid operation."""
        args = create_test_args(html_report=True)
        # Should not raise exception
        validate_arguments(args)


class TestDefaultBehavior:
    """Test default behavior of HTML flags."""
    
    def test_default_html_report_is_false(self):
        """Test that html_report defaults to False."""
        args = create_test_args()
        assert args.html_report is False
    
    def test_default_html_output_is_none(self):
        """Test that html_output defaults to None."""
        args = create_test_args()
        assert args.html_output is None
    
    def test_html_report_with_other_flags(self):
        """Test --html-report can be combined with -o and -i flags."""
        args = create_test_args(
            html_report=True,
            graph_organization=True,
            graph_identity=True
        )
        # Should not raise exception
        validate_arguments(args)


class TestWatchCommandHTMLFlag:
    """Test --html flag in watch command."""
    
    def test_watch_command_with_html_flag(self):
        """Test watch command can have html attribute."""
        args = create_test_args(commands='watch')
        # Add watch-specific attributes
        args.html = True
        args.watch_graph_organization = 'diagrams/json/organizations.json'
        
        # Should not raise exception
        validate_arguments(args)
    
    def test_watch_command_without_html_flag(self):
        """Test watch command without html flag."""
        args = create_test_args(commands='watch')
        args.html = False
        args.watch_graph_organization = 'diagrams/json/organizations.json'
        
        # Should not raise exception
        validate_arguments(args)
