"""Describe SSO."""
import logging

from boto3 import client


def list_instances(region: str):
    """
    List all instances in the region.

    :param region:
    :return:
    """
    sso_client = client("sso-admin", region_name=region)
    response = sso_client.list_instances()

    return response["Instances"]


# def list account assignments with pagination
def list_account_assignments_pag(
    instance_arn, account_id, permission_set_arn, region, next_token
):
    """
    List all account assignments.

    :param instance_arn:
    :param account_id:
    :param permission_set_arn:
    :param region:
    :return:

    """
    sso_client = client("sso-admin", region_name=region)
    paginator = sso_client.get_paginator("list_account_assignments")
    response_iterator = paginator.paginate(
        InstanceArn=instance_arn,
        AccountId=account_id,
        PermissionSetArn=permission_set_arn,
        PaginationConfig={
            "MaxItems": 1000,
            "PageSize": 20,
            "StartingToken": next_token,
        },
    )
    return response_iterator["AccountAssignments"]


def list_account_assignments(
    instance_arn, account_id, permission_set_arn, region, sso_client
):
    """
    List all account assignments.

    :param sso_client:
    :param instance_arn:
    :param account_id:
    :param permission_set_arn:
    :param region:
    :return:

    """
    response = sso_client.list_account_assignments(
        InstanceArn=instance_arn,
        AccountId=account_id,
        PermissionSetArn=permission_set_arn,
        MaxResults=50,
    )
    account_assignments = response["AccountAssignments"]
    if len(response["AccountAssignments"]) >= 50:
        logging.info("Paginating ...")
        response_iterator = list_account_assignments_pag(
            instance_arn,
            account_id,
            permission_set_arn,
            region,
            next_token=response["NextToken"],
        )
        for response in response_iterator:
            logging.debug(response)
            account_assignments.append(response["AccountAssignments"])
            logging.info(response["AccountAssignments"])
    return account_assignments


def list_permissions_set_pag(instance_arn, region, next_token):
    """
    List all permission set in a region.

    :param next_token:
    :param instance_arn:
    :param region:
    :return:
    """
    sso_client = client("sso-admin", region_name=region)
    paginator = sso_client.get_paginator("list_permission_sets")
    response_iterator = paginator.paginate(
        InstanceArn=instance_arn,
        PaginationConfig={
            "MaxItems": 1000,
            "PageSize": 20,
            "StartingToken": next_token,
        },
    )
    response_iterator = response_iterator.build_full_result()
    return response_iterator["PermissionSets"]


def list_permissions_set(instance_arn, region):
    """
    List all permission set in a region.

    :param instance_arn:
    :param region:
    :return:
    """
    sso_client = client(
        "sso-admin",
        region_name=region,
    )
    response = sso_client.list_permission_sets(InstanceArn=instance_arn, MaxResults=20)
    logging.debug(response)
    permissions_set = response["PermissionSets"]

    if len(response["PermissionSets"]) >= 20:
        logging.info("Paginating ...")
        response_iterator = list_permissions_set_pag(
            instance_arn, region, next_token=response["NextToken"]
        )
        for response in response_iterator:
            logging.debug(response)
            permissions_set.append(response)
            logging.info(response)

    return permissions_set


def list_permission_provisioned(account_id, instance_arn, region):
    """
    List permission provisioned.

    :param account_id:
    :param instance_arn:
    :param region:
    :return:
    """
    l_client = client("sso-admin", region_name=region)
    response = l_client.list_permission_sets_provisioned_to_account(
        InstanceArn=instance_arn,
        AccountId=account_id,
    )
    logging.debug(response)
    return response["PermissionSets"]


def extends_permissions_set(permissions_sets, store_arn, region):
    """
    List all permission set in a region.

    :param permissions_sets:
    :param store_arn:
    :param region:
    :return:
    """
    sso_client = client("sso-admin", region_name=region)
    l_permissions_set_arn_name = {}
    for p in permissions_sets:
        response = sso_client.describe_permission_set(
            InstanceArn=store_arn, PermissionSetArn=p
        )

        l_permissions_set_arn_name[p] = response["PermissionSet"]["Name"]

        logging.debug(response["PermissionSet"]["Name"])
    return l_permissions_set_arn_name
