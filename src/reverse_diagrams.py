"""Create graphs."""
import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

import argcomplete
from colorama import Fore

from .aws.describe_identity_store import graph_identity_center
from .aws.describe_organization import graph_organizations
from .aws.exceptions import AWSError, AWSCredentialsError, AWSPermissionError
from .banner.banner import get_version
from .config import get_config, Config
from .reports.console_view import watch_on_demand
from .reports.html_report import (
    generate_report_from_files,
    HTMLGenerationError,
    JSONFileNotFoundError,
    JSONParseError,
    InvalidOutputPathError,
    HTMLWriteError
)
from .version import __version__
from .utils.progress import get_progress_tracker


def validate_arguments(args) -> None:
    """
    Validate command line arguments.
    
    Args:
        args: Parsed command line arguments
        
    Raises:
        ValueError: If arguments are invalid
    """
    # Validate region format
    if args.region and not args.region.replace('-', '').replace('_', '').isalnum():
        raise ValueError(f"Invalid AWS region format: {args.region}")
    
    # Validate output directory path
    if args.output_dir_path:
        try:
            Path(args.output_dir_path).resolve()
        except Exception as e:
            raise ValueError(f"Invalid output directory path: {e}")
    
    # Validate HTML output flag usage
    if hasattr(args, 'html_output') and args.html_output and not args.html_report:
        raise ValueError("--html-output flag requires --html-report flag to be specified")
    
    # Ensure at least one operation is selected
    if not any([args.graph_organization, args.graph_identity, args.commands == "watch", 
                args.list_plugins, args.plugins, args.html_report]):
        if not args.version:
            raise ValueError("Please specify at least one operation: -o, -i, --html-report, or watch command")
    
    # Validate explore mode arguments
    if hasattr(args, 'explore') and args.explore:
        # Validate JSON directory exists if specified
        if hasattr(args, 'json_dir'):
            json_path = Path(args.json_dir)
            if not json_path.exists():
                raise ValueError(f"JSON directory not found: {args.json_dir}")
        
        # Explore mode doesn't require other watch flags
        return


def setup_logging_from_args(args, config: Config) -> None:
    """Setup logging based on command line arguments and configuration."""
    if args.debug:
        config.logging.level = "DEBUG"
        config.setup_logging()
        logging.info("Debug mode enabled")
    else:
        config.setup_logging()


