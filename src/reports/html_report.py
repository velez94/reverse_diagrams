"""Generate modern HTML reports from AWS data."""
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


# Custom exceptions for HTML generation
class HTMLGenerationError(Exception):
    """Base exception for HTML generation errors."""
    pass


class JSONFileNotFoundError(HTMLGenerationError):
    """Raised when a required JSON file is not found."""
    pass


class JSONParseError(HTMLGenerationError):
    """Raised when JSON parsing fails."""
    pass


class InvalidOutputPathError(HTMLGenerationError):
    """Raised when the output path is invalid or unwritable."""
    pass


class HTMLWriteError(HTMLGenerationError):
    """Raised when writing HTML file fails."""
    pass


def _validate_json_structure(data: Any, data_type: str) -> None:
    """
    Validate JSON data structure.
    
    Args:
        data: The data to validate
        data_type: Type of data (organizations, groups, assignments)
        
    Raises:
        JSONParseError: If data structure is invalid
    """
    if data is None:
        return  # None is acceptable (optional data)
    
    if data_type == "organizations":
        if not isinstance(data, dict):
            raise JSONParseError(f"Organizations data must be a dictionary, got {type(data).__name__}")
    elif data_type == "groups":
        if not isinstance(data, list):
            raise JSONParseError(f"Groups data must be a list, got {type(data).__name__}")
    elif data_type == "assignments":
        if not isinstance(data, dict):
            raise JSONParseError(f"Account assignments data must be a dictionary, got {type(data).__name__}")


def _validate_output_path(output_path: str) -> Path:
    """
    Validate and prepare output path.
    
    Args:
        output_path: Path where HTML report will be saved
        
    Returns:
        Validated Path object
        
    Raises:
        InvalidOutputPathError: If path is invalid or unwritable
    """
    try:
        path = Path(output_path).resolve()
        
        # Check if parent directory exists or can be created
        if not path.parent.exists():
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                raise InvalidOutputPathError(
                    f"Cannot create directory {path.parent}: Permission denied. "
                    f"Please check directory permissions or specify a different output path."
                )
            except Exception as e:
                raise InvalidOutputPathError(
                    f"Cannot create directory {path.parent}: {e}. "
                    f"Please verify the path is valid."
                )
        
        # Check if directory is writable
        if not os.access(path.parent, os.W_OK):
            raise InvalidOutputPathError(
                f"Directory {path.parent} is not writable. "
                f"Please check permissions or specify a different output path."
            )
        
        return path
    except InvalidOutputPathError:
        raise
    except Exception as e:
        raise InvalidOutputPathError(
            f"Invalid output path '{output_path}': {e}. "
            f"Please provide a valid file path."
        )


def generate_html_report(
    organizations_data: Optional[Dict[str, Any]] = None,
    groups_data: Optional[List[Dict[str, Any]]] = None,
    account_assignments_data: Optional[Dict[str, Any]] = None,
    output_path: str = "diagrams/reports/aws_report.html"
) -> str:
    """
    Generate a modern HTML report from AWS data.
    
    Args:
        organizations_data: Organizations structure data
        groups_data: Identity Center groups data
        account_assignments_data: Account assignments data
        output_path: Output file path
        
    Returns:
        Path to generated HTML file
        
    Raises:
        JSONParseError: If data structure is invalid
        InvalidOutputPathError: If output path is invalid or unwritable
        HTMLWriteError: If writing HTML file fails
    """
    logger.debug(f"Generating HTML report at {output_path}")
    
    # Validate data structures
    try:
        _validate_json_structure(organizations_data, "organizations")
        _validate_json_structure(groups_data, "groups")
        _validate_json_structure(account_assignments_data, "assignments")
    except JSONParseError as e:
        logger.error(f"Invalid data structure: {e}")
        raise
    
    # Validate and prepare output path
    try:
        output_file = _validate_output_path(output_path)
    except InvalidOutputPathError as e:
        logger.error(f"Invalid output path: {e}")
        raise
    
    # Generate HTML content
    try:
        html_content = _generate_html_template(
            organizations_data,
            groups_data,
            account_assignments_data
        )
    except Exception as e:
        logger.error(f"Failed to generate HTML content: {e}")
        raise HTMLGenerationError(f"HTML generation failed: {e}")
    
    # Write to file
    try:
        output_file.write_text(html_content, encoding='utf-8')
    except PermissionError:
        raise HTMLWriteError(
            f"Permission denied writing to {output_file}. "
            f"Please check file permissions."
        )
    except Exception as e:
        raise HTMLWriteError(
            f"Failed to write HTML file to {output_file}: {e}. "
            f"Please check disk space and permissions."
        )
    
    logger.info(f"HTML report generated successfully: {output_path}")
    return str(output_file)


