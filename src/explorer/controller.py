"""Explorer Controller for the Interactive Identity Center Explorer.

This module orchestrates the entire exploration experience from initialization
to termination.
"""

import sys
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .data_loader import DataLoader
from .navigation import NavigationEngine, NavigationState
from .display import DisplayManager
from .models import ExplorerData


class ExplorerController:
    """Main orchestrator for the Interactive Identity Center Explorer."""
    
    def __init__(self, json_dir: str):
        """
        Initialize the explorer with the JSON data directory.
        
        Args:
            json_dir: Path to directory containing JSON files
        """
        self.json_dir = json_dir
        self.console = Console()
        self.display_manager: Optional[DisplayManager] = None
        self.navigation_engine: Optional[NavigationEngine] = None
        self.data: Optional[ExplorerData] = None
        self.is_first_iteration = True
    
    def start(self) -> None:
        """
        Start the interactive exploration session.
        
        This method initializes all components and starts the exploration loop.
        """
        try:
            # Validate JSON directory exists
            json_path = Path(self.json_dir)
            if not json_path.exists():
                self.console.print(
                    f"[red]❌ Error: JSON directory not found: {self.json_dir}[/red]"
                )
                self.console.print(
                    "\n[yellow]Please ensure you have run 'reverse_diagrams -o' to generate "
                    "organization data first.[/yellow]"
                )
                sys.exit(1)
            
            # Load data with progress indicator
            self.console.print("[cyan]Loading AWS Organizations data...[/cyan]\n")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Loading JSON files...", total=None)
                
                try:
                    data_loader = DataLoader(self.json_dir)
                    self.data = data_loader.load_all_data()
                    progress.update(task, description="✓ Data loaded successfully")
                except FileNotFoundError as e:
                    progress.stop()
                    self.console.print(f"\n[red]❌ Error: {e}[/red]")
                    self.console.print(
                        "\n[yellow]Please ensure you have run 'reverse_diagrams -o -i' to generate "
                        "all required data files.[/yellow]"
                    )
                    sys.exit(1)
                except Exception as e:
                    progress.stop()
                    self.console.print(f"\n[red]❌ Error loading data: {e}[/red]")
                    sys.exit(1)
            
            # Display validation warnings if any
            if self.data.validation_warnings:
                self.console.print("\n[yellow]⚠️  Data Validation Warnings:[/yellow]")
                for warning in self.data.validation_warnings[:5]:  # Show first 5
                    self.console.print(f"  [dim]• {warning}[/dim]")
                if len(self.data.validation_warnings) > 5:
                    remaining = len(self.data.validation_warnings) - 5
                    self.console.print(f"  [dim]... and {remaining} more warnings[/dim]")
                self.console.print()
            
            # Initialize components
            self.display_manager = DisplayManager(self.console)
            self.navigation_engine = NavigationEngine(self.data)
            
            # Start exploration loop
            self.run_exploration_loop()
            
        except KeyboardInterrupt:
            self.shutdown()
        except Exception as e:
            self.console.print(f"\n[red]❌ Unexpected error: {e}[/red]")
            sys.exit(1)
    
    def run_exploration_loop(self) -> None:
        """
        Main loop handling navigation and display.
        
        This loop continues until the user chooses to exit.
        """
        try:
            while True:
                # Show welcome screen on first iteration
                if self.is_first_iteration:
                    self.display_manager.show_welcome_screen()
                    self.is_first_iteration = False
                
                # Get current view from navigation engine
                current_view = self.navigation_engine.get_current_view()
                
                # Check if user wants to exit
                if self.navigation_engine.current_state == NavigationState.EXIT:
                    self.shutdown()
                    break
                
                # Display breadcrumb
                self.display_manager.display_breadcrumb(current_view.breadcrumb)
                
                # Handle account detail view specially
                if current_view.is_account_detail():
                    # Get account and display details
                    account = self.data.organization.get_account_by_id(
                        self.navigation_engine.current_item_id
                    )
                    if account:
                        assignments = self.data.get_assignments_for_account(account.id)
                        self.display_manager.display_account_details(
                            account,
                            assignments,
                            self.data.groups_by_id
                        )
                    
                    # Show navigation options
                    self.console.print()
                
                # Prompt for selection
                selected_id = self.display_manager.prompt_selection(
                    current_view.items,
                    prompt="Select an option"
                )
                
                # Handle selection
                if selected_id == "exit":
                    self.shutdown()
                    break
                
                self.navigation_engine.handle_selection(selected_id)
                
                # Clear screen for next iteration (optional)
                self.console.print("\n" * 2)
                
        except KeyboardInterrupt:
            self.shutdown()
        except Exception as e:
            self.console.print(f"\n[red]❌ Error during exploration: {e}[/red]")
            self.shutdown()
    
    def shutdown(self) -> None:
        """
        Clean up resources and exit gracefully.
        """
        self.console.print("\n[cyan]👋 Thank you for using AWS Organizations Explorer![/cyan]\n")
        sys.exit(0)
