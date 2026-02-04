"""Save results with enhanced error handling and validation."""
import json
import logging
from pathlib import Path
from typing import Any, Union, Optional
import os

from ..config import get_config
from ..utils.progress import get_progress_tracker

logger = logging.getLogger(__name__)


def save_results(
    results: Any, 
    filename: str, 
    directory_path: Union[str, Path] = ".",
    indent: Optional[int] = None,
    validate_json: bool = True
) -> bool:
    """
    Save results to a JSON file with proper error handling.

    Args:
        results: Data to save
        filename: Output filename
        directory_path: Directory to save the file
        indent: JSON indentation (uses config default if None)
        validate_json: Whether to validate JSON before saving

    Returns:
        True if successful, False otherwise
    """
    config = get_config()
    progress = get_progress_tracker()
    
    if indent is None:
        indent = config.output.json_indent
    
    try:
        # Ensure directory exists
        directory = Path(directory_path)
        if config.output.create_directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Validate directory is writable
        if not directory.exists():
            raise FileNotFoundError(f"Directory {directory} does not exist")
        
        if not os.access(directory, os.W_OK):
            raise PermissionError(f"No write permission for directory {directory}")
        
        # Prepare file path
        file_path = directory / filename
        
        # Validate JSON serialization if requested
        if validate_json:
            try:
                json.dumps(results, indent=indent, default=str)
            except (TypeError, ValueError) as e:
                raise ValueError(f"Data is not JSON serializable: {e}")
        
        # Write file
        with file_path.open('w', encoding='utf-8') as f:
            json.dump(results, f, indent=indent, default=str, ensure_ascii=False)
        
        # Set file permissions
        try:
            os.chmod(file_path, config.output.file_permissions)
        except OSError as e:
            logger.warning(f"Could not set file permissions for {file_path}: {e}")
        
        # Log success
        file_size = file_path.stat().st_size
        logger.debug(f"Saved {filename} ({file_size} bytes) to {directory}")
        
        progress.show_success(
            f"💾 Data saved successfully",
            f"File: {file_path}\nSize: {file_size:,} bytes"
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to save {filename}: {e}")
        progress.show_error(
            f"Failed to save {filename}",
            f"Error: {e}\nDirectory: {directory_path}"
        )
        return False


def load_results(
    filename: str, 
    directory_path: Union[str, Path] = ".",
    validate_exists: bool = True
) -> Optional[Any]:
    """
    Load results from a JSON file with error handling.

    Args:
        filename: Input filename
        directory_path: Directory containing the file
        validate_exists: Whether to validate file exists

    Returns:
        Loaded data or None if failed
    """
    progress = get_progress_tracker()
    
    try:
        file_path = Path(directory_path) / filename
        
        if validate_exists and not file_path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist")
        
        if not os.access(file_path, os.R_OK):
            raise PermissionError(f"No read permission for file {file_path}")
        
        with file_path.open('r', encoding='utf-8') as f:
            data = json.load(f)
        
        file_size = file_path.stat().st_size
        logger.info(f"Loaded {filename} ({file_size} bytes) from {directory_path}")
        
        return data
        
    except Exception as e:
        logger.error(f"Failed to load {filename}: {e}")
        progress.show_error(
            f"Failed to load {filename}",
            f"Error: {e}\nPath: {Path(directory_path) / filename}"
        )
        return None


def backup_file(file_path: Union[str, Path], max_backups: int = 5) -> bool:
    """
    Create a backup of an existing file.

    Args:
        file_path: Path to file to backup
        max_backups: Maximum number of backups to keep

    Returns:
        True if backup created successfully, False otherwise
    """
    try:
        file_path = Path(file_path)
        
        if not file_path.exists():
            return True  # No file to backup
        
        # Create backup filename
        backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
        
        # If backup already exists, rotate backups
        if backup_path.exists():
            for i in range(max_backups - 1, 0, -1):
                old_backup = file_path.with_suffix(f"{file_path.suffix}.backup.{i}")
                new_backup = file_path.with_suffix(f"{file_path.suffix}.backup.{i + 1}")
                
                if old_backup.exists():
                    if new_backup.exists():
                        new_backup.unlink()
                    old_backup.rename(new_backup)
            
            # Move current backup to .backup.1
            backup_1 = file_path.with_suffix(f"{file_path.suffix}.backup.1")
            if backup_1.exists():
                backup_1.unlink()
            backup_path.rename(backup_1)
        
        # Create new backup
        import shutil
        shutil.copy2(file_path, backup_path)
        
        logger.debug(f"Created backup: {backup_path}")
        return True
        
    except Exception as e:
        logger.warning(f"Failed to create backup for {file_path}: {e}")
        return False


def ensure_directory_structure(base_path: Union[str, Path]) -> bool:
    """
    Ensure the standard directory structure exists.

    Args:
        base_path: Base directory path

    Returns:
        True if structure created successfully, False otherwise
    """
    try:
        base_path = Path(base_path)
        
        # Standard directories
        directories = [
            base_path,
            base_path / "json",
            base_path / "code",
            base_path / "images"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
            # Set permissions
            try:
                os.chmod(directory, 0o755)
            except OSError:
                pass
        
        logger.info(f"Directory structure ensured at {base_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create directory structure at {base_path}: {e}")
        return False
