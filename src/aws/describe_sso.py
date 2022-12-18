import boto3
import logging

def list_instances(client=boto3.client('sso-admin', region_name="us-east-2")):
    response = client.list_instances(

    )

    return response["Instances"]


def list_account_assignments(instance_arn, account_id,
                             permission_set_arn,
                             client=boto3.client('sso-admin', region_name="us-east-2"), ):
    response = client.list_account_assignments(
        InstanceArn=instance_arn,
        AccountId=account_id,
        PermissionSetArn=permission_set_arn,

    )

    return response["AccountAssignments"]


def list_permissions_set(instance_arn, client=boto3.client('sso-admin', region_name="us-east-2"), ):
    response = client.list_permission_sets(
        InstanceArn=instance_arn,

    )
    logging.debug(response)
    return response["PermissionSets"]


def list_permission_provisioned(account_id, instance_arn, client=boto3.client('sso-admin', region_name="us-east-2"), ):
    response = client.list_permission_sets_provisioned_to_account(
        InstanceArn=instance_arn,
        AccountId=account_id,

    )
    logging.debug(response)
    return response["PermissionSets"]


def extends_permissions_set(permissions_sets, store_arn, client_sso=boto3.client('sso-admin', region_name="us-east-2")):
    l_permissions_set_arn_name = {}
    for p in permissions_sets:
        response = client_sso.describe_permission_set(
            InstanceArn=store_arn,
            PermissionSetArn=p
        )

        l_permissions_set_arn_name[p] = response["PermissionSet"]["Name"]

        logging.debug(response["PermissionSet"]["Name"])
    return l_permissions_set_arn_name
