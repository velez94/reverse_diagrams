"""Create Console View."""
import json

import inquirer
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel


# load json file from path function
def load_json(path):
    """
    Load json file.

    :param path:
    :return:
    """
    with open(path, "r") as f:
        return json.load(f)


def get_members(group):
    """
    Get members name.

    :param group: Can be either a list of group dicts or a dict with numeric keys
    :return: Dictionary mapping group names to member lists
    """
    members_groups = {}
    
    # Handle new format (list of dicts with group_id, group_name, members)
    if isinstance(group, list):
        for g in group:
            group_name = g.get("group_name", "Unknown Group")
            members_groups[group_name] = []
            for member in g.get("members", []):
                # Handle both old and new member formats
                if isinstance(member, dict):
                    if "MemberId" in member and "UserName" in member["MemberId"]:
                        members_groups[group_name].append(member["MemberId"]["UserName"])
                    elif "UserName" in member:
                        members_groups[group_name].append(member["UserName"])
    
    # Handle old format (dict with numeric keys)
    elif isinstance(group, dict):
        for key in group:
            g = group[key]
            if isinstance(g, dict) and "group_name" in g:
                group_name = g["group_name"]
                members_groups[group_name] = []
                for member in g.get("members", []):
                    if isinstance(member, dict):
                        if "MemberId" in member and "UserName" in member["MemberId"]:
                            members_groups[group_name].append(member["MemberId"]["UserName"])
                        elif "UserName" in member:
                            members_groups[group_name].append(member["UserName"])
    
    return members_groups


def pretty_members(members):
    """
    Print pretty members.

    :param members:
    :return:
    """
    string = ""
    for m in members:
        string += f"{m}\n"

    return string


def create_group_console_view(groups):
    """
    Create tree.

    :param groups: Can be either a list of group dicts or a dict with numeric keys
    :return:
    """
    members = get_members(groups)
    console = Console()
    c = [
        Panel(
            f"[b][green]{group_name}[/b]\n[yellow]{pretty_members(members[group_name])}",
            expand=True,
        )
        for group_name in members.keys()
    ]
    console.print(Columns(c))


def single_create_group_assignments_view(members, group_name):
    """
    Create tree.

    :param group_name:
    :param members:
    :return:
    """
    console = Console()
    c = [Panel(f"[b]{group_name}[/b]\n[blue]{pretty_members(members)}", expand=True)]
    console.print(Columns(c))


def create_string_account_assignment(account_assignment):
    """
    Create string account assignment.

    :param account_assignment:
    :return:
    """
    string = ""
    if (
        account_assignment["PrincipalType"] == "GROUP"
        and "GroupName" in account_assignment.keys()
    ):
        string += f"GroupName: {account_assignment['GroupName']}\n"
    elif account_assignment["PrincipalType"] == "USER":
        string += f"UserName: {account_assignment['UserName']}\n"
    if "PermissionSetName" in account_assignment.keys():
        string += f"PermissionSetName: {account_assignment['PermissionSetName']}\n\n"
    return string


# get account  assignments
def pretty_account_assignments(accounts: dict):
    """
    Print pretty members.

    :type accounts: object
    :return:
    """
    string = ""
    if isinstance(accounts, dict):
        for a in accounts.keys():
            for c in accounts[a]:
                string += create_string_account_assignment(account_assignment=c)
    elif isinstance(accounts, list):
        for c in accounts:
            string += create_string_account_assignment(account_assignment=c)
    return string


def single_create_account_assignments_view(assign, account_name):
    """
    Create tree.

    :param account_name:
    :param assign:
    :return:
    """
    console = Console()
    c = [
        Panel(
            f"[b]{account_name}[/b]\n[blue]{pretty_account_assignments(assign)}",
            expand=True,
        )
    ]
    console.print(Columns(c))


