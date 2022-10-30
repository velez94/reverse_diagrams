import boto3


def list_instances(client=boto3.client('sso-admin', region_name="us-east-2")):
    response = client.list_instances(
        # MaxResults=123,
        # NextToken='string'
    )

    return response["Instances"]


def list_account_assignments(instance_arn, account_id,
                             permission_set_arn,
                             client=boto3.client('sso-admin', region_name="us-east-2"), ):
    response = client.list_account_assignments(
        InstanceArn=instance_arn,
        AccountId=account_id,
        PermissionSetArn=permission_set_arn,
        # MaxResults=123,
        # NextToken='string'
    )

    return response["AccountAssignments"]


def list_permissions_set(instance_arn, client=boto3.client('sso-admin', region_name="us-east-2"), ):
    response = client.list_permission_sets(
        InstanceArn=instance_arn,
        # NextToken='string',
        # MaxResults=123
    )
    print(response)
    return response["PermissionSets"]


def list_permission_provisioned(account_id, instance_arn, client=boto3.client('sso-admin', region_name="us-east-2"), ):
    response = client.list_permission_sets_provisioned_to_account(
        InstanceArn=instance_arn,
        AccountId=account_id,
        # ProvisioningStatus='LATEST_PERMISSION_SET_PROVISIONED'|'LATEST_PERMISSION_SET_NOT_PROVISIONED',
        # MaxResults=123,
        # NextToken='string'
    )
    print(response)
    return response["PermissionSets"]


def extends_permissions_set(permissions_sets, store_arn, client_sso=boto3.client('sso-admin', region_name="us-east-2")):
    l_permissions_set_arn_name = {}
    for p in permissions_sets:
        response = client_sso.describe_permission_set(
            InstanceArn=store_arn,
            PermissionSetArn=p
        )
        # 'PermissionSetName':
        l_permissions_set_arn_name[p] = response["PermissionSet"]["Name"]

        print(response["PermissionSet"]["Name"])
    return l_permissions_set_arn_name
