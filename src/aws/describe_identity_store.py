"""Describe Identity store."""
import logging
import os

import emoji
from colorama import Fore
from rich.progress import track

from ..dgms.graph_mapper import (
    create_file,
    create_sso_mapper,
    create_sso_mapper_complete,
)
from ..dgms.graph_template import (
    graph_template_sso,
    graph_template_sso_complete,
)
from ..reports.save_results import save_results
from .describe_organization import list_accounts
from .describe_sso import (
    client,
    extends_permissions_set,
    list_account_assignments,
    list_instances,
    list_permissions_set,
)
from ..reports.console_view import create_console_view, create_account_assignments_view


def list_groups_pag(identity_store_id, region, next_token: str = None):
    """
    List groups using pagination.

    :param identity_store_id:
    :param region:
    :param next_token:
    :return:
    """
    identity_client = client("identitystore", region_name=region)

    paginator = identity_client.get_paginator("list_groups")
    response_iterator = paginator.paginate(
        IdentityStoreId=identity_store_id,
        PaginationConfig={"MaxItems": 1000, "PageSize": 4, "StartingToken": next_token},
    )
    response = response_iterator.build_full_result()
    logging.info(response_iterator.build_full_result())
    return response["Groups"]


def list_groups(identity_store_id, region):
    """
    List Groups.

    :param identity_store_id:
    :param region:
    :return:
    """
    identity_client = client("identitystore", region_name=region)

    groups = identity_client.list_groups(
        IdentityStoreId=identity_store_id,
        MaxResults=20
    )

    logging.info(groups)
    l_groups = groups["Groups"]
    logging.info(len(groups["Groups"]))

    if len(groups["Groups"]) >= 20 and "NextToken" in groups.keys():
        logging.info("Paginating ...")
        ad_groups = list_groups_pag(
            identity_store_id=identity_store_id,
            region=region,
            next_token=groups["NextToken"],
        )
        for ad in ad_groups:
            l_groups.append(ad)
        logging.info(f"You have {len(l_groups)} Groups")

    return l_groups


# define pagination list user function
def list_users_pag(
    identity_store_id,
    identity_client,
    next_token: str = None,
):
    """
    List member in identity story using pagination.

    :param identity_store_id:
    :param identity_client:
    :param next_token:
    :return:
    """
    paginator = identity_client.get_paginator("list_users")
    response_iterator = paginator.paginate(
        IdentityStoreId=identity_store_id,
        PaginationConfig={
            "MaxItems": 1000,
            "PageSize": 20,
            "StartingToken": next_token,
        },
    )
    response_iterator = response_iterator.build_full_result()
    return response_iterator["Users"]


def list_users(identity_store_id, region):
    """
    List User in identity store.

    :param identity_store_id:
    :param region:
    :return:
    """
    identity_client = client("identitystore", region_name=region)

    response = identity_client.list_users(
        IdentityStoreId=identity_store_id, MaxResults=20
    )
    # create pagination option
    users = response["Users"]

    if len(users) >= 20:
        logging.info("Paginating ...")
        ad_users = list_users_pag(
            identity_store_id=identity_store_id,
            next_token=response["NextToken"],
            identity_client=identity_client,
        )
        for ad in ad_users:
            users.append(ad)
        logging.info(f"You have {len(users)} Users")

    return users


def get_members_pag(identity_store_id, identity_client, next_token: str = None):
    """
    Get members using paginator.

    :param identity_store_id:
    :param identity_client:
    :param next_token:
    :return:
    """
    paginator = identity_client.get_paginator("list_group_memberships")
    response_iterator = paginator.paginate(
        IdentityStoreId=identity_store_id,
        PaginationConfig={"MaxItems": 1000, "PageSize": 4, "StartingToken": next_token},
    )
    response = response_iterator.build_full_result()
    logging.info(response_iterator.build_full_result())
    return response["GroupMemberships"]


def get_members(identity_store_id, groups, region):
    """
    Ger members.

    :param identity_store_id:
    :param groups:
    :param region:
    :return:
    """
    l_client = client("identitystore", region_name=region)
    group_members = []
    for g, y in zip(
        groups, track(range(len(groups)), description="Getting groups members...")
    ):
        response = l_client.list_group_memberships(
            IdentityStoreId=identity_store_id,
            GroupId=g["GroupId"],
            MaxResults=20,
        )
        members = response["GroupMemberships"]
        logging.info(members)

        logging.info(len(members))

        if len(members) >= 20:
            logging.info("Paginating ...")
            ad_members = get_members_pag(
                identity_store_id=identity_store_id,
                identity_client=l_client,
                next_token=response["NextToken"],
            )
            for ad in ad_members:
                members.append(ad)
                logging.info(f"You have {len(ad_members)} Members")

        group_members.append(
            {
                "group_id": g["GroupId"],
                "group_name": g["DisplayName"],
                "members": members,
            }
        )

    return group_members


