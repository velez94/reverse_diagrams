from .graph_template import graph_template, graph_template_sso, graph_template_sso_complete
import re

root = 'r-w3ow'
org_data = {'Id': 'o-9tlhkjyoii', 'Arn': 'arn:aws:organizations::029921763173:organization/o-9tlhkjyoii',
            'FeatureSet': 'ALL',
            'MasterAccountArn': 'arn:aws:organizations::029921763173:account/o-9tlhkjyoii/029921763173',
            'MasterAccountId': '029921763173',
            'MasterAccountEmail': 'velez94@protonmail.com',
            'AvailablePolicyTypes': [{'Type': 'SERVICE_CONTROL_POLICY', 'Status': 'ENABLED'}]}

ous = [
    {'Id': 'ou-w3ow-oegm0al0', 'Arn': 'arn:aws:organizations::029921763173:ou/o-9tlhkjyoii/ou-w3ow-oegm0al0',
     'Name': 'Research', 'Parents': [{'Id': 'r-w3ow', 'Type': 'ROOT'}]},
    {'Id': 'ou-w3ow-k24p2opx', 'Arn': 'arn:aws:organizations::029921763173:ou/o-9tlhkjyoii/ou-w3ow-k24p2opx',
     'Name': 'Dev', 'Parents': [{'Id': 'r-w3ow', 'Type': 'ROOT'}]},
    {'Id': 'ou-w3ow-93hiq3zr', 'Arn': 'arn:aws:organizations::029921763173:ou/o-9tlhkjyoii/ou-w3ow-93hiq3zr',
     'Name': 'Core', 'Parents': [{'Id': 'r-w3ow', 'Type': 'ROOT'}]},
    {'Id': 'ou-w3ow-5qsqi8b5', 'Arn': 'arn:aws:organizations::029921763173:ou/o-9tlhkjyoii/ou-w3ow-5qsqi8b5',
     'Name': 'Custom', 'Parents': [{'Id': 'r-w3ow', 'Type': 'ROOT'}]},
    {'Id': 'ou-w3ow-w7dzhzcz', 'Arn': 'arn:aws:organizations::029921763173:ou/o-9tlhkjyoii/ou-w3ow-w7dzhzcz',
     'Name': 'Shared', 'Parents': [{'Id': 'r-w3ow', 'Type': 'ROOT'}]},
    {'Id': 'ou-w3ow-i9xzgb9x', 'Arn': 'arn:aws:organizations::029921763173:ou/o-9tlhkjyoii/ou-w3ow-i9xzgb9x',
     'Name': 'NetstedOU', 'Parents': [{'Id': 'ou-w3ow-5qsqi8b5', 'Type': 'ORGANIZATIONAL_UNIT'}]}]

accounts = [
    {'account': '884478634998', 'name': 'Log archive',
     'parents': [{'Id': 'ou-w3ow-93hiq3zr', 'Type': 'ORGANIZATIONAL_UNIT'}]},
    {'account': '582441254763', 'name': 'Prod',
     'parents': [{'Id': 'ou-w3ow-5qsqi8b5', 'Type': 'ORGANIZATIONAL_UNIT'}]},
    {'account': '895882538541', 'name': 'Audit',
     'parents': [{'Id': 'ou-w3ow-93hiq3zr', 'Type': 'ORGANIZATIONAL_UNIT'}]},
    {'account': '105171185823', 'name': 'DevSecOps',
     'parents': [{'Id': 'ou-w3ow-w7dzhzcz', 'Type': 'ORGANIZATIONAL_UNIT'}]},
    {'account': '994261317734', 'name': 'LabVelCT',
     'parents': [{'Id': 'ou-w3ow-k24p2opx', 'Type': 'ORGANIZATIONAL_UNIT'}]},
    {'account': '155794986228', 'name': 'SharedServices',
     'parents': [{'Id': 'ou-w3ow-w7dzhzcz', 'Type': 'ORGANIZATIONAL_UNIT'}]},
    {'account': '029921763173', 'name': 'Alejandro Velez', 'parents': [{'Id': 'r-w3ow', 'Type': 'ROOT'}]},
    {'account': '571340586587', 'name': 'Dev',
     'parents': [{'Id': 'ou-w3ow-k24p2opx', 'Type': 'ORGANIZATIONAL_UNIT'}]}]

