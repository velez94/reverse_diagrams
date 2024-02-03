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

    :param group:
    :return:
    """
    members_groups = {}
    for m in group:
        members_groups[group[m]["group_name"]] = []
        for mm in group[m]["members"]:
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


def create_group_console_view(groups):
    """
    Create tree.

    :param groups:
    :return:
    """
    members = get_members(groups)
    console = Console()
    c = [
        Panel(
            f"[b][green]{group}[/b]\n[yellow]{pretty_members(members[group])}",
            expand=True,
        )
        for group in groups
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


def watch_on_demand(
    args,
):
    """
    Watch on demand graphs in console.

    :param args:
    :return:
    """
    if args.watch_graph_organization:
        # create_console_view(file_path=f"{diagrams_path}/json/organizations.json")
        print("Not available jet")
    if args.watch_graph_accounts_assignments:
        assign = load_json(args.watch_graph_accounts_assignments)
        create_account_assignments_view(assign=assign)
    if args.watch_graph_identity:
        c = load_json(args.watch_graph_identity)
        create_group_console_view(groups=c)
