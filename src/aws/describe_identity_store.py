import logging

from colorama import Fore
from rich.progress import track

from .describe_sso import client, list_account_assignments


def list_groups_pag(identity_store_id, region, next_token: str = None):
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
    identity_client = client("identitystore", region_name=region)

    groups = identity_client.list_groups(
        IdentityStoreId=identity_store_id, MaxResults=20
    )

    logging.info(groups)
    l_groups = groups["Groups"]
    logging.info(len(groups["Groups"]))

    if len(groups["Groups"]) >= 20:
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
def list_users_pag(identity_store_id, region, next_token: str = None):
    identity_client = client("identitystore", region_name=region)
    paginator = identity_client.get_paginator("list_users")
    response_iterator = paginator.paginate(
        IdentityStoreId=identity_store_id,
        PaginationConfig={"MaxItems": 1000, "PageSize": 4, "StartingToken": next_token},
    )
    response_iterator = response_iterator.build_full_result()
    return response_iterator["Users"]


def list_users(identity_store_id, region):
    identity_client = client("identitystore", region_name=region)

    response = identity_client.list_users(
        IdentityStoreId=identity_store_id,
        MaxResults=20
    )
    # create pagination option
    users = response["Users"]

    if len(users) >= 20:
        logging.info("Paginating ...")
        ad_users = list_users_pag(
            identity_store_id=identity_store_id,
            region=region,
            next_token=response["NextToken"],
        )
        for ad in ad_users:
            users.append(ad)
        logging.info(f"You have {len(users)} Users")

    return users


def get_members_pag(identity_store_id, region, next_token: str = None):
    identity_client = client("identitystore", region_name=region)

    paginator = identity_client.get_paginator("list_group_memberships")
    response_iterator = paginator.paginate(
        IdentityStoreId=identity_store_id,
        PaginationConfig={"MaxItems": 1000, "PageSize": 4, "StartingToken": next_token},
    )
    response = response_iterator.build_full_result()
    logging.info(response_iterator.build_full_result())
    return response["GroupMemberships"]


def get_members(identity_store_id, groups, region):
    l_client = client("identitystore", region_name=region)
    group_members = []
    for g, y in zip(
        groups, track(range(len(groups) - 1), description="Getting groups members...")
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
                region=region,
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
    Lists memberships for a group in an AWS SSO identity store.

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
    for m in group_members:
        for u in m["members"]:
            for a in users_list:
                if u["MemberId"]["UserId"] == a["UserId"]:
                    u["MemberId"]["UserName"] = a["UserName"]

    return group_members


def l_groups_to_d_groups(l_groups: list = None):
    """

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
    account_assignments = []
    sso_client = client("sso-admin", region_name=region)
    for p, y in zip(
        permissions_sets,
        track(
            range(len(permissions_sets) - 1),
            description="Getting account assignments ...",
        ),
    ):
        for ac in accounts_list:
            assign = list_account_assignments(
                instance_arn=store_arn,
                account_id=ac["Id"],
                region=region,
                permission_set_arn=p,
                sso_client = sso_client
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
    for a, y in zip(
        account_assignments_list,
        track(
            range(len(account_assignments_list) - 1),
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
    final_account_assignments = {}
    for ac in accounts_dict:
        final_account_assignments[ac["Name"]] = []
        for a in account_assignments:
            if ac["Id"] == a["AccountId"]:
                final_account_assignments[ac["Name"]].append(a)

        logging.debug(f"Final Account Assignments: {final_account_assignments}")
    return final_account_assignments
