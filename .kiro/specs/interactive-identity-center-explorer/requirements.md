# Requirements Document

## Introduction

The Interactive Identity Center Explorer is a terminal-based interactive tool that enables AWS administrators and DevOps engineers to navigate through their AWS Organizations structure while simultaneously viewing IAM Identity Center (SSO) access patterns. This feature combines organizational hierarchy with permission assignments, providing a unified view of who has access to what resources across the entire AWS organization.

## Glossary

- **Explorer**: The interactive terminal-based navigation system for browsing AWS Organizations and IAM Identity Center data
- **Navigation_Engine**: The component responsible for handling user input and managing navigation state
- **Data_Loader**: The component that reads and parses JSON files containing AWS resource data
- **Display_Manager**: The component that renders the hierarchical view using the rich library
- **OU**: Organizational Unit - a container for AWS accounts within AWS Organizations
- **Permission_Set**: An IAM Identity Center collection of permissions that can be assigned to users or groups
- **Account_Assignment**: A mapping between a permission set, a principal (user or group), and an AWS account
- **Principal**: Either a user or a group that can be assigned permissions
- **Breadcrumb**: A navigation indicator showing the current location in the hierarchy

## Requirements

### Requirement 1: Interactive Navigation System

**User Story:** As an AWS administrator, I want to navigate through my organization's structure using keyboard controls, so that I can efficiently explore the hierarchy without using a mouse.

#### Acceptance Criteria

1. WHEN the Explorer starts, THE Navigation_Engine SHALL display a list of root-level organizational units and accounts
2. WHEN a user presses arrow keys, THE Navigation_Engine SHALL move the selection indicator to the corresponding item
3. WHEN a user presses Enter on an OU, THE Navigation_Engine SHALL expand that OU and display its child OUs and accounts
4. WHEN a user presses Enter on an account, THE Display_Manager SHALL show the permission sets and access details for that account
5. WHEN a user selects a "Back" option, THE Navigation_Engine SHALL return to the previous navigation level
6. WHEN a user presses Escape or selects "Exit", THE Explorer SHALL terminate gracefully

### Requirement 2: Data Integration and Loading

**User Story:** As a DevOps engineer, I want the Explorer to automatically load and combine data from multiple JSON sources, so that I can see a complete view of my organization and access patterns.

#### Acceptance Criteria

1. WHEN the Explorer starts, THE Data_Loader SHALL read organizations_complete.json and parse the organizational structure
2. WHEN the Explorer starts, THE Data_Loader SHALL read account_assignments.json and parse permission set assignments
3. WHEN the Explorer starts, THE Data_Loader SHALL read groups.json and parse group membership information
4. WHEN all JSON files are loaded, THE Data_Loader SHALL create a unified data model linking accounts to permission sets to groups to users
5. IF any required JSON file is missing, THEN THE Data_Loader SHALL display a descriptive error message and terminate gracefully
6. IF a JSON file contains invalid data, THEN THE Data_Loader SHALL log the error and continue with partial data where possible

### Requirement 3: Hierarchical Display Rendering

**User Story:** As an AWS administrator, I want to see a clear visual hierarchy of my organization structure and access patterns, so that I can quickly understand the relationships between OUs, accounts, permission sets, groups, and users.

#### Acceptance Criteria

1. WHEN displaying organizational units, THE Display_Manager SHALL render them with tree-style indentation and branch characters
2. WHEN displaying accounts, THE Display_Manager SHALL show the account name and account ID in a formatted manner
3. WHEN displaying permission sets, THE Display_Manager SHALL use distinct icons or colors to differentiate them from other elements
4. WHEN displaying groups, THE Display_Manager SHALL show the group name with a group icon (👥)
5. WHEN displaying users, THE Display_Manager SHALL show the user email or username with a user icon (👤)
6. WHEN displaying direct user assignments, THE Display_Manager SHALL indicate that the assignment is not through a group
7. WHEN rendering any level of the hierarchy, THE Display_Manager SHALL use consistent indentation to show parent-child relationships

### Requirement 4: Account Access Details View

**User Story:** As a security auditor, I want to see all permission sets, groups, and users that have access to a specific account, so that I can audit access patterns and identify potential security issues.

#### Acceptance Criteria

1. WHEN a user selects an account, THE Display_Manager SHALL show all permission sets assigned to that account
2. FOR each permission set, THE Display_Manager SHALL show all groups that have that permission set
3. FOR each group, THE Display_Manager SHALL show all member users
4. WHEN an account has direct user assignments, THE Display_Manager SHALL show those users separately from group-based assignments
5. WHEN an account has no IAM Identity Center assignments, THE Display_Manager SHALL display a message indicating no assignments exist
6. WHEN displaying account details, THE Display_Manager SHALL show summary statistics including total permission sets, groups, and users

### Requirement 5: Command-Line Interface Integration

