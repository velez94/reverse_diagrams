"""Base plugin system for AWS service integrations."""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type
from dataclasses import dataclass
from pathlib import Path

from ..aws.client_manager import AWSClientManager
from ..models import DiagramConfig

logger = logging.getLogger(__name__)


@dataclass
class PluginMetadata:
    """Metadata for a plugin."""
    name: str
    version: str
    description: str
    author: str
    aws_services: List[str]  # AWS services this plugin supports
    dependencies: List[str] = None  # Additional dependencies
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class AWSServicePlugin(ABC):
    """Base class for AWS service plugins."""
    
    def __init__(self):
        """Initialize the plugin."""
        self._metadata: Optional[PluginMetadata] = None
        self._client_manager: Optional[AWSClientManager] = None
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        pass
    
    @abstractmethod
    def collect_data(self, client_manager: AWSClientManager, region: str, **kwargs) -> Dict[str, Any]:
        """
        Collect data from AWS services.
        
        Args:
            client_manager: AWS client manager
            region: AWS region
            **kwargs: Additional parameters
            
        Returns:
            Collected data dictionary
        """
        pass
    
    @abstractmethod
    def generate_diagram_code(self, data: Dict[str, Any], config: DiagramConfig) -> str:
        """
        Generate diagram code from collected data.
        
        Args:
            data: Data collected from AWS
            config: Diagram configuration
            
        Returns:
            Python code for generating diagram
        """
        pass
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate collected data.
        
        Args:
            data: Data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        return bool(data)  # Default implementation
    
    def get_required_permissions(self) -> List[str]:
        """
        Get list of required AWS permissions.
        
        Returns:
            List of IAM permission strings
        """
        return []  # Default implementation
    
    def setup(self, client_manager: AWSClientManager) -> None:
        """
        Setup the plugin with client manager.
        
        Args:
            client_manager: AWS client manager
        """
        self._client_manager = client_manager
        logger.debug(f"Plugin {self.metadata.name} setup complete")
    
    def cleanup(self) -> None:
        """Cleanup plugin resources."""
        self._client_manager = None
        logger.debug(f"Plugin {self.metadata.name} cleanup complete")


class PluginManager:
    """Manager for AWS service plugins."""
    
    def __init__(self):
        """Initialize plugin manager."""
        self._plugins: Dict[str, AWSServicePlugin] = {}
        self._plugin_classes: Dict[str, Type[AWSServicePlugin]] = {}
        
    def register_plugin(self, plugin_class: Type[AWSServicePlugin]) -> None:
        """
        Register a plugin class.
        
        Args:
            plugin_class: Plugin class to register
        """
        try:
            # Create instance to get metadata
            plugin_instance = plugin_class()
            metadata = plugin_instance.metadata
            
            if metadata.name in self._plugin_classes:
                logger.warning(f"Plugin {metadata.name} is already registered, overriding")
            
            self._plugin_classes[metadata.name] = plugin_class
            logger.debug(f"Registered plugin: {metadata.name} v{metadata.version}")
            
        except Exception as e:
            logger.error(f"Failed to register plugin {plugin_class.__name__}: {e}")
            raise
    
    def load_plugin(self, plugin_name: str, client_manager: AWSClientManager) -> AWSServicePlugin:
        """
        Load and setup a plugin.
        
        Args:
            plugin_name: Name of the plugin to load
            client_manager: AWS client manager
            
        Returns:
            Loaded plugin instance
            
        Raises:
            ValueError: If plugin is not found
        """
        if plugin_name not in self._plugin_classes:
            raise ValueError(f"Plugin {plugin_name} not found. Available: {list(self._plugin_classes.keys())}")
        
        if plugin_name in self._plugins:
            logger.debug(f"Plugin {plugin_name} already loaded")
            return self._plugins[plugin_name]
        
        try:
            plugin_class = self._plugin_classes[plugin_name]
            plugin_instance = plugin_class()
            plugin_instance.setup(client_manager)
            
            self._plugins[plugin_name] = plugin_instance
            logger.debug(f"Loaded plugin: {plugin_name}")
            
            return plugin_instance
            
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}")
            raise
    
    def unload_plugin(self, plugin_name: str) -> None:
        """
        Unload a plugin.
        
        Args:
            plugin_name: Name of the plugin to unload
        """
        if plugin_name in self._plugins:
            plugin = self._plugins[plugin_name]
            plugin.cleanup()
            del self._plugins[plugin_name]
            logger.debug(f"Unloaded plugin: {plugin_name}")
    
    def get_plugin(self, plugin_name: str) -> Optional[AWSServicePlugin]:
        """
        Get a loaded plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin instance if loaded, None otherwise
        """
        return self._plugins.get(plugin_name)
    
    def list_available_plugins(self) -> List[PluginMetadata]:
        """
        List all available plugins.
        
        Returns:
            List of plugin metadata
        """
        metadata_list = []
        for plugin_class in self._plugin_classes.values():
            try:
                instance = plugin_class()
                metadata_list.append(instance.metadata)
            except Exception as e:
                logger.warning(f"Failed to get metadata for plugin {plugin_class.__name__}: {e}")
        
        return metadata_list
    
    def list_loaded_plugins(self) -> List[str]:
        """
        List names of loaded plugins.
        
        Returns:
            List of loaded plugin names
        """
        return list(self._plugins.keys())
    
    def get_plugins_for_service(self, aws_service: str) -> List[AWSServicePlugin]:
        """
        Get all loaded plugins that support a specific AWS service.
        
        Args:
            aws_service: AWS service name
            
        Returns:
            List of plugins supporting the service
        """
        matching_plugins = []
        
        for plugin in self._plugins.values():
            if aws_service in plugin.metadata.aws_services:
                matching_plugins.append(plugin)
        
        return matching_plugins
    
    def cleanup_all(self) -> None:
        """Cleanup all loaded plugins."""
        for plugin_name in list(self._plugins.keys()):
            self.unload_plugin(plugin_name)
        
        logger.debug("All plugins cleaned up")


def discover_plugins_in_directory(directory: Path) -> List[Type[AWSServicePlugin]]:
    """
    Discover plugins in a directory.
    
    Args:
        directory: Directory to search for plugins
        
    Returns:
        List of discovered plugin classes
    """
    discovered_plugins = []
    
    if not directory.exists() or not directory.is_dir():
        logger.debug(f"Plugin directory {directory} does not exist")
        return discovered_plugins
    
    # Look for Python files in the directory
    for plugin_file in directory.glob("*.py"):
        if plugin_file.name.startswith("_"):
            continue  # Skip private files
        
        try:
            # Import the module dynamically
            import importlib.util
            spec = importlib.util.spec_from_file_location(plugin_file.stem, plugin_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Look for plugin classes
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, AWSServicePlugin) and 
                        attr != AWSServicePlugin):
                        discovered_plugins.append(attr)
                        logger.debug(f"Discovered plugin class: {attr.__name__} in {plugin_file}")
                        
        except Exception as e:
            logger.warning(f"Failed to load plugin from {plugin_file}: {e}")
    
    return discovered_plugins