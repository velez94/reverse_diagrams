<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  

- [Reverse Diagrams](#reverse-diagrams)
- [Requirement](#requirement)
- [Install](#install)
- [Use](#use)
  - [Subcommands](#subcommands)
    - [watch](#watch)
- [Service supported](#service-supported)
  - [Built-in Services](#built-in-services)
    - [AWS Organizations](#aws-organizations)
    - [Identity and Access Manager Center (SSO)](#identity-and-access-manager-center-sso)
    - [EC2 Infrastructure (Plugin)](#ec2-infrastructure-plugin)
  - [Plugin Architecture](#plugin-architecture)
    - [Using Plugins](#using-plugins)
    - [Creating Custom Plugins](#creating-custom-plugins)
- [Additional Commands](#additional-commands)
  - [watch](#watch-1)
    - [Options](#options)
    - [Combine the options](#combine-the-options)
  - [Tag-Based Filtering (Coming Soon)](#tag-based-filtering-coming-soon)
  - [Troubleshooting](#troubleshooting)
    - [IAM Identity Center Not Enabled](#iam-identity-center-not-enabled)
    - [AWS Credentials Not Found](#aws-credentials-not-found)
    - [Plugin Not Loading](#plugin-not-loading)
    - [Permission Denied Errors](#permission-denied-errors)
    - [Performance Issues with Large Organizations](#performance-issues-with-large-organizations)
  - [Extras](#extras)
    - [Enable autocomplete](#enable-autocomplete)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Reverse Diagrams

> Continuous Documentation Tool - Documentation as Code Tool

This package creates diagrams and helps audit your AWS services from your shell using a modern plugin architecture.

![Complete demo](docs/images/complete_demo.gif)

## What's New in v1.3.5

### 🔌 Plugin Architecture
Extensible system for adding new AWS services with minimal code. Built-in plugins for Organizations, Identity Center, and EC2.

**Benefits:**
- Easy to add new AWS services
- Consistent interface across all services
- Automatic plugin discovery
- Backward compatible with existing commands

### 🏗️ Enhanced Error Handling
Comprehensive error messages with actionable suggestions and graceful fallbacks.

**Features:**
- Clear error messages for common issues
- Automatic retry with exponential backoff
- Graceful degradation when services unavailable
- Detailed logging for troubleshooting

### ⚡ Performance Improvements
Concurrent processing and intelligent caching for faster diagram generation.

**Optimizations:**
- Multi-threaded AWS API calls with `--concurrent` flag
- TTL-based caching for API responses
- Connection pooling and reuse
- Configurable pagination limits

### 📊 Progress Tracking
Rich console output with progress bars, spinners, and status indicators.

**Features:**
- Real-time progress bars for long operations
- Color-coded status messages
- Operation-specific tracking
- Clear success/error feedback

### 🎯 Coming Soon: Tag-Based Filtering
Filter AWS resources by tags when generating diagrams (specification complete, implementation in progress).

**Planned capabilities:**
- Service-specific filtering: `--service-tag ec2 Environment=Production`
- Account-wide filtering: `--tag Environment=Production`
- Multiple tags with AND/OR logic
- Exclude filters and preset management

See [Tag-Based Filtering](#tag-based-filtering-coming-soon) section for details.

# Requirement

AWS programmatic access using AWS CLI.  [Configuring the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)


# Install 

`pip install reverse-diagrams`

# Use

The following are the available options

```commandline
$ reverse_diagrams  -h
usage: reverse_diagrams [-h] [-p PROFILE] [-od OUTPUT_DIR_PATH] [-r REGION] [-o] [-i] [-a] [--plugin PLUGINS]
                        [--list-plugins] [--concurrent] [-v] [-d]
                        {watch} ...

Create architecture diagram, inspect and audit your AWS services from your current state.

options:
  -h, --help            show this help message and exit
  -p PROFILE, --profile PROFILE
                        AWS cli profile for AWS Apis
  -od OUTPUT_DIR_PATH, --output_dir_path OUTPUT_DIR_PATH
                        Name of folder to save the diagrams python code files
  -r REGION, --region REGION
                        AWS region
  -o, --graph_organization
                        Set if you want to create graph for your organization
  -i, --graph_identity  Set if you want to create graph for your IAM Center
  -a, --auto_create     Create Automatically diagrams
  --plugin PLUGINS      Use specific plugin for diagram generation (e.g., ec2, rds)
  --list-plugins        List available plugins
  --concurrent          Enable concurrent processing for better performance
  -v, --version         Show version
  -d, --debug           Debug Mode

Commands:
  Command and functionalities

  {watch}               reverse_diagrams Commands
    watch               Create pretty console view
                        For example: reverse_diagrams watch -wi diagrams/json/account_assignments.json

Thanks for using reverse_diagrams!

```
For example: 

```commandline
reverse_diagrams -p labvel-master -o -i -r us-east-1

❇️ Describe Organization 
❇️ Getting Organization Info
❇️ Listing Organizational Units 
❇️ Getting the Account list info
ℹ️  There are 11 Accounts in your organization
ℹ️  The accounts are stored in diagrams/json/organizations.json 
❇️ Creating diagrams in diagrams/code
❇️ Getting Identity store instance info
❇️ List groups
ℹ️  There are 10 Groups in your Identity Store
❇️ Get groups and Users info
Getting groups members... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:07
Getting account assignments ... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:05:23
Create user and groups assignments ... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00
❇️ Getting account assignments, users and groups
ℹ️  The accounts are stored in diagrams/json/account_assignments.json
ℹ️  The accounts are stored in diagrams/json/groups.json
❇️ Creating diagrams in diagrams/code

```

**Using concurrent processing for better performance:**

```commandline
reverse_diagrams -p labvel-master -o -i --concurrent -r us-east-1
```

**Using specific plugins:**

```commandline
# List available plugins
reverse_diagrams --list-plugins

# Use EC2 plugin
reverse_diagrams --plugin ec2 -p labvel-master -r us-east-1

# Use Organizations plugin explicitly
reverse_diagrams --plugin organizations -p labvel-master -r us-east-1
```

Then run `python3 graph_org.py` to create a png screenshot (`organizations-state.png`) for your current state.

> Both files are saved into the current directory.

```commandline
$  reverse_diagrams -p labvel-master -o -r us-east-2
Date: 2022-12-17 22:44:07.623260
❇️ Getting Organization Info
❇️ The Organizational Units list 
❇️ Getting the Account list info
Run -> python3 graph_org.py 


$ python3 graph_org.py 
$ ls 
graph_org.py
organizations-state.png
```
For example:

![Organizations Diagram](./docs/images/organizations-state-copy.png)

Now you can edit `graph_org.py` file or add to your repositories for keeping the documentation update.

## Output Files

The tool generates several types of output files organized in the `diagrams/` directory:

### Directory Structure
```
diagrams/
├── json/                       # Raw AWS data exports
│   ├── organizations.json      # Organization structure
│   ├── organizations_complete.json
│   ├── groups.json            # Identity Center groups
│   ├── account_assignments.json
│   └── *_data.json            # Plugin-generated data
├── code/                       # Generated Python diagram code
│   ├── graph_org.py           # Organizations diagram script
│   ├── graph_sso.py           # SSO diagram script
│   └── graph_*.py             # Plugin-generated scripts
└── images/                     # Generated diagram images
    └── *.png                  # Diagram output files
```

### JSON Files
JSON files contain the raw AWS data collected from your account. These files can be:
- Used with the `watch` command for console viewing
- Imported into other tools for analysis
- Version controlled to track infrastructure changes over time
- Shared with team members for documentation

### Python Diagram Code
Generated Python files use the [diagrams](https://diagrams.mingrammer.com/) library to create visual representations. You can:
- Edit the code to customize diagram appearance
- Add additional resources manually
- Integrate into CI/CD pipelines
- Version control alongside your infrastructure code

### Running Generated Diagrams
```commandline
# Navigate to the code directory
cd diagrams/code

# Run the generated script
python3 graph_org.py

# View the generated PNG
ls -la *.png
```

## Subcommands

### watch

Watch the result in console with a beautiful print style.
```commandline
 reverse_diagrams  watch  -h
usage: reverse_diagrams watch [-h] [-wo WATCH_GRAPH_ORGANIZATION] [-wi WATCH_GRAPH_IDENTITY] [-wa WATCH_GRAPH_ACCOUNTS_ASSIGNMENTS]

Create view of diagrams in console based on kind of diagram and json file.

options:
  -h, --help            show this help message and exit

Create view of diagrams in console based on kind of diagram and json file.:
  -wo WATCH_GRAPH_ORGANIZATION, --watch_graph_organization WATCH_GRAPH_ORGANIZATION
                        Set if you want to see graph for your organization structure summary. For example: reverse_diagrams watch watch -wi diagrams/json/organizations.json        
  -wi WATCH_GRAPH_IDENTITY, --watch_graph_identity WATCH_GRAPH_IDENTITY
                        Set if you want to see graph for your groups and users. For example: reverse_diagrams watch watch -wi diagrams/json/groups.json
  -wa WATCH_GRAPH_ACCOUNTS_ASSIGNMENTS, --watch_graph_accounts_assignments WATCH_GRAPH_ACCOUNTS_ASSIGNMENTS
                        Set if you want to see graph for your IAM Center- Accounts assignments. For example: reverse_diagrams watch watch -wi
                        diagrams/json/account_assignments.json.jso
```

# Service supported

The tool uses a modern plugin architecture that makes it easy to extend with new AWS services.

## Built-in Services

### AWS Organizations

Generate diagrams of your AWS Organizations structure including organizational units, accounts, and hierarchies.

```commandline
reverse_diagrams -p my-profile -o -r us-east-2
```

**Features:**
- Visualize organizational unit hierarchies
- Map account relationships
- Show complete organization structure
- Export to JSON and PNG formats

### Identity and Access Manager Center (SSO)

Create diagrams for IAM Identity Center configurations including groups, users, and permission assignments.

```commandline
reverse_diagrams -p my-profile -i -r us-east-2
```

**Features:**
- Map groups and users
- Visualize permission sets
- Show account assignments
- Track group memberships

**Note:** Requires IAM Identity Center to be enabled in your AWS account. If not enabled, you'll receive a clear error message with instructions.

### EC2 Infrastructure (Plugin)

Generate diagrams for EC2 instances, VPCs, security groups, and related networking resources.

```commandline
reverse_diagrams --plugin ec2 -p my-profile -r us-east-2
```

**Features:**
- VPC and subnet visualization
- EC2 instance mapping
- Security group relationships
- Network topology

## Plugin Architecture

The tool supports extensible plugins for adding new AWS services. Each plugin can:
- Collect data from specific AWS services
- Generate custom diagram code
- Export data in JSON format
- Integrate with the concurrent processing system

### Using Plugins

**List available plugins:**
```commandline
reverse_diagrams --list-plugins
```

**Use a specific plugin:**
```commandline
reverse_diagrams --plugin ec2 -p my-profile -r us-east-2
```

**Enable concurrent processing for better performance:**
```commandline
reverse_diagrams -o -i --concurrent -p my-profile -r us-east-2
```

### Creating Custom Plugins

To create a custom plugin:

1. Extend the `AWSServicePlugin` base class
2. Implement required methods: `collect_data()` and `generate_diagram_code()`
3. Define plugin metadata (name, version, AWS services)
4. Place in `src/plugins/builtin/` or external plugin directory

Example plugin structure:
```python
from src.plugins.base import AWSServicePlugin, PluginMetadata

class MyServicePlugin(AWSServicePlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="myservice",
            version="1.0.0",
            description="My AWS service plugin",
            author="Your Name",
            aws_services=["myservice"]
        )
    
    def collect_data(self, client_manager, region, **kwargs):
        # Collect data from AWS
        pass
    
    def generate_diagram_code(self, data, config):
        # Generate diagram code
        pass
```
# Additional Commands

## watch
You can watch the configuration and summary in your shell based on json files generated previously.

### Options

```commandline
$ reverse_diagrams watch -h 
usage: reverse_diagrams watch [-h] [-wo WATCH_GRAPH_ORGANIZATION] [-wi WATCH_GRAPH_IDENTITY] [-wa WATCH_GRAPH_ACCOUNTS_ASSIGNMENTS]

Create view of diagrams in console based on kind of diagram and json file.

options:
  -h, --help            show this help message and exit

Create view of diagrams in console based on kind of diagram and json file.:
  -wo WATCH_GRAPH_ORGANIZATION, --watch_graph_organization WATCH_GRAPH_ORGANIZATION
                        Set if you want to see graph for your organization structure summary. For example: reverse_diagrams watch watch -wo diagrams/json/organizations.json
  -wi WATCH_GRAPH_IDENTITY, --watch_graph_identity WATCH_GRAPH_IDENTITY
                        Set if you want to see graph for your groups and users. For example: reverse_diagrams watch watch -wi diagrams/json/groups.json
  -wa WATCH_GRAPH_ACCOUNTS_ASSIGNMENTS, --watch_graph_accounts_assignments WATCH_GRAPH_ACCOUNTS_ASSIGNMENTS
                        Set if you want to see graph for your IAM Center- Accounts assignments. For example: reverse_diagrams watch watch -wa diagrams/json/account_assignments.json

```

For example, to watch account assignments: 

![view Acoount assigments](docs/images/show_console_view.gif)

### Combine the options

```commandline
reverse_diagrams  -p my-profile -o -i -r us-east-2
```

## Tag-Based Filtering (Coming Soon)

Filter AWS resources by tags when generating diagrams. This feature is currently in specification and will be available in a future release.

**Planned capabilities:**

**Service-specific filtering** - Filter only specific services:
```commandline
# Filter only EC2 instances by environment tag
reverse_diagrams --service-tag ec2 Environment=Production -p my-profile -r us-east-1
```

**Account-wide filtering** - Apply filters across all services:
```commandline
# Filter all services by environment tag
reverse_diagrams -o -i --tag Environment=Production -p my-profile -r us-east-1

# Multiple tags with AND logic
reverse_diagrams -o --tag Environment=Production --tag Team=DevOps -p my-profile

# Multiple tags with OR logic
reverse_diagrams -o --tag Environment=Production --tag Environment=Staging --tag-logic OR -p my-profile
```

**Exclude filters** - Exclude resources with specific tags:
```commandline
reverse_diagrams -o --tag Environment=Production --exclude-tag Status=Deprecated -p my-profile
```

**Filter presets** - Save and reuse common filter configurations:
```commandline
# Save a preset
reverse_diagrams --tag Environment=Production --save-preset prod-only

# Use a preset
reverse_diagrams -o -i --preset prod-only -p my-profile
```

For more details, see the specification in `.kiro/specs/tag-based-filtering/`.

## Troubleshooting

### IAM Identity Center Not Enabled

**Error:** "list index out of range" when using `-i` flag

**Cause:** Your AWS account doesn't have IAM Identity Center (formerly AWS SSO) enabled.

**Solution:**
1. Go to AWS Console
2. Navigate to IAM Identity Center
3. Enable the service
4. Run the command again: `reverse_diagrams -i -p my-profile -r us-east-1`

**Workaround:** Use only the `-o` flag for Organizations diagrams if you don't need Identity Center.

### AWS Credentials Not Found

**Error:** "No AWS credentials found"

**Cause:** AWS CLI is not configured or the specified profile doesn't exist.

**Solution:**
1. Configure AWS CLI: `aws configure --profile my-profile`
2. Or set environment variables:
   ```bash
   export AWS_ACCESS_KEY_ID=your_key
   export AWS_SECRET_ACCESS_KEY=your_secret
   export AWS_DEFAULT_REGION=us-east-1
   ```
3. Verify credentials: `aws sts get-caller-identity --profile my-profile`

### Plugin Not Loading

**Issue:** Plugins show as available but don't load when used

**Cause:** Import issues in installed package (fallback to original implementations works)

**Workaround:** The tool automatically falls back to the original implementations, which work perfectly. This doesn't affect functionality.

### Permission Denied Errors

**Error:** "Access Denied" when collecting AWS data

**Cause:** IAM user/role lacks required permissions.

**Solution:** Ensure your IAM user/role has these permissions:
- Organizations: `organizations:Describe*`, `organizations:List*`
- Identity Center: `sso:Describe*`, `sso:List*`, `identitystore:Describe*`, `identitystore:List*`
- EC2: `ec2:Describe*`

### Performance Issues with Large Organizations

**Issue:** Slow diagram generation for organizations with many accounts

**Solution:** Enable concurrent processing:
```commandline
reverse_diagrams -o -i --concurrent -p my-profile -r us-east-1
```

This uses multi-threading to speed up AWS API calls significantly.

## Extras

### Configuration

The tool supports configuration through environment variables for advanced use cases:

**AWS Configuration:**
```bash
export AWS_PROFILE=my-profile
export AWS_DEFAULT_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

**Tool Configuration:**
```bash
# Enable debug logging
export REVERSE_DIAGRAMS_DEBUG=true

# Set custom output directory
export REVERSE_DIAGRAMS_OUTPUT_DIR=my-diagrams

# Configure concurrent processing
export REVERSE_DIAGRAMS_CONCURRENT=true

# Set pagination limits
export REVERSE_DIAGRAMS_MAX_ITEMS=1000
```

**Logging:**
The tool uses Python's logging module. Set the log level:
```bash
export REVERSE_DIAGRAMS_LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

### Enable autocomplete
Argcomplete provides easy, extensible command line tab completion of arguments for your Python application.

It makes two assumptions:

* You’re using bash or zsh as your shell

* You’re using argparse to manage your command line arguments/options

Argcomplete is particularly useful if your program has lots of options or subparsers, and if your program can dynamically suggest completions for your argument/option values (for example, if the user is browsing resources over the network).
Run: 
```bash
activate-global-python-argcomplete
```
and to make sure that bash knows about this script, you use
```bash

echo 'eval "$(register-python-argcomplete reverse_diagrams)"' >> ~/.bashrc
source ~/.bashrc

```

## Contributing

Contributions are welcome! Here are some ways you can contribute:

### Report Issues
- Bug reports
- Feature requests
- Documentation improvements

### Create Plugins
Extend the tool with new AWS services by creating plugins. See [Creating Custom Plugins](#creating-custom-plugins) for details.

### Improve Core Features
- Performance optimizations
- Error handling improvements
- Test coverage
- Documentation

### Development Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/reverse-diagrams.git
cd reverse-diagrams

# Install in development mode
pip install -e .

# Run tests
pytest

# Run linting
black src/ tests/
flake8 src/ tests/
mypy src/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: See this README and the [docs/](docs/) directory
- **Issues**: Report bugs and request features via GitHub Issues
- **Discussions**: Join the conversation in GitHub Discussions

## Roadmap

### Current Version (v1.3.5)
- ✅ Plugin architecture
- ✅ Enhanced error handling
- ✅ Performance improvements
- ✅ Progress tracking

### Upcoming Features
- 🎯 Tag-based filtering (specification complete)
- 🔄 Additional AWS service plugins (RDS, Lambda, VPC, S3)
- 📊 Enhanced diagram customization
- 🔍 Resource search and filtering
- 📈 Historical tracking and diff visualization
- 🌐 Multi-region support
- 🔐 Enhanced security analysis

## Acknowledgments

- Built with [diagrams](https://diagrams.mingrammer.com/) library
- Uses [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) for AWS API interactions
- Console output powered by [rich](https://rich.readthedocs.io/)

---

**Made with ❤️ for AWS infrastructure documentation**
