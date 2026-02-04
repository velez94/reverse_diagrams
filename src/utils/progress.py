"""Progress tracking utilities with rich console output."""
import logging
from typing import List, Optional, Any, Iterator
from contextlib import contextmanager

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
    TaskID
)
from rich.panel import Panel
from rich.text import Text

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Enhanced progress tracking with rich console output."""
    
    def __init__(self, console: Optional[Console] = None):
        """
        Initialize progress tracker.
        
        Args:
            console: Rich console instance (optional)
        """
        self.console = console or Console()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
            transient=True  # Progress bars disappear after completion
        )
        self._active_tasks: List[TaskID] = []
    
    @contextmanager
    def track_operation(self, description: str, total: Optional[int] = None):
        """
        Context manager for tracking a single operation.
        
        Args:
            description: Operation description
            total: Total number of items (optional for indeterminate progress)
            
        Yields:
            Task ID for updating progress
        """
        with self.progress:
            task_id = self.progress.add_task(
                f"[cyan]{description}",
                total=total
            )
            self._active_tasks.append(task_id)
            
            try:
                yield task_id
            finally:
                if task_id in self._active_tasks:
                    self._active_tasks.remove(task_id)
    
    def update_progress(self, task_id: TaskID, advance: int = 1, description: Optional[str] = None):
        """
        Update progress for a task.
        
        Args:
            task_id: Task identifier
            advance: Number of items to advance
            description: Updated description (optional)
        """
        kwargs = {"advance": advance}
        if description:
            kwargs["description"] = f"[cyan]{description}"
        
        self.progress.update(task_id, **kwargs)
    
    def complete_task(self, task_id: TaskID, description: Optional[str] = None):
        """
        Mark a task as completed.
        
        Args:
            task_id: Task identifier
            description: Completion message (optional)
        """
        if description:
            self.progress.update(task_id, description=f"[green]✓ {description}")
        else:
            current_desc = self.progress.tasks[task_id].description
            self.progress.update(task_id, description=f"[green]✓ {current_desc}")
    
    def track_aws_operations(self, operations: List[str]) -> Iterator[TaskID]:
        """
        Track multiple AWS operations with progress bars.
        
        Args:
            operations: List of operation descriptions
            
        Yields:
            Task IDs for each operation
        """
        with self.progress:
            task_ids = []
            
            # Create tasks for all operations
            for operation in operations:
                task_id = self.progress.add_task(
                    f"[cyan]{operation}",
                    total=None  # Indeterminate progress
                )
                task_ids.append(task_id)
            
            # Yield task IDs for updating
            for task_id in task_ids:
                yield task_id
    
    def show_summary(self, title: str, items: List[str], color: str = "blue"):
        """
        Display a summary panel with items.
        
        Args:
            title: Panel title
            items: List of items to display
            color: Panel border color
        """
        if not items:
            content = Text("No items to display", style="italic")
        else:
            content = Text("\n".join(f"• {item}" for item in items))
        
        panel = Panel(
            content,
            title=f"[bold {color}]{title}[/bold {color}]",
            border_style=color,
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
    def show_error(self, message: str, details: Optional[str] = None):
        """
        Display an error message with optional details.
        
        Args:
            message: Error message
            details: Additional error details (optional)
        """
        content = Text(message, style="bold red")
        if details:
            content.append("\n\n")
            content.append(details, style="red")
        
        panel = Panel(
            content,
            title="[bold red]❌ Error[/bold red]",
            border_style="red",
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
    def show_success(self, message: str, details: Optional[str] = None):
        """
        Display a success message with optional details.
        
        Args:
            message: Success message
            details: Additional details (optional)
        """
        content = Text(message, style="bold green")
        if details:
            content.append("\n\n")
            content.append(details, style="green")
        
        panel = Panel(
            content,
            title="[bold green]✅ Success[/bold green]",
            border_style="green",
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
    def show_warning(self, message: str, details: Optional[str] = None):
        """
        Display a warning message with optional details.
        
        Args:
            message: Warning message
            details: Additional details (optional)
        """
        content = Text(message, style="bold yellow")
        if details:
            content.append("\n\n")
            content.append(details, style="yellow")
        
        panel = Panel(
            content,
            title="[bold yellow]⚠️  Warning[/bold yellow]",
            border_style="yellow",
            padding=(1, 2)
        )
        
        self.console.print(panel)


# Global progress tracker instance
_progress_tracker: Optional[ProgressTracker] = None


def get_progress_tracker() -> ProgressTracker:
    """Get or create global progress tracker instance."""
    global _progress_tracker
    if _progress_tracker is None:
        _progress_tracker = ProgressTracker()
    return _progress_tracker


def track_items(items: List[Any], description: str = "Processing items") -> Iterator[Any]:
    """
    Track progress while iterating over items.
    
    Args:
        items: List of items to process
        description: Progress description
        
    Yields:
        Items from the list with progress tracking
    """
    tracker = get_progress_tracker()
    
    with tracker.track_operation(description, total=len(items)) as task_id:
        for item in items:
            yield item
            tracker.update_progress(task_id)


@contextmanager
def track_operation(description: str, total: Optional[int] = None):
    """
    Context manager for tracking operations with global progress tracker.
    
    Args:
        description: Operation description
        total: Total number of items (optional)
        
    Yields:
        Task ID for updating progress
    """
    tracker = get_progress_tracker()
    with tracker.track_operation(description, total) as task_id:
        yield task_id