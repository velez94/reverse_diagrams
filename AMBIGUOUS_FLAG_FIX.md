# Ambiguous Flag Fix - v2.1.0

## Issue
The `--html` flag in the watch subcommand was causing an "ambiguous option" error because argparse couldn't distinguish between:
- `--html-report` (main command)
- `--html-output` (main command)
- `--html` (watch subcommand)

When users tried to use `--html` with the watch command, argparse would throw an error because it matched multiple options.

## Root Cause
Argparse performs prefix matching on long options. When a user types `--html`, it tries to match against all available options:
- `--html` could match `--html-report`
- `--html` could match `--html-output`
- `--html` could match the watch command's `--html`

This creates ambiguity that argparse cannot resolve.

## Solution
Renamed the watch subcommand's `--html` flag to `--generate-html` to eliminate the ambiguity.

### Changes Made

1. **src/reverse_diagrams.py**
   - Changed `--html` to `--generate-html` in watch subcommand argument parser
   - Updated help text to reflect new flag name

2. **src/reports/console_view.py**
   - Updated reference from `args.html` to `args.generate_html`

3. **README.md**
   - Updated all examples using `--html` with watch command to use `--generate-html`

4. **ORGANIZATIONS_WATCH_IMPLEMENTATION.md**
   - Updated documentation to reference `--generate-html` instead of `--html`

## Usage Examples

### Before (Caused Error)
```bash
# This would fail with "ambiguous option: --html"
reverse_diagrams watch -wo diagrams/json/organizations.json --html
```

### After (Works Correctly)
```bash
# Console view (default)
reverse_diagrams watch -wo diagrams/json/organizations.json

# HTML generation
reverse_diagrams watch -wo diagrams/json/organizations.json --generate-html

# Custom output
reverse_diagrams watch -wo diagrams/json/organizations.json --generate-html --html-output reports/org.html
```

## Main Command Flags (Unchanged)
These flags remain the same and work without ambiguity:
```bash
# Generate HTML report from existing JSON data
reverse_diagrams --html-report

# Generate HTML report with custom output path
reverse_diagrams --html-report --html-output reports/my_report.html

# Generate diagrams AND HTML report
reverse_diagrams -o -i --html-report
```

## Testing
Verified the fix by running:
```bash
# Check watch command help (no errors)
python3 -m src.reverse_diagrams watch --help

# Check main command help (no conflicts)
python3 -m src.reverse_diagrams --help
```

Both commands now work without ambiguity errors.

## Commits
- Initial release: `feat: Add HTML report generation and organizations watch command (v2.1.0)` (commit b27c188)
- Bug fix: `fix: Rename --html to --generate-html in watch command to avoid ambiguity` (commit 1af86d4)

## Version
Fixed in v2.1.0 (post-release hotfix)
