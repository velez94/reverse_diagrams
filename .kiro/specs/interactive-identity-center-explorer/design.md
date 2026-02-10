# Design Document: Interactive Identity Center Explorer

## Overview

The Interactive Identity Center Explorer is a terminal-based user interface (TUI) that provides an interactive navigation experience for exploring AWS Organizations structure alongside IAM Identity Center access patterns. The feature integrates with the existing `reverse_diagrams` CLI tool as a new mode under the `watch` subcommand.

The Explorer combines three data sources (organizations structure, account assignments, and group memberships) into a unified navigable hierarchy. Users can drill down from the organization root through OUs and accounts to see detailed permission assignments, including which groups and users have access through which permission sets.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI Entry Point                          │
│              (reverse_diagrams.py)                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ --explore flag
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Explorer Controller                         │
│           (explorer/controller.py)                           │
│  - Orchestrates data loading and navigation                  │
│  - Manages application lifecycle                             │
└────┬──────────────┬──────────────┬──────────────────────────┘
     │              │               │
     ▼              ▼               ▼
┌─────────┐  ┌──────────┐  ┌──────────────┐
│  Data   │  │Navigation│  │   Display    │
│ Loader  │  │  Engine  │  │   Manager    │
└─────────┘  └──────────┘  └──────────────┘
     │              │               │
     │              │               │
     ▼              ▼               ▼
┌─────────┐  ┌──────────┐  ┌──────────────┐
│  Data   │  │Navigation│  │     Rich     │
│ Models  │  │  State   │  │   Console    │
└─────────┘  └──────────┘  └──────────────┘
```

### Component Responsibilities

1. **Explorer Controller**: Main orchestrator that initializes components and manages the exploration loop
2. **Data Loader**: Reads JSON files, validates data, and constructs the unified data model
3. **Navigation Engine**: Handles user input, manages navigation state, and determines what to display
4. **Display Manager**: Renders the UI using the rich library with proper formatting and colors
5. **Data Models**: Type-safe representations of organizations, accounts, assignments, groups, and users

### Module Structure

```
src/
├── explorer/
│   ├── __init__.py
│   ├── controller.py          # Main explorer orchestration
│   ├── data_loader.py         # JSON loading and data integration
│   ├── navigation.py          # Navigation state and logic
│   ├── display.py             # Rich-based UI rendering
│   └── models.py              # Data models for explorer
```

## Components and Interfaces

### 1. Explorer Controller

**Purpose**: Orchestrates the entire exploration experience from initialization to termination.

**Interface**:
```python
class ExplorerController:
    def __init__(self, json_dir: str):
        """Initialize the explorer with the JSON data directory."""
        
    def start(self) -> None:
        """Start the interactive exploration session."""
        
    def run_exploration_loop(self) -> None:
        """Main loop handling navigation and display."""
        
    def shutdown(self) -> None:
        """Clean up resources and exit gracefully."""
```

**Responsibilities**:
- Initialize Data Loader, Navigation Engine, and Display Manager
- Handle top-level error catching and graceful shutdown
- Coordinate the exploration loop
- Manage application state transitions

### 2. Data Loader

**Purpose**: Load and integrate data from multiple JSON sources into a unified model.

**Interface**:
```python
class DataLoader:
    def __init__(self, json_dir: str):
        """Initialize with the directory containing JSON files."""
        
    def load_all_data(self) -> ExplorerData:
        """Load and integrate all JSON data sources."""
        
    def load_organizations(self) -> OrganizationTree:
        """Load and parse organizations_complete.json."""
        
    def load_account_assignments(self) -> Dict[str, List[Assignment]]:
        """Load and parse account_assignments.json."""
        
    def load_groups(self) -> Dict[str, Group]:
        """Load and parse groups.json."""
        
    def validate_data_integrity(self) -> List[ValidationWarning]:
        """Validate cross-references between data sources."""
