"""Create Mapper files."""
import logging
import os.path
import re
from pathlib import Path


def format_name_string(a_string, action=None):
    """
    Format name strings to avoid no allowed characters.

    :param a_string:
    :param action:
    :return: sring --terragrunt-json-out
    """
    if action == "split":
        if len(a_string) > 17:
            a_string = a_string[:16] + "\\n" + a_string[16:]
    elif action == "format":
        a_string = re.sub("[-!?@.+]", "", a_string)
        a_string = a_string.replace(" ", "")
    return a_string


def create_sso_mapper_complete(template_file, acc_assignments, d_groups):
    """
    Create sso mapper.

    :param template_file: Template file
    :param acc_assignments:
    :param d_groups:
    :return:
    """
    with open(template_file, "a") as f:
        ident = "        "

        for key, value in acc_assignments.items():
            if len(value) > 0:
                print(f"\n    with Cluster('Account: {key}'):", file=f)
                for m in value:
                    logging.debug(m)

                    if "GroupName" in m.keys():
                        print(
                            f"\n{ident}with Cluster('Group: {m['GroupName']}'):", file=f
                        )
                        print(
                            f"\n{ident}{ident}gg_{format_name_string(m['GroupName'], 'format')}=Users(\"{format_name_string(m['GroupName'], 'split')}\")\n"
                            f"{ident}{ident}gg_{format_name_string(m['GroupName'], 'format')} \\\n"
                            f"{ident}{ident}{ident}- Edge(color=\"brown\", style=\"dotted\", label=\"Permissions Set\") \\\n"
                            f"{ident}{ident}{ident}- IAMPermissions(\"{format_name_string(m['PermissionSetName'], 'split')}\")\n"
                            f"{ident}{ident}mm_{format_name_string(m['GroupName'], 'format')}={create_users_men(d_groups[m['GroupName']]['members'])} \n"  # ['members']}
                            f"{ident}{ident}gg_{format_name_string(m['GroupName'], 'format')} \\\n"
                            f"{ident}{ident}{ident}- Edge(color=\"darkgreen\", style=\"dotted\", label=\"Member\") \\\n"
                            f"{ident}{ident}{ident}- mm_{format_name_string(m['GroupName'], 'format')} \n",
                            file=f,
                        )

                    if "UserName" in m.keys():
                        print(
                            f"\n{ident}with Cluster('User: {m['UserName']}'):", file=f
                        )
                        print(
                            f"\n{ident}{ident}uu_{format_name_string(m['UserName'], 'format')}=User(\"{format_name_string(m['UserName'], 'split')}\")\n"
                            f"{ident}{ident}uu_{format_name_string(m['UserName'], 'format')} \\\n"
                            f"{ident}{ident}{ident}- Edge(color=\"brown\", style=\"dotted\") \\\n"
                            f"{ident}{ident}{ident}- IAMPermissions(\"{format_name_string(m['PermissionSetName'], 'split')}\")",
                            file=f,
                        )
                        # print(f"\n{ident}ou >> uu_{format_name_string(m['UserName'])}\n", file=f)
    f.close()


def create_file(template_content, file_name, directory_path="."):
    """
    Create file into directory.

    :param template_content:
    :param file_name:
    :param directory_path:
    :return:
    """
    # create directory if not exists and is different from .
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        logging.debug(f"Directory {directory_path} created")
    f_path = Path(os.path.join(directory_path, file_name))
    with open(f_path, "w") as f:
        f.write(template_content)
    f.close()


def find_ou_name(ous, search_id):
    """
    Find OU Name in list.

    :param ous:
    :param search_id:
    :return:
    """
    for a in ous:
        if a["Id"] == search_id:
            return a["Name"]


def create_mapper(template_file, org, root_id, list_ous, list_accounts):
    """
    Create complete mapper file.

    :param template_file:
    :param org:
    :param root_id:
    :param list_ous:
    :param list_accounts:
    :return:
    """
    with open(template_file, "a") as f:
        ident = "        "
        print("\n    with Cluster('Organizations'):", file=f)
        print(
            f"\n{ident}oo = Organizations('{org['Id']}\\n{org['MasterAccountId']}\\n{root_id}')",
            file=f,
        )
        for a, i in zip(list_ous, range(len(list_ous))):
            print(
                f"\n{ident}ou_{format_name_string(a['Name'], 'format')}= OrganizationsOrganizationalUnit(\"{a['Id']}\\n{a['Name']}\")",
                file=f,
            )

            for p in a["Parents"]:
                if p["Type"] == "ROOT":
                    print(
                        f"\n{ident}oo>> ou_{format_name_string(a['Name'], 'format')}",
                        file=f,
                    )
                if p["Type"] == "ORGANIZATIONAL_UNIT":
                    print(
                        f"\n{ident}ou_{format_name_string(find_ou_name(list_ous, p['Id']), 'format')}>> ou_{format_name_string(a['Name'], 'format')}",
                        file=f,
                    )

        for c, i in zip(list_accounts, range(len(list_accounts))):
            # print(f"\n    aa_{i}= OrganizationsAccount(\"{c['account']}\")", file=f)
            for p in c["parents"]:
                if p["Type"] == "ROOT":
                    print(
                        f"\n{ident}oo >> OrganizationsAccount(\"{c['account']}\\n{c['name']}\")",
                        file=f,
                    )

                for o, j in zip(list_ous, range(len(list_ous))):
                    if p["Id"] == o["Id"] and p["Type"] == "ORGANIZATIONAL_UNIT":
                        print(
                            f"\n{ident}ou_{format_name_string(o['Name'], 'format')}>> OrganizationsAccount(\"{c['account']}\\n{format_name_string(c['name'], action='split')}\")",
                            file=f,
                        )

        f.close()


def create_sso_mapper(template_file, group_and_members):
    """
    Create sso mapper.

    :param template_file:
    :param group_and_members:
    :return:
    """
    with open(template_file, "a") as f:
        ident = "        "
        print("\n    with Cluster('Groups'):", file=f)
        for g, ll in zip(group_and_members, range(len(group_and_members))):
            if len(g["members"]) > 0:
                print(f"\n{ident}with Cluster(\"{g['group_name']}\"):", file=f)
                users = "["
                for m in g["members"]:
                    user_name = m["MemberId"]["UserName"]
                    users += f"User(\"{format_name_string(user_name, 'split')}\"),"

                users += "]"
                print(f"\n{ident}{ident}gg_{ll}= {users}", file=f)
            else:
                print(
                    f"\n{ident}gg_{ll}= Users(\"{format_name_string(g['group_name'], 'split')}\")",
                    file=f,
                )


def create_users_men(members):
    """
    Create member users.

    :param members:
    :return:
    """
    if len(members) > 0:
        users = "["
        for m in members:
            user_name = m["MemberId"]["UserName"]
            users += f"User(\"{format_name_string(user_name, 'split')}\"),"

        users += "]"

    else:
        users = "[]"

    return users
