# Version 2.1.1 Release Summary

## Release Information
- **Version**: v2.1.1
- **Release Date**: 2026-02-05
- **Release Type**: Patch (Bug Fix)
- **Previous Version**: v2.1.0

## What Changed

### Bug Fix: Ambiguous Option Error
Fixed a critical bug where the `--html` flag in the watch subcommand was causing an "ambiguous option" error due to conflicts with the main command's `--html-report` and `--html-output` flags.

**Solution**: Renamed the watch subcommand's `--html` flag to `--generate-html` to eliminate ambiguity.

## Files Modified

1. **src/version.py**
   - Updated version from "2.1.0" to "2.1.1"

2. **src/reverse_diagrams.py**
   - Changed `--html` to `--generate-html` in watch subcommand
   - Updated help text

3. **src/reports/console_view.py**
   - Updated reference from `args.html` to `args.generate_html`

4. **README.md**
   - Updated all watch command examples to use `--generate-html`

5. **ORGANIZATIONS_WATCH_IMPLEMENTATION.md**
   - Updated documentation with new flag name

6. **CHANGELOG.md**
   - Added v2.1.1 release notes

7. **AMBIGUOUS_FLAG_FIX.md** (New)
   - Detailed documentation of the issue and fix

## Usage Changes

### Before (v2.1.0 - Broken)
```bash
# This caused "ambiguous option: --html" error
reverse_diagrams watch -wo diagrams/json/organizations.json --html
```

### After (v2.1.1 - Fixed)
```bash
# Console view (default)
reverse_diagrams watch -wo diagrams/json/organizations.json

# HTML generation
reverse_diagrams watch -wo diagrams/json/organizations.json --generate-html

# Custom output path
reverse_diagrams watch -wo diagrams/json/organizations.json --generate-html --html-output reports/org.html
```

## Main Command (Unchanged)
The main command flags remain the same and work correctly:
```bash
# Generate HTML report from existing JSON
reverse_diagrams --html-report

# Custom output path
reverse_diagrams --html-report --html-output reports/my_report.html

# Combined with diagram generation
reverse_diagrams -o -i --html-report
```

## Git Commits

1. **v2.1.0 Release** (commit b27c188)
   - Tag: v2.1.0
   - Initial release with HTML report generation and organizations watch command

2. **Bug Fix** (commit 1af86d4)
   - Fixed ambiguous option error
   - Renamed `--html` to `--generate-html`

3. **Version Bump** (commit 3641618)
   - Tag: v2.1.1
   - Updated version to 2.1.1
   - Updated CHANGELOG
   - Added documentation

## Testing

Verified the fix works correctly:
```bash
# Watch command help (no errors)
python3 -m src.reverse_diagrams watch --help

# Main command help (no conflicts)
python3 -m src.reverse_diagrams --help
```

Both commands now work without ambiguity errors.

## Impact

**Breaking Change**: Users who were attempting to use `--html` with the watch command (which was broken in v2.1.0) will need to update to `--generate-html`.

**Migration**: Simply replace `--html` with `--generate-html` in watch commands:
```bash
# Old (broken)
reverse_diagrams watch -wo file.json --html

# New (working)
reverse_diagrams watch -wo file.json --generate-html
```

## Repository

- **GitHub**: https://github.com/velez94/reverse_diagrams
- **Tag**: v2.1.1
- **Compare**: https://github.com/velez94/reverse_diagrams/compare/v2.1.0...v2.1.1

## Next Steps

Users should upgrade to v2.1.1 to get the bug fix:
```bash
pip install --upgrade reverse_diagrams
```

## Summary

This patch release fixes a critical bug that prevented the watch command's HTML generation feature from working. The fix is minimal and focused, changing only the flag name to avoid argparse ambiguity. All functionality remains the same, just with a clearer, non-ambiguous flag name.