groups = [
    {'group_id': '9a672b3314-f46f413e-44d7-4d3d-918b-f86721413097', 'group_name': 'AWSSecurityAuditors', 'members': []},
    {'group_id': '9a672b3314-c481fbee-8062-432a-8b87-eeaa36b763a8', 'group_name': 'AWSLogArchiveAdmins', 'members': []},
    {'group_id': '318bc590-a071-70f5-63f6-ab21233e4e33', 'group_name': 'DevSecOps_Admins', 'members': [
        {'IdentityStoreId': 'd-9a672b3314', 'MembershipId': '51bbe5a0-7001-7010-d7c0-46f5044d014e',
         'GroupId': '318bc590-a071-70f5-63f6-ab21233e4e33',
         'MemberId': {'UserId': '010be510-1061-70df-8274-96526bc47eb7', 'UserName': 'DevSecOpsAdm'}}]},
    {'group_id': '9a672b3314-ff479c57-03cb-440e-8902-be8ea9d7d25b', 'group_name': 'AWSLogArchiveViewers',
     'members': []},
    {'group_id': '9a672b3314-b858476a-2ef9-4018-90e7-29e5e4bc4388', 'group_name': 'AWSSecurityAuditPowerUsers',
     'members': []},
    {'group_id': '9a672b3314-faf36c54-a70c-4db6-aefc-e5ac006ad5a1', 'group_name': 'AWSAuditAccountAdmins',
     'members': []},
    {'group_id': '9a672b3314-f8065505-3174-4d46-a1b4-f134fd0ca2fc', 'group_name': 'AWSAccountFactory', 'members': [
        {'IdentityStoreId': 'd-9a672b3314', 'MembershipId': 'e18bb590-9031-70a0-5469-42c9799e8a6b',
         'GroupId': '9a672b3314-f8065505-3174-4d46-a1b4-f134fd0ca2fc',
         'MemberId': {'UserId': '9a672b3314-bd21c8b3-1aa0-4922-9374-92321b4979bf',
                      'UserName': 'velez94@protonmail.com'}}]},
    {'group_id': '9a672b3314-7f743f07-169a-4172-bdbc-561e7908e463', 'group_name': 'AWSServiceCatalogAdmins',
     'members': []},
    {'group_id': '9a672b3314-43117aac-887b-48ee-af49-b6b6cd059199', 'group_name': 'AWSControlTowerAdmins', 'members': [
        {'IdentityStoreId': 'd-9a672b3314', 'MembershipId': 'e14b3500-3051-70b2-25b7-d5729d383061',
         'GroupId': '9a672b3314-43117aac-887b-48ee-af49-b6b6cd059199',
         'MemberId': {'UserId': '9a672b3314-bd21c8b3-1aa0-4922-9374-92321b4979bf',
                      'UserName': 'velez94@protonmail.com'}}]}]

