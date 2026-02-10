"""Navigation engine for the Interactive Identity Center Explorer.

This module handles navigation state management and determines what content
to display based on user actions.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from .models import (
    ExplorerData,
    NavigationView,
    SelectableItem,
    OrganizationalUnit,
    Account,
)


class NavigationState(Enum):
    """Navigation state enumeration."""
    ROOT_LEVEL = "ROOT"
    OU_LEVEL = "OU"
    ACCOUNT_DETAIL = "ACCOUNT_DETAIL"
    EXIT = "EXIT"


@dataclass
class NavigationHistoryEntry:
    """Represents a single entry in navigation history."""
    state: NavigationState
    item_id: Optional[str] = None
    item_name: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class NavigationEngine:
    """Manages navigation state and determines what to display."""
    
    def __init__(self, data: ExplorerData):
        """
        Initialize the navigation engine.
        
        Args:
            data: The loaded explorer data
        """
        self.data = data
        self.current_state = NavigationState.ROOT_LEVEL
        self.current_item_id: Optional[str] = None
        self.history: List[NavigationHistoryEntry] = []
        
        # Push initial state to history
        self.history.append(NavigationHistoryEntry(
            state=NavigationState.ROOT_LEVEL
        ))
    
    def get_current_view(self) -> NavigationView:
        """
        Get the current view to display.
        
        Returns:
            NavigationView: The current navigation view
        """
        if self.current_state == NavigationState.ROOT_LEVEL:
            return self._get_root_view()
        elif self.current_state == NavigationState.OU_LEVEL:
            return self._get_ou_view()
        elif self.current_state == NavigationState.ACCOUNT_DETAIL:
            return self._get_account_detail_view()
        else:
            # EXIT state
            return NavigationView(
                level="EXIT",
                items=[],
                breadcrumb="",
                title="Exiting..."
            )
    
    def handle_selection(self, selected_item: str) -> None:
        """
        Process user selection and update navigation state.
        
        Args:
            selected_item: The ID of the selected item
        """
        # Find the selected item in current view
        current_view = self.get_current_view()
        selected = None
        
        for item in current_view.items:
            if item.item_id == selected_item:
                selected = item
                break
        
        if not selected:
            return
        
        # Handle different item types
        if selected.is_exit():
            self.current_state = NavigationState.EXIT
        elif selected.is_back():
            self.go_back()
        elif selected.is_ou():
            # Navigate to OU
            self.current_state = NavigationState.OU_LEVEL
            self.current_item_id = selected.item_id
            self.history.append(NavigationHistoryEntry(
                state=NavigationState.OU_LEVEL,
                item_id=selected.item_id,
                item_name=selected.metadata.get("name", ""),
                metadata=selected.metadata
            ))
        elif selected.is_account():
            # Navigate to account detail
            self.current_state = NavigationState.ACCOUNT_DETAIL
            self.current_item_id = selected.item_id
            self.history.append(NavigationHistoryEntry(
                state=NavigationState.ACCOUNT_DETAIL,
                item_id=selected.item_id,
                item_name=selected.metadata.get("name", ""),
                metadata=selected.metadata
            ))
    
    def go_back(self) -> bool:
        """
        Navigate to previous level.
        
        Returns:
            bool: False if at root (can't go back), True otherwise
        """
        if len(self.history) <= 1:
            # Already at root
            return False
        
        # Pop current state
        self.history.pop()
        
        # Restore previous state
        previous = self.history[-1]
        self.current_state = previous.state
        self.current_item_id = previous.item_id
        
        return True
    
    def get_breadcrumb(self, max_width: int = 80) -> str:
        """
        Get the current navigation breadcrumb path.
        
        Args:
            max_width: Maximum width for the breadcrumb (default: 80)
        
        Returns:
            str: The breadcrumb path, truncated if necessary
        """
        if len(self.history) == 1:
            return "Root"
        
        # Build breadcrumb from history
        parts = ["Root"]
        for entry in self.history[1:]:
            if entry.item_name:
                parts.append(entry.item_name)
        
        full_breadcrumb = " > ".join(parts)
        
        # If breadcrumb fits within max_width, return it as-is
        if len(full_breadcrumb) <= max_width:
            return full_breadcrumb
        
        # Intelligent truncation: preserve root, current location, and immediate parent
        if len(parts) <= 2:
            # Only root and one item, truncate the item name if needed
            return self._truncate_breadcrumb_simple(parts, max_width)
        
        # For longer paths, try: Root > ... > Parent > Current
        if len(parts) >= 3:
            preserved_parts = ["Root", "...", parts[-2], parts[-1]]
            truncated = " > ".join(preserved_parts)
            
            # If this fits, use it
            if len(truncated) <= max_width:
                return truncated
        
        # If still too long, use simple truncation
        return self._truncate_breadcrumb_simple(parts, max_width)
    
    def _truncate_breadcrumb_simple(self, parts: List[str], max_width: int) -> str:
        """
        Simple truncation that shortens item names.
        
        Args:
            parts: List of breadcrumb parts
            max_width: Maximum width
            
        Returns:
            str: Truncated breadcrumb
        """
        separator = " > "
        separator_len = len(separator)
        
        # For very narrow widths, show minimal info
        if max_width < 20:
            if len(parts) > 1:
                return f"...{parts[-1][:max_width-3]}"
            return parts[0][:max_width]
        
        # Calculate available space for each part
        num_parts = len(parts)
        separators_len = separator_len * (num_parts - 1)
        available_for_parts = max_width - separators_len
        
        if available_for_parts < num_parts * 3:  # Need at least 3 chars per part
            # Extreme truncation: just show first and last
            if num_parts > 2:
                first_len = min(8, len(parts[0]))
                last_len = min(max_width - first_len - 10, len(parts[-1]))
                if last_len < 3:
                    last_len = 3
                first = parts[0][:first_len]
                last = parts[-1][:last_len]
                result = f"{first} > ... > {last}"
                # Ensure we don't exceed max_width
                if len(result) > max_width:
                    last = parts[-1][:max(3, max_width - first_len - 10)]
                    result = f"{first} > ... > {last}"
                return result[:max_width]
            else:
                # Just two parts, truncate each
                part_len = (max_width - separator_len) // 2
                return separator.join(p[:part_len] for p in parts)
        
        # Distribute space evenly, but preserve more for the current item
        max_part_len = available_for_parts // num_parts
        
        truncated_parts = []
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                # Give more space to the current item
                max_len = min(len(part), max_part_len + 10)
            else:
                max_len = max_part_len
            
            if len(part) > max_len and max_len > 3:
                truncated_parts.append(part[:max_len - 3] + "...")
            else:
                truncated_parts.append(part[:max_len])
        
        result = separator.join(truncated_parts)
        
        # Final safety check: ensure we don't exceed max_width
        if len(result) > max_width:
            # Aggressive truncation
            if len(parts) > 2:
                return f"{parts[0][:5]}...{parts[-1][:max(3, max_width-10)]}"
            else:
                return result[:max_width]
        
        return result
    
    def get_selectable_items(self) -> List[SelectableItem]:
        """
        Get list of items user can select at current level.
        
        Returns:
            List[SelectableItem]: List of selectable items
        """
        return self.get_current_view().items
    
    def _get_root_view(self) -> NavigationView:
        """Get the root level view."""
        items = []
        
        # Add root OUs
        for ou in self.data.organization.root_ous:
            items.append(SelectableItem(
                display_text=f"📁 {ou.name}",
                item_type="OU",
                item_id=ou.id,
                metadata={"name": ou.name, "ou": ou}
            ))
        
        # Add root accounts
        for account in self.data.organization.root_accounts:
            items.append(SelectableItem(
                display_text=f"  {account.get_display_text()}",
                item_type="ACCOUNT",
                item_id=account.id,
                metadata={"name": account.name, "account": account}
            ))
        
        # Add exit option
        items.append(SelectableItem(
            display_text="❌ Exit",
            item_type="EXIT",
            item_id="exit",
            metadata={}
        ))
        
        return NavigationView(
            level="ROOT",
            items=items,
            breadcrumb=self.get_breadcrumb(),
            title="AWS Organizations Explorer"
        )
    
    def _get_ou_view(self) -> NavigationView:
        """Get the OU level view."""
        items = []
        
        # Find the current OU
        ou = self._find_ou_by_id(self.current_item_id)
        
        if not ou:
            # OU not found, go back to root
            self.current_state = NavigationState.ROOT_LEVEL
            self.current_item_id = None
            return self._get_root_view()
        
        # Add child OUs
        for child_ou in ou.children_ous:
            items.append(SelectableItem(
                display_text=f"📁 {child_ou.name}",
                item_type="OU",
                item_id=child_ou.id,
                metadata={"name": child_ou.name, "ou": child_ou}
            ))
        
        # Add accounts in this OU
        for account in ou.accounts:
            items.append(SelectableItem(
                display_text=f"  {account.get_display_text()}",
                item_type="ACCOUNT",
                item_id=account.id,
                metadata={"name": account.name, "account": account}
            ))
        
        # Add back option
        items.append(SelectableItem(
            display_text="⬅️  Back",
            item_type="BACK",
            item_id="back",
            metadata={}
        ))
        
        # Add exit option
        items.append(SelectableItem(
            display_text="❌ Exit",
            item_type="EXIT",
            item_id="exit",
            metadata={}
        ))
        
        return NavigationView(
            level="OU",
            items=items,
            breadcrumb=self.get_breadcrumb(),
            title=f"OU: {ou.name}"
        )
    
    def _get_account_detail_view(self) -> NavigationView:
        """Get the account detail view."""
        items = []
        
        # Find the current account
        account = self.data.organization.get_account_by_id(self.current_item_id)
        
        if not account:
            # Account not found, go back
            self.go_back()
            return self.get_current_view()
        
        # Add back option
        items.append(SelectableItem(
            display_text="⬅️  Back",
            item_type="BACK",
            item_id="back",
            metadata={}
        ))
        
        # Add exit option
        items.append(SelectableItem(
            display_text="❌ Exit",
            item_type="EXIT",
            item_id="exit",
            metadata={}
        ))
        
        return NavigationView(
            level="ACCOUNT_DETAIL",
            items=items,
            breadcrumb=self.get_breadcrumb(),
            title=f"Account: {account.get_display_text()}"
        )
    
    def _find_ou_by_id(self, ou_id: str) -> Optional[OrganizationalUnit]:
        """
        Find an OU by its ID recursively.
        
        Args:
            ou_id: The OU ID to find
            
        Returns:
            Optional[OrganizationalUnit]: The OU if found, None otherwise
        """
        # Search in root OUs
        for ou in self.data.organization.root_ous:
            if ou.id == ou_id:
                return ou
            # Search recursively in children
            found = self._find_ou_in_children(ou, ou_id)
            if found:
                return found
        
        return None
    
    def _find_ou_in_children(self, parent_ou: OrganizationalUnit, ou_id: str) -> Optional[OrganizationalUnit]:
        """
        Recursively search for an OU in children.
        
        Args:
            parent_ou: The parent OU to search in
            ou_id: The OU ID to find
            
        Returns:
            Optional[OrganizationalUnit]: The OU if found, None otherwise
        """
        for child_ou in parent_ou.children_ous:
            if child_ou.id == ou_id:
                return child_ou
            # Search recursively
            found = self._find_ou_in_children(child_ou, ou_id)
            if found:
                return found
        
        return None