**User Story:** As a DevOps engineer, I want to launch the interactive explorer using a command-line flag, so that I can easily access this feature alongside other reverse_diagrams functionality.

#### Acceptance Criteria

1. WHEN a user runs "reverse_diagrams watch --explore", THE Explorer SHALL start in interactive mode
2. WHEN a user runs "reverse_diagrams watch -e", THE Explorer SHALL start in interactive mode (short flag)
3. WHEN a user provides "--json-dir" flag, THE Data_Loader SHALL read JSON files from the specified directory
4. IF no "--json-dir" flag is provided, THEN THE Data_Loader SHALL use the default "diagrams/json" directory
5. WHEN invalid command-line arguments are provided, THE Explorer SHALL display usage help and exit gracefully

### Requirement 6: Navigation State Management

**User Story:** As an AWS administrator, I want to see where I am in the navigation hierarchy at all times, so that I don't get lost while exploring deep organizational structures.

#### Acceptance Criteria

1. WHEN navigating through the hierarchy, THE Display_Manager SHALL show a breadcrumb trail indicating the current location
2. WHEN at the root level, THE Display_Manager SHALL show "Root" in the breadcrumb
3. WHEN inside an OU, THE Display_Manager SHALL show the path from root to current OU in the breadcrumb
4. WHEN viewing an account, THE Display_Manager SHALL show the full path including the account name in the breadcrumb
5. WHEN the breadcrumb exceeds display width, THE Display_Manager SHALL truncate it intelligently while preserving context

### Requirement 7: Error Handling and Edge Cases

**User Story:** As a DevOps engineer, I want the Explorer to handle missing or incomplete data gracefully, so that I can still use the tool even when some data is unavailable.

#### Acceptance Criteria

1. WHEN an OU has no child OUs or accounts, THE Display_Manager SHALL show a message indicating the OU is empty
2. WHEN an account has no permission set assignments, THE Display_Manager SHALL show a message indicating no IAM Identity Center access
3. WHEN a group has no members, THE Display_Manager SHALL show the group with an indication that it is empty
4. WHEN JSON data is missing expected fields, THE Data_Loader SHALL use default values and log a warning
5. IF the organizations_complete.json file is missing, THEN THE Explorer SHALL display an error and exit
6. IF the account_assignments.json file is missing, THEN THE Explorer SHALL display accounts without assignment information
7. IF the groups.json file is missing, THEN THE Explorer SHALL display group names without member details

### Requirement 8: Performance and Scalability

**User Story:** As an enterprise AWS administrator, I want the Explorer to handle large organizations with hundreds of accounts efficiently, so that navigation remains responsive.

#### Acceptance Criteria

1. WHEN loading JSON files, THE Data_Loader SHALL complete parsing within 5 seconds for organizations with up to 500 accounts
2. WHEN navigating between levels, THE Navigation_Engine SHALL respond to user input within 100 milliseconds
3. WHEN rendering account details, THE Display_Manager SHALL display the view within 200 milliseconds regardless of the number of assignments
4. WHEN the organization has more than 100 accounts in a single OU, THE Display_Manager SHALL implement pagination or scrolling
5. THE Explorer SHALL maintain memory usage below 100MB for organizations with up to 1000 accounts

### Requirement 9: User Experience and Accessibility

**User Story:** As an AWS administrator, I want clear visual feedback and intuitive controls, so that I can use the Explorer efficiently without referring to documentation.

#### Acceptance Criteria

1. WHEN the Explorer starts, THE Display_Manager SHALL show a help message with basic keyboard controls
2. WHEN displaying selectable items, THE Display_Manager SHALL use a clear selection indicator (arrow or highlight)
3. WHEN an action is in progress, THE Display_Manager SHALL show a loading indicator
4. WHEN displaying lists, THE Display_Manager SHALL use colors to differentiate between item types (OUs, accounts, permission sets, groups, users)
5. WHEN an error occurs, THE Display_Manager SHALL show the error message in a distinct color (red) with an error icon
6. THE Display_Manager SHALL support terminal widths from 80 to 200 characters

### Requirement 10: Data Model Consistency

**User Story:** As a developer maintaining the tool, I want a well-defined data model that represents the relationships between organizations, accounts, permission sets, groups, and users, so that the code is maintainable and extensible.

#### Acceptance Criteria

1. THE Data_Loader SHALL create a hierarchical data structure representing the organization tree
2. THE Data_Loader SHALL create a mapping from account IDs to permission set assignments
3. THE Data_Loader SHALL create a mapping from group IDs to user lists
4. THE Data_Loader SHALL validate that all account IDs in assignments exist in the organization structure
5. THE Data_Loader SHALL validate that all group IDs in assignments exist in the groups data
6. WHEN data validation fails, THE Data_Loader SHALL log warnings but continue processing valid data
