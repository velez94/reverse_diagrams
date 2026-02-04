"""Plugin registry and discovery system."""
import logging
from pathlib import Path
from typing import Type, List, Optional
import os

from .base import AWSServicePlugin, PluginManager, discover_plugins_in_directory

logger = logging.getLogger(__name__)

# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get or create global plugin manager instance."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
        # Auto-discover built-in plugins
        discover_plugins()
    return _plugin_manager


def register_plugin(plugin_class: Type[AWSServicePlugin]) -> None:
    """
    Register a plugin class with the global manager.
    
    Args:
        plugin_class: Plugin class to register
    """
    manager = get_plugin_manager()
    manager.register_plugin(plugin_class)


def discover_plugins() -> List[Type[AWSServicePlugin]]:
    """
    Discover and register plugins from standard locations.
    
    Returns:
        List of discovered plugin classes
    """
    manager = get_plugin_manager()
    all_discovered = []
    
    # Standard plugin directories
    plugin_directories = [
        Path(__file__).parent / "builtin",  # Built-in plugins
        Path.home() / ".reverse_diagrams" / "plugins",  # User plugins
        Path.cwd() / "plugins",  # Local plugins
    ]
    
    # Add plugins from environment variable
    env_plugin_dirs = os.environ.get("REVERSE_DIAGRAMS_PLUGIN_DIRS", "")
    if env_plugin_dirs:
        for dir_path in env_plugin_dirs.split(":"):
            if dir_path.strip():
                plugin_directories.append(Path(dir_path.strip()))
    
    # Discover plugins in each directory
    for plugin_dir in plugin_directories:
        try:
            discovered = discover_plugins_in_directory(plugin_dir)
            for plugin_class in discovered:
                manager.register_plugin(plugin_class)
                all_discovered.append(plugin_class)
                
        except Exception as e:
            logger.warning(f"Failed to discover plugins in {plugin_dir}: {e}")
    
    logger.debug(f"Discovered and registered {len(all_discovered)} plugins")
    return all_discovered


def list_available_plugins() -> List[str]:
    """
    List names of all available plugins.
    
    Returns:
        List of plugin names
    """
    manager = get_plugin_manager()
    metadata_list = manager.list_available_plugins()
    return [metadata.name for metadata in metadata_list]


def get_plugin_info(plugin_name: str) -> Optional[dict]:
    """
    Get information about a specific plugin.
    
    Args:
        plugin_name: Name of the plugin
        
    Returns:
        Plugin information dictionary or None if not found
    """
    manager = get_plugin_manager()
    
    # Try to get from loaded plugins first
    plugin = manager.get_plugin(plugin_name)
    if plugin:
        metadata = plugin.metadata
        return {
            "name": metadata.name,
            "version": metadata.version,
            "description": metadata.description,
            "author": metadata.author,
            "aws_services": metadata.aws_services,
            "dependencies": metadata.dependencies,
            "status": "loaded"
        }
    
    # Check available plugins
    for metadata in manager.list_available_plugins():
        if metadata.name == plugin_name:
            return {
                "name": metadata.name,
                "version": metadata.version,
                "description": metadata.description,
                "author": metadata.author,
                "aws_services": metadata.aws_services,
                "dependencies": metadata.dependencies,
                "status": "available"
            }
    
    return None