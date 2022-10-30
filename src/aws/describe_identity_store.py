import boto3
from describe_sso import list_instances, list_account_assignments, list_permissions_set


def list_groups(identity_store_id, client=boto3.client('identitystore', region_name="us-east-2"), ):
    response = client.list_groups(
        IdentityStoreId=identity_store_id,
        # MaxResults=123,
        # NextToken='string',
        # Filters=[
        #    {
        #        'AttributePath': 'string',
        #        'AttributeValue': 'string'
        #    },
        # ]
    )

    return response["Groups"]


def list_users(identity_store_id, client=boto3.client('identitystore', region_name="us-east-2"), ):
    response = client.list_users(
        IdentityStoreId=identity_store_id,
        # MaxResults=123,
        # NextToken='string',
        # Filters=[
        #    {
        #        'AttributePath': 'string',
        #        'AttributeValue': 'string'
        #    },
        # ]
    )

    return response["Users"]


def get_members(identity_store_id, groups, client=boto3.client('identitystore', region_name="us-east-2")):
    group_members = []
    for g in groups:
        response = client.list_group_memberships(
            IdentityStoreId=identity_store_id,
            GroupId=g["GroupId"],
            # MaxResults=123,
            # NextToken='string'
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


boto3.setup_default_session(profile_name='labvel-master', region_name="us-east-2")
client_identity = boto3.client('identitystore', region_name="us-east-2")
client_sso = boto3.client('sso-admin', region_name="us-east-2")

store_instances = list_instances(client=client_sso)
print(store_instances)
store_id = store_instances[0]["IdentityStoreId"]
store_arn = store_instances[0]["InstanceArn"]
print("list groups")
l_groups = list_groups(store_id, client=client_identity)
print(l_groups)

print("Get memeber group")

m_groups = get_members(store_id, l_groups, client=client_identity)

print(m_groups)

print("Extend Group Members")
l_users = list_users(store_id, client=client_identity)
print(l_users)
c_users_and_groups = complete_group_members(m_groups, l_users)

print(c_users_and_groups)
# Get Account assingments
permissions_set = list_permissions_set(instance_arn=store_arn, client=client_sso)
l_permissions_set_arn_name = {}
account_assignments = []
for p in permissions_set:
    response = client_sso.describe_permission_set(
        InstanceArn=store_arn,
        PermissionSetArn=p
    )
    # 'PermissionSetName':
    l_permissions_set_arn_name[p] = response["PermissionSet"]["Name"]

    print(response["PermissionSet"]["Name"])
    # TODO make for each account
    accounts = ["029921763173", "105171185823"]
    for ac in accounts:
        assign = list_account_assignments(instance_arn=store_arn, account_id=ac, client=client_sso,
                                          permission_set_arn=p)
        print("AccountAssignments ", assign)
        for a in assign:
            account_assignments.append(a)
final_account_assignments = {}
for a in account_assignments:
    for g in c_users_and_groups:
        if len(a) > 0 and a['PrincipalType'] == 'GROUP' and g["group_id"] == a['PrincipalId']:
            print(
                f"Account {a['AccountId']} assign to {a['PrincipalType']} {g['group_name']} with permission set {l_permissions_set_arn_name[a['PermissionSetArn']]} or {a['PermissionSetArn']}")

            a["GroupName"] = g['group_name']
            a["PermissionSetName"] = l_permissions_set_arn_name[a['PermissionSetArn']]
    for u in l_users:
        if len(a) > 0 and a['PrincipalType'] == 'USER' and u["UserId"] == a['PrincipalId']:
            print(
                f"Account {a['AccountId']} assign to {a['PrincipalType']} {u['UserName']} with permission set {a['PermissionSetArn']} or {l_permissions_set_arn_name[a['PermissionSetArn']]}")
            a["UserName"] = u['UserName']
            a["PermissionSetName"] = l_permissions_set_arn_name[a['PermissionSetArn']]
print(f"Account Assignments --> {account_assignments}")

accounts = [
    {'account': '029921763173', 'name': 'Master',
     'parents': [{'Id': 'ou-w3ow-93hiq3zr', 'Type': 'ORGANIZATIONAL_UNIT'}]},
    {'account': '105171185823', 'name': 'DevSecOps',
     'parents': [{'Id': 'ou-w3ow-5qsqi8b5', 'Type': 'ORGANIZATIONAL_UNIT'}]}
]
for ac in accounts:
    final_account_assignments[ac["name"]] = []
    for a in account_assignments:
        print(a)
        if ac["account"] == a["AccountId"]:
            final_account_assignments[ac["name"]].append(a)
            l = len(final_account_assignments[ac["name"]])
            print(l)

    print(f"Final Account Assignments: {final_account_assignments}")