```

**Responsibilities**:
- Read JSON files from the specified directory
- Parse JSON into structured data models
- Validate data integrity (e.g., account IDs exist, group IDs are valid)
- Create mappings for efficient lookups during navigation
- Handle missing files and malformed data gracefully

### 3. Navigation Engine

**Purpose**: Manage navigation state and determine what content to display based on user actions.

**Interface**:
```python
class NavigationEngine:
    def __init__(self, data: ExplorerData):
        """Initialize with the loaded explorer data."""
        
    def get_current_view(self) -> NavigationView:
        """Get the current view to display."""
        
    def handle_selection(self, selected_item: str) -> None:
        """Process user selection and update navigation state."""
        
    def go_back(self) -> bool:
        """Navigate to previous level. Returns False if at root."""
        
    def get_breadcrumb(self) -> str:
        """Get the current navigation breadcrumb path."""
        
    def get_selectable_items(self) -> List[SelectableItem]:
        """Get list of items user can select at current level."""
```

**Navigation States**:
- `ROOT_LEVEL`: Showing root OUs and accounts
- `OU_LEVEL`: Showing contents of a specific OU
- `ACCOUNT_DETAIL`: Showing permission sets and access for an account
- `EXIT`: User has chosen to exit

**Responsibilities**:
- Track current position in the hierarchy
- Maintain navigation history for "back" functionality
- Determine what items are selectable at each level
- Generate breadcrumb trails
- Translate user selections into state transitions

### 4. Display Manager

**Purpose**: Render the user interface using the rich library with proper formatting, colors, and icons.

**Interface**:
```python
class DisplayManager:
    def __init__(self, console: Console):
        """Initialize with a rich Console instance."""
        
    def show_welcome_screen(self) -> None:
        """Display welcome message and keyboard shortcuts."""
        
    def prompt_selection(self, items: List[SelectableItem], 
                        prompt: str) -> str:
        """Show interactive selection prompt using inquirer."""
        
    def display_account_details(self, account: Account, 
                               assignments: List[Assignment],
                               groups: Dict[str, Group]) -> None:
        """Display detailed view of account access patterns."""
        
    def display_breadcrumb(self, breadcrumb: str) -> None:
        """Display navigation breadcrumb."""
        
    def display_error(self, message: str) -> None:
        """Display error message with appropriate styling."""
        
    def display_empty_state(self, message: str) -> None:
        """Display message for empty OUs or accounts with no access."""
```

**Styling Guidelines**:
- OUs: Blue color with folder icon (📁)
- Accounts: Green color with account ID in parentheses
- Permission Sets: Yellow color with key icon (🔑)
- Groups: Cyan color with group icon (👥)
- Users: White color with user icon (👤)
- Errors: Red color with error icon (❌)
- Warnings: Yellow color with warning icon (⚠️)

**Responsibilities**:
- Render all UI elements using rich library
- Format hierarchical data with proper indentation
- Apply consistent color scheme and icons
- Handle terminal width constraints
- Display loading indicators during data operations
- Show help text and keyboard shortcuts

### 5. Data Models

**Purpose**: Provide type-safe representations of all data structures used in the explorer.

**Core Models**:

```python
@dataclass
class OrganizationalUnit:
    id: str
    name: str
    parent_id: Optional[str]
    children_ous: List['OrganizationalUnit']
    accounts: List['Account']

@dataclass
class Account:
    id: str
    name: str
    email: str
    parent_ou_id: Optional[str]

@dataclass
class PermissionSet:
    arn: str
    name: str

@dataclass
class Assignment:
    account_id: str
    permission_set: PermissionSet
    principal_type: str  # "GROUP" or "USER"
    principal_id: str
    principal_name: str

@dataclass
class Group:
    id: str
    name: str
    description: Optional[str]
    members: List['User']

@dataclass
class User:
    id: str
    username: str
    email: Optional[str]
    display_name: Optional[str]

