# Implementation Plan: Interactive Identity Center Explorer

## Overview

This implementation plan breaks down the Interactive Identity Center Explorer feature into discrete, incremental coding tasks. Each task builds on previous work, with testing integrated throughout to catch errors early. The implementation follows a bottom-up approach: data models → data loading → navigation logic → display rendering → CLI integration.

## Tasks

- [x] 1. Create explorer module structure and data models
  - Create `src/explorer/` directory with `__init__.py`
  - Define data models in `src/explorer/models.py` (OrganizationalUnit, Account, PermissionSet, Assignment, Group, User, OrganizationTree, ExplorerData, SelectableItem, NavigationView)
  - Add type hints and dataclass decorators
  - Include validation methods for data integrity
  - _Requirements: 10.1, 10.2, 10.3_

- [x] 1.1 Write property test for data model validation
  - **Property 21: Organization Tree Structure Integrity**
  - **Validates: Requirements 10.1**
  - Generate random organization structures and verify tree integrity (valid parent references, no orphaned accounts)

- [x] 2. Implement Data Loader component
  - [x] 2.1 Create `src/explorer/data_loader.py` with DataLoader class
    - Implement `__init__(json_dir: str)` to store directory path
    - Implement `load_organizations()` to parse organizations_complete.json
    - Implement `load_account_assignments()` to parse account_assignments.json
    - Implement `load_groups()` to parse groups.json
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 2.2 Implement data integration logic
    - Implement `load_all_data()` to orchestrate loading all JSON files
    - Create unified ExplorerData model linking accounts → assignments → groups → users
    - Build lookup dictionaries for efficient access (account_id → Account, group_id → Group)
    - _Requirements: 2.4_

  - [x] 2.3 Write property test for data integration
    - **Property 4: Data Integration Completeness**
    - **Validates: Requirements 2.4, 10.4, 10.5**
    - Generate random JSON data and verify all cross-references are valid or generate warnings

  - [x] 2.4 Implement validation logic
    - Implement `validate_data_integrity()` to check account IDs and group IDs
    - Generate ValidationWarning objects for invalid references
    - Log warnings but continue with valid data
    - _Requirements: 10.4, 10.5, 10.6_

  - [x] 2.5 Write property test for malformed data handling
    - **Property 5: Graceful Handling of Malformed Data**
    - **Validates: Requirements 2.6, 7.4, 10.6**
    - Generate JSON with missing/invalid fields and verify no crashes occur

  - [x] 2.6 Implement error handling for missing files
    - Handle missing organizations_complete.json (error and exit)
    - Handle missing account_assignments.json (graceful degradation)
    - Handle missing groups.json (graceful degradation)
    - Display descriptive error messages with file paths
    - _Requirements: 2.5, 7.5, 7.6, 7.7_

  - [x] 2.7 Write unit tests for Data Loader
    - Test parsing valid JSON files with known structures
    - Test handling of missing files (organizations should error, others degrade)
    - Test handling of malformed JSON syntax
    - Test validation warning generation for invalid IDs

- [x] 2.8 Write property tests for data mapping completeness
  - **Property 22: Assignment Mapping Completeness**
  - **Validates: Requirements 10.2**
  - **Property 23: Group Mapping Completeness**
  - **Validates: Requirements 10.3**
  - Generate random assignments and groups data, verify complete mappings

- [x] 3. Implement Navigation Engine component
  - [x] 3.1 Create `src/explorer/navigation.py` with NavigationEngine class
    - Implement `__init__(data: ExplorerData)` to store explorer data
    - Define navigation state enum (ROOT_LEVEL, OU_LEVEL, ACCOUNT_DETAIL, EXIT)
    - Implement navigation history stack for back functionality
    - _Requirements: 1.1, 6.1_

  - [x] 3.2 Implement navigation state methods
    - Implement `get_current_view()` to return NavigationView for current state
    - Implement `get_selectable_items()` to build list of items at current level
    - Implement `handle_selection(selected_item: str)` to process user choice and update state
    - Implement `go_back()` to pop navigation history and return to previous level
    - _Requirements: 1.3, 1.4, 1.5_

  - [x] 3.3 Write property test for OU navigation
    - **Property 1: Navigation State Transitions for OUs**
    - **Validates: Requirements 1.3**
    - Generate random OUs with children, verify selecting OU shows all children

  - [x] 3.4 Write property test for account navigation
    - **Property 2: Navigation State Transitions for Accounts**
    - **Validates: Requirements 1.4**
    - Generate random accounts, verify selecting account shows detail view

  - [x] 3.5 Write property test for navigation history
    - **Property 3: Navigation History Consistency**
    - **Validates: Requirements 1.5**
    - Generate random navigation sequences, verify forward then back returns to original state

  - [x] 3.6 Implement breadcrumb generation
    - Implement `get_breadcrumb()` to build path string from navigation history
    - Handle root level (show "Root")
    - Handle OU level (show "Root > OU Name")
    - Handle account level (show "Root > OU Name > Account Name")
    - Implement intelligent truncation for long paths
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 3.7 Write property test for breadcrumb accuracy
    - **Property 14: Breadcrumb Path Accuracy**
    - **Validates: Requirements 6.1, 6.3, 6.4**
    - Generate random navigation states, verify breadcrumb reflects full path

  - [x] 3.8 Write property test for breadcrumb truncation
    - **Property 15: Breadcrumb Truncation Preservation**
    - **Validates: Requirements 6.5**
    - Generate long breadcrumbs, verify truncation preserves context

  - [x] 3.9 Write unit tests for Navigation Engine
    - Test initial state shows root level items
    - Test navigation to specific OU
    - Test navigation to specific account
    - Test back navigation from various levels
    - Test breadcrumb generation at each level

