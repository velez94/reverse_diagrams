"""Display manager for the Interactive Identity Center Explorer.

This module handles rendering the UI using the rich library with proper
formatting, colors, and icons.
"""

from typing import List, Dict, Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

from .models import (
    Account,
    Assignment,
    Group,
    OrganizationalUnit,
    PermissionSet,
    User,
)


class DisplayManager:
    """Manages display rendering using the rich library."""
    
    # Color scheme constants
    COLOR_OU = "blue"
    COLOR_ACCOUNT = "green"
    COLOR_PERMISSION_SET = "yellow"
    COLOR_GROUP = "cyan"
    COLOR_USER = "white"
    COLOR_ERROR = "red"
    COLOR_WARNING = "yellow"
    COLOR_SUCCESS = "green"
    
    # Icon constants
    ICON_OU = "📁"
    ICON_PERMISSION_SET = "🔑"
    ICON_GROUP = "👥"
    ICON_USER = "👤"
    ICON_ERROR = "❌"
    ICON_WARNING = "⚠️"
    ICON_SUCCESS = "✅"
    ICON_BACK = "⬅️"
    ICON_EXIT = "❌"
    
    def __init__(self, console: Optional[Console] = None):
        """
        Initialize the display manager.
        
        Args:
            console: Rich Console instance (creates new one if not provided)
        """
        self.console = console or Console()
        self.terminal_width = self.console.width
        self.pagination_threshold = 100  # Paginate lists with more than 100 items
    
    def get_terminal_width(self) -> int:
        """
        Get the current terminal width.
        
        Returns:
            int: Terminal width in characters
        """
        return self.console.width
    
    def should_paginate(self, item_count: int) -> bool:
        """
        Determine if a list should be paginated.
        
        Args:
            item_count: Number of items in the list
            
        Returns:
            bool: True if pagination should be used
        """
        return item_count > self.pagination_threshold
    
    def show_welcome_screen(self) -> None:
        """Display welcome message and keyboard shortcuts."""
        welcome_text = Text()
        welcome_text.append("AWS Organizations Explorer\n\n", style="bold cyan")
        welcome_text.append("Navigate through your AWS Organizations structure and IAM Identity Center access patterns.\n\n")
        welcome_text.append("Keyboard Shortcuts:\n", style="bold")
        welcome_text.append("  • ", style="dim")
        welcome_text.append("Arrow Keys", style="bold")
        welcome_text.append(" - Navigate through options\n", style="dim")
        welcome_text.append("  • ", style="dim")
        welcome_text.append("Enter", style="bold")
        welcome_text.append(" - Select an option\n", style="dim")
        welcome_text.append("  • ", style="dim")
        welcome_text.append("Escape", style="bold")
        welcome_text.append(" - Exit the explorer\n", style="dim")
        
        panel = Panel(welcome_text, border_style="cyan", padding=(1, 2))
        self.console.print(panel)
        self.console.print()
    
    def display_breadcrumb(self, breadcrumb: str) -> None:
        """
        Display navigation breadcrumb.
        
        Args:
            breadcrumb: The breadcrumb path string
        """
        breadcrumb_text = Text()
        breadcrumb_text.append("📍 ", style="bold")
        breadcrumb_text.append(breadcrumb, style="bold cyan")
        self.console.print(breadcrumb_text)
        self.console.print()
    
    def display_error(self, message: str) -> None:
        """
        Display error message with appropriate styling.
        
        Args:
            message: The error message to display
        """
        error_text = Text()
        error_text.append(f"{self.ICON_ERROR} ", style=f"bold {self.COLOR_ERROR}")
        error_text.append(message, style=self.COLOR_ERROR)
        self.console.print(error_text)
    
    def display_warning(self, message: str) -> None:
        """
        Display warning message with appropriate styling.
        
        Args:
            message: The warning message to display
        """
        warning_text = Text()
        warning_text.append(f"{self.ICON_WARNING} ", style=f"bold {self.COLOR_WARNING}")
        warning_text.append(message, style=self.COLOR_WARNING)
        self.console.print(warning_text)
    
    def display_success(self, message: str) -> None:
        """
        Display success message with appropriate styling.
        
        Args:
            message: The success message to display
        """
        success_text = Text()
        success_text.append(f"{self.ICON_SUCCESS} ", style=f"bold {self.COLOR_SUCCESS}")
        success_text.append(message, style=self.COLOR_SUCCESS)
        self.console.print(success_text)
    
    def display_empty_state(self, message: str) -> None:
        """
        Display message for empty OUs or accounts with no access.
        
        Args:
            message: The empty state message to display
        """
        empty_text = Text()
        empty_text.append("ℹ️  ", style="bold blue")
        empty_text.append(message, style="dim")
        self.console.print(empty_text)
    
    def prompt_selection(self, items: List, prompt: str = "Select an option") -> str:
        """
        Show interactive selection prompt using inquirer.
        
        Args:
            items: List of SelectableItem objects to choose from
            prompt: The prompt message to display
            
        Returns:
            str: The item_id of the selected item
        """
        import inquirer
        from inquirer.themes import GreenPassion
        
        # Build choices list with formatted display text
        choices = []
        for item in items:
            choices.append((item.display_text, item.item_id))
        
        # Create the selection question
        questions = [
            inquirer.List(
                'selection',
                message=prompt,
                choices=choices,
            )
        ]
        
        # Get user selection
        try:
            answers = inquirer.prompt(questions, theme=GreenPassion())
            if answers is None:
                # User pressed Ctrl+C or Escape
                return "exit"
            return answers['selection']
        except (KeyboardInterrupt, EOFError):
            # Handle Ctrl+C gracefully
            return "exit"
    
    def format_ou(self, ou: OrganizationalUnit) -> str:
        """
        Format an organizational unit for display.
        
        Args:
            ou: The organizational unit to format
            
        Returns:
            str: Formatted display text
        """
        return f"{self.ICON_OU} {ou.name}"
    
    def format_account(self, account: Account) -> str:
        """
        Format an account for display.
        
        Args:
            account: The account to format
            
        Returns:
            str: Formatted display text
        """
        return f"  {account.get_display_text()}"
    
    def format_permission_set(self, ps: PermissionSet) -> str:
        """
        Format a permission set for display.
        
        Args:
            ps: The permission set to format
            
        Returns:
            str: Formatted display text
        """
        return f"{self.ICON_PERMISSION_SET} {ps.name}"
    
    def format_group(self, group: Group) -> str:
        """
        Format a group for display.
        
        Args:
            group: The group to format
            
        Returns:
            str: Formatted display text
        """
        member_count = group.get_member_count()
        return f"{self.ICON_GROUP} {group.name} ({member_count} members)"
    
    def format_user(self, user: User) -> str:
        """
        Format a user for display.
        
        Args:
            user: The user to format
            
        Returns:
            str: Formatted display text
        """
        return f"{self.ICON_USER} {user.get_display_text()}"
    
    def display_account_details(
        self,
        account: Account,
        assignments: List[Assignment],
        groups: Dict[str, Group]
    ) -> None:
        """
        Display detailed view of account access patterns.
        
        Args:
            account: The account to display details for
            assignments: List of assignments for this account
            groups: Dictionary of group ID to Group objects
        """
        # Display account header
        self.console.print()
        header = Text()
        header.append(f"Account Details: ", style="bold")
        header.append(account.get_display_text(), style=f"bold {self.COLOR_ACCOUNT}")
        self.console.print(header)
        self.console.print()
        
        if not assignments:
            self.display_empty_state("No IAM Identity Center assignments for this account")
            return
        
        # Group assignments by permission set
        assignments_by_ps: Dict[str, List[Assignment]] = {}
        for assignment in assignments:
            ps_name = assignment.permission_set.name
            if ps_name not in assignments_by_ps:
                assignments_by_ps[ps_name] = []
            assignments_by_ps[ps_name].append(assignment)
        
        # Separate direct user assignments from group assignments
        direct_user_assignments: List[Assignment] = []
        group_assignments: List[Assignment] = []
        
        for assignment in assignments:
            if assignment.is_user_assignment():
                direct_user_assignments.append(assignment)
            else:
                group_assignments.append(assignment)
        
        # Display group-based assignments
        if group_assignments:
            self.console.print(Text("Group-Based Access:", style="bold underline"))
            self.console.print()
            
            # Group by permission set
            group_ps_map: Dict[str, List[Assignment]] = {}
            for assignment in group_assignments:
                ps_name = assignment.permission_set.name
                if ps_name not in group_ps_map:
                    group_ps_map[ps_name] = []
                group_ps_map[ps_name].append(assignment)
            
            for ps_name, ps_assignments in sorted(group_ps_map.items()):
                # Display permission set
                ps_text = Text()
                ps_text.append(f"  {self.ICON_PERMISSION_SET} ", style=self.COLOR_PERMISSION_SET)
                ps_text.append(ps_name, style=f"bold {self.COLOR_PERMISSION_SET}")
                self.console.print(ps_text)
                
                # Display groups for this permission set
                for assignment in ps_assignments:
                    group = groups.get(assignment.principal_id)
                    if group:
                        group_text = Text()
                        group_text.append(f"    {self.ICON_GROUP} ", style=self.COLOR_GROUP)
                        group_text.append(f"{group.name} ({group.get_member_count()} members)", 
                                        style=self.COLOR_GROUP)
                        self.console.print(group_text)
                        
                        # Display users in the group
                        for user in group.members:
                            user_text = Text()
                            user_text.append(f"      {self.ICON_USER} ", style=self.COLOR_USER)
                            user_text.append(user.get_display_text(), style=self.COLOR_USER)
                            self.console.print(user_text)
                    else:
                        # Group not found in groups data
                        group_text = Text()
                        group_text.append(f"    {self.ICON_GROUP} ", style=self.COLOR_GROUP)
                        group_text.append(f"{assignment.principal_name} (members unknown)", 
                                        style="dim")
                        self.console.print(group_text)
                
                self.console.print()
        
        # Display direct user assignments
        if direct_user_assignments:
            self.console.print(Text("Direct User Access:", style="bold underline"))
            self.console.print()
            
            # Group by permission set
            user_ps_map: Dict[str, List[Assignment]] = {}
            for assignment in direct_user_assignments:
                ps_name = assignment.permission_set.name
                if ps_name not in user_ps_map:
                    user_ps_map[ps_name] = []
                user_ps_map[ps_name].append(assignment)
            
            for ps_name, ps_assignments in sorted(user_ps_map.items()):
                # Display permission set
                ps_text = Text()
                ps_text.append(f"  {self.ICON_PERMISSION_SET} ", style=self.COLOR_PERMISSION_SET)
                ps_text.append(ps_name, style=f"bold {self.COLOR_PERMISSION_SET}")
                self.console.print(ps_text)
                
                # Display users for this permission set
                for assignment in ps_assignments:
                    user_text = Text()
                    user_text.append(f"    {self.ICON_USER} ", style=self.COLOR_USER)
                    user_text.append(f"{assignment.principal_name} (direct)", 
                                    style=f"{self.COLOR_USER} italic")
                    self.console.print(user_text)
                
                self.console.print()
        
        # Display summary statistics
        self._display_summary_statistics(account, assignments, groups)
    
    def _display_summary_statistics(
        self,
        account: Account,
        assignments: List[Assignment],
        groups: Dict[str, Group]
    ) -> None:
        """
        Display summary statistics for account access.
        
        Args:
            account: The account
            assignments: List of assignments
            groups: Dictionary of groups
        """
        # Calculate statistics
        permission_sets = set()
        group_ids = set()
        user_ids = set()
        
        for assignment in assignments:
            permission_sets.add(assignment.permission_set.name)
            
            if assignment.is_group_assignment():
                group_ids.add(assignment.principal_id)
                group = groups.get(assignment.principal_id)
                if group:
                    for user in group.members:
                        user_ids.add(user.id)
            else:
                user_ids.add(assignment.principal_id)
        
        # Display summary
        summary_text = Text()
        summary_text.append("Summary: ", style="bold")
        summary_text.append(f"{len(permission_sets)} permission sets, ", style="dim")
        summary_text.append(f"{len(group_ids)} groups, ", style="dim")
        summary_text.append(f"{len(user_ids)} unique users", style="dim")
        
        self.console.print(summary_text)
        self.console.print()