def list_group_memberships(identitystore_client, group_name, pagination=True):
    """
    List memberships for a group in an AWS SSO identity store.

    Args:
        identitystore_client (client): Boto3 SSO identity store client
        group_name (str): Name of the group to list memberships for
        pagination (bool): Whether to enable result pagination (default: True)

    Returns:
        list: List of member objects
    """
    params = {"GroupName": group_name}
    members = []

    if pagination:
        paginator = identitystore_client.get_paginator("list_group_memberships")
        for page in paginator.paginate(**params):
            members.extend(page["Members"])
    else:
        response = identitystore_client.list_group_memberships(**params)
        members.extend(response["Members"])

    return members


def complete_group_members(group_members, users_list):
    """
    Complete group members.

    :param group_members:
    :param users_list:
    :return:
    """
    for m in group_members:
        for u in m["members"]:
            for a in users_list:
                if u["MemberId"]["UserId"] == a["UserId"]:
                    u["MemberId"]["UserName"] = a["UserName"]

    return group_members


def l_groups_to_d_groups(l_groups: list = None):
    """
    Create group dictionary for groups.

    :param l_groups:
    :return:
    """
    names = []
    for a in l_groups:
        names.append(a["group_name"])
    logging.info(names)

    d_user_groups = dict(zip(names, l_groups))
    logging.info(d_user_groups)
    return d_user_groups


def extend_account_assignments(accounts_list, permissions_sets, store_arn, region):
    """
    Extend accounts assignments.

    :param accounts_list:
    :param permissions_sets:
    :param store_arn:
    :param region:
    :return:
    """
    account_assignments = []
    sso_client = client("sso-admin", region_name=region)
    for p, y in zip(
        permissions_sets,
        track(
            range(len(permissions_sets) ),
            description="Getting account assignments ...",
        ),
    ):
        for ac in accounts_list:
            assign = list_account_assignments(
                instance_arn=store_arn,
                account_id=ac["Id"],
                region=region,
                permission_set_arn=p,
                sso_client=sso_client,
            )
            logging.debug(f"AccountAssignments  {assign}")
            for a in assign:
                account_assignments.append(a)
    return account_assignments


def add_users_and_groups_assign(
    account_assignments_list,
    user_and_group_list,
    user_list,
    list_permissions_set_arn_name,
):
    """
    Add user to groups.

    :param account_assignments_list:
    :param user_and_group_list:
    :param user_list:
    :param list_permissions_set_arn_name:
    :return:
    """
    for a, y in zip(
        account_assignments_list,
        track(
            range(len(account_assignments_list) ),
            description="Create user and groups assignments ...",
        ),
    ):
        for g in user_and_group_list:
            if (
                len(a) > 0
                and a["PrincipalType"] == "GROUP"
                and g["group_id"] == a["PrincipalId"]
            ):
                logging.info(
                    Fore.YELLOW
                    + f"Account {a['AccountId']} assign to {a['PrincipalType']} {g['group_name']} with permission set {list_permissions_set_arn_name[a['PermissionSetArn']]} or {a['PermissionSetArn']}"
                    + Fore.RESET
                )

                a["GroupName"] = g["group_name"]
                a["PermissionSetName"] = list_permissions_set_arn_name[
                    a["PermissionSetArn"]
                ]
        for u in user_list:
            if (
                len(a) > 0
                and a["PrincipalType"] == "USER"
                and u["UserId"] == a["PrincipalId"]
            ):
                logging.info(
                    Fore.YELLOW
                    + f"Account {a['AccountId']} assign to {a['PrincipalType']} {u['UserName']} with permission set {a['PermissionSetArn']} or {list_permissions_set_arn_name[a['PermissionSetArn']]}"
                    + Fore.RESET
                )
                a["UserName"] = u["UserName"]
                a["PermissionSetName"] = list_permissions_set_arn_name[
                    a["PermissionSetArn"]
                ]
    logging.debug(f"Account Assignments --> {account_assignments_list}")
    return account_assignments_list