@dataclass
class OrganizationTree:
    root_id: str
    root_ous: List[OrganizationalUnit]
    root_accounts: List[Account]
    all_accounts: Dict[str, Account]  # For quick lookup

@dataclass
class ExplorerData:
    organization: OrganizationTree
    assignments_by_account: Dict[str, List[Assignment]]
    groups_by_id: Dict[str, Group]

@dataclass
class SelectableItem:
    display_text: str
    item_type: str  # "OU", "ACCOUNT", "BACK", "EXIT"
    item_id: str
    metadata: Dict[str, Any]

@dataclass
class NavigationView:
    level: str  # "ROOT", "OU", "ACCOUNT_DETAIL"
    items: List[SelectableItem]
    breadcrumb: str
    title: str
```

## Data Models

### JSON Data Structures

The Explorer expects three JSON files with the following structures:

**organizations_complete.json**:
```json
{
  "Id": "r-xxxx",
  "Arn": "arn:aws:organizations::...",
  "OrganizationalUnits": [
    {
      "Id": "ou-xxxx",
      "Name": "Core OU",
      "Arn": "arn:aws:organizations::...",
      "ParentId": "r-xxxx",
      "Accounts": [
        {
          "Id": "123456789012",
          "Name": "Log Archive",
          "Email": "log-archive@example.com",
          "Arn": "arn:aws:organizations::...",
          "Status": "ACTIVE"
        }
      ],
      "OrganizationalUnits": []
    }
  ],
  "Accounts": []
}
```

**account_assignments.json**:
```json
{
  "123456789012": [
    {
      "PermissionSetArn": "arn:aws:sso:::permissionSet/...",
      "PermissionSetName": "AWSPowerUserAccess",
      "PrincipalType": "GROUP",
      "PrincipalId": "group-id-123",
      "PrincipalName": "AWSSecurityAuditPowerUsers"
    }
  ]
}
```

**groups.json**:
```json
{
  "group-id-123": {
    "GroupId": "group-id-123",
    "DisplayName": "AWSSecurityAuditPowerUsers",
    "Description": "Power users for security audit",
    "Members": [
      {
        "UserId": "user-id-456",
        "UserName": "user1@example.com",
        "DisplayName": "User One",
        "Email": "user1@example.com"
      }
    ]
  }
}
```

### Data Integration Strategy

The Data Loader creates a unified model by:

1. **Building Organization Tree**: Parse organizations_complete.json recursively to create the OU hierarchy
2. **Indexing Accounts**: Create a map of account ID → Account for quick lookups
3. **Mapping Assignments**: Group assignments by account ID for efficient retrieval
4. **Linking Groups**: Create a map of group ID → Group with member details
5. **Validation**: Check that all account IDs in assignments exist in the organization, and all group IDs exist in groups data

### Data Flow

```
JSON Files → Data Loader → Unified Model → Navigation Engine → Display Manager → User
     ↑                                                                            │
     └────────────────────────────────────────────────────────────────────────────┘
                              User selections update navigation state
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

After analyzing all acceptance criteria, I've identified several areas where properties can be consolidated:

**Redundancy Analysis**:

1. **Display Format Properties (3.1-3.7, 4.1-4.4)**: Many of these test similar rendering concerns. Properties 3.4, 3.5, 3.6 all test that specific icons appear in rendered output. These can be combined into a single comprehensive property about icon presence. Similarly, 4.1, 4.2, 4.3 all test completeness of display and can be combined.

2. **Data Structure Creation (10.1-10.3)**: These three properties all test that the Data Loader creates correct mappings. They can be combined into a single property about data model completeness.

3. **Validation Properties (10.4-10.6)**: These test data validation behavior and can be combined into a comprehensive validation property.

4. **Breadcrumb Properties (6.1, 6.3, 6.4)**: These all test breadcrumb generation accuracy and can be combined into a single property.

