"""Unit tests for the Explorer Controller.

Feature: interactive-identity-center-explorer
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

from src.explorer.controller import ExplorerController
from src.explorer.models import (
    OrganizationTree,
    ExplorerData,
    Account,
    OrganizationalUnit,
)


@pytest.fixture
def temp_json_dir(tmp_path):
    """Create a temporary JSON directory."""
    json_dir = tmp_path / "json"
    json_dir.mkdir()
    return str(json_dir)


@pytest.fixture
def mock_explorer_data():
    """Create mock explorer data."""
    org_tree = OrganizationTree(
        root_id="r-test",
        root_ous=[],
        root_accounts=[],
        all_accounts={}
    )
    return ExplorerData(
        organization=org_tree,
        assignments_by_account={},
        groups_by_id={},
        validation_warnings=[]
    )


def test_controller_initialization(temp_json_dir):
    """Test controller initialization."""
    controller = ExplorerController(temp_json_dir)
    
    assert controller.json_dir == temp_json_dir
    assert controller.console is not None
    assert controller.display_manager is None
    assert controller.navigation_engine is None
    assert controller.data is None
    assert controller.is_first_iteration is True


def test_controller_start_with_missing_directory():
    """Test controller start with missing JSON directory."""
    controller = ExplorerController("/nonexistent/path")
    
    with pytest.raises(SystemExit) as exc_info:
        controller.start()
    
    assert exc_info.value.code == 1


@patch('src.explorer.controller.DataLoader')
@patch('src.explorer.controller.DisplayManager')
@patch('src.explorer.controller.NavigationEngine')
def test_controller_start_with_valid_directory(
    mock_nav_engine,
    mock_display_manager,
    mock_data_loader,
    temp_json_dir,
    mock_explorer_data
):
    """Test controller start with valid directory."""
    # Setup mocks
    mock_loader_instance = Mock()
    mock_loader_instance.load_all_data.return_value = mock_explorer_data
    mock_data_loader.return_value = mock_loader_instance
    
    controller = ExplorerController(temp_json_dir)
    
    # Mock the exploration loop to exit immediately
    with patch.object(controller, 'run_exploration_loop'):
        controller.start()
    
    # Verify components were initialized
    assert controller.data is not None
    assert controller.display_manager is not None
    assert controller.navigation_engine is not None


@patch('src.explorer.controller.DataLoader')
def test_controller_start_with_file_not_found_error(
    mock_data_loader,
    temp_json_dir
):
    """Test controller handles FileNotFoundError during data loading."""
    # Setup mock to raise FileNotFoundError
    mock_loader_instance = Mock()
    mock_loader_instance.load_all_data.side_effect = FileNotFoundError("organizations_complete.json not found")
    mock_data_loader.return_value = mock_loader_instance
    
    controller = ExplorerController(temp_json_dir)
    
    with pytest.raises(SystemExit) as exc_info:
        controller.start()
    
    assert exc_info.value.code == 1


@patch('src.explorer.controller.DataLoader')
def test_controller_start_with_generic_error(
    mock_data_loader,
    temp_json_dir
):
    """Test controller handles generic errors during data loading."""
    # Setup mock to raise generic exception
    mock_loader_instance = Mock()
    mock_loader_instance.load_all_data.side_effect = Exception("Generic error")
    mock_data_loader.return_value = mock_loader_instance
    
    controller = ExplorerController(temp_json_dir)
    
    with pytest.raises(SystemExit) as exc_info:
        controller.start()
    
    assert exc_info.value.code == 1


@patch('src.explorer.controller.DataLoader')
@patch('src.explorer.controller.DisplayManager')
@patch('src.explorer.controller.NavigationEngine')
def test_controller_displays_validation_warnings(
    mock_nav_engine,
    mock_display_manager,
    mock_data_loader,
    temp_json_dir
):
    """Test controller displays validation warnings."""
    # Create data with warnings
    org_tree = OrganizationTree(
        root_id="r-test",
        root_ous=[],
        root_accounts=[],
        all_accounts={}
    )
    data_with_warnings = ExplorerData(
        organization=org_tree,
        assignments_by_account={},
        groups_by_id={},
        validation_warnings=["Warning 1", "Warning 2", "Warning 3"]
    )
    
    # Setup mocks
    mock_loader_instance = Mock()
    mock_loader_instance.load_all_data.return_value = data_with_warnings
    mock_data_loader.return_value = mock_loader_instance
    
    controller = ExplorerController(temp_json_dir)
    
    # Mock the exploration loop to exit immediately
    with patch.object(controller, 'run_exploration_loop'):
        controller.start()
    
    # Verify data was loaded with warnings
    assert len(controller.data.validation_warnings) == 3


def test_controller_shutdown():
    """Test controller shutdown."""
    controller = ExplorerController("/tmp")
    
    with pytest.raises(SystemExit) as exc_info:
        controller.shutdown()
    
    assert exc_info.value.code == 0


@patch('src.explorer.controller.DataLoader')
@patch('src.explorer.controller.DisplayManager')
@patch('src.explorer.controller.NavigationEngine')
def test_controller_handles_keyboard_interrupt_in_start(
    mock_nav_engine,
    mock_display_manager,
    mock_data_loader,
    temp_json_dir,
    mock_explorer_data
):
    """Test controller handles KeyboardInterrupt in start method."""
    # Setup mocks
    mock_loader_instance = Mock()
    mock_loader_instance.load_all_data.return_value = mock_explorer_data
    mock_data_loader.return_value = mock_loader_instance
    
    controller = ExplorerController(temp_json_dir)
    
    # Mock the exploration loop to raise KeyboardInterrupt
    with patch.object(controller, 'run_exploration_loop', side_effect=KeyboardInterrupt):
        with pytest.raises(SystemExit) as exc_info:
            controller.start()
        
        assert exc_info.value.code == 0