- [x] 4. Checkpoint - Ensure core data and navigation logic works
  - Run all tests for data loader and navigation engine
  - Verify data integration with sample JSON files
  - Ask user if questions arise

- [x] 5. Implement Display Manager component
  - [x] 5.1 Create `src/explorer/display.py` with DisplayManager class
    - Implement `__init__(console: Console)` to store rich Console instance
    - Define color scheme constants (blue for OUs, green for accounts, yellow for permission sets, cyan for groups, white for users, red for errors)
    - Define icon constants (📁, 🔑, 👥, 👤, ❌, ⚠️)
    - _Requirements: 3.3, 3.4, 3.5, 9.4, 9.5_

  - [x] 5.2 Implement basic display methods
    - Implement `show_welcome_screen()` to display help and keyboard shortcuts
    - Implement `display_breadcrumb(breadcrumb: str)` to show navigation path
    - Implement `display_error(message: str)` to show red error with icon
    - Implement `display_empty_state(message: str)` to show empty OU/account messages
    - _Requirements: 9.1, 9.5, 7.1, 7.2_

  - [x] 5.3 Implement item formatting methods
    - Implement `format_ou(ou: OrganizationalUnit)` to render OU with icon and color
    - Implement `format_account(account: Account)` to render account with name and ID
    - Implement `format_permission_set(ps: PermissionSet)` to render with icon
    - Implement `format_group(group: Group)` to render with icon
    - Implement `format_user(user: User)` to render with icon
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 5.4 Write property test for hierarchical display formatting
    - **Property 6: Hierarchical Display Formatting**
    - **Validates: Requirements 3.1, 3.3, 3.4, 3.5, 3.7**
    - Generate random hierarchical data, verify indentation and icons are correct

  - [x] 5.5 Write property test for account display formatting
    - **Property 7: Account Display Formatting**
    - **Validates: Requirements 3.2**
    - Generate random accounts, verify rendered text contains name and ID

  - [x] 5.6 Implement account detail display
    - Implement `display_account_details(account, assignments, groups)` to show full access view
    - Group assignments by permission set
    - Show groups under each permission set
    - Show users under each group
    - Separate direct user assignments from group assignments
    - Calculate and display summary statistics (total permission sets, groups, users)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [x] 5.7 Write property test for display completeness
    - **Property 9: Display Completeness for Account Details**
    - **Validates: Requirements 4.1, 4.2, 4.3**
    - Generate random account assignments, verify all items appear in output

  - [x] 5.8 Write property test for direct assignment indication
    - **Property 8: Direct Assignment Indication**
    - **Validates: Requirements 3.6**
    - Generate accounts with direct user assignments, verify indication is present

  - [x] 5.9 Write property test for assignment type separation
    - **Property 10: Assignment Type Separation**
    - **Validates: Requirements 4.4**
    - Generate accounts with mixed assignments, verify visual separation

  - [x] 5.10 Write property test for summary statistics accuracy
    - **Property 11: Summary Statistics Accuracy**
    - **Validates: Requirements 4.6**
    - Generate random account details, verify counts match actual items

  - [x] 5.11 Implement selection prompt
    - Implement `prompt_selection(items, prompt)` using inquirer library
    - Apply colors to different item types in the selection list
    - Handle keyboard navigation (arrow keys, enter)
    - _Requirements: 1.1, 1.2, 9.2_

  - [x] 5.12 Implement responsive rendering
    - Implement terminal width detection
    - Adjust formatting for widths 80-200 characters
    - Implement pagination for lists > 100 items
    - _Requirements: 9.6, 8.4_

  - [x] 5.13 Write property test for pagination
    - **Property 16: Pagination for Large Lists**
    - **Validates: Requirements 8.4**
    - Generate OUs with >100 accounts, verify pagination is implemented

  - [x] 5.14 Write property test for terminal width responsiveness
    - **Property 20: Terminal Width Responsiveness**
    - **Validates: Requirements 9.6**
    - Test rendering at various widths (80-200), verify no overflow

  - [x] 5.15 Write property test for item type color differentiation
    - **Property 18: Item Type Color Differentiation**
    - **Validates: Requirements 9.4**
    - Generate mixed item lists, verify each type has correct color

  - [x] 5.16 Write property test for error display formatting
    - **Property 19: Error Display Formatting**
    - **Validates: Requirements 9.5**
    - Generate various errors, verify red color and icon are present

  - [x] 5.17 Write unit tests for Display Manager
    - Test formatting of each item type with known inputs
    - Test icon inclusion in rendered output
    - Test color application (verify ANSI codes or rich markup)
    - Test indentation for hierarchical data
    - Test summary statistics calculation
    - Test empty state messages