5. **CLI Argument Properties (5.3, 5.5)**: Both test argument handling and can be combined.

**Properties to Keep Separate**:
- Navigation state transitions (1.3, 1.4, 1.5) - each tests different navigation behavior
- Round-trip properties for data loading (2.4) - critical for data integrity
- Error handling for malformed data (2.6, 7.4) - important edge case coverage
- Display completeness (4.6) - tests summary calculation accuracy

### Correctness Properties

Property 1: Navigation State Transitions for OUs
*For any* organizational unit with child OUs or accounts, selecting that OU should result in a navigation state containing all of its children (both child OUs and accounts).
**Validates: Requirements 1.3**

Property 2: Navigation State Transitions for Accounts
*For any* account in the organization, selecting that account should result in a navigation state showing the account detail view with all associated permission set assignments.
**Validates: Requirements 1.4**

Property 3: Navigation History Consistency
*For any* sequence of navigation actions (forward selections), performing those actions followed by an equal number of "back" actions should return the navigation state to its original position.
**Validates: Requirements 1.5**

Property 4: Data Integration Completeness
*For any* valid set of JSON files (organizations, assignments, groups), the Data Loader should create a unified model where every account ID in assignments maps to an account in the organization tree, and every group ID in assignments maps to a group in the groups data (or generates a validation warning).
**Validates: Requirements 2.4, 10.4, 10.5**

Property 5: Graceful Handling of Malformed Data
*For any* JSON file with missing or invalid fields, the Data Loader should not crash but should log warnings and continue processing with default values or partial data.
**Validates: Requirements 2.6, 7.4, 10.6**

Property 6: Hierarchical Display Formatting
*For any* hierarchical data structure (OUs, accounts, permission sets, groups, users), the rendered output should use consistent indentation where child items have greater indentation than their parents, and each item type should include its designated icon (📁 for OUs, 🔑 for permission sets, 👥 for groups, 👤 for users).
**Validates: Requirements 3.1, 3.3, 3.4, 3.5, 3.7**

Property 7: Account Display Formatting
*For any* account, the rendered display text should contain both the account name and the account ID in a formatted manner (e.g., "Account Name (123456789012)").
**Validates: Requirements 3.2**

Property 8: Direct Assignment Indication
*For any* account with direct user assignments (principal type is USER), the rendered output should clearly indicate that the assignment is direct and not through a group.
**Validates: Requirements 3.6**

Property 9: Display Completeness for Account Details
*For any* account with permission set assignments, the account detail view should display all permission sets, all groups associated with each permission set, and all users in each group, with no omissions.
**Validates: Requirements 4.1, 4.2, 4.3**

Property 10: Assignment Type Separation
*For any* account with both direct user assignments and group-based assignments, the rendered output should visually separate or distinguish between these two types of assignments.
**Validates: Requirements 4.4**

Property 11: Summary Statistics Accuracy
*For any* account detail view, the displayed summary statistics (total permission sets, total groups, total users) should exactly match the count of items shown in the detailed view.
**Validates: Requirements 4.6**

Property 12: JSON Directory Configuration
*For any* valid directory path provided via the --json-dir flag, the Data Loader should attempt to read JSON files from that directory rather than the default location.
**Validates: Requirements 5.3**

Property 13: Invalid Argument Handling
*For any* invalid command-line argument combination, the Explorer should display usage help and exit gracefully without crashing or showing stack traces.
**Validates: Requirements 5.5**

Property 14: Breadcrumb Path Accuracy
*For any* navigation state (root, OU, or account), the breadcrumb should accurately reflect the full path from root to the current location, including all intermediate OUs.
**Validates: Requirements 6.1, 6.3, 6.4**

Property 15: Breadcrumb Truncation Preservation
*For any* breadcrumb that exceeds the terminal width, the truncated version should preserve the most important context (typically the current location and immediate parent).
**Validates: Requirements 6.5**

