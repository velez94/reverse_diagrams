# Requirements Document

## Introduction

The HTML Report Generation feature extends the reverse_diagrams tool to produce interactive, visually appealing HTML reports from AWS infrastructure data. This feature enables users to generate standalone HTML documentation of their AWS Organizations structure, IAM Identity Center configurations, and account assignments without requiring diagram generation or console viewing.

## Glossary

- **CLI**: Command Line Interface - the primary user interaction method for reverse_diagrams
- **HTML_Report_Generator**: The system component responsible for creating HTML reports from JSON data
- **JSON_Data_File**: Structured data files containing AWS resource information (organizations.json, groups.json, account_assignments.json)
- **Report_Output_Path**: The file system location where HTML reports are saved
- **Watch_Command**: The existing CLI command that monitors and displays JSON data files
- **AWS_Organizations_Data**: Hierarchical structure of AWS accounts and organizational units
- **IAM_Identity_Center_Data**: User groups, members, and permission assignments
- **Account_Assignment**: The mapping between IAM Identity Center groups and AWS accounts with specific permission sets

## Requirements

### Requirement 1: HTML Report CLI Flag

**User Story:** As a DevOps engineer, I want to generate HTML reports via a CLI flag, so that I can create documentation without modifying existing workflows.

#### Acceptance Criteria

1. WHEN a user executes the CLI with `--html-report` flag, THE CLI SHALL generate an HTML report from available JSON data files
2. WHEN the `--html-report` flag is used without other generation flags, THE CLI SHALL only generate the HTML report without creating diagrams
3. WHEN the `--html-report` flag is combined with `-o` or `-i` flags, THE CLI SHALL generate both diagrams and HTML report
4. WHEN no JSON data files exist and `--html-report` is specified, THE CLI SHALL display an error message indicating missing data files
5. THE CLI SHALL validate the `--html-report` flag during argument parsing

### Requirement 2: Custom HTML Output Path

**User Story:** As a cloud architect, I want to specify where HTML reports are saved, so that I can organize reports according to my project structure.

#### Acceptance Criteria

1. WHEN a user provides `--html-output <path>` flag, THE CLI SHALL save the HTML report to the specified path
2. WHEN the specified output path directory does not exist, THE CLI SHALL create the directory structure
3. WHEN the `--html-output` flag is used without `--html-report`, THE CLI SHALL display an error message
4. WHEN no `--html-output` is specified, THE CLI SHALL save reports to `diagrams/reports/aws_report.html`
5. WHEN the output path is invalid or unwritable, THE CLI SHALL display a descriptive error message

### Requirement 3: HTML Report Content Structure

**User Story:** As an AWS administrator, I want comprehensive HTML reports with all infrastructure details, so that I can review and audit my AWS environment.

#### Acceptance Criteria

1. WHEN organizations.json exists, THE HTML_Report_Generator SHALL include AWS Organizations structure with account counts and organizational unit hierarchy
2. WHEN groups.json exists, THE HTML_Report_Generator SHALL include IAM Identity Center groups with member counts and user details
3. WHEN account_assignments.json exists, THE HTML_Report_Generator SHALL include account assignments with permission sets and target accounts
4. WHEN multiple JSON files exist, THE HTML_Report_Generator SHALL combine all data into a single comprehensive report
5. WHEN a JSON file is missing, THE HTML_Report_Generator SHALL include only available sections without failing

### Requirement 4: HTML Report Visual Design

**User Story:** As a user, I want visually appealing and professional HTML reports, so that I can share documentation with stakeholders.

#### Acceptance Criteria

1. THE HTML_Report_Generator SHALL create reports with modern CSS styling including gradient backgrounds and card layouts
2. THE HTML_Report_Generator SHALL ensure reports are responsive and viewable on different screen sizes
3. THE HTML_Report_Generator SHALL use color-coded badges to distinguish different resource types
4. THE HTML_Report_Generator SHALL include a report header with generation timestamp
5. THE HTML_Report_Generator SHALL create self-contained HTML files with embedded CSS and no external dependencies

### Requirement 5: Standalone HTML Generation

**User Story:** As a DevOps engineer, I want to generate HTML reports from existing JSON files, so that I can create documentation without re-querying AWS APIs.

#### Acceptance Criteria

1. WHEN JSON data files exist in the diagrams/json directory, THE HTML_Report_Generator SHALL generate reports without requiring AWS API calls
2. WHEN the `--html-report` flag is used alone, THE CLI SHALL not require AWS profile or region parameters
3. THE HTML_Report_Generator SHALL read JSON files from the standard diagrams/json directory
4. WHEN JSON files are malformed or invalid, THE HTML_Report_Generator SHALL display descriptive error messages
5. THE HTML_Report_Generator SHALL validate JSON file structure before processing

### Requirement 6: Watch Command Integration

**User Story:** As a user, I want to generate HTML reports through the watch command, so that I can create reports from any JSON file.

#### Acceptance Criteria

1. WHEN the watch command is executed with `--html` flag, THE CLI SHALL generate an HTML report from the specified JSON file
2. WHEN the watch command receives a JSON file path, THE CLI SHALL determine the appropriate report format based on file content
3. THE CLI SHALL support watch command HTML generation for organizations.json, groups.json, and account_assignments.json files
4. WHEN the watch command generates HTML, THE CLI SHALL save the report to the default or specified output path
5. THE CLI SHALL display progress indicators during HTML report generation in watch mode

### Requirement 7: Progress Tracking and User Feedback

**User Story:** As a user, I want clear feedback during HTML report generation, so that I know the operation is progressing successfully.

#### Acceptance Criteria

1. WHEN HTML report generation starts, THE CLI SHALL display a progress indicator using the existing progress tracking system
2. WHEN HTML report generation completes successfully, THE CLI SHALL display the output file path
3. WHEN HTML report generation encounters errors, THE CLI SHALL display descriptive error messages with suggested actions
4. THE CLI SHALL display the number of sections included in the generated report
5. THE CLI SHALL indicate which JSON data files were processed during report generation

### Requirement 8: Error Handling and Validation

**User Story:** As a user, I want clear error messages when HTML generation fails, so that I can troubleshoot issues quickly.

#### Acceptance Criteria

1. WHEN JSON files cannot be read, THE HTML_Report_Generator SHALL raise an exception with the file path and error reason
2. WHEN the output directory cannot be created, THE HTML_Report_Generator SHALL display a permission error message
3. WHEN JSON data is malformed, THE HTML_Report_Generator SHALL identify which file contains invalid data
4. WHEN no JSON data files exist, THE CLI SHALL suggest running data collection commands first
5. THE HTML_Report_Generator SHALL validate all file paths before attempting file operations

### Requirement 9: Integration with Existing Architecture

**User Story:** As a developer, I want HTML generation to integrate seamlessly with existing code, so that maintenance is straightforward.

#### Acceptance Criteria

1. THE CLI SHALL use the existing html_report.py module for HTML generation
2. THE CLI SHALL use the existing progress.py utilities for user feedback
3. THE CLI SHALL follow the existing error handling patterns and exception hierarchy
4. THE CLI SHALL save HTML reports using the existing file structure conventions
5. THE CLI SHALL integrate with the existing configuration management system
