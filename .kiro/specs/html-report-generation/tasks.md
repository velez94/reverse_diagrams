# Implementation Plan: HTML Report Generation

## Overview

This implementation plan breaks down the HTML Report Generation feature into discrete, incremental coding tasks. Each task builds on previous work and includes references to specific requirements. The plan follows a bottom-up approach: first enhancing the HTML generator module, then integrating with the CLI, and finally adding comprehensive testing.

## Tasks

- [x] 1. Enhance HTML report generator with validation and error handling
  - Add JSON structure validation before processing
  - Implement custom exception types (JSONFileNotFoundError, JSONParseError, InvalidOutputPathError, HTMLWriteError)
  - Add descriptive error messages with file paths and suggested actions
  - Ensure graceful degradation when JSON files are missing
  - _Requirements: 3.5, 5.5, 8.1, 8.3, 8.5_

- [x] 1.1 Write property test for HTML content completeness
  - **Property 5: HTML Content Completeness**
  - **Validates: Requirements 3.1, 3.2, 3.3**

- [x] 1.2 Write property test for HTML self-containment
  - **Property 6: HTML Self-Containment**
  - **Validates: Requirements 4.5**

- [x] 1.3 Write property test for HTML structure validity
  - **Property 7: HTML Structure Validity**
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**

- [x] 2. Add CLI argument parsing for HTML report flags
  - Add `--html-report` flag to main argument parser
  - Add `--html-output` flag with path validation
  - Add `--html` flag to watch command subparser
  - Implement validation logic for flag combinations
  - Add helpful error messages for invalid flag usage
  - _Requirements: 1.1, 1.5, 2.1, 2.3, 5.2_

- [x] 2.1 Write unit tests for CLI argument parsing
  - Test `--html-report` flag recognition
  - Test `--html-output` with valid and invalid paths
  - Test invalid flag combinations
  - Test default behavior
  - _Requirements: 1.5, 2.3, 2.4_

- [x] 3. Implement HTML report orchestration function
  - Create `generate_html_report_cli()` function in reverse_diagrams.py
  - Implement output path determination (custom or default)
  - Add JSON file existence checking
  - Implement output directory creation with error handling
  - Integrate progress tracking with ProgressTracker
  - Add success message display with output path and section count
  - _Requirements: 1.1, 2.1, 2.2, 2.4, 7.1, 7.2, 7.4, 7.5_

- [x] 3.1 Write property test for custom output path handling
  - **Property 4: Custom Output Path Handling**
  - **Validates: Requirements 2.1, 2.2**

- [x] 3.2 Write property test for progress feedback completeness
  - **Property 11: Progress Feedback Completeness**
  - **Validates: Requirements 6.5, 7.1, 7.2, 7.4, 7.5**

- [x] 4. Integrate HTML generation into main CLI flow
  - Add conditional logic to check for `--html-report` flag
  - Implement standalone HTML generation (without diagram generation)
  - Implement combined generation (diagrams + HTML)
  - Add validation to ensure JSON files exist or are generated
  - Handle errors with descriptive messages
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 8.4_

- [x] 4.1 Write property test for HTML generation from available JSON files
  - **Property 1: HTML Generation from Available JSON Files**
  - **Validates: Requirements 1.1, 3.1, 3.2, 3.3, 3.4, 3.5**

- [x] 4.2 Write property test for HTML-only generation isolation
  - **Property 2: HTML-Only Generation Isolation**
  - **Validates: Requirements 1.2**

- [x] 4.3 Write property test for combined generation completeness
  - **Property 3: Combined Generation Completeness**
  - **Validates: Requirements 1.3**

- [x] 5. Checkpoint - Ensure basic HTML generation works
  - Test CLI with `--html-report` flag
  - Verify HTML file is created at default location
  - Verify HTML file is created at custom location with `--html-output`
  - Ensure all tests pass, ask the user if questions arise

- [x] 6. Implement watch command HTML generation
  - Extend watch command handler to support `--html` flag
  - Add logic to determine JSON file type from content
  - Implement HTML generation for each JSON file type
  - Integrate with existing watch command flow
  - Add progress tracking for watch mode HTML generation
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 6.1 Write property test for watch command HTML generation
  - **Property 10: Watch Command HTML Generation**
  - **Validates: Requirements 6.1, 6.2, 6.4**

- [x] 6.2 Write unit tests for watch command integration
  - Test watch command with `--html` flag for each JSON file type
  - Test output path handling in watch mode
  - Test progress indicators in watch mode
  - _Requirements: 6.3, 6.5_

- [x] 7. Implement offline generation capability
  - Ensure HTML generation does not instantiate AWS clients
  - Verify no AWS API calls are made during HTML generation
  - Add validation that HTML generation works without network access
  - Update documentation to clarify offline capability
  - _Requirements: 5.1, 5.3_

- [x] 7.1 Write property test for offline generation capability
  - **Property 8: Offline Generation Capability**
  - **Validates: Requirements 5.1**

- [x] 8. Enhance error handling and validation
  - Implement JSON validation before processing
  - Add file path validation before operations
  - Implement descriptive error messages for all error conditions
  - Add suggested actions to error messages
  - Ensure proper exit codes for different error types
  - _Requirements: 5.4, 5.5, 7.3, 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 8.1 Write property test for JSON validation before processing
  - **Property 9: JSON Validation Before Processing**
  - **Validates: Requirements 5.5, 8.5**

- [x] 8.2 Write property test for error message descriptiveness
  - **Property 12: Error Message Descriptiveness**
  - **Validates: Requirements 7.3, 8.1, 8.2, 8.3**

- [x] 8.3 Write unit tests for error handling
  - Test unreadable JSON files
  - Test malformed JSON
  - Test permission errors
  - Test missing files with helpful suggestions
  - _Requirements: 1.4, 2.5, 5.4, 8.1, 8.2, 8.3, 8.4_

- [x] 9. Add integration tests for end-to-end workflows
  - [x] 9.1 Create test fixtures for JSON files
    - Create valid organizations.json fixture
    - Create valid groups.json fixture
    - Create valid account_assignments.json fixture
    - Create malformed JSON fixtures for error testing
    - _Requirements: All_

  - [x] 9.2 Write integration test for standalone HTML generation
    - Test CLI execution with `--html-report` only
    - Verify HTML file creation and content
    - Verify no diagram files are created
    - _Requirements: 1.1, 1.2_

  - [x] 9.3 Write integration test for combined generation
    - Test CLI execution with `--html-report` and `-o` flags
    - Verify both diagram and HTML files are created
    - _Requirements: 1.3_

  - [x] 9.4 Write integration test for custom output paths
    - Test various output path scenarios
    - Test directory creation
    - Test path validation
    - _Requirements: 2.1, 2.2, 2.5_

  - [x] 9.5 Write integration test for watch command HTML generation
    - Test watch command with each JSON file type
    - Verify HTML generation and output
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 10. Final checkpoint - Comprehensive testing
  - Run all unit tests and verify 90%+ coverage
  - Run all property tests with 100+ iterations
  - Test all CLI flag combinations
  - Test error scenarios and verify error messages
  - Verify backward compatibility with existing functionality
  - Ensure all tests pass, ask the user if questions arise

- [x] 11. Update documentation and help text
  - Update CLI help text for new flags
  - Add examples to README for HTML report generation
  - Document offline generation capability
  - Add troubleshooting section for common errors
  - _Requirements: All_

## Notes

- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The HTML report generator module (`src/reports/html_report.py`) already exists and provides the core HTML generation functionality
- Focus is on CLI integration, validation, error handling, and comprehensive testing
- All tasks including tests are required for comprehensive implementation
