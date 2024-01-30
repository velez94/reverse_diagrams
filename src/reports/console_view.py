import json
from rich.console import Console
from rich.columns import Columns
from rich.panel import Panel
from rich.progress import track


# load json file from path function
def load_json(path):
    """
    Load json file.

    :param path:
    :return:
    """
    with open(path, 'r') as f:
        return json.load(f)


def get_members(group):
    """
    Get members name.

    :param group:
    :return:
    """
    members_groups = {}
    for m in group:
        members_groups[group[m]["group_name"]] = []
        for mm in group[m]['members']:
            members_groups[group[m]["group_name"]].append(mm["MemberId"]["UserName"])

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


def create_console_view(file_path="diagrams/json/groups.json"):
    """
    Create tree.

    :param file_path:
    :return:
    """
    c = load_json(file_path)
    members = get_members(c)
    console = Console()
    c = [Panel(f"[b][green]{group}[/b]\n[yellow]{pretty_members(members[group])}", expand=True) for group in c]
    console.print(Columns(c))


# get account  assignments
def pretty_account_assignments(accounts: dict):
    """
    Print pretty members.

    :type accounts: object
    :return:
    """
    string = ""

    for a in accounts.keys():
        for c in accounts[a]:

            if c['PrincipalType'] == "GROUP" and "GroupName" in c.keys():
                string += f"GroupName: {c['GroupName']}\n"
            elif c['PrincipalType'] == "USER":
                string += f"UserName: {c['UserName']}\n"

            string += f"PermissionSetName: {c['PermissionSetName']}\n\n"

    return string


def create_account_assignments_view(file_path="diagrams/json/account_assignments.json"):
    """
    Create tree.

    :param file_path:
    :return:
    """
    assign = load_json(file_path)

    console = Console()
    c = [Panel(f"[b]{account}[/b]\n[blue]{pretty_account_assignments(assign)}", expand=True) for account in assign]
    console.print(Columns(c))

# pretty for organizations