def create_console_view_from_input(assign):
    """
    Ask print single account.

    :param assign:
    :return:
    """
    # execute while the user decide to leave
    con = "yes"
    while con == "yes":
        questions = [
            inquirer.List(
                "account",
                message="Which account do you want to see?",
                choices=list(assign.keys()),
            ),
        ]
        answers = inquirer.prompt(questions)
        single_create_account_assignments_view(
            assign[answers["account"]], account_name=answers["account"]
        )
        # execute while the user decide to leave
        continue_ = [
            inquirer.List(
                name="ans",
                message="Do you want to watch another account ?",
                choices=["yes", "no"],
            )
        ]
        continue_ans = inquirer.prompt(continue_)
        con = continue_ans["ans"]


def ask_control(case):
    """
    Ask control.

    :type case: object
    :param case:
    :return:
    """
    control_ = [
        inquirer.List(
            name="ans",
            message=f"Do you want to watch all {case}?",
            choices=["all", "one-at-time"],
        )
    ]
    control_ans = inquirer.prompt(control_)
    control = control_ans["ans"]
    return control


def create_account_assignments_view(assign):
    """
    Create tree.

    :param assign:
    :return:
    """
    control = ask_control(case="account assignments or account by account")
    if control == "one-at-time":
        create_console_view_from_input(assign=assign)
    else:
        console = Console()
        c = [
            Panel(
                f"[b]{account}[/b]\n[blue]{pretty_account_assignments(assign)}",
                expand=True,
            )
            for account in assign
        ]
        console.print(Columns(c))


# create console view based on user input using inquirer

# pretty for organizations


def pretty_accounts(accounts):
    """
    Format accounts list for display.
    
    :param accounts: List of account dictionaries
    :return: Formatted string
    """
    string = ""
    for account in accounts:
        name = account.get("Name", "Unknown")
        account_id = account.get("Id", "N/A")
        status = account.get("Status", "N/A")
        string += f"ID: {account_id}\nStatus: {status}\n"
    return string


def create_organizations_console_view(org_data):
    """
    Create console view for AWS Organizations.
    
    :param org_data: Organizations data from JSON file
    :return:
    """
    console = Console()
    
    # Get organization info
    org_info = org_data.get("organization", {})
    accounts = org_data.get("accounts", [])
    ous = org_data.get("organizational_units", [])
    org_complete = org_data.get("organizations_complete", {})
    
    panels = []
    
    # Organization overview panel
    org_overview = f"[b]Organization ID:[/b] {org_info.get('Id', 'N/A')}\n"
    org_overview += f"[b]Master Account:[/b] {org_info.get('MasterAccountId', 'N/A')}\n"
    org_overview += f"[b]Total Accounts:[/b] {len(accounts)}\n"
    org_overview += f"[b]Organizational Units:[/b] {len(ous)}"
    
    panels.append(Panel(org_overview, title="[cyan]Organization Overview[/cyan]", expand=True))
    
    # Root level accounts
    if org_complete:
        root_accounts = org_complete.get("noOutAccounts", [])
        if root_accounts:
            root_content = ""
            for acc in root_accounts:
                root_content += f"[green]• {acc.get('name', 'Unknown')}[/green] (ID: {acc.get('id', 'N/A')})\n"
            panels.append(Panel(root_content, title="[yellow]Root Level Accounts[/yellow]", expand=True))
        
        # Organizational Units with accounts
        org_units = org_complete.get("organizationalUnits", {})
        if org_units:
            for ou_name, ou_data in org_units.items():
                ou_content = f"[b]Organizational Unit:[/b] {ou_name}\n\n"
                ou_accounts = ou_data.get("accounts", {})
                if ou_accounts:
                    ou_content += "[b]Accounts:[/b]\n"
                    for acc_name, acc_info in ou_accounts.items():
                        ou_content += f"[blue]• {acc_name}[/blue] (ID: {acc_info.get('id', 'N/A')})\n"
                else:
                    ou_content += "[dim]No accounts in this OU[/dim]"
                
                panels.append(Panel(ou_content, title=f"[magenta]🏢 {ou_name}[/magenta]", expand=True))
    else:
        # Fallback: show all accounts if organizations_complete is not available
        if accounts:
            accounts_content = ""
            for account in accounts[:10]:  # Show first 10 accounts
                accounts_content += f"[green]• {account.get('Name', 'Unknown')}[/green]\n"
                accounts_content += f"  ID: {account.get('Id', 'N/A')}\n"
                accounts_content += f"  Status: {account.get('Status', 'N/A')}\n\n"
            
            if len(accounts) > 10:
                accounts_content += f"[dim]... and {len(accounts) - 10} more accounts[/dim]"
            
            panels.append(Panel(accounts_content, title="[cyan]Accounts[/cyan]", expand=True))
    
    # Print all panels
    for panel in panels:
        console.print(panel)
        console.print()  # Add spacing between panels


