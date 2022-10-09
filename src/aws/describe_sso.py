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