account_assignments = {'Master': [{'AccountId': '029921763173',
                                   'PermissionSetArn': 'arn:aws:sso:::permissionSet/ssoins-66845289d6823727/ps-ab185f05acde5e90',
                                   'PrincipalType': 'GROUP',
                                   'PrincipalId': '9a672b3314-b858476a-2ef9-4018-90e7-29e5e4bc4388',
                                   'GroupName': 'AWSSecurityAuditPowerUsers',
                                   'PermissionSetName': 'AWSPowerUserAccess'},
                                  {'AccountId': '029921763173',
                                   'PermissionSetArn': 'arn:aws:sso:::permissionSet/ssoins-66845289d6823727/ps-7cc34a5a03379f6f',
                                   'PrincipalType': 'GROUP',
                                   'PrincipalId': '9a672b3314-f8065505-3174-4d46-a1b4-f134fd0ca2fc',
                                   'GroupName': 'AWSAccountFactory',
                                   'PermissionSetName': 'AWSServiceCatalogEndUserAccess'},
                                  {'AccountId': '029921763173',
                                   'PermissionSetArn': 'arn:aws:sso:::permissionSet/ssoins-66845289d6823727/ps-21058a9d1f62c7e2',
                                   'PrincipalType': 'GROUP',
                                   'PrincipalId': '9a672b3314-43117aac-887b-48ee-af49-b6b6cd059199',
                                   'GroupName': 'AWSControlTowerAdmins', 'PermissionSetName': 'AWSAdministratorAccess'},
                                  {'AccountId': '029921763173',
                                   'PermissionSetArn': 'arn:aws:sso:::permissionSet/ssoins-66845289d6823727/ps-cf27b0efdc941a09',
                                   'PrincipalType': 'GROUP',
                                   'PrincipalId': '9a672b3314-f46f413e-44d7-4d3d-918b-f86721413097',
                                   'GroupName': 'AWSSecurityAuditors', 'PermissionSetName': 'AWSReadOnlyAccess'},
                                  {'AccountId': '029921763173',
                                   'PermissionSetArn': 'arn:aws:sso:::permissionSet/ssoins-66845289d6823727/ps-83e7c23c8b2df8b3',
                                   'PrincipalType': 'GROUP',
                                   'PrincipalId': '9a672b3314-7f743f07-169a-4172-bdbc-561e7908e463',
                                   'GroupName': 'AWSServiceCatalogAdmins',
                                   'PermissionSetName': 'AWSServiceCatalogAdminFullAccess'}],
                       'DevSecOps': [
                           {'AccountId': '105171185823',
                            'PermissionSetArn': 'arn:aws:sso:::permissionSet/ssoins-66845289d6823727/ps-ab185f05acde5e90',
                            'PrincipalType': 'GROUP', 'PrincipalId': '9a672b3314-b858476a-2ef9-4018-90e7-29e5e4bc4388',
                            'GroupName': 'AWSSecurityAuditPowerUsers', 'PermissionSetName': 'AWSPowerUserAccess'},
                           {'AccountId': '105171185823',
                            'PermissionSetArn': 'arn:aws:sso:::permissionSet/ssoins-66845289d6823727/ps-21058a9d1f62c7e2',
                            'PrincipalType': 'GROUP', 'PrincipalId': '318bc590-a071-70f5-63f6-ab21233e4e33',
                            'GroupName': 'DevSecOps_Admins',
                            'PermissionSetName': 'AWSAdministratorAccess'},
                           {'AccountId': '105171185823',
                            'PermissionSetArn': 'arn:aws:sso:::permissionSet/ssoins-66845289d6823727/ps-21058a9d1f62c7e2',
                            'PrincipalType': 'USER',
                            'PrincipalId': '81bb65b0-40f1-7082-2b16-83138563c37b',
                            'UserName': 'w.alejovl+devsecops-labs@gmail.com',
                            'PermissionSetName': 'AWSAdministratorAccess'},
                           {'AccountId': '105171185823',
                            'PermissionSetArn': 'arn:aws:sso:::permissionSet/ssoins-66845289d6823727/ps-cf27b0efdc941a09',
                            'PrincipalType': 'GROUP', 'PrincipalId': '9a672b3314-f46f413e-44d7-4d3d-918b-f86721413097',
                            'GroupName': 'AWSSecurityAuditors', 'PermissionSetName': 'AWSReadOnlyAccess'},
                           {'AccountId': '105171185823',
                            'PermissionSetArn': 'arn:aws:sso:::permissionSet/ssoins-66845289d6823727/ps-c6046bbbf15aaafc',
                            'PrincipalType': 'GROUP',
                            'PrincipalId': '9a672b3314-43117aac-887b-48ee-af49-b6b6cd059199',
                            'GroupName': 'AWSControlTowerAdmins',
                            'PermissionSetName': 'AWSOrganizationsFullAccess'}]}

from diagrams.aws.general import Users, User


def format_name_string(a_string, action=None):
    if action == 'split':
        if len(a_string) > 17:
            a_string = a_string[:16] + "\\n" + a_string[16:]
    elif action== 'format':

        a_string = re.sub('[-!?@.+]', '', a_string)
        a_string = a_string.replace(" ", '')
    return a_string


