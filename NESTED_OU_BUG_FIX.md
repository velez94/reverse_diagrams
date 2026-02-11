# Nested OU Bug Fix

## Issue Description

The `organizations_complete.json` file was only capturing one level of nested Organizational Units (OUs), even though AWS Organizations supports unlimited nesting depth. The `nestedOus` field was always empty, regardless of the actual OU hierarchy.

## Root Cause

The `create_organization_complete_map()` function in both:
- `src/aws/describe_organization.py`
- `src/plugins/builtin/organizations_plugin.py`

Was only processing OUs that had a direct ROOT parent, and never recursively building the nested OU structure.

### Original Code Issue

```python
# Only added OUs with ROOT parent
for ou in organizational_units:
    for parent in ou.get("Parents", []):
        if parent["Type"] == "ROOT":
            organizations_complete["organizationalUnits"][ou["Name"]] = {
                "Id": ou["Id"],
                "Name": ou["Name"],
                "accounts": {},
                "nestedOus": {},  # Always empty!
            }
```

## Solution

Implemented a recursive `build_ou_structure()` function that:

1. **Creates lookup dictionaries** for efficient access to OUs and accounts by parent ID
2. **Recursively builds OU structure** by:
   - Adding accounts directly under each OU
   - Finding child OUs and recursively building their structures
   - Properly nesting child OUs under their parents
3. **Handles unlimited nesting depth** - works with any level of OU hierarchy

### New Code Structure

```python
def build_ou_structure(ou_id: str) -> Dict[str, Any]:
    """Recursively build OU structure with nested OUs and accounts."""
    ou = ou_by_id.get(ou_id)
    if not ou:
        return {}
    
    ou_structure = {
        "Id": ou["Id"],
        "Name": ou["Name"],
        "accounts": {},
        "nestedOus": {},
    }
    
    # Add accounts directly under this OU
    if ou_id in accounts_by_parent:
        for account in accounts_by_parent[ou_id]:
            ou_structure["accounts"][account["name"]] = {
                "account": account["account"],
                "name": account["name"]
            }
    
    # Find and add nested OUs (recursive)
    for child_ou in organizational_units:
        for parent in child_ou.get("Parents", []):
            if parent["Type"] == "ORGANIZATIONAL_UNIT" and parent["Id"] == ou_id:
                child_structure = build_ou_structure(child_ou["Id"])
                if child_structure:
                    ou_structure["nestedOus"][child_ou["Name"]] = child_structure
    
    return ou_structure
```

## Files Modified

1. **src/aws/describe_organization.py**
   - Updated `create_organization_complete_map()` function
   - Added recursive `build_ou_structure()` helper function

2. **src/plugins/builtin/organizations_plugin.py**
   - Updated `_create_organization_complete_map()` method
   - Added recursive `build_ou_structure()` helper function

3. **tests/unit/test_nested_ou_generation.py** (NEW)
   - Added comprehensive tests for nested OU functionality
   - Tests 3+ levels of nesting
   - Tests multiple branches
   - Tests empty OUs

## Testing

Created 3 comprehensive tests:

### 1. test_nested_ou_structure
Tests a 4-level deep OU hierarchy:
- Root → Root OU → Level 1 OU → Level 2 OU → Level 3 OU
- Verifies accounts are correctly placed at each level
- Verifies nested structure is properly maintained

### 2. test_multiple_nested_branches
Tests multiple independent branches:
- Branch 1 with nested child
- Branch 2 with nested child
- Verifies both branches are independent and correctly structured

### 3. test_empty_nested_ous
Tests OUs with no children:
- Verifies empty `nestedOus` dict
- Verifies empty `accounts` dict

**All tests passing:** ✅

## Impact

### Before Fix
```json
{
  "organizationalUnits": {
    "Root OU": {
      "Id": "ou-root-1",
      "Name": "Root OU",
      "accounts": {},
      "nestedOus": {}  // Always empty!
    }
  }
}
```

### After Fix
```json
{
  "organizationalUnits": {
    "Root OU": {
      "Id": "ou-root-1",
      "Name": "Root OU",
      "accounts": {
        "Root OU Account": {
          "account": "222222222222",
          "name": "Root OU Account"
        }
      },
      "nestedOus": {
        "Level 1 OU": {
          "Id": "ou-level1-1",
          "Name": "Level 1 OU",
          "accounts": {
            "Level 1 Account": {
              "account": "333333333333",
              "name": "Level 1 Account"
            }
          },
          "nestedOus": {
            "Level 2 OU": {
              // ... and so on
            }
          }
        }
      }
    }
  }
}
```

## Benefits

1. **Accurate representation** of AWS Organizations hierarchy
2. **Interactive Explorer** can now navigate through deeply nested OUs
3. **Complete visibility** into complex organizational structures
4. **No depth limit** - handles any level of nesting
5. **Backward compatible** - existing functionality unchanged

## Verification Steps

To verify the fix works with your AWS environment:

1. **Regenerate organization data:**
   ```bash
   reverse_diagrams -p your-profile -o -r us-east-1
   ```

2. **Check the JSON file:**
   ```bash
   cat diagrams/json/organizations_complete.json | python3 -m json.tool
   ```
   Look for populated `nestedOus` fields

3. **Test the explorer:**
   ```bash
   reverse_diagrams watch --explore
   ```
   Navigate through nested OUs to verify they appear correctly

## Related Components

The Interactive Identity Center Explorer already had proper recursive handling for nested OUs in:
- `src/explorer/data_loader.py` - `_parse_ou()` method (already recursive)
- `src/explorer/navigation.py` - Navigation engine (handles any depth)
- `src/explorer/display.py` - Display manager (renders nested structures)

This fix ensures the data generation matches the explorer's capabilities.

## Version

This fix will be included in version 2.2.1 (patch release).

---

**Fixed by:** Kiro AI Assistant  
**Date:** February 10, 2026  
**Issue reported by:** User (labvel)