- [x] 6. Checkpoint - Ensure display rendering works correctly
  - Run all tests for display manager
  - Manually test display output with sample data
  - Ask user if questions arise

- [x] 7. Implement Explorer Controller
  - [x] 7.1 Create `src/explorer/controller.py` with ExplorerController class
    - Implement `__init__(json_dir: str)` to store configuration
    - Implement `start()` to initialize all components (DataLoader, NavigationEngine, DisplayManager)
    - Handle initialization errors gracefully
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 7.2 Implement exploration loop
    - Implement `run_exploration_loop()` as main interaction loop
    - Show welcome screen on first iteration
    - Display breadcrumb and current view
    - Prompt for user selection
    - Handle selection (navigate or exit)
    - Handle "Back" option
    - Handle "Exit" option
    - _Requirements: 1.1, 1.3, 1.4, 1.5, 1.6_

  - [x] 7.3 Implement loading indicators
    - Show loading indicator during JSON file loading
    - Show loading indicator during data integration
    - Use rich Progress or Spinner
    - _Requirements: 9.3_

  - [x] 7.4 Write property test for loading indicator presence
    - **Property 17: Loading Indicator Presence**
    - **Validates: Requirements 9.3**
    - Mock long-running operations, verify indicator is shown

  - [x] 7.5 Implement graceful shutdown
    - Implement `shutdown()` to clean up resources
    - Handle Ctrl+C gracefully
    - Display exit message
    - _Requirements: 1.6_

  - [x] 7.6 Write unit tests for Explorer Controller
    - Test initialization with valid JSON directory
    - Test initialization with invalid JSON directory
    - Test exploration loop with mocked user input
    - Test graceful shutdown

- [x] 8. Integrate with CLI (reverse_diagrams.py)
  - [x] 8.1 Add --explore flag to watch subcommand
    - Add `--explore` / `-e` flag to argparse configuration
    - Add `--json-dir` flag to specify JSON directory (default: "diagrams/json")
    - Update help text to describe explorer mode
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [x] 8.2 Implement explorer mode entry point
    - Check if `--explore` flag is set in watch subcommand
    - If set, instantiate ExplorerController with json_dir
    - Call controller.start() to begin exploration
    - Handle any top-level exceptions and display user-friendly errors
    - _Requirements: 5.1, 5.2_

  - [x] 8.3 Implement argument validation
    - Validate that json_dir exists and is readable
    - Display usage help for invalid argument combinations
    - Exit gracefully with appropriate error codes
    - _Requirements: 5.5_

  - [x] 8.4 Write property test for invalid argument handling
    - **Property 13: Invalid Argument Handling**
    - **Validates: Requirements 5.5**
    - Generate invalid argument combinations, verify graceful exit with help

  - [x] 8.5 Write property test for JSON directory configuration
    - **Property 12: JSON Directory Configuration**
    - **Validates: Requirements 5.3**
    - Test with various directory paths, verify correct path is used

  - [x] 8.6 Write unit tests for CLI integration
    - Test `reverse_diagrams watch --explore` launches explorer
    - Test `reverse_diagrams watch -e` launches explorer
    - Test `--json-dir` flag changes data source
    - Test invalid flags show usage help

- [x] 9. End-to-end integration testing
  - [x] 9.1 Write integration test for complete navigation flow
    - Start explorer → Navigate to OU → Select account → View details → Back → Exit
    - Use real JSON fixtures
    - Verify all components work together

  - [x] 9.2 Write integration test for graceful degradation
    - Start with missing account_assignments.json
    - Verify accounts are shown without assignment information
    - Verify no crashes occur

  - [x] 9.3 Write integration test for error handling
    - Start with invalid organizations_complete.json
    - Verify descriptive error message is shown
    - Verify graceful exit

  - [x] 9.4 Write integration test for deep navigation
    - Navigate through deeply nested OU structure (5+ levels)
    - Verify breadcrumbs are accurate at each level
    - Verify back navigation works correctly

  - [x] 9.5 Write integration test for large organization
    - Use fixture with 50+ accounts in single OU
    - Verify pagination is implemented
    - Verify performance is acceptable

- [x] 10. Documentation and polish
  - Update README.md with explorer feature documentation
  - Add usage examples for --explore flag
  - Document keyboard shortcuts and navigation
  - Add screenshots or ASCII art examples of the UI
  - Update CHANGELOG.md with new feature

- [x] 11. Final checkpoint - Complete feature validation
  - Run full test suite (unit + property + integration)
  - Manually test with real AWS data (if available)
  - Verify all requirements are met
  - Ask user for final review

## Notes

- All tasks are required for comprehensive implementation
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties across random inputs
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end workflows
- Checkpoints ensure incremental validation and provide opportunities for user feedback
- The implementation follows a bottom-up approach: data models → loading → navigation → display → integration
- All components use type hints for better code quality and IDE support
- Error handling is integrated throughout to ensure robustness
