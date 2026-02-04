# Technology Stack

## Build System
- **Build Backend**: Hatchling (modern Python packaging)
- **Package Manager**: pip (standard Python package installation)
- **Distribution**: PyPI package `reverse_diagrams`

## Core Dependencies
- **boto3** (>=1.42.19): AWS SDK for Python - core AWS API interactions
- **diagrams** (>=0.25.1): Python library for creating architecture diagrams
- **rich** (>=14.2.0): Terminal formatting and console output
- **inquirer** (>=3.4.1): Interactive command-line prompts
- **colorama** (>=0.4.6): Cross-platform colored terminal text
- **emoji** (>=2.15.0): Emoji support in terminal output
- **argcomplete** (>=3.6.3): Command-line tab completion

## Python Requirements
- **Minimum Version**: Python 3.8+
- **Package Structure**: Source layout with `src/` directory

## Common Commands

### Installation
```bash
pip install reverse_diagrams
```

### Development Setup
```bash
# Install in development mode
pip install -e .

# Enable autocomplete (optional)
activate-global-python-argcomplete
echo 'eval "$(register-python-argcomplete reverse_diagrams)"' >> ~/.bashrc
source ~/.bashrc
```

### Usage Examples
```bash
# Generate organization diagram
reverse_diagrams -p my-profile -o -r us-east-1

# Generate IAM Identity Center diagram  
reverse_diagrams -p my-profile -i -r us-east-1

# Both diagrams with auto-creation
reverse_diagrams -p my-profile -o -i -a -r us-east-1

# Watch console view
reverse_diagrams watch -wa diagrams/json/account_assignments.json
```

## Architecture Notes
- Uses AWS CLI profiles for authentication with proper validation
- Comprehensive error handling with retry logic and user-friendly messages
- Outputs both Python diagram code and PNG images
- Stores intermediate data as JSON files with proper validation
- Supports pagination for large AWS environments with configurable limits
- Rich console output with progress tracking and status indicators
- Centralized configuration management with environment variable support
- Type-safe data models with automatic validation
- Modular architecture with clear separation of concerns