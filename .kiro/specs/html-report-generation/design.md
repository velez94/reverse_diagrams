# Design Document: HTML Report Generation

## Overview

The HTML Report Generation feature adds a new output format to the reverse_diagrams tool, enabling users to create interactive, visually appealing HTML reports from AWS infrastructure data. This feature leverages the existing `html_report.py` module and integrates seamlessly with the current CLI architecture.

The design focuses on:
- Minimal changes to existing CLI argument parsing
- Reuse of existing HTML generation logic
- Consistent error handling and progress tracking
- Flexible report generation from JSON files or data objects
- Integration with both main CLI and watch command

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI Entry Point                          │
│                  (reverse_diagrams.py)                       │
│  - Parse --html-report and --html-output flags              │
│  - Validate arguments                                        │
│  - Coordinate HTML generation workflow                       │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ├──────────────────────────────────────┐
                  │                                      │
                  ▼                                      ▼
┌─────────────────────────────────┐    ┌────────────────────────────────┐
│   HTML Report Generator         │    │   Progress Tracker             │
│   (html_report.py)              │    │   (utils/progress.py)          │
│                                 │    │                                │
│ - generate_report_from_files()  │    │ - Display progress indicators  │
│ - generate_html_report()        │    │ - Show success/error messages  │
│ - Read JSON data files          │    │ - Track operation status       │
│ - Generate HTML with CSS        │    └────────────────────────────────┘
│ - Write output file             │
└─────────────────┬───────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                   File System                                │
│                                                              │
│  Input:  diagrams/json/*.json                               │
│  Output: diagrams/reports/aws_report.html (default)         │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

**Main CLI Flow:**
1. User executes CLI with `--html-report` flag
2. CLI validates arguments and checks for required flags
3. CLI determines if JSON files exist or need to be generated
4. If diagrams are requested (-o, -i), generate them first
5. CLI calls HTML report generator with appropriate parameters
6. Progress tracker displays generation status
7. HTML file is written to output path
8. Success message displays output location

**Watch Command Flow:**
1. User executes watch command with `--html` flag and JSON file path
2. CLI validates JSON file exists and is readable
3. CLI determines report type based on JSON file content
4. CLI calls HTML report generator with file path
5. HTML report is generated and saved
6. Success message displays output location

## Components and Interfaces

### 1. CLI Argument Parser Extension

**Location:** `src/reverse_diagrams.py`

**New Arguments:**
```python
parser.add_argument(
    '--html-report',
    action='store_true',
    help='Generate HTML report from JSON data files'
)

parser.add_argument(
    '--html-output',
    type=str,
    metavar='PATH',
    help='Custom output path for HTML report (default: diagrams/reports/aws_report.html)'
)
```

**Watch Command Extension:**
```python
watch_parser.add_argument(
    '--html',
    action='store_true',
    help='Generate HTML report from the specified JSON file'
)
```

**Validation Logic:**
- If `--html-output` is provided without `--html-report`, raise error
- If `--html-report` is used alone, AWS profile/region are optional
- If `--html-report` is combined with `-o` or `-i`, validate AWS credentials

### 2. HTML Report Orchestration

**Location:** `src/reverse_diagrams.py` (new function)

**Function Signature:**
```python
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
        FileNotFoundError: If no JSON data files exist
        PermissionError: If output directory is not writable
        ValueError: If JSON files are malformed
    """
```

**Implementation Logic:**
1. Determine output path (custom or default)
2. Check if JSON data files exist
3. Create output directory if needed
4. Call `generate_report_from_files()` with progress tracking
5. Display success message with output path
6. Handle errors with descriptive messages

### 3. HTML Report Generator Interface

**Location:** `src/reports/html_report.py` (existing module)

**Primary Function:**
```python
def generate_report_from_files(
    org_file: Optional[str] = None,
    groups_file: Optional[str] = None,
    assignments_file: Optional[str] = None,
    output_path: str = "diagrams/reports/aws_report.html"
) -> str:
    """
    Generate HTML report from JSON data files.
    
    Args:
        org_file: Path to organizations.json
        groups_file: Path to groups.json
        assignments_file: Path to account_assignments.json
        output_path: Where to save the HTML report
        
    Returns:
        Path to generated HTML file
        
    Raises:
        FileNotFoundError: If specified files don't exist
        json.JSONDecodeError: If JSON files are malformed
        PermissionError: If output path is not writable
    """
```

**Secondary Function:**
```python
def generate_html_report(
    org_data: Optional[Dict] = None,
    groups_data: Optional[List] = None,
    assignments_data: Optional[List] = None,
    output_path: str = "diagrams/reports/aws_report.html"
) -> str:
    """
    Generate HTML report from data objects.
    
    Args:
        org_data: AWS Organizations data dictionary
        groups_data: List of IAM Identity Center groups
        assignments_data: List of account assignments
        output_path: Where to save the HTML report
        
    Returns:
        Path to generated HTML file
    """
```

### 4. Progress Tracking Integration

**Location:** `src/utils/progress.py` (existing module)

**Usage Pattern:**
```python
from utils.progress import ProgressTracker

with ProgressTracker("Generating HTML report") as progress:
    progress.update("Reading JSON data files...")
    # Read files
    
    progress.update("Processing AWS Organizations data...")
    # Process org data
    
    progress.update("Processing IAM Identity Center data...")
    # Process IAM data
    
    progress.update("Writing HTML report...")
    # Write file
    
    progress.success(f"HTML report saved to: {output_path}")
```

### 5. Watch Command Integration

**Location:** `src/reverse_diagrams.py` (watch command handler)

**Enhanced Watch Function:**
```python
def handle_watch_command(args):
    """Handle watch command with optional HTML generation."""
    if args.html:
        # Determine JSON file type
        json_file = args.watch_assignments or args.watch_groups or args.watch_orgs
        
        # Generate HTML report
        output_path = args.html_output or "diagrams/reports/aws_report.html"
        
        # Call appropriate HTML generator based on file type
        generate_html_from_watch(json_file, output_path)
    else:
        # Existing console view logic
        display_console_view(args)
```

## Data Models

### JSON File Structure

**organizations.json:**
```python
{
    "Id": str,              # Organization ID
    "Arn": str,             # Organization ARN
    "MasterAccountId": str, # Management account ID
    "Roots": [              # Root organizational units
        {
            "Id": str,
            "Name": str,
            "Arn": str,
            "Children": [...]  # Nested OUs
        }
    ],
    "Accounts": [           # All accounts
        {
            "Id": str,
            "Name": str,
            "Email": str,
            "Status": str,
            "JoinedTimestamp": str
        }
    ]
}
```

**groups.json:**
```python
[
    {
        "GroupId": str,
        "DisplayName": str,
        "Description": str,
        "Members": [
            {
                "UserId": str,
                "UserName": str,
                "DisplayName": str,
                "Email": str
            }
        ]
    }
]
```

**account_assignments.json:**
```python
[
    {
        "AccountId": str,
        "PermissionSetArn": str,
        "PermissionSetName": str,
        "PrincipalType": str,  # "GROUP" or "USER"
        "PrincipalId": str,
        "PrincipalName": str
    }
]
```

### HTML Report Structure

**Report Sections:**
1. **Header Section**
   - Report title
   - Generation timestamp
   - Summary statistics

2. **AWS Organizations Section** (if organizations.json exists)
   - Organization overview
   - Account count and status
   - Organizational unit hierarchy
   - Account details table

3. **IAM Identity Center Groups Section** (if groups.json exists)
   - Group count
   - Groups with member details
   - User information

4. **Account Assignments Section** (if account_assignments.json exists)
   - Assignment count
   - Permission sets
   - Group-to-account mappings
   - Assignment details table

**CSS Styling:**
- Gradient background (linear-gradient)
- Card-based layout with shadows
- Color-coded badges for resource types
- Responsive grid layout
- Modern typography
- Self-contained (no external dependencies)

## Correctness Properties


*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: HTML Generation from Available JSON Files

*For any* combination of JSON data files (organizations.json, groups.json, account_assignments.json) that exist in the diagrams/json directory, when the CLI is executed with `--html-report`, the generated HTML file should contain sections corresponding to each available JSON file with the appropriate data rendered.

**Validates: Requirements 1.1, 3.1, 3.2, 3.3, 3.4, 3.5**

### Property 2: HTML-Only Generation Isolation

*For any* execution of the CLI with only the `--html-report` flag (without `-o` or `-i` flags), the diagrams/code and diagrams/images directories should remain unchanged, and only the HTML report file should be created or modified.

**Validates: Requirements 1.2**

### Property 3: Combined Generation Completeness

*For any* execution of the CLI with `--html-report` combined with `-o` or `-i` flags, both the diagram outputs (Python code and/or PNG images) and the HTML report should be generated successfully.

**Validates: Requirements 1.3**

### Property 4: Custom Output Path Handling

*For any* valid file system path provided via `--html-output`, the HTML report should be saved to exactly that path, creating any necessary parent directories, and the file should be readable and contain valid HTML.

**Validates: Requirements 2.1, 2.2**

### Property 5: HTML Content Completeness

*For any* valid JSON data file (organizations, groups, or assignments), the generated HTML should include all key information from that file, including counts, names, IDs, and hierarchical relationships where applicable.

**Validates: Requirements 3.1, 3.2, 3.3**

### Property 6: HTML Self-Containment

*For any* generated HTML report, the file should contain no external resource references (no external CSS links, no external JavaScript, no external images), and should be viewable in a browser without network access.

**Validates: Requirements 4.5**

### Property 7: HTML Structure Validity

*For any* generated HTML report, the file should contain a header with timestamp, modern CSS styling (including gradients and card layouts), color-coded badges for resource types, and responsive design elements.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4**

### Property 8: Offline Generation Capability

*For any* execution of HTML report generation from existing JSON files, no AWS client should be instantiated, no AWS API calls should be made, and the operation should complete successfully without network access.

**Validates: Requirements 5.1**

### Property 9: JSON Validation Before Processing

*For any* JSON file provided to the HTML generator, the file structure should be validated before any HTML generation begins, and invalid structures should result in descriptive error messages that identify the problematic file.

**Validates: Requirements 5.5, 8.5**

### Property 10: Watch Command HTML Generation

*For any* valid JSON file path provided to the watch command with the `--html` flag, an HTML report should be generated with content appropriate to the JSON file type (organizations, groups, or assignments), and saved to the specified or default output path.

**Validates: Requirements 6.1, 6.2, 6.4**

### Property 11: Progress Feedback Completeness

*For any* HTML report generation operation, the CLI should display progress indicators during generation, display the output file path upon success, display the number of sections included, and list which JSON files were processed.

**Validates: Requirements 6.5, 7.1, 7.2, 7.4, 7.5**

### Property 12: Error Message Descriptiveness

*For any* error condition during HTML generation (unreadable files, permission errors, malformed JSON, missing files), the error message should include the specific file path or resource involved, the nature of the error, and a suggested action for resolution.

**Validates: Requirements 7.3, 8.1, 8.2, 8.3**

## Error Handling

### Error Categories

**1. Input Validation Errors**
- Missing JSON data files when `--html-report` is specified
- Invalid flag combinations (e.g., `--html-output` without `--html-report`)
- Invalid output paths or file names
- Malformed JSON file structure

**Error Response:**
- Display clear error message identifying the issue
- Suggest corrective action (e.g., "Run with -o flag to generate organizations data first")
- Exit with non-zero status code
- Do not create partial or empty HTML files

**2. File System Errors**
- JSON files cannot be read (permissions, corruption)
- Output directory cannot be created (permissions)
- Output file cannot be written (disk full, permissions)

**Error Response:**
- Display error with specific file path and system error message
- Suggest permission or disk space checks
- Exit with non-zero status code
- Clean up any partial files created

**3. Data Processing Errors**
- JSON parsing failures
- Unexpected JSON structure
- Missing required fields in JSON data

**Error Response:**
- Identify which JSON file contains the error
- Display the specific parsing error or missing field
- Suggest regenerating the JSON file
- Exit with non-zero status code

**4. Integration Errors**
- HTML report module import failures
- Progress tracker initialization failures
- Configuration system errors

**Error Response:**
- Display technical error details for debugging
- Suggest checking installation integrity
- Exit with non-zero status code

### Error Handling Strategy

**Fail Fast Principle:**
- Validate all inputs before starting generation
- Check file existence and readability upfront
- Verify output path writability before processing

**Graceful Degradation:**
- If one JSON file is missing, generate report with available data
- If optional sections fail, continue with remaining sections
- Log warnings for non-critical issues

**User-Friendly Messages:**
- Avoid technical jargon in error messages
- Provide actionable suggestions
- Include relevant file paths and context
- Use consistent error message format

### Exception Hierarchy

```python
# Existing exceptions from aws/exceptions.py
AWSException
├── AWSAuthenticationError
├── AWSPermissionError
└── AWSResourceNotFoundError

# New exceptions for HTML generation
HTMLGenerationError (base class)
├── JSONFileNotFoundError
├── JSONParseError
├── InvalidOutputPathError
└── HTMLWriteError
```

## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests to ensure comprehensive coverage:

**Unit Tests** focus on:
- Specific examples of CLI flag combinations
- Edge cases like missing files or invalid paths
- Error conditions and exception handling
- Integration points between CLI and HTML generator
- Default behavior (e.g., default output path)

**Property-Based Tests** focus on:
- Universal properties across all valid inputs
- HTML generation from random JSON data structures
- Path handling across different file system structures
- Content completeness across various data combinations
- HTML validity and structure across all generated reports

Together, these approaches provide comprehensive coverage: unit tests catch concrete bugs and validate specific scenarios, while property tests verify general correctness across a wide range of inputs.

### Property-Based Testing Configuration

**Testing Library:** Use `hypothesis` for Python property-based testing

**Test Configuration:**
- Minimum 100 iterations per property test (due to randomization)
- Each property test must reference its design document property
- Tag format: `# Feature: html-report-generation, Property {number}: {property_text}`

**Example Property Test Structure:**
```python
from hypothesis import given, strategies as st
import pytest

@given(
    org_data=st.dictionaries(
        keys=st.text(),
        values=st.one_of(st.text(), st.integers(), st.lists(st.text()))
    )
)
@pytest.mark.property_test
def test_html_content_completeness(org_data):
    """
    Feature: html-report-generation
    Property 5: HTML Content Completeness
    
    For any valid JSON data file, the generated HTML should include
    all key information from that file.
    """
    # Generate HTML from random org data
    html = generate_html_report(org_data=org_data)
    
    # Verify all keys from org_data appear in HTML
    for key in org_data.keys():
        assert key in html or str(org_data[key]) in html
```

### Unit Testing Strategy

**Test Categories:**

1. **CLI Argument Parsing Tests**
   - Test `--html-report` flag is recognized
   - Test `--html-output` with valid paths
   - Test invalid flag combinations raise errors
   - Test default output path behavior

2. **HTML Generation Tests**
   - Test HTML generation from each JSON file type
   - Test HTML generation with missing files
   - Test HTML generation with malformed JSON
   - Test HTML output contains expected sections

3. **File System Tests**
   - Test directory creation for output paths
   - Test handling of unwritable paths
   - Test handling of unreadable JSON files
   - Test cleanup on errors

4. **Integration Tests**
   - Test end-to-end CLI execution with `--html-report`
   - Test watch command with `--html` flag
   - Test combined diagram and HTML generation
   - Test progress tracking integration

5. **Error Handling Tests**
   - Test each error condition produces correct error message
   - Test error messages include file paths
   - Test error messages include suggested actions
   - Test proper exit codes on errors

### Test Data Strategy

**Mock JSON Files:**
- Create fixture files for each JSON type
- Include valid, minimal, and maximal examples
- Include malformed JSON for error testing
- Include edge cases (empty arrays, missing fields)

**Temporary File System:**
- Use pytest's `tmp_path` fixture for isolated testing
- Create temporary JSON and output directories
- Clean up after each test
- Test with various permission scenarios

### Coverage Goals

- Minimum 90% code coverage for new CLI code
- 100% coverage for error handling paths
- All properties implemented as property-based tests
- All edge cases covered by unit tests

## Implementation Notes

### Integration Points

**1. CLI Entry Point (`src/reverse_diagrams.py`)**
- Add argument parsing for new flags
- Add validation logic for flag combinations
- Add orchestration function for HTML generation
- Integrate with existing error handling

**2. HTML Report Module (`src/reports/html_report.py`)**
- Already exists with required functions
- May need minor enhancements for error handling
- Should validate JSON structure before processing
- Should use consistent exception types

**3. Progress Tracking (`src/utils/progress.py`)**
- Use existing ProgressTracker context manager
- Display progress during file reading and HTML generation
- Show success message with output path
- Show section count and processed files

**4. Watch Command**
- Extend existing watch command parser
- Add HTML generation option
- Determine report type from JSON content
- Reuse main HTML generation logic

### File System Conventions

**Input Files:**
- Default location: `diagrams/json/`
- Expected files: `organizations.json`, `groups.json`, `account_assignments.json`
- Files are optional (graceful degradation)

**Output Files:**
- Default location: `diagrams/reports/aws_report.html`
- Custom location via `--html-output` flag
- Create parent directories as needed
- Overwrite existing files with confirmation

### Performance Considerations

**File Reading:**
- Read JSON files sequentially (not performance-critical)
- Use streaming for large files if needed
- Cache parsed JSON in memory during generation

**HTML Generation:**
- Generate HTML in memory before writing
- Write file atomically (write to temp, then rename)
- Use buffered I/O for large reports

**Progress Feedback:**
- Update progress at key milestones
- Avoid excessive progress updates
- Keep UI responsive

### Backward Compatibility

**Existing Functionality:**
- No changes to existing diagram generation
- No changes to existing watch command console view
- No changes to existing JSON file formats
- No changes to existing CLI flags

**New Functionality:**
- New flags are optional (backward compatible)
- HTML generation is opt-in
- Existing workflows continue to work unchanged

### Future Enhancements

**Potential Additions:**
- Interactive HTML with JavaScript (filtering, sorting)
- Multiple report templates (detailed, summary, executive)
- PDF export from HTML
- Report scheduling and automation
- Comparison reports (diff between two time periods)
- Custom branding and styling options