def handle_aws_errors(func):
    """Decorator to handle AWS-specific errors gracefully."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AWSCredentialsError as e:
            logging.error(f"{Fore.RED}❌ AWS Credentials Error: {e}{Fore.RESET}")
            logging.error(f"{Fore.YELLOW}💡 Please check your AWS credentials and try again.{Fore.RESET}")
            sys.exit(1)
        except AWSPermissionError as e:
            logging.error(f"{Fore.RED}❌ AWS Permission Error: {e}{Fore.RESET}")
            logging.error(f"{Fore.YELLOW}💡 Please check your AWS permissions and try again.{Fore.RESET}")
            sys.exit(1)
        except AWSError as e:
            logging.error(f"{Fore.RED}❌ AWS Error: {e}{Fore.RESET}")
            sys.exit(1)
        except Exception as e:
            logging.error(f"{Fore.RED}❌ Unexpected error: {e}{Fore.RESET}")
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                logging.exception("Full traceback:")
            sys.exit(1)
    return wrapper


def generate_html_report_cli(
    html_output: Optional[str] = None,
    json_dir: str = "diagrams/json"
) -> None:
    """
    Orchestrate HTML report generation from CLI.
    
    Args:
        html_output: Custom output path for HTML report
        json_dir: Directory containing JSON data files
        
    Raises:
        JSONFileNotFoundError: If no JSON data files exist
        InvalidOutputPathError: If output directory is not writable
        JSONParseError: If JSON files are malformed
        HTMLWriteError: If HTML file cannot be written
    """
    progress = get_progress_tracker()
    
    # Determine output path
    output_path = html_output or "diagrams/reports/aws_report.html"
    
    # Check for JSON data files
    json_path = Path(json_dir)
    org_file = json_path / "organizations.json"
    groups_file = json_path / "groups.json"
    assignments_file = json_path / "account_assignments.json"
    
    # Determine which files exist
    available_files = []
    org_file_path = str(org_file) if org_file.exists() else None
    groups_file_path = str(groups_file) if groups_file.exists() else None
    assignments_file_path = str(assignments_file) if assignments_file.exists() else None
    
    if org_file_path:
        available_files.append("organizations.json")
    if groups_file_path:
        available_files.append("groups.json")
    if assignments_file_path:
        available_files.append("account_assignments.json")
    
    if not available_files:
        progress.show_error(
            "No JSON data files found",
            f"Please run with -o or -i flags to generate data first.\n"
            f"Expected files in: {json_path}"
        )
        raise JSONFileNotFoundError(
            f"No JSON data files found in {json_dir}. "
            f"Please run with -o or -i flags to generate data first."
        )
    
    # Generate HTML report with progress tracking
    try:
        progress.show_success(
            "Generating HTML report",
            f"Processing {len(available_files)} data file(s): {', '.join(available_files)}"
        )
        
        html_path = generate_report_from_files(
            organizations_file=org_file_path,
            groups_file=groups_file_path,
            assignments_file=assignments_file_path,
            output_path=output_path
        )
        
        # Count sections included
        sections = []
        if org_file_path:
            sections.append("AWS Organizations")
        if groups_file_path:
            sections.append("IAM Identity Center Groups")
        if assignments_file_path:
            sections.append("Account Assignments")
        
        progress.show_success(
            "HTML report generated successfully",
            f"📄 Output: {html_path}\n"
            f"📊 Sections: {len(sections)} ({', '.join(sections)})\n"
            f"📁 Processed: {', '.join(available_files)}"
        )
        
    except JSONFileNotFoundError as e:
        progress.show_error("JSON file not found", str(e))
        raise
    except JSONParseError as e:
        progress.show_error("Invalid JSON data", str(e))
        raise
    except InvalidOutputPathError as e:
        progress.show_error("Invalid output path", str(e))
        raise
    except HTMLWriteError as e:
        progress.show_error("Failed to write HTML file", str(e))
        raise
    except Exception as e:
        progress.show_error("HTML generation failed", str(e))
        raise


@handle_aws_errors


def main() -> int:
    """
    Create architecture diagram from your current state.

    :return: Exit code
    """
    # Load configuration
    config = get_config()
    
    # Initialize parser
    parser = argparse.ArgumentParser(
        prog="reverse_diagrams",
        description="Create architecture diagram, inspect and audit your AWS services from your current state.",
        epilog="Thanks for using %(prog)s!",
    )

    parser.add_argument(
        "-p", "--profile", help="AWS cli profile for AWS Apis", default=None
    )
    parser.add_argument(
        "-od",
        "--output_dir_path",
        help="Name of folder to save the diagrams python code files",
        default=config.output.default_output_dir,
    )
    parser.add_argument("-r", "--region", help="AWS region", default="us-east-1")
    parser.add_argument(
        "-o",
        "--graph_organization",
        help="Set if you want to create graph for your organization",
        action="store_true",
    )
    parser.add_argument(
        "-i",
        "--graph_identity",
        help="Set if you want to create graph for your IAM Center",
        action="store_true",
    )
    parser.add_argument(
        "-a",
        "--auto_create",
        help="Create Automatically diagrams",
        action="store_true",
        default=True,
    )
    parser.add_argument(
        "--plugin",
        help="Use specific plugin for diagram generation (e.g., ec2, rds)",
        action="append",
        dest="plugins"
    )
    parser.add_argument(
        "--list-plugins",
        help="List available plugins",
        action="store_true"
    )
    parser.add_argument(
        "--concurrent",
        help="Enable concurrent processing for better performance",
        action="store_true",
        default=True
    )
    parser.add_argument(
        "--html-report",
        help="Generate HTML report from JSON data files (works offline, no AWS credentials needed)",
        action="store_true"
    )
    parser.add_argument(
        "--html-output",
        type=str,
        metavar="PATH",
        help="Custom output path for HTML report (default: diagrams/reports/aws_report.html). "
             "Example: --html-output reports/my_report.html"
    )
    
    # Create subparsers
    subparsers = parser.add_subparsers(
        dest="commands",
        title="Commands",
        help="%(prog)s Commands",
        description="Command and functionalities",
    )
    
    # Create watch subcommand options
    watch_parser = subparsers.add_parser(
        name="watch",
        description="Create view of diagrams in console based on kind of diagram and json file.",
        help="Create pretty console view: \n"
        "For example: %(prog)s watch -wi diagrams/json/account_assignments.json ",
    )
    
    # Add watch options
    watch_group = watch_parser.add_argument_group(
        "Create view of diagrams in console based on kind of diagram and json file."
    )
    watch_group.add_argument(
        "-wo",
        "--watch_graph_organization",
        help="Set if you want to see graph for your organization structure summary.\n"
        "For example: %(prog)s watch  -wo diagrams/json/organizations.json",
    )
    watch_group.add_argument(
        "-wi",
        "--watch_graph_identity",
        help="Set if you want to see graph for your groups and users. \n"
        "For example: %(prog)s watch  -wi diagrams/json/groups.json",
    )
    watch_group.add_argument(
        "-wa",
        "--watch_graph_accounts_assignments",
        help="Set if you want to see graph for your IAM Center- Accounts assignments. \n"
        "For example: %(prog)s watch  -wa diagrams/json/account_assignments.json",
    )
    watch_group.add_argument(
        "--generate-html",
        action="store_true",
        help="Generate HTML report from the specified JSON file instead of console view. "
             "Example: reverse_diagrams watch -wi groups.json --generate-html"
    )
    watch_group.add_argument(
        "-e",
        "--explore",
        action="store_true",
        help="Launch interactive explorer for AWS Organizations and IAM Identity Center. "
             "Navigate through OUs, accounts, and permission assignments interactively. "
             "Example: reverse_diagrams watch --explore"
    )
    watch_group.add_argument(
        "--json-dir",
        default="diagrams/json",
        help="Directory containing JSON files for explorer mode (default: diagrams/json). "
             "Example: reverse_diagrams watch --explore --json-dir /path/to/json"
    )

    parser.add_argument("-v", "--version", help="Show version", action="store_true")
    parser.add_argument("-d", "--debug", help="Debug Mode", action="store_true")

    # Add autocomplete
    argcomplete.autocomplete(parser)
    
    # Read arguments from command line
    args = parser.parse_args()
    
    try:
        # Validate arguments
        validate_arguments(args)
        
        # Setup logging
        setup_logging_from_args(args, config)
        
        logging.debug(f"Starting reverse_diagrams with arguments: {vars(args)}")
        
        # Handle list plugins request
        if args.list_plugins:
            from .plugins.registry import get_plugin_manager
            manager = get_plugin_manager()
            plugins = manager.list_available_plugins()
            
            progress = get_progress_tracker()
            if plugins:
                progress.show_summary(
                    "Available Plugins",
                    [f"{p.name} v{p.version} - {p.description}" for p in plugins]
                )
            else:
                progress.show_warning("No plugins available", "Install plugins or check plugin directories")
            return 0
        
        # Handle plugin-based diagram generation
        if args.plugins:
            from .plugins.registry import get_plugin_manager
            from .models import DiagramConfig
            from .aws.client_manager import get_client_manager
            
            manager = get_plugin_manager()
            client_manager = get_client_manager(region=args.region, profile=args.profile)
            progress = get_progress_tracker()
            
            # Create output directories
            output_path = Path(args.output_dir_path)
            output_path.mkdir(parents=True, exist_ok=True)
            (output_path / "json").mkdir(exist_ok=True)
            (output_path / "code").mkdir(exist_ok=True)
            
            for plugin_name in args.plugins:
                try:
                    plugin = manager.load_plugin(plugin_name, client_manager)
                    
                    # Collect data
                    progress.show_success(f"🔌 Running {plugin_name} plugin")
                    data = plugin.collect_data(client_manager, args.region)
                    
                    # Generate diagram
                    diagram_config = DiagramConfig(
                        title=f"{plugin_name.upper()} Infrastructure",
                        direction="TB",
                        output_format="png"
                    )
                    
                    diagram_code = plugin.generate_diagram_code(data, diagram_config)
                    
                    # Save diagram code
                    plugin_file = output_path / "code" / f"graph_{plugin_name}.py"
                    plugin_file.write_text(diagram_code)
                    
                    # Save data
                    data_file = output_path / "json" / f"{plugin_name}_data.json"
                    import json
                    data_file.write_text(json.dumps(data, indent=2, default=str))
                    
                    if args.auto_create:
                        import os
                        command = os.system(f"cd {output_path / 'code'} && python3 graph_{plugin_name}.py")
                        if command == 0:
                            progress.show_success(f"✅ {plugin_name} diagram created successfully")
                        else:
                            progress.show_error(f"Failed to create {plugin_name} diagram", f"Exit code: {command}")
                    
                except Exception as e:
                    progress.show_error(f"Plugin {plugin_name} failed", str(e))
                    if not args.debug:
                        continue
                    raise
            
            return 0
        
        # Handle version request
        if args.version:
            get_version(version=__version__)
            return 0
        
        # Handle watch command
        if args.commands == "watch":
            # Check if explorer mode is requested
            if hasattr(args, 'explore') and args.explore:
                from .explorer.controller import ExplorerController
                
                # Get JSON directory from args or use default
                json_dir = getattr(args, 'json_dir', 'diagrams/json')
                
                logging.info(f"Starting Interactive Identity Center Explorer with JSON directory: {json_dir}")
                
                # Create and start the explorer controller
                controller = ExplorerController(json_dir)
                controller.start()
                return 0
            else:
                # Normal watch mode (console view)
                watch_on_demand(args=args)
                return 0
        
        # Handle HTML report generation (standalone or combined)
        should_generate_html = args.html_report
        should_generate_diagrams = args.graph_organization or args.graph_identity
        
        # If only HTML report is requested (no diagrams)
        if should_generate_html and not should_generate_diagrams:
            logging.info("Generating HTML report from existing JSON data")
            try:
                generate_html_report_cli(
                    html_output=args.html_output,
                    json_dir=f"{args.output_dir_path}/json"
                )
                return 0
            except (JSONFileNotFoundError, JSONParseError, InvalidOutputPathError, HTMLWriteError) as e:
                logging.error(f"{Fore.RED}❌ HTML generation failed: {e}{Fore.RESET}")
                return 1
            except Exception as e:
                logging.error(f"{Fore.RED}❌ Unexpected error during HTML generation: {e}{Fore.RESET}")
                if logging.getLogger().isEnabledFor(logging.DEBUG):
                    logging.exception("Full traceback:")
                return 1
        
        # Setup AWS client manager
        from .aws.client_manager import get_client_manager
        client_manager = get_client_manager(region=args.region, profile=args.profile)
        
        diagrams_path = args.output_dir_path
        region = args.region
        
        # Create output directories
        output_path = Path(diagrams_path)
        output_path.mkdir(parents=True, exist_ok=True)
        (output_path / "json").mkdir(exist_ok=True)
        (output_path / "code").mkdir(exist_ok=True)
        
        logging.info(f"Output directory: {output_path.absolute()}")
        
        # Execute requested operations using plugins
        if args.graph_organization:
            logging.info("Starting AWS Organizations diagram generation using plugin")
            progress = get_progress_tracker()
            try:
                from .plugins.registry import get_plugin_manager
                from .models import DiagramConfig
                
                manager = get_plugin_manager()
                plugin = manager.load_plugin("organizations", client_manager)
                
                # Collect data
                progress.show_success("🏢 Running Organizations plugin")
                data = plugin.collect_data(client_manager, args.region)
                
                # Generate diagram
                diagram_config = DiagramConfig(
                    title="Organizations Structure",
                    direction="TB",
                    output_format="png"
                )
                
                diagram_code = plugin.generate_diagram_code(data, diagram_config)
                
                # Save diagram code
                org_file = output_path / "code" / "graph_org.py"
                org_file.write_text(diagram_code)
                
                # Save data
                from .reports.save_results import save_results
                save_results(data["accounts"], "organizations.json", str(output_path / "json"))
                save_results(data["organizations_complete"], "organizations_complete.json", str(output_path / "json"))
                
                if args.auto_create:
                    import os
                    command = os.system(f"cd {output_path / 'code'} && python3 graph_org.py")
                    if command == 0:
                        progress.show_success("✅ Organizations diagram created successfully")
                    else:
                        progress.show_error("Failed to create Organizations diagram", f"Exit code: {command}")
                
                logging.info("AWS Organizations diagram generation completed")
                
            except Exception as e:
                logging.error(f"Organizations plugin failed: {e}")
                # Fallback to original implementation with same client manager
                logging.info("Falling back to original Organizations implementation")
                # Pass the region and profile to ensure credentials are used
                import os
                os.environ['AWS_PROFILE'] = args.profile if args.profile else ''
                graph_organizations(
                    diagrams_path=diagrams_path, region=region, auto=args.auto_create
                )

        if args.graph_identity:
            logging.info("Starting IAM Identity Center diagram generation using plugin")
            progress = get_progress_tracker()
            try:
                from .plugins.registry import get_plugin_manager
                from .models import DiagramConfig
                
                manager = get_plugin_manager()
                plugin = manager.load_plugin("identity-center", client_manager)
                
                # Collect data
                progress.show_success("🔐 Running Identity Center plugin")
                data = plugin.collect_data(client_manager, args.region)
                
                # Generate diagram
                diagram_config = DiagramConfig(
                    title="IAM Identity Center",
                    direction="LR",
                    output_format="png"
                )
                
                diagram_code = plugin.generate_diagram_code(data, diagram_config)
                
                # Save diagram code
                sso_file = output_path / "code" / "graph_sso_complete.py"
                sso_file.write_text(diagram_code)
                
                # Save data
                from .reports.save_results import save_results
                save_results(data["final_account_assignments"], "account_assignments.json", str(output_path / "json"))
                save_results(data["group_memberships"], "groups.json", str(output_path / "json"))
                
                if args.auto_create:
                    import os
                    command = os.system(f"cd {output_path / 'code'} && python3 graph_sso_complete.py")
                    if command == 0:
                        progress.show_success("✅ Identity Center diagram created successfully")
                    else:
                        progress.show_error("Failed to create Identity Center diagram", f"Exit code: {command}")
                
                logging.info("IAM Identity Center diagram generation completed")
                
            except Exception as e:
                logging.error(f"Identity Center plugin failed: {e}")
                # Fallback to original implementation with same client manager
                logging.info("Falling back to original Identity Center implementation")
                # Pass the region and profile to ensure credentials are used
                import os
                os.environ['AWS_PROFILE'] = args.profile if args.profile else ''
                graph_identity_center(
                    diagrams_path=diagrams_path, region=region, auto=args.auto_create
                )
        
        # Generate HTML report if requested (combined with diagrams)
        if should_generate_html and should_generate_diagrams:
            logging.info("Generating HTML report from diagram data")
            try:
                generate_html_report_cli(
                    html_output=args.html_output,
                    json_dir=f"{args.output_dir_path}/json"
                )
            except (JSONFileNotFoundError, JSONParseError, InvalidOutputPathError, HTMLWriteError) as e:
                logging.error(f"{Fore.RED}❌ HTML generation failed: {e}{Fore.RESET}")
                logging.error(f"{Fore.YELLOW}💡 Diagrams were generated successfully, but HTML report failed.{Fore.RESET}")
                return 1
            except Exception as e:
                logging.error(f"{Fore.RED}❌ Unexpected error during HTML generation: {e}{Fore.RESET}")
                if logging.getLogger().isEnabledFor(logging.DEBUG):
                    logging.exception("Full traceback:")
                return 1
        
        logging.info("All operations completed successfully")
        return 0
        
    except ValueError as e:
        logging.error(f"{Fore.RED}❌ Invalid arguments: {e}{Fore.RESET}")
        parser.print_help()
        return 1
    except KeyboardInterrupt:
        logging.info(f"{Fore.YELLOW}⚠️  Operation cancelled by user{Fore.RESET}")
        return 1
    except Exception as e:
        logging.error(f"{Fore.RED}❌ Unexpected error: {e}{Fore.RESET}")
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logging.exception("Full traceback:")
        return 1


if __name__ == "__main__":
    main()