def order_accounts_assignments_list(accounts_dict, account_assignments):
    """
    Order accounts and assigments list.

    :param accounts_dict:
    :param account_assignments:
    :return:
    """
    final_account_assignments = {}
    for ac in accounts_dict:
        final_account_assignments[ac["Name"]] = []
        for a in account_assignments:
            if ac["Id"] == a["AccountId"]:
                final_account_assignments[ac["Name"]].append(a)

        logging.debug(f"Final Account Assignments: {final_account_assignments}")
    return final_account_assignments


def graph_identity_center(diagrams_path, region, auto):
    """
    Create Identity center diagram.

    :param auto:
    :param diagrams_path:
    :param region:
    :return:
    """
    template_file = "graph_sso.py"
    template_file_complete = "graph_sso_complete.py"

    code_path = f"{diagrams_path}/code"
    json_path = f"{diagrams_path}/json"

    create_file(
        template_content=graph_template_sso,
        file_name=template_file,
        directory_path=code_path,
    )
    create_file(
        template_content=graph_template_sso_complete,
        file_name=template_file_complete,
        directory_path=code_path,
    )

    store_instances = list_instances(region=region)
    print(
        Fore.BLUE
        + emoji.emojize(":sparkle: Getting Identity store instance info" + Fore.RESET)
    )
    logging.debug(store_instances)
    store_id = store_instances[0]["IdentityStoreId"]
    store_arn = store_instances[0]["InstanceArn"]

    print(Fore.BLUE + emoji.emojize(":sparkle: List groups" + Fore.RESET))
    l_groups = list_groups(store_id, region=region)
    logging.debug(l_groups)
    print(
        Fore.YELLOW
        + emoji.emojize(
            f":information:  There are {len(l_groups)} Groups in your Identity Store"
            + Fore.RESET
        )
    )

    print(Fore.BLUE + emoji.emojize(":sparkle: Get groups and Users info" + Fore.RESET))
    m_groups = get_members(store_id, l_groups, region=region)
    logging.debug(m_groups)
    logging.debug("Extend Group Members")
    l_users = list_users(store_id, region=region)
    logging.debug(l_users)
    c_users_and_groups = complete_group_members(m_groups, l_users)
    d_groups = l_groups_to_d_groups(l_groups=c_users_and_groups)

    logging.debug(c_users_and_groups)
    # Get Account assignments
    permissions_set = list_permissions_set(instance_arn=store_arn, region=region)
    l_permissions_set_arn_name = extends_permissions_set(
        permissions_sets=permissions_set, store_arn=store_arn, region=region
    )

    l_accounts = list_accounts(region=region)
    account_assignments = extend_account_assignments(
        accounts_list=l_accounts,
        permissions_sets=l_permissions_set_arn_name,
        region=region,
        store_arn=store_arn,
    )

    account_assignments = add_users_and_groups_assign(
        account_assignments_list=account_assignments,
        user_and_group_list=c_users_and_groups,
        user_list=l_users,
        list_permissions_set_arn_name=l_permissions_set_arn_name,
    )

    print(
        Fore.BLUE
        + emoji.emojize(
            ":sparkle: Getting account assignments, users and groups" + Fore.RESET
        )
    )
    f_accounts = order_accounts_assignments_list(
        accounts_dict=l_accounts, account_assignments=account_assignments
    )
    f_path = os.path.join(code_path, template_file_complete)
    create_sso_mapper_complete(
        template_file=f_path, acc_assignments=f_accounts, d_groups=d_groups
    )

    save_results(
        results=f_accounts,
        filename="account_assignments.json",
        directory_path=json_path,
    )
    save_results(results=d_groups, filename="groups.json", directory_path=json_path)

    f_path = os.path.join(code_path, template_file)

    create_sso_mapper(template_file=f_path, group_and_members=c_users_and_groups)

    if auto:
        print(f"{Fore.GREEN}❇️ Creating diagrams in {code_path}")
        command_1 = os.system(f"cd {code_path} && python3 {template_file}")
        command = os.system(f"cd {code_path} && python3 {template_file_complete}")

        if command != 0 or command_1 != 0:
            print(Fore.RED + "❌ Error creating diagrams")
            print(command)

        create_console_view(file_path=f"{json_path}/groups.json")
        create_account_assignments_view(file_path=f"{json_path}/account_assignments.json")
    else:
        print(
            Fore.YELLOW
            + emoji.emojize(
                f":sparkles:  Run -> python3 {code_path}/{template_file_complete}"
                f" or python3 {code_path}/{template_file}" + Fore.RESET
            )
        )