def _generate_html_template(
    organizations_data: Optional[Dict[str, Any]],
    groups_data: Optional[List[Dict[str, Any]]],
    account_assignments_data: Optional[Dict[str, Any]]
) -> str:
    """Generate the complete HTML template."""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Generate sections
    org_section = _generate_organizations_section(organizations_data) if organizations_data else ""
    groups_section = _generate_groups_section(groups_data) if groups_data else ""
    assignments_section = _generate_assignments_section(account_assignments_data) if account_assignments_data else ""
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AWS Infrastructure Report - Reverse Diagrams</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .header .subtitle {{
            color: #666;
            font-size: 1.1em;
        }}
        
        .header .timestamp {{
            color: #999;
            font-size: 0.9em;
            margin-top: 10px;
        }}
        
        .section {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        
        .section-title {{
            font-size: 1.8em;
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 3px solid #667eea;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .card {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .card:hover {{
            transform: translateX(5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        
        .card-title {{
            font-size: 1.3em;
            color: #333;
            margin-bottom: 10px;
            font-weight: 600;
        }}
        
        .card-content {{
            color: #666;
            line-height: 1.6;
        }}
        
        .badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            margin-right: 8px;
            margin-bottom: 8px;
        }}
        
        .badge-primary {{
            background: #667eea;
            color: white;
        }}
        
        .badge-success {{
            background: #48bb78;
            color: white;
        }}
        
        .badge-info {{
            background: #4299e1;
            color: white;
        }}
        
        .badge-warning {{
            background: #ed8936;
            color: white;
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            padding: 25px;
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 3em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .stat-label {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .tree {{
            margin-left: 20px;
            border-left: 2px solid #e2e8f0;
            padding-left: 20px;
        }}
        
        .tree-item {{
            margin: 10px 0;
            padding: 10px;
            background: #f7fafc;
            border-radius: 5px;
        }}
        
        .member-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
        }}
        
        .footer {{
            text-align: center;
            color: white;
            padding: 20px;
            margin-top: 30px;
        }}
        
        .footer a {{
            color: white;
            text-decoration: none;
            font-weight: 600;
        }}
        
        .footer a:hover {{
            text-decoration: underline;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.8em;
            }}
            
            .section-title {{
                font-size: 1.4em;
            }}
            
            .grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>
                <span>🔄</span>
                AWS Infrastructure Report
            </h1>
            <div class="subtitle">Generated by Reverse Diagrams</div>
            <div class="timestamp">📅 Generated: {timestamp}</div>
        </div>
        
        {org_section}
        {groups_section}
        {assignments_section}
        
        <div class="footer">
            <p>Generated with ❤️ by <a href="https://github.com/velez94/reverse_diagrams" target="_blank">Reverse Diagrams</a></p>
            <p style="margin-top: 10px; opacity: 0.8;">Documentation as Code for AWS Infrastructure</p>
        </div>
    </div>
</body>
</html>"""
    
    return html


def _generate_organizations_section(data: Dict[str, Any]) -> str:
    """Generate the organizations section."""
    if not data:
        return ""
    
    org_info = data.get('organization', {})
    accounts = data.get('accounts', [])
    ous = data.get('organizational_units', [])
    org_complete = data.get('organizations_complete', {})
    
    # Statistics
    stats_html = f"""
    <div class="grid">
        <div class="stat-card">
            <div class="stat-number">{len(accounts)}</div>
            <div class="stat-label">AWS Accounts</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{len(ous)}</div>
            <div class="stat-label">Organizational Units</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{org_info.get('Id', 'N/A')}</div>
            <div class="stat-label">Organization ID</div>
        </div>
    </div>
    """
    
    # Organizational structure
    structure_html = ""
    if org_complete:
        structure_html = "<h3 style='margin-top: 30px; color: #667eea;'>📊 Organization Structure</h3>"
        
        # Root accounts
        root_accounts = org_complete.get('noOutAccounts', [])
        if root_accounts:
            structure_html += "<div class='card'><div class='card-title'>Root Level Accounts</div><div class='card-content'>"
            for acc in root_accounts:
                structure_html += f"<span class='badge badge-primary'>{acc.get('name', 'Unknown')}</span>"
            structure_html += "</div></div>"
        
        # Organizational Units
        org_units = org_complete.get('organizationalUnits', {})
        if org_units:
            for ou_name, ou_data in org_units.items():
                structure_html += f"<div class='card'><div class='card-title'>🏢 {ou_name}</div><div class='card-content'>"
                ou_accounts = ou_data.get('accounts', {})
                if ou_accounts:
                    structure_html += "<div style='margin-top: 10px;'><strong>Accounts:</strong><br>"
                    for acc_name in ou_accounts.keys():
                        structure_html += f"<span class='badge badge-info'>{acc_name}</span>"
                    structure_html += "</div>"
                structure_html += "</div></div>"
    
    return f"""
    <div class="section">
        <div class="section-title">
            <span>🏢</span>
            AWS Organizations
        </div>
        {stats_html}
        {structure_html}
    </div>
    """


def _generate_groups_section(data: List[Dict[str, Any]]) -> str:
    """Generate the groups section."""
    if not data:
        return ""
    
    # Statistics
    total_members = sum(len(group.get('members', [])) for group in data)
    
    stats_html = f"""
    <div class="grid">
        <div class="stat-card">
            <div class="stat-number">{len(data)}</div>
            <div class="stat-label">Identity Center Groups</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{total_members}</div>
            <div class="stat-label">Total Members</div>
        </div>
    </div>
    """
    
    # Groups list
    groups_html = "<h3 style='margin-top: 30px; color: #667eea;'>👥 Groups & Members</h3>"
    
    for group in data:
        group_name = group.get('group_name', 'Unknown Group')
        members = group.get('members', [])
        
        groups_html += f"<div class='card'><div class='card-title'>👥 {group_name}</div><div class='card-content'>"
        groups_html += f"<div><strong>Members ({len(members)}):</strong></div>"
        groups_html += "<div class='member-list'>"
        
        for member in members:
            member_id = member.get('MemberId', {})
            username = member_id.get('UserName', 'Unknown')
            groups_html += f"<span class='badge badge-success'>{username}</span>"
        
        groups_html += "</div></div></div>"
    
    return f"""
    <div class="section">
        <div class="section-title">
            <span>👥</span>
            IAM Identity Center Groups
        </div>
        {stats_html}
        {groups_html}
    </div>
    """


def _generate_assignments_section(data: Dict[str, Any]) -> str:
    """Generate the account assignments section."""
    if not data:
        return ""
    
    # Count total assignments
    total_assignments = sum(len(assignments) for assignments in data.values())
    
    stats_html = f"""
    <div class="grid">
        <div class="stat-card">
            <div class="stat-number">{len(data)}</div>
            <div class="stat-label">Accounts with Assignments</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{total_assignments}</div>
            <div class="stat-label">Total Assignments</div>
        </div>
    </div>
    """
    
    # Assignments list
    assignments_html = "<h3 style='margin-top: 30px; color: #667eea;'>🔐 Account Assignments</h3>"
    
    for account_name, assignments in data.items():
        assignments_html += f"<div class='card'><div class='card-title'>🏦 {account_name}</div><div class='card-content'>"
        
        for assignment in assignments:
            principal_type = assignment.get('PrincipalType', 'Unknown')
            principal_name = assignment.get('GroupName') or assignment.get('UserName', 'Unknown')
            permission_set = assignment.get('PermissionSetName', 'N/A')
            
            badge_class = 'badge-primary' if principal_type == 'GROUP' else 'badge-info'
            
            assignments_html += f"""
            <div style='margin: 10px 0; padding: 10px; background: white; border-radius: 5px;'>
                <span class='badge {badge_class}'>{principal_type}</span>
                <strong>{principal_name}</strong>
                <span style='color: #666;'> → </span>
                <span class='badge badge-warning'>{permission_set}</span>
            </div>
            """
        
        assignments_html += "</div></div>"
    
    return f"""
    <div class="section">
        <div class="section-title">
            <span>🔐</span>
            Account Assignments
        </div>
        {stats_html}
        {assignments_html}
    </div>
    """


def generate_report_from_files(
    organizations_file: Optional[str] = None,
    groups_file: Optional[str] = None,
    assignments_file: Optional[str] = None,
    output_path: str = "diagrams/reports/aws_report.html"
) -> str:
    """
    Generate HTML report from JSON files.
    
    Args:
        organizations_file: Path to organizations JSON file
        groups_file: Path to groups JSON file
        assignments_file: Path to account assignments JSON file
        output_path: Output HTML file path
        
    Returns:
        Path to generated HTML file
        
    Raises:
        JSONFileNotFoundError: If specified file doesn't exist
        JSONParseError: If JSON file is malformed
        InvalidOutputPathError: If output path is invalid
        HTMLWriteError: If writing HTML file fails
    """
    logger.debug("Loading data from JSON files for HTML report generation")
    
    # Load data from files with error handling
    org_data = None
    groups_data = None
    assignments_data = None
    
    files_processed = []
    
    if organizations_file:
        org_path = Path(organizations_file)
        if not org_path.exists():
            raise JSONFileNotFoundError(
                f"Organizations file not found: {organizations_file}. "
                f"Please run with -o flag to generate organizations data first."
            )
        try:
            with open(org_path, 'r') as f:
                org_data = json.load(f)
            _validate_json_structure(org_data, "organizations")
            files_processed.append("organizations.json")
            logger.debug(f"Loaded organizations data from {organizations_file}")
        except json.JSONDecodeError as e:
            raise JSONParseError(
                f"Invalid JSON in {organizations_file}: {e}. "
                f"The file may be corrupted. Please regenerate it with -o flag."
            )
        except Exception as e:
            raise JSONParseError(
                f"Failed to read {organizations_file}: {e}"
            )
    
    if groups_file:
        groups_path = Path(groups_file)
        if not groups_path.exists():
            raise JSONFileNotFoundError(
                f"Groups file not found: {groups_file}. "
                f"Please run with -i flag to generate groups data first."
            )
        try:
            with open(groups_path, 'r') as f:
                groups_data = json.load(f)
            _validate_json_structure(groups_data, "groups")
            files_processed.append("groups.json")
            logger.debug(f"Loaded groups data from {groups_file}")
        except json.JSONDecodeError as e:
            raise JSONParseError(
                f"Invalid JSON in {groups_file}: {e}. "
                f"The file may be corrupted. Please regenerate it with -i flag."
            )
        except Exception as e:
            raise JSONParseError(
                f"Failed to read {groups_file}: {e}"
            )
    
    if assignments_file:
        assignments_path = Path(assignments_file)
        if not assignments_path.exists():
            raise JSONFileNotFoundError(
                f"Account assignments file not found: {assignments_file}. "
                f"Please run with -i flag to generate assignments data first."
            )
        try:
            with open(assignments_path, 'r') as f:
                assignments_data = json.load(f)
            _validate_json_structure(assignments_data, "assignments")
            files_processed.append("account_assignments.json")
            logger.debug(f"Loaded assignments data from {assignments_file}")
        except json.JSONDecodeError as e:
            raise JSONParseError(
                f"Invalid JSON in {assignments_file}: {e}. "
                f"The file may be corrupted. Please regenerate it with -i flag."
            )
        except Exception as e:
            raise JSONParseError(
                f"Failed to read {assignments_file}: {e}"
            )
    
    # Check if at least one file was processed
    if not files_processed:
        raise JSONFileNotFoundError(
            "No JSON data files found. "
            "Please run with -o or -i flags to generate data first, "
            "or specify file paths explicitly."
        )
    
    logger.debug(f"Processed {len(files_processed)} JSON files: {', '.join(files_processed)}")
    
    # Generate HTML report
    return generate_html_report(
        org_data,
        groups_data,
        assignments_data,
        output_path
    )
