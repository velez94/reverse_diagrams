"""Plugin system for Reverse Diagrams."""

from .base import AWSServicePlugin, PluginManager
from .registry import get_plugin_manager, register_plugin, discover_plugins

__all__ = [
    'AWSServicePlugin',
    'PluginManager', 
    'get_plugin_manager',
    'register_plugin',
    'discover_plugins'
]