Property 16: Pagination for Large Lists
*For any* OU containing more than 100 accounts, the display should implement pagination or scrolling rather than attempting to show all items at once.
**Validates: Requirements 8.4**

Property 17: Loading Indicator Presence
*For any* operation that takes longer than 500 milliseconds (such as loading JSON files), a loading indicator should be displayed to provide user feedback.
**Validates: Requirements 9.3**

Property 18: Item Type Color Differentiation
*For any* list of mixed item types (OUs, accounts, permission sets, groups, users), each item type should be rendered in its designated color to enable quick visual differentiation.
**Validates: Requirements 9.4**

Property 19: Error Display Formatting
*For any* error condition, the error message should be displayed in red color with an error icon (❌) to clearly indicate the error state.
**Validates: Requirements 9.5**

Property 20: Terminal Width Responsiveness
*For any* terminal width between 80 and 200 characters, the display should render without line breaks in unexpected places or content overflow.
**Validates: Requirements 9.6**

Property 21: Organization Tree Structure Integrity
*For any* valid organizations_complete.json file, the Data Loader should create a tree structure where every OU has a valid parent reference (or is a root OU), and every account belongs to exactly one OU or the root.
**Validates: Requirements 10.1**

Property 22: Assignment Mapping Completeness
*For any* valid account_assignments.json file, the Data Loader should create a mapping where every account ID maps to a list of assignments, and accounts with no assignments map to an empty list.
**Validates: Requirements 10.2**

Property 23: Group Mapping Completeness
*For any* valid groups.json file, the Data Loader should create a mapping where every group ID maps to a Group object containing all member users.
**Validates: Requirements 10.3**

## Error Handling

### Error Categories

1. **File System Errors**
   - Missing JSON files
   - Unreadable files (permissions)
   - Invalid JSON syntax
   - **Handling**: Display clear error message with file path and suggested resolution

2. **Data Validation Errors**
   - Invalid account IDs in assignments
   - Invalid group IDs in assignments
   - Missing required fields in JSON
   - **Handling**: Log warnings, continue with partial data, display validation summary

3. **Navigation Errors**
   - Attempting to navigate to non-existent items
   - Invalid navigation state
   - **Handling**: Reset to safe state (root level), log error

4. **Display Errors**
   - Terminal too narrow (< 80 characters)
   - Rendering failures
   - **Handling**: Display simplified view or error message

5. **User Input Errors**
   - Invalid command-line arguments
   - Unexpected user input
   - **Handling**: Display usage help, prompt for valid input

### Error Recovery Strategies

**Graceful Degradation**:
- If account_assignments.json is missing: Show accounts without assignment information
- If groups.json is missing: Show group names without member details
- If some accounts have invalid data: Skip those accounts, continue with valid ones

**User Guidance**:
- All error messages should include:
  - Clear description of what went wrong
  - The specific file or data causing the issue
  - Suggested action to resolve the problem
  - Example: "Error: Cannot find organizations_complete.json in diagrams/json/. Please ensure you have run 'reverse_diagrams -o' to generate organization data first."

**Logging**:
- All errors and warnings should be logged with appropriate severity levels
- Validation warnings should be collected and displayed as a summary
- Debug logging should be available for troubleshooting

## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests to ensure comprehensive coverage:

**Unit Tests** focus on:
- Specific examples of JSON parsing (known input → expected output)
- Edge cases like empty OUs, accounts with no assignments, groups with no members
- Error conditions like missing files, malformed JSON
- Integration points between components
- CLI argument parsing for specific flag combinations

**Property-Based Tests** focus on:
- Universal properties that hold for all inputs
- Navigation state transitions across randomly generated organization structures
- Data integration correctness across varied JSON inputs
- Display formatting consistency across different data types
- Validation behavior across various invalid data scenarios

### Property-Based Testing Configuration

**Library Selection**: Use `hypothesis` for Python property-based testing