def create_sso_mapper_complete(template_file, acc_assignments):
    with open(template_file, 'a') as f:
        ident = "        "

        for key, value in acc_assignments.items():
            print(f"\n    with Cluster('Account: {key}'):", file=f)
            if len(value) > 0:
                # print(value[0])
                # groups = "groups= ["
                for m in value:
                    print(m)

                    if "GroupName" in m.keys():
                        # groups += f"Users(\"{m['GroupName']}\"),"
                        # groups += "]"
                        print(f"\n{ident}with Cluster('Group: {m['GroupName']}'):", file=f)
                        print(f"\n{ident}{ident}gg_{format_name_string(m['GroupName'], 'format')}=Users(\"{format_name_string(m['GroupName'],'split')}\")\n"
                              f"{ident}{ident}gg_{format_name_string(m['GroupName'], 'format')} \\\n"
                              f"{ident}{ident}{ident}- Edge(color=\"brown\", style=\"dotted\") \\\n"
                              f"{ident}{ident}{ident}- IAMPermissions(\"{format_name_string(m['PermissionSetName'], 'split')}\")",
                              file=f)
                        # print(f"\n{ident}ou >> gg_{m['GroupName']}\n", file=f)
                    if "UserName" in m.keys():
                        # groups += f"Users(\"{m['GroupName']}\"),"
                        # groups += "]"
                        print(f"\n{ident}with Cluster('User: {m['UserName']}'):", file=f)
                        print(
                            f"\n{ident}{ident}uu_{format_name_string(m['UserName'], 'format')}=User(\"{format_name_string(m['UserName'],'split')}\")\n"
                            f"{ident}{ident}uu_{format_name_string(m['UserName'],'format')} \\\n"
                            f"{ident}{ident}{ident}- Edge(color=\"brown\", style=\"dotted\") \\\n"
                            f"{ident}{ident}{ident}- IAMPermissions(\"{format_name_string(m['PermissionSetName'],'split')}\")",
                            file=f)
                        # print(f"\n{ident}ou >> uu_{format_name_string(m['UserName'])}\n", file=f)
    f.close()


def create_file(template_content, file_name):
    with open(file_name, 'w') as f:
        f.write(template_content)
    f.close()


def find_ou_name(ous, search_id):
    for a in ous:
        if a["Id"] == search_id:
            return a["Name"]


def create_mapper(template_file, org, root_id, list_ous, list_accounts):
    with open(template_file, 'a') as f:
        ident = "        "
        print(f"\n    with Cluster('Organizations'):", file=f)
        print(f"\n{ident}oo = Organizations('{org['Id']}\\n{org['MasterAccountId']}\\n{root_id}')", file=f)
        for a, i in zip(list_ous, range(len(list_ous))):
            print(
                f"\n{ident}ou_{format_name_string(a['Name'], 'format')}= OrganizationsOrganizationalUnit(\"{a['Id']}\\n{a['Name']}\")",
                file=f)

            for p in a["Parents"]:
                if p['Type'] == 'ROOT':
                    print(f"\n{ident}oo>> ou_{format_name_string(a['Name'],'format')}", file=f)
                if p['Type'] == 'ORGANIZATIONAL_UNIT':
                    print(
                        f"\n{ident}ou_{format_name_string(find_ou_name(list_ous, p['Id']),'format')}>> ou_{format_name_string(a['Name'],'format')}",
                        file=f)

        for c, i in zip(list_accounts, range(len(list_accounts))):
            # print(f"\n    aa_{i}= OrganizationsAccount(\"{c['account']}\")", file=f)
            for p in c["parents"]:
                if p['Type'] == 'ROOT':
                    print(f"\n{ident}oo >> OrganizationsAccount(\"{c['account']}\\n{c['name']}\")", file=f)

                for o, j in zip(list_ous, range(len(list_ous))):
                    if p['Id'] == o["Id"] and p['Type'] == 'ORGANIZATIONAL_UNIT':
                        print(
                            f"\n{ident}ou_{format_name_string(o['Name'],'format')}>> OrganizationsAccount(\"{c['account']}\\n{c['name']}\")",
                            file=f)

        f.close()


def create_sso_mapper(template_file, group_and_members):
    with open(template_file, 'a') as f:
        ident = "        "
        print(f"\n    with Cluster('Groups'):", file=f)
        for g, l in zip(group_and_members, range(len(group_and_members))):

            if len(g["members"]) > 0:
                print(f"\n{ident}with Cluster(\"{g['group_name']}\"):", file=f)
                users = "["
                for m in g["members"]:
                    user_name = m["MemberId"]["UserName"]
                    users += f"User(\"{format_name_string(user_name,'split')}\"),"
                    # print(f"\n{ident}gg_{l}>> User(\"{user_name}\")", file=f)
                users += "]"
                print(f"\n{ident}{ident}gg_{l}= {users}", file=f)
            else:
                print(f"\n{ident}gg_{l}= Users(\"{format_name_string(g['group_name'], 'split')}\")", file=f)


create_file(template_content=graph_template, file_name="graph_org.py")
create_file(template_content=graph_template_sso, file_name="graph_sso.py")
create_file(template_content=graph_template_sso_complete, file_name="graph_sso_complete.py")

# create_mapper(template_file="graph_org.py", org=org_data, root_id=root, ous=ous)
