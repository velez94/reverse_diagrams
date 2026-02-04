# Project Structure

## Source Layout
The project follows Python's `src/` layout pattern for better packaging and testing isolation.

```
src/
├── __init__.py
├── reverse_diagrams.py          # Main CLI entry point with error handling
├── version.py                   # Version management
├── config.py                    # Centralized configuration management
├── models.py                    # Data models with validation
├── aws/                         # AWS service integrations
│   ├── __init__.py
│   ├── exceptions.py           # Custom AWS exception hierarchy
│   ├── client_manager.py       # AWS client management with retry logic
│   ├── describe_organization.py # AWS Organizations API calls
│   ├── describe_sso.py         # IAM Identity Center API calls
│   └── describe_identity_store.py
├── dgms/                        # Diagram generation
│   ├── graph_template.py       # Python code templates for diagrams
│   └── graph_mapper.py         # Logic for mapping AWS data to diagrams
├── reports/                     # Output and visualization
│   ├── save_results.py         # Enhanced JSON file operations
│   └── console_view.py         # Terminal-based viewing
├── utils/                       # Utility modules
│   ├── __init__.py
│   ├── progress.py             # Progress tracking with rich console
│   ├── cache.py                # Caching system for AWS API responses
│   └── concurrent.py           # Concurrent processing utilities
├── plugins/                     # Plugin system
│   ├── __init__.py
│   ├── base.py                 # Base plugin classes and manager
│   ├── registry.py             # Plugin discovery and registration
│   └── builtin/                # Built-in plugins
│       ├── __init__.py
│       └── ec2_plugin.py       # EC2 service plugin
└── banner/                      # CLI utilities
    └── banner.py               # Version display and branding
```

## Testing Structure
Comprehensive testing framework with unit and integration tests:

```
tests/
├── __init__.py
├── conftest.py                 # Pytest configuration and fixtures
├── unit/                       # Unit tests
│   ├── __init__.py
│   ├── test_client_manager.py  # AWS client manager tests
│   ├── test_models.py          # Data model validation tests
│   ├── test_config.py          # Configuration management tests
│   └── test_progress.py        # Progress tracking tests
└── integration/                # Integration tests
    ├── __init__.py
    ├── test_cli_integration.py  # End-to-end CLI tests
    └── test_aws_integration.py  # AWS API integration tests
```

## Output Structure
Generated files are organized in the `diagrams/` directory:

```
diagrams/
├── json/                       # Raw AWS data exports
│   ├── organizations.json
│   ├── organizations_complete.json
│   ├── groups.json
│   ├── account_assignments.json
│   └── *_data.json            # Plugin-generated data files
├── code/                       # Generated Python diagram code
│   ├── graph_org.py           # Organizations diagram script
│   ├── graph_sso.py           # SSO diagram script
│   └── graph_*.py             # Plugin-generated diagram scripts
└── images/                     # Generated diagram images
    └── *.png                  # Diagram output files
```

## Module Responsibilities

### `aws/` - AWS API Integration
- **exceptions.py**: Custom exception hierarchy for AWS errors
- **client_manager.py**: Centralized AWS client management with retry logic and error handling
- **describe_*.py**: Service-specific API calls with proper error handling
- Handle AWS service API calls with pagination and retry logic
- Manage AWS CLI profile authentication with validation
- Transform AWS API responses into structured data models
- Support for Organizations and IAM Identity Center services

### `config.py` - Configuration Management
- Centralized configuration with environment variable support
- Structured settings for pagination, AWS operations, output, and logging
- Runtime configuration validation and setup

### `models.py` - Data Models & Validation
- Type-safe data models for AWS resources
- Input validation and sanitization
- Structured representations of organizations, accounts, users, and groups
- Data transformation utilities for diagram generation

### `dgms/` - Diagram Generation
- Contains Python code templates for diagram generation
- Maps AWS resource relationships to diagram structures
- Handles nested organizational unit hierarchies
- Creates executable Python scripts using the `diagrams` library

### `reports/` - Output Management
- **save_results.py**: Enhanced JSON serialization with error handling, backup, and validation
- **console_view.py**: Rich terminal-based console viewing
- Interactive prompts for selective viewing
- Formatted output with colors and panels

### `utils/` - Utility Modules
- **progress.py**: Rich console progress tracking with bars, spinners, and status panels
- **cache.py**: Intelligent caching system for AWS API responses with TTL support
- **concurrent.py**: Concurrent processing utilities for improved performance
- Reusable utility functions for common operations
- Helper functions for data processing and formatting

