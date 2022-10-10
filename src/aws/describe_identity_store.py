import boto3
from describe_sso import list_instances


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

def complete_group_members(group_members,users_list):
    for m in group_members:
        for u in m["members"]:
            for a in users_list:
                if u["MemberId"]["UserId"]== a["UserId"]:
                    u["MemberId"]["UserName"] = a["UserName"]

    return group_members
"""

boto3.setup_default_session(profile_name='labvel-master', region_name="us-east-2")
client_identity = boto3.client('identitystore', region_name="us-east-2")
client_sso = boto3.client('sso-admin', region_name="us-east-2")

store_instances = list_instances(client=client_sso)
print(store_instances)
store_id = store_instances[0]["IdentityStoreId"]
print("list groups")
l_groups = list_groups(store_id, client=client_identity)
print(l_groups)

print("Get memeber group")

m_groups = get_members(store_id, l_groups, client=client_identity)

print(m_groups)

print("Extend Group Members")
l_users= list_users(store_id,client=client_identity)
print(l_users)
c_users_and_groups = complete_group_members(m_groups,l_users)

print(c_users_and_groups)

"""