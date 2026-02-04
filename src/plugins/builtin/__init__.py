"""Built-in plugins for Reverse Diagrams."""

# Import all built-in plugins to ensure they're available for discovery
from .ec2_plugin import EC2Plugin
from .organizations_plugin import OrganizationsPlugin
from .identity_center_plugin import IdentityCenterPlugin

__all__ = [
    'EC2Plugin',
    'OrganizationsPlugin', 
    'IdentityCenterPlugin'
]