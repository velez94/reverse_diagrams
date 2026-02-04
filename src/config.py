"""Configuration management for Reverse Diagrams."""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any
import logging


@dataclass
class PaginationConfig:
    """Configuration for AWS API pagination."""
    default_page_size: int = 20
    max_page_size: int = 1000
    max_items: int = 10000


@dataclass
class AWSConfig:
    """Configuration for AWS operations."""
    timeout: int = 30
    max_retries: int = 3
    backoff_factor: float = 2.0
    
    # Required permissions documentation
    required_permissions: Dict[str, list] = field(default_factory=lambda: {
        'organizations': [
            'organizations:DescribeOrganization',
            'organizations:ListRoots',
            'organizations:ListOrganizationalUnitsForParent',
            'organizations:ListAccounts',
            'organizations:ListParents'
        ],
        'sso-admin': [
            'sso:ListInstances',
            'sso:ListPermissionSets',
            'sso:DescribePermissionSet',
            'sso:ListAccountAssignments'
        ],
        'identitystore': [
            'identitystore:ListGroups',
            'identitystore:ListUsers',
            'identitystore:ListGroupMemberships'
        ]
    })


@dataclass
class OutputConfig:
    """Configuration for output generation."""
    default_output_dir: str = "diagrams"
    json_indent: int = 4
    create_directories: bool = True
    file_permissions: int = 0o644
    
    # Supported output formats
    supported_formats: list = field(default_factory=lambda: ['png', 'svg', 'pdf'])


@dataclass
class LoggingConfig:
    """Configuration for logging."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[Path] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


@dataclass
class Config:
    """Main configuration class."""
    pagination: PaginationConfig = field(default_factory=PaginationConfig)
    aws: AWSConfig = field(default_factory=AWSConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # Performance settings
    max_concurrent_workers: int = 5
    enable_caching: bool = True
    cache_ttl_hours: int = 1
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create configuration from environment variables."""
        config = cls()
        
        # AWS configuration from environment
        if os.getenv('AWS_TIMEOUT'):
            config.aws.timeout = int(os.getenv('AWS_TIMEOUT'))
        if os.getenv('AWS_MAX_RETRIES'):
            config.aws.max_retries = int(os.getenv('AWS_MAX_RETRIES'))
        
        # Output configuration from environment
        if os.getenv('REVERSE_DIAGRAMS_OUTPUT_DIR'):
            config.output.default_output_dir = os.getenv('REVERSE_DIAGRAMS_OUTPUT_DIR')
        
        # Logging configuration from environment
        if os.getenv('LOG_LEVEL'):
            config.logging.level = os.getenv('LOG_LEVEL').upper()
        if os.getenv('LOG_FILE'):
            config.logging.file_path = Path(os.getenv('LOG_FILE'))
        
        # Performance settings from environment
        if os.getenv('MAX_WORKERS'):
            config.max_concurrent_workers = int(os.getenv('MAX_WORKERS'))
        if os.getenv('ENABLE_CACHING'):
            config.enable_caching = os.getenv('ENABLE_CACHING').lower() == 'true'
        
        return config
    
    def setup_logging(self):
        """Setup logging based on configuration."""
        handlers = [logging.StreamHandler()]
        
        if self.logging.file_path:
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                self.logging.file_path,
                maxBytes=self.logging.max_file_size,
                backupCount=self.logging.backup_count
            )
            handlers.append(file_handler)
        
        logging.basicConfig(
            level=getattr(logging, self.logging.level),
            format=self.logging.format,
            handlers=handlers
        )
        
        # Reduce noise from AWS SDK
        logging.getLogger('boto3').setLevel(logging.WARNING)
        logging.getLogger('botocore').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = Config.from_env()
        _config.setup_logging()
    return _config


def set_config(config: Config):
    """Set global configuration instance."""
    global _config
    _config = config
    _config.setup_logging()