def watch_on_demand(
    args,
):
    """
    Watch on demand graphs in console.

    :param args:
    :return:
    """
    try:
        # Check if HTML generation is requested
        if hasattr(args, 'generate_html') and args.generate_html:
            # Import HTML generation functions
            from .html_report import generate_report_from_files
            from ..utils.progress import get_progress_tracker
            
            progress = get_progress_tracker()
            
            # Determine which JSON file to use and generate HTML
            json_file = None
            report_type = None
            
            if args.watch_graph_organization:
                json_file = args.watch_graph_organization
                report_type = "organizations"
            elif args.watch_graph_identity:
                json_file = args.watch_graph_identity
                report_type = "groups"
            elif args.watch_graph_accounts_assignments:
                json_file = args.watch_graph_accounts_assignments
                report_type = "assignments"
            
            if not json_file:
                progress.show_error(
                    "No JSON file specified",
                    "Please specify a JSON file with -wo, -wi, or -wa flag"
                )
                return
            
            # Determine output path
            output_path = getattr(args, 'html_output', None) or "diagrams/reports/aws_report.html"
            
            # Generate HTML report based on file type
            progress.show_success(
                "Generating HTML report from watch command",
                f"Processing {report_type} data from {json_file}"
            )
            
            try:
                if report_type == "organizations":
                    html_path = generate_report_from_files(
                        organizations_file=json_file,
                        output_path=output_path
                    )
                elif report_type == "groups":
                    html_path = generate_report_from_files(
                        groups_file=json_file,
                        output_path=output_path
                    )
                elif report_type == "assignments":
                    html_path = generate_report_from_files(
                        assignments_file=json_file,
                        output_path=output_path
                    )
                
                progress.show_success(
                    "HTML report generated successfully",
                    f"📄 Output: {html_path}\n"
                    f"📊 Report type: {report_type.capitalize()}\n"
                    f"📁 Source: {json_file}"
                )
            except Exception as e:
                progress.show_error("HTML generation failed", str(e))
                raise
            
            return
        
        # Original console view functionality
        if args.watch_graph_organization:
            org_data = load_json(args.watch_graph_organization)
            create_organizations_console_view(org_data=org_data)
        if args.watch_graph_accounts_assignments:
            assign = load_json(args.watch_graph_accounts_assignments)
            create_account_assignments_view(assign=assign)
        if args.watch_graph_identity:
            c = load_json(args.watch_graph_identity)
            create_group_console_view(groups=c)
    except FileNotFoundError as e:
        print(f"❌ Error: File not found - {e}")
        print("💡 Make sure you've generated the diagrams first using:")
        print("   reverse_diagrams -o -i -p <profile> -r <region>")
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON file - {e}")
        print("💡 The file may be corrupted. Try regenerating it.")
    except KeyError as e:
        print(f"❌ Error: Missing expected data in file - {e}")
        print("💡 The file format may be outdated. Try regenerating it.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