**Test Configuration**:
- Minimum 100 iterations per property test
- Each test tagged with: **Feature: interactive-identity-center-explorer, Property {number}: {property_text}**
- Custom generators for:
  - Organization structures (random OUs, accounts, nesting levels)
  - Account assignments (random permission sets, principals)
  - Group memberships (random users per group)

**Example Property Test Structure**:
```python
from hypothesis import given, strategies as st
import pytest

# Feature: interactive-identity-center-explorer, Property 1: Navigation State Transitions for OUs
@given(st.builds(OrganizationalUnit))
def test_ou_navigation_shows_children(ou):
    """For any OU with children, selecting it should show all children."""
    nav_engine = NavigationEngine(create_test_data_with_ou(ou))
    nav_engine.handle_selection(ou.id)
    view = nav_engine.get_current_view()
    
    expected_children = set(child.id for child in ou.children_ous + ou.accounts)
    actual_children = set(item.item_id for item in view.items 
                         if item.item_type in ["OU", "ACCOUNT"])
    
    assert expected_children == actual_children
```

### Unit Test Coverage

**Data Loader Tests**:
- Test parsing of valid JSON files with known structures
- Test handling of missing files (organizations_complete.json should error, others should degrade gracefully)
- Test handling of malformed JSON (syntax errors, missing fields)
- Test data integration with mismatched IDs (account IDs in assignments not in org structure)
- Test validation warning generation

**Navigation Engine Tests**:
- Test initial state (root level view)
- Test navigation to specific OU
- Test navigation to specific account
- Test back navigation
- Test breadcrumb generation at each level
- Test handling of invalid selections

**Display Manager Tests**:
- Test formatting of each item type (OU, account, permission set, group, user)
- Test icon inclusion in rendered output
- Test color application (verify ANSI color codes)
- Test indentation for hierarchical data
- Test summary statistics calculation
- Test empty state messages
- Test error message formatting

**Controller Tests**:
- Test initialization with valid JSON directory
- Test initialization with invalid JSON directory
- Test exploration loop (mock user input)
- Test graceful shutdown

### Integration Tests

**End-to-End Scenarios**:
1. Start explorer → Navigate to OU → Select account → View details → Back → Exit
2. Start with missing account_assignments.json → Verify graceful degradation
3. Start with invalid organizations_complete.json → Verify error message
4. Navigate through deeply nested OU structure → Verify breadcrumbs
5. View account with 50+ permission sets → Verify all displayed

**CLI Integration**:
- Test `reverse_diagrams watch --explore` launches explorer
- Test `reverse_diagrams watch -e` launches explorer
- Test `--json-dir` flag changes data source
- Test invalid flags show usage help

### Test Data Strategy

**Fixtures**:
- Small organization (5 OUs, 10 accounts) for basic tests
- Large organization (50 OUs, 200 accounts) for performance and pagination tests
- Edge case organization (empty OUs, accounts with no assignments)
- Invalid data (missing fields, wrong types, invalid references)

**Generators** (for property-based tests):
- Random organization structures with configurable depth and breadth
- Random account assignments with varied permission sets and principals
- Random group memberships with varied user counts
- Random invalid data (missing fields, wrong types)

### Performance Testing

While not part of property-based testing, performance should be validated:
- Load time for 500-account organization: < 5 seconds
- Navigation response time: < 100ms
- Account detail rendering: < 200ms
- Memory usage for 1000-account organization: < 100MB

These can be tested with specific performance test cases using `pytest-benchmark`.

### Test Execution

```bash
# Run all tests
pytest tests/explorer/

# Run with coverage
pytest --cov=src/explorer --cov-report=html tests/explorer/

# Run only property-based tests
pytest -m property tests/explorer/

# Run with more iterations for property tests
pytest --hypothesis-iterations=1000 tests/explorer/

# Run specific test file
pytest tests/explorer/test_navigation.py
```