### `plugins/` - Plugin System
- **base.py**: Abstract base classes for AWS service plugins and plugin manager
- **registry.py**: Plugin discovery, registration, and lifecycle management
- **builtin/**: Built-in plugins for common AWS services (EC2, RDS, etc.)
- Extensible architecture for adding new AWS service support
- Plugin metadata and dependency management

### Entry Point Pattern
- `reverse_diagrams.py` serves as the main CLI entry point with comprehensive error handling
- Uses `argparse` with validation and user-friendly error messages
- Supports both direct execution and watch mode
- Integrates `argcomplete` for shell tab completion
- Plugin system integration with `--plugin` and `--list-plugins` options
- Concurrent processing support with `--concurrent` flag
- Proper logging setup and configuration management

## Architecture Improvements

### Error Handling Strategy
- **Hierarchical Exceptions**: Custom exception types for different error categories
- **Retry Logic**: Automatic retry with exponential backoff for transient errors
- **User-Friendly Messages**: Clear error messages with actionable suggestions
- **Graceful Degradation**: Proper handling of partial failures

### Configuration Management
- **Environment Variables**: Support for configuration via environment variables
- **Structured Config**: Type-safe configuration with validation
- **Runtime Setup**: Automatic logging and client configuration

### Progress Tracking
- **Rich Console Output**: Progress bars, spinners, and status panels
- **Contextual Tracking**: Operation-specific progress indicators
- **User Feedback**: Clear success/error/warning messages

### Performance Optimization
- **Concurrent Processing**: Multi-threaded processing for AWS API calls
- **Intelligent Caching**: TTL-based caching for AWS API responses
- **Connection Reuse**: Efficient AWS client management with connection pooling
- **Configurable Limits**: Adjustable pagination and concurrency settings

### Plugin Architecture
- **Extensible Design**: Easy addition of new AWS service support
- **Plugin Discovery**: Automatic discovery from multiple directories
- **Lifecycle Management**: Proper plugin loading, setup, and cleanup
- **Metadata System**: Rich plugin information and dependency tracking

## Coding Conventions

### Enhanced Standards
- **Type Hints**: Comprehensive type annotations throughout
- **Error Handling**: Proper exception handling with specific error types
- **Logging**: Structured logging with configurable levels
- **Validation**: Input validation using data models
- **Documentation**: Comprehensive docstrings following Google style

### Design Patterns
- **Dependency Injection**: Configuration and client management
- **Factory Pattern**: Client creation and management
- **Context Managers**: Resource management and progress tracking
- **Decorator Pattern**: Retry logic and error handling
- **Plugin Pattern**: Extensible service support
- **Observer Pattern**: Progress tracking and event handling

### Code Quality
- **Separation of Concerns**: Clear module boundaries and responsibilities
- **Single Responsibility**: Functions and classes with focused purposes
- **Error Recovery**: Graceful handling of failures with user guidance
- **Performance**: Efficient API usage with caching and connection reuse
- **Testability**: Comprehensive unit and integration test coverage

## Testing Strategy

### Unit Tests
- AWS client manager functionality with retry logic
- Configuration management and environment variable handling
- Data model validation and sanitization
- Error handling scenarios and exception propagation
- Plugin system functionality and lifecycle management
- Concurrent processing utilities
- Caching system behavior and TTL handling

### Integration Tests
- End-to-end diagram generation workflows
- AWS API integration with comprehensive mocks
- File system operations and permission handling
- CLI argument processing and validation
- Plugin loading and execution
- Multi-service diagram generation

### Performance Tests
- Large organization processing with thousands of accounts
- Memory usage optimization and leak detection
- Concurrent operation efficiency and scaling
- API rate limit handling and backoff behavior
- Cache effectiveness and hit rates

## Development Workflow

### Code Quality Tools
- **Black**: Code formatting with 88-character line length
- **isort**: Import sorting with Black compatibility
- **flake8**: Linting with extended ignore rules
- **mypy**: Static type checking with gradual typing
- **pre-commit**: Automated code quality checks

### Testing Commands
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/

# Type checking
mypy src/

# Code formatting
black src/ tests/
isort src/ tests/
```

### Plugin Development
- Extend `AWSServicePlugin` base class
- Implement required methods: `collect_data()`, `generate_diagram_code()`
- Define plugin metadata with service dependencies
- Place in `src/plugins/builtin/` or external plugin directory
- Automatic discovery and registration on startup