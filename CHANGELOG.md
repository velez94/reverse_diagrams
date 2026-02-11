# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!-- insertion marker -->
## [v2.2.1](https://github.com/velez94/reverse_diagrams/releases/tag/v2.2.1) - 2026-02-10

<small>[Compare with v2.2.0](https://github.com/velez94/reverse_diagrams/compare/v2.2.0...v2.2.1)</small>

### Bug Fixes

- **Nested OU Support**: Fixed organizations_complete.json to properly handle nested Organizational Units at unlimited depth
  - Updated `create_organization_complete_map()` in `src/aws/describe_organization.py`
  - Updated `_create_organization_complete_map()` in `src/plugins/builtin/organizations_plugin.py`
  - Implemented recursive `build_ou_structure()` function for proper nesting
  - Previously only captured one level of OUs, now handles any depth
  - Accounts are now correctly placed in their respective nested OUs
  - Interactive Explorer can now navigate through deeply nested OU structures

### Testing

- Added 3 comprehensive tests for nested OU functionality
  - Test 4-level deep OU hierarchy
  - Test multiple independent branches
  - Test empty OUs
  - All tests passing

### Documentation

- Created NESTED_OU_BUG_FIX.md documenting the issue and solution

## [v2.2.0](https://github.com/velez94/reverse_diagrams/releases/tag/v2.2.0) - 2026-02-10

<small>[Compare with v2.1.1](https://github.com/velez94/reverse_diagrams/compare/v2.1.1...v2.2.0)</small>

### Features

- **Interactive Identity Center Explorer**: New interactive terminal-based explorer for AWS Organizations and IAM Identity Center
  - Added `--explore` / `-e` flag to watch command for launching interactive mode
  - Added `--json-dir` flag to specify custom JSON data directory
  - Navigate through organizational units and accounts hierarchically
  - View detailed IAM Identity Center assignments for any account
  - Explore groups, users, and permission sets interactively
  - Color-coded display with icons for different resource types
  - Keyboard navigation with arrow keys, search, and selection
  - Breadcrumb navigation showing current location in hierarchy
  - Summary statistics for permission sets, groups, and users
  - Graceful degradation when optional JSON files are missing
  - Comprehensive error handling with actionable messages
  - Handles large organizations (100+ accounts) with pagination support
  - Responsive terminal rendering (80-200 character widths)

### Testing

- Added 103 comprehensive tests for explorer feature
  - 23 property-based tests validating universal correctness properties
  - 75 unit tests for individual components
  - 5 integration tests for end-to-end workflows
  - Tests cover navigation, display, data loading, and error handling
  - Property tests use hypothesis library with 100+ iterations each

### Documentation

- Updated README.md with Interactive Identity Center Explorer section
- Added usage examples and keyboard shortcuts
- Documented graceful degradation behavior
- Added troubleshooting guide for common issues

## [v2.1.1](https://github.com/velez94/reverse_diagrams/releases/tag/v2.1.1) - 2026-02-05

<small>[Compare with v2.1.0](https://github.com/velez94/reverse_diagrams/compare/v2.1.0...v2.1.1)</small>

### Bug Fixes

- **Ambiguous Option Error**: Fixed argparse ambiguous option error with watch command
  - Renamed `--html` flag to `--generate-html` in watch subcommand
  - Resolved conflict with `--html-report` and `--html-output` flags
  - Updated all documentation and examples to use new flag name
  - Watch command now works without ambiguity errors

### Documentation

- Updated README with correct `--generate-html` flag usage
- Updated ORGANIZATIONS_WATCH_IMPLEMENTATION.md with new flag
- Added AMBIGUOUS_FLAG_FIX.md documenting the issue and solution

## [v2.1.0](https://github.com/velez94/reverse_diagrams/releases/tag/v2.1.0) - 2026-02-04

<small>[Compare with v2.0.0](https://github.com/velez94/reverse_diagrams/compare/v2.0.0...v2.1.0)</small>

### Features

- **HTML Report Generation**: Complete HTML report generation feature with standalone and combined modes
  - Added `--html-report` flag for generating HTML reports from JSON files
  - Added `--html-output` flag for custom HTML output paths
  - Added `--html` flag to watch command for HTML generation
  - Self-contained HTML reports with no external dependencies
  - Comprehensive validation and error handling with custom exceptions
  - Offline generation capability (no AWS API calls required)
- **Organizations Watch Command**: Implemented `-wo` (watch organizations) console view
  - Rich console output with organization overview, root accounts, and OUs
  - Supports both console view and HTML generation modes
  - Handles multiple data formats with fallback support
  - Color-coded panels with emoji icons for better visualization

### Testing

- Added 60+ comprehensive tests (unit, integration, property-based)
- Property-based testing with hypothesis for HTML report generation
- Integration tests for CLI workflows and watch commands
- Unit tests for organizations console view functionality

### Documentation

- Updated README with HTML report generation examples
- Added troubleshooting section for common issues
- Documented new CLI flags and usage patterns
- Created implementation guides for new features
## [v1.3.0](https://github.com/velez94/reverse_diagrams/releases/tag/v1.3.0) - 2024-02-03

<small>[Compare with v1.2.0](https://github.com/velez94/reverse_diagrams/compare/v1.2.0...v1.3.0)</small>

### Bug Fixes

- fix graph on demand ([e24481a](https://github.com/velez94/reverse_diagrams/commit/e24481a4acb04e1dcfbccfac1392f28d8c3b701f) by wilmar.velezl).
- get information organization complete just one level of netsted OUs ([a01d149](https://github.com/velez94/reverse_diagrams/commit/a01d14952f56d6a80526db6eaecbc8f859ad705f) by alejandro.velez).

### Features

- get organization info into json ([f108156](https://github.com/velez94/reverse_diagrams/commit/f1081560cbd6d4e45f3cefe546dae62b3b67be69) by alejandro.velez).

### Code Refactoring

- add interactive option to watch account assigments ([b57cfba](https://github.com/velez94/reverse_diagrams/commit/b57cfba9db5d2f5c0c809506a957da41ea61afe2) by wilmar.velezl).

### Docs

- update readme ([1a7a173](https://github.com/velez94/reverse_diagrams/commit/1a7a173642cec9bf08cdd56dbd3499eb70058e95) by alejandro.velez).

## [v1.2.0](https://github.com/velez94/reverse_diagrams/releases/tag/v1.2.0) - 2024-01-31

<small>[Compare with v1.1.2](https://github.com/velez94/reverse_diagrams/compare/v1.1.2...v1.2.0)</small>

### Bug Fixes

- update version ([57bdb14](https://github.com/velez94/reverse_diagrams/commit/57bdb143631616314fddecd43be3f1211fa387b3) by alejandro.velez).

### Features

- add watch subcommand ([a1844c3](https://github.com/velez94/reverse_diagrams/commit/a1844c3b114e3d3174618b5cd50e1d140e4dc5a2) by alejandro.velez).

### Docs

- update change log ([8616c15](https://github.com/velez94/reverse_diagrams/commit/8616c1575deff814ee50c5aec4b45c9279d4672e) by alejandro.velez).

## [v1.1.2](https://github.com/velez94/reverse_diagrams/releases/tag/v1.1.2) - 2024-01-31

<small>[Compare with v1.1.0](https://github.com/velez94/reverse_diagrams/compare/v1.1.0...v1.1.2)</small>

### Bug Fixes

- modify console view according to describe account assgnments information ([5214926](https://github.com/velez94/reverse_diagrams/commit/52149269bad5919fa1f32088774022e1b4d43e10) by wilmar.velezl).

### Docs

- update Readme.md ([0e020ac](https://github.com/velez94/reverse_diagrams/commit/0e020acf15522c5355617c014134a95ae0cd97a6) by alejandro.velez).

## [v1.1.0](https://github.com/velez94/reverse_diagrams/releases/tag/v1.1.0) - 2024-01-30

<small>[Compare with v1.0.4](https://github.com/velez94/reverse_diagrams/compare/v1.0.4...v1.1.0)</small>

### Bug Fixes

- optimize execution describe identity ([717a099](https://github.com/velez94/reverse_diagrams/commit/717a099c9e2b74fa1bc409b2fe651b6722bfe9ff) by alejandro.velez).

### Features

- add print to console pretty ([e23dbfb](https://github.com/velez94/reverse_diagrams/commit/e23dbfb2bd8719b4416f7edfb92ab5a52fe5471c) by wilmar.velezl).

### Docs

- update changelog ([1dce63d](https://github.com/velez94/reverse_diagrams/commit/1dce63d0bbfef2b6223ebddc1fe3de8866065506) by wilmar.velezl).
- run pre-commit ([143415f](https://github.com/velez94/reverse_diagrams/commit/143415f200b58cea4b5714b35d379aabcbeab7f4) by wilmar.velezl).

## [v1.0.4](https://github.com/velez94/reverse_diagrams/releases/tag/v1.0.4) - 2024-01-29

<small>[Compare with v1.0.2](https://github.com/velez94/reverse_diagrams/compare/v1.0.2...v1.0.4)</small>

### Bug Fixes

- optimize execution describe identity ([2db7868](https://github.com/velez94/reverse_diagrams/commit/2db7868647e002435d082616c1afa9900ffcf6e7) by alejandro.velez).

## [v1.0.2](https://github.com/velez94/reverse_diagrams/releases/tag/v1.0.2) - 2024-01-29

<small>[Compare with v1.0.1](https://github.com/velez94/reverse_diagrams/compare/v1.0.1...v1.0.2)</small>

### Bug Fixes

- repair describe organizations function ([a8e0f2b](https://github.com/velez94/reverse_diagrams/commit/a8e0f2b341bf0cb1d17576d2aa57f9a51f027463) by alejandro.velez).

### Code Refactoring

- refactor getting account assignments ([9c77a98](https://github.com/velez94/reverse_diagrams/commit/9c77a985e93ddd4a86158fda123752b18673c1a9) by alejandro.velez).

## [v1.0.1](https://github.com/velez94/reverse_diagrams/releases/tag/v1.0.1) - 2024-01-29

<small>[Compare with v1.0.0](https://github.com/velez94/reverse_diagrams/compare/v1.0.0...v1.0.1)</small>

### Code Refactoring

- refactor getting account assignments ([42f29cd](https://github.com/velez94/reverse_diagrams/commit/42f29cd131f356b871b2c2aed8f7a996ed114435) by alejandro.velez).

### Docs

- add changelog ([f57076c](https://github.com/velez94/reverse_diagrams/commit/f57076c0f8cf9cbdc9b2a286c6ef3ee553dc3818) by alejandro.velez).

## [v1.0.0](https://github.com/velez94/reverse_diagrams/releases/tag/v1.0.0) - 2024-01-29

<small>[Compare with v0.2.5](https://github.com/velez94/reverse_diagrams/compare/v0.2.5...v1.0.0)</small>

### Features

- v1.0.0 release beta ([8c2fcb2](https://github.com/velez94/reverse_diagrams/commit/8c2fcb253fc0bc4b5dbfdf292979d9fd63c3393f) by alejandro.velez).
- update license ([e6446f0](https://github.com/velez94/reverse_diagrams/commit/e6446f059cbfd52708f4f3fa5b0bbc33d7af5dae) by alejandro.velez).
- add workflow ([4800e02](https://github.com/velez94/reverse_diagrams/commit/4800e0215336b6e3d54be7dbc6f72b5608ed2847) by alejandro.velez).
- add pagination option to get group members ([79f26e7](https://github.com/velez94/reverse_diagrams/commit/79f26e7729655e2c0acc220d1daaa909b47e2b24) by wilmar.velezl).

## [v0.2.5](https://github.com/velez94/reverse_diagrams/releases/tag/v0.2.5) - 2023-01-30

<small>[Compare with v0.2.3](https://github.com/velez94/reverse_diagrams/compare/v0.2.3...v0.2.5)</small>

## [v0.2.3](https://github.com/velez94/reverse_diagrams/releases/tag/v0.2.3) - 2023-01-30

<small>[Compare with first commit](https://github.com/velez94/reverse_diagrams/compare/9ee05c383bf95a8f575e794e08b52672ad7c16cb...v0.2.3)</small>

## [v1.2.1](https://github.com/velez94/reverse_diagrams/releases/tag/v1.2.1) - 2024-01-31

<small>[Compare with v1.2.0](https://github.com/velez94/reverse_diagrams/compare/v1.2.0...v1.2.1)</small>

### Docs

- update readme ([4510b94](https://github.com/velez94/reverse_diagrams/commit/4510b948f8571dbd8bec1f82e7ceb57bea426dd7) by alejandro.velez).

## [v1.2.0](https://github.com/velez94/reverse_diagrams/releases/tag/v1.2.0) - 2024-01-31

<small>[Compare with v1.1.2](https://github.com/velez94/reverse_diagrams/compare/v1.1.2...v1.2.0)</small>

### Features

- add watch subcommand ([a1844c3](https://github.com/velez94/reverse_diagrams/commit/a1844c3b114e3d3174618b5cd50e1d140e4dc5a2) by alejandro.velez).

## [v1.1.2](https://github.com/velez94/reverse_diagrams/releases/tag/v1.1.2) - 2024-01-31

<small>[Compare with v1.1.0](https://github.com/velez94/reverse_diagrams/compare/v1.1.0...v1.1.2)</small>

### Bug Fixes

- modify console view according to describe account assgnments information ([5214926](https://github.com/velez94/reverse_diagrams/commit/52149269bad5919fa1f32088774022e1b4d43e10) by wilmar.velezl).

### Docs

- update Readme.md ([0e020ac](https://github.com/velez94/reverse_diagrams/commit/0e020acf15522c5355617c014134a95ae0cd97a6) by alejandro.velez).

## [v1.1.0](https://github.com/velez94/reverse_diagrams/releases/tag/v1.1.0) - 2024-01-30

<small>[Compare with v1.0.4](https://github.com/velez94/reverse_diagrams/compare/v1.0.4...v1.1.0)</small>

### Bug Fixes

- optimize execution describe identity ([717a099](https://github.com/velez94/reverse_diagrams/commit/717a099c9e2b74fa1bc409b2fe651b6722bfe9ff) by alejandro.velez).

### Features

- add print to console pretty ([e23dbfb](https://github.com/velez94/reverse_diagrams/commit/e23dbfb2bd8719b4416f7edfb92ab5a52fe5471c) by wilmar.velezl).

### Docs

- update changelog ([1dce63d](https://github.com/velez94/reverse_diagrams/commit/1dce63d0bbfef2b6223ebddc1fe3de8866065506) by wilmar.velezl).
- run pre-commit ([143415f](https://github.com/velez94/reverse_diagrams/commit/143415f200b58cea4b5714b35d379aabcbeab7f4) by wilmar.velezl).

## [v1.0.4](https://github.com/velez94/reverse_diagrams/releases/tag/v1.0.4) - 2024-01-29

<small>[Compare with v1.0.2](https://github.com/velez94/reverse_diagrams/compare/v1.0.2...v1.0.4)</small>

### Bug Fixes

- optimize execution describe identity ([2db7868](https://github.com/velez94/reverse_diagrams/commit/2db7868647e002435d082616c1afa9900ffcf6e7) by alejandro.velez).

## [v1.0.2](https://github.com/velez94/reverse_diagrams/releases/tag/v1.0.2) - 2024-01-29

<small>[Compare with v1.0.1](https://github.com/velez94/reverse_diagrams/compare/v1.0.1...v1.0.2)</small>

### Bug Fixes

- repair describe organizations function ([a8e0f2b](https://github.com/velez94/reverse_diagrams/commit/a8e0f2b341bf0cb1d17576d2aa57f9a51f027463) by alejandro.velez).

### Code Refactoring

- refactor getting account assignments ([9c77a98](https://github.com/velez94/reverse_diagrams/commit/9c77a985e93ddd4a86158fda123752b18673c1a9) by alejandro.velez).

## [v1.0.1](https://github.com/velez94/reverse_diagrams/releases/tag/v1.0.1) - 2024-01-29

<small>[Compare with v1.0.0](https://github.com/velez94/reverse_diagrams/compare/v1.0.0...v1.0.1)</small>

### Code Refactoring

- refactor getting account assignments ([42f29cd](https://github.com/velez94/reverse_diagrams/commit/42f29cd131f356b871b2c2aed8f7a996ed114435) by alejandro.velez).

### Docs

- add changelog ([f57076c](https://github.com/velez94/reverse_diagrams/commit/f57076c0f8cf9cbdc9b2a286c6ef3ee553dc3818) by alejandro.velez).

## [v1.0.0](https://github.com/velez94/reverse_diagrams/releases/tag/v1.0.0) - 2024-01-29

<small>[Compare with v0.2.5](https://github.com/velez94/reverse_diagrams/compare/v0.2.5...v1.0.0)</small>

### Features

- v1.0.0 release beta ([8c2fcb2](https://github.com/velez94/reverse_diagrams/commit/8c2fcb253fc0bc4b5dbfdf292979d9fd63c3393f) by alejandro.velez).
- update license ([e6446f0](https://github.com/velez94/reverse_diagrams/commit/e6446f059cbfd52708f4f3fa5b0bbc33d7af5dae) by alejandro.velez).
- add workflow ([4800e02](https://github.com/velez94/reverse_diagrams/commit/4800e0215336b6e3d54be7dbc6f72b5608ed2847) by alejandro.velez).
- add pagination option to get group members ([79f26e7](https://github.com/velez94/reverse_diagrams/commit/79f26e7729655e2c0acc220d1daaa909b47e2b24) by wilmar.velezl).

## [v0.2.5](https://github.com/velez94/reverse_diagrams/releases/tag/v0.2.5) - 2023-01-30

<small>[Compare with v0.2.3](https://github.com/velez94/reverse_diagrams/compare/v0.2.3...v0.2.5)</small>

## [v0.2.3](https://github.com/velez94/reverse_diagrams/releases/tag/v0.2.3) - 2023-01-30

<small>[Compare with first commit](https://github.com/velez94/reverse_diagrams/compare/9ee05c383bf95a8f575e794e08b52672ad7c16cb...v0.2.3)</small>
