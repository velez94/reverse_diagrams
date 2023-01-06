import logging
import re

def format_name_string(a_string, action=None):
    """

    :param a_string:
    :param action:
    :return: sring --terragrunt-json-out
    """
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

                for m in value:
                    logging.debug(m)

                    if "GroupName" in m.keys():

                        print(f"\n{ident}with Cluster('Group: {m['GroupName']}'):", file=f)
                        print(f"\n{ident}{ident}gg_{format_name_string(m['GroupName'], 'format')}=Users(\"{format_name_string(m['GroupName'],'split')}\")\n"
                              f"{ident}{ident}gg_{format_name_string(m['GroupName'], 'format')} \\\n"
                              f"{ident}{ident}{ident}- Edge(color=\"brown\", style=\"dotted\") \\\n"
                              f"{ident}{ident}{ident}- IAMPermissions(\"{format_name_string(m['PermissionSetName'], 'split')}\")",
                              file=f)

                    if "UserName" in m.keys():

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
                            f"\n{ident}ou_{format_name_string(o['Name'],'format')}>> OrganizationsAccount(\"{c['account']}\\n{format_name_string(c['name'], action='split')}\")",
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

                users += "]"
                print(f"\n{ident}{ident}gg_{l}= {users}", file=f)
            else:
                print(f"\n{ident}gg_{l}= Users(\"{format_name_string(g['group_name'], 'split')}\")", file=f)

