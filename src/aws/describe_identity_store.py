import boto3
from .describe_sso import list_account_assignments
from colorama import Fore
import logging


def list_groups_pag(identity_store_id, client=boto3.client('identitystore', region_name="us-east-2"),
                    next_token: str = None):
    paginator = client.get_paginator('list_groups')
    response_iterator = paginator.paginate(
        IdentityStoreId=identity_store_id,
        PaginationConfig={
            'MaxItems': 1000,
            'PageSize': 4,
            'StartingToken': next_token
        }
    )
    response = response_iterator.build_full_result()
    logging.info(response_iterator.build_full_result())
    return response["Groups"]


def list_groups(identity_store_id, client=boto3.client('identitystore', region_name="us-east-2"), ):
    groups = client.list_groups(
        IdentityStoreId=identity_store_id,
        MaxResults=5
    )

    logging.info(groups)
    l_groups = groups["Groups"]
    logging.info(len(groups["Groups"]))

    if len(groups["Groups"]) >= 5:
        logging.info("Paginating ...")
        ad_groups = list_groups_pag(identity_store_id=identity_store_id, client=client, next_token=groups["NextToken"])
        for ad in ad_groups:
            l_groups.append(ad)
        logging.info(f"You have {len(l_groups)} Groups")

    return l_groups


def list_users(identity_store_id, client=boto3.client('identitystore', region_name="us-east-2"), ):
    response = client.list_users(
        IdentityStoreId=identity_store_id,

    )

    return response["Users"]


def get_members(identity_store_id, groups, client=boto3.client('identitystore', region_name="us-east-2")):
    group_members = []
    for g in groups:
        response = client.list_group_memberships(
            IdentityStoreId=identity_store_id,
            GroupId=g["GroupId"],

        )
        group_members.append(
            {"group_id": g["GroupId"],
             "group_name": g["DisplayName"],
             "members": response["GroupMemberships"]
             }
        )

    return group_members


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
        names.append(a['group_name'])
    logging.info(names)

    d_user_groups = dict(zip(names, l_groups))
    logging.info(d_user_groups)
    return d_user_groups


def extend_account_assignments(accounts_list, permissions_sets, store_arn,
                               client_sso=boto3.client('identitystore', region_name="us-east-2")):
    account_assignments = []
    for p in permissions_sets:

        for ac in accounts_list:
            assign = list_account_assignments(instance_arn=store_arn, account_id=ac["Id"], client=client_sso,
                                              permission_set_arn=p)
            logging.debug(f"AccountAssignments  {assign}")
            for a in assign:
                account_assignments.append(a)
    return account_assignments


def add_users_and_groups_assign(account_assignments_list, user_and_group_list, user_list,
                                list_permissions_set_arn_name):
    for a in account_assignments_list:
        for g in user_and_group_list:
            if len(a) > 0 and a['PrincipalType'] == 'GROUP' and g["group_id"] == a['PrincipalId']:
                print(Fore.YELLOW +
                      f"Account {a['AccountId']} assign to {a['PrincipalType']} {g['group_name']} with permission set {list_permissions_set_arn_name[a['PermissionSetArn']]} or {a['PermissionSetArn']}" + Fore.RESET)

                a["GroupName"] = g['group_name']
                a["PermissionSetName"] = list_permissions_set_arn_name[a['PermissionSetArn']]
        for u in user_list:
            if len(a) > 0 and a['PrincipalType'] == 'USER' and u["UserId"] == a['PrincipalId']:
                print(Fore.YELLOW +
                      f"Account {a['AccountId']} assign to {a['PrincipalType']} {u['UserName']} with permission set {a['PermissionSetArn']} or {list_permissions_set_arn_name[a['PermissionSetArn']]}" + Fore.RESET)
                a["UserName"] = u['UserName']
                a["PermissionSetName"] = list_permissions_set_arn_name[a['PermissionSetArn']]
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
