"""Describe Organizations."""
import logging
import os

import emoji
from colorama import Fore

from ..dgms.graph_mapper import create_file, create_mapper, find_ou_name
from ..dgms.graph_template import graph_template
from ..reports.save_results import save_results
from .describe_sso import client


def describe_organization(region, org_client):
    """
    Describe the organization.

    :param region: AWS Region
    :return:
    """
    print(f"{Fore.GREEN}❇️ Describe Organization {Fore.RESET}")

    organization = org_client.describe_organization()
    organization = organization["Organization"]
    return organization


def list_roots(region):
    """
    List the roots.

    :param region: AWS Region
    :return:
    """
    org_client = client("organizations", region_name=region)
    roots = org_client.list_roots()
    return roots["Roots"]


# def list organizational units pagination
def list_organizational_units_pag(parent_id, region, next_token=None):
    """
    List organizational Units with pagination.

    :param parent_id:
    :param region:
    :param next_token:
    :return:
    """
    org_client = client("organizations", region_name=region)
    paginator = org_client.get_paginator("list_organizational_units_for_parent")
    response_iterator = paginator.paginate(
        ParentId=parent_id,
        PaginationConfig={"MaxItems": 1000, "PageSize": 4, "StartingToken": next_token},
    )
    response_iterator = response_iterator.build_full_result()
    return response_iterator["OrganizationalUnits"]


def list_organizational_units(parent_id, region, org_client, org_units=None):
    """
    List Organizational units.

    :param org_client:
    :param parent_id:
    :param region:
    :param org_units:
    :return:
    """

    if org_units is None:
        org_units = []
    ous = org_client.list_organizational_units_for_parent(
        ParentId=parent_id,
        MaxResults=20,
    )
    ous = ous["OrganizationalUnits"]

    if len(ous) >= 20:
        logging.info("Paginating ...")
        add_ous = list_organizational_units_pag(parent_id=parent_id,
                                                region=region, next_token=ous["NextToken"]
                                                )
        for ou in add_ous:
            ous.append(ou)
        logging.debug(add_ous)

    for o in ous:
        org_units.append(o)
    logging.debug(
        f"The parent Id is: {parent_id}",
    )
    logging.debug(ous)
    if len(ous) > 0:
        for ou in ous:
            logging.debug(ou)
            if "Id" in ou.keys():
                logging.debug(f"Search nested for: {ou['Name']}")
                ous_next = list_organizational_units(parent_id=ou["Id"],
                                                     region=region, org_units=org_units,
                                                     org_client=org_client,
                                                     )
                logging.debug(ous_next)
                if len(ous_next) > 0:
                    logging.debug("Find Nested")

    return org_units


def list_parents(child_id, region):
    """
    List the parents of a child.

    :param child_id:
    :param region:
    :return:
    """
    org_client = client("organizations", region_name=region)
    response = org_client.list_parents(
        ChildId=child_id,
    )
    return response["Parents"]


def index_ous(list_ous, region):
    """
    Index the parents of a child.

    :param list_ous:
    :param region:
    :return list_ous:

    """
    org_client = client("organizations", region_name=region)
    for ou in list_ous:
        if "Id" in ou.keys() and len(ou) > 0:
            response = org_client.list_parents(
                ChildId=ou["Id"],
            )
            logging.debug(response["Parents"])
            ou["Parents"] = response["Parents"]
    return list_ous


def list_accounts_pag(region, next_token: str = None):
    """
    List accounts with pagination.

    :param region:
    :param next_token:
    :return:
    """
    org_client = client("organizations", region_name=region)
    paginator = org_client.get_paginator("list_accounts")
    response_iterator = paginator.paginate(
        PaginationConfig={"MaxItems": 1000, "PageSize": 20, "StartingToken": next_token}
    )
    response = response_iterator.build_full_result()
    logging.info(response_iterator.build_full_result())
    return response["Accounts"]


def list_accounts(region, org_client):
    """
    List accounts.

    :param org_client:
    :param region:
    :return:
    """

    accounts = org_client.list_accounts()
    logging.info(accounts)
    l_account = accounts["Accounts"]
    logging.info(len(accounts["Accounts"]))
    if len(accounts["Accounts"]) >= 20:
        logging.info("Paginating ...")
        ad_accounts = list_accounts_pag(region=region, next_token=accounts["NextToken"])
        for ad in ad_accounts:
            l_account.append(ad)
        logging.info(f"You Organizations have {len(l_account)} Accounts")

    return l_account


def index_accounts(list_account, region, org_client):
    """
    Index accounts.

    :param list_account:
    :param region:
    :return:
    """
    accounts = []

    for a in list_account:
        response = org_client.list_parents(
            ChildId=a["Id"],
        )

        accounts.append(
            {"account": a["Id"], "name": a["Name"], "parents": response["Parents"]}
        )
    return accounts


# create organization complete map
def find_ou_index(ous, search_id):
    """
    Find OU Name in list.

    :param ous:
    :param search_id:
    :return:
    """
    for a in ous:
        if a["Id"] == search_id:
            return a


# search ou in map
def search_ou_map(map_ou: dict, ou_id, level=0, tree="."):
    """
    Search OU in map.

    :param tree:
    :param level:
    :param map_ou:
    :param ou_id:
    :return:
    """
    for a in map_ou.keys():
        # print(f'Searching {ou_id}... in {map_ou[a]["nestedOus"]}')

        if len(map_ou[a]["nestedOus"]) > 0:
            level += 1
            tree += f".{a}"

            if ou_id in map_ou[a]["nestedOus"].keys():
                # search_ou_map(map_ou=map_ou[a]["nestedOus"], ou_id=ou_id, level=level, tree=tree)

                return map_ou[a]
            # else:
            # search_ou_map(map_ou=map_ou[a]["nestedOus"], ou_id=ou_id, level=level, tree=tree)
    return None


def init_org_complete(
        root_id,
        org,
        list_ous,
):
    """
    Init organization dictionary.

    :param root_id:
    :param org:
    :param list_ous:
    :return:
    """
    organizations_complete = {
        "rootId": root_id,
        "masterAccountId": org["MasterAccountId"],
        "noOutAccounts": [],
        "organizationalUnits": {},
    }
    # Iterate in ous for getting ous tree
    for a, i in zip(list_ous, range(len(list_ous))):
        for p in a["Parents"]:
            if p["Type"] == "ROOT":
                organizations_complete["organizationalUnits"][a["Name"]] = {
                    "Id": a["Id"],
                    "Name": a["Name"],
                    "accounts": {},
                    "nestedOus": {},
                }
    return organizations_complete


# create organization complete map
def map_organizations_complete(
        organizations_complete: dict,
        list_ous,
        llist_accounts,
        reference_outs_list,
):
    """
    Create complete mapper file.

    :param reference_outs_list:
    :param organizations_complete:
    :param list_ous:
    :param llist_accounts:
    :return:
    """
    # Iterate in ous for getting ous tree
    for a, i in zip(list_ous, range(len(list_ous))):
        for p in a["Parents"]:
            if p["Type"] == "ORGANIZATIONAL_UNIT":
                o = find_ou_name(reference_outs_list, p["Id"])

                if o not in organizations_complete["organizationalUnits"].keys():
                    p = search_ou_map(
                        organizations_complete["organizationalUnits"], ou_id=o
                    )
                    o = p["Name"]

                organizations_complete["organizationalUnits"][o]["nestedOus"][
                    find_ou_name(reference_outs_list, a["Id"])
                ] = {"Id": a["Id"], "Name": a["Name"], "accounts": [], "nestedOus": {}}
                # print(organizations_complete["organizationalUnits"][o]["nestedOus"])
                if (
                        len(organizations_complete["organizationalUnits"][o]["nestedOus"])
                        > 0
                ):
                    new_list_ous = organizations_complete["organizationalUnits"][o][
                        "nestedOus"
                    ]

                    new_list_ous = plop_dict_out(ous_list=list_ous, ou=new_list_ous)
                    organizations_complete = map_organizations_complete(
                        organizations_complete=organizations_complete,
                        list_ous=new_list_ous,
                        llist_accounts=llist_accounts,
                        reference_outs_list=reference_outs_list,
                    )

    return organizations_complete


def plop_dict_out(
        ous_list: list,
        ou,
):
    """
    Clean list.

    :param ous_list:
    :param ou:
    :return:
    """
    for o in ou.keys():
        # for c in ou.keys():
        for unit in ous_list:
            if unit["Id"] == ou[o]["Id"]:
                ous_list.remove(unit)

    return ous_list


def set_accounts_tree(llist_accounts, organizations_complete, list_ous):
    """
    Set accounts tree.

    :param llist_accounts:
    :param organizations_complete:
    :param list_ous:
    :return:
    """
    # Iterate in list accounts to get parent ous
    for c, i in zip(llist_accounts, range(len(llist_accounts))):
        # print(f"\n    aa_{i}= OrganizationsAccount(\"{c['account']}\")", file=f)
        for p in c["parents"]:
            if p["Type"] == "ROOT":
                organizations_complete["noOutAccounts"].append(
                    {"account": c["account"], "name": c["name"]}
                )

            for o, j in zip(list_ous, range(len(list_ous))):
                if p["Id"] == o["Id"] and p["Type"] == "ORGANIZATIONAL_UNIT":
                    organizations_complete["organizationalUnits"][
                        find_ou_name(list_ous, o["Id"])
                    ]["accounts"][c["name"]] = {
                        "account": c["account"],
                        "name": c["name"],
                    }

    return organizations_complete


def graph_organizations(diagrams_path, region, auto):
    """
    Create organizations Graph.

    :param auto:
    :param diagrams_path:
    :param region:
    :return:
    """
    template_file = "graph_org.py"
    code_path = f"{diagrams_path}/code"
    json_path = f"{diagrams_path}/json"
    create_file(
        template_content=graph_template,
        file_name=template_file,
        directory_path=code_path,
    )
    org_client = client("organizations", region_name=region)
    organization = describe_organization(region=region, org_client=org_client)
    print(Fore.BLUE + emoji.emojize(":sparkle: Getting Organization Info" + Fore.RESET))
    logging.debug(organization)
    logging.debug("The Roots Info")
    roots = list_roots(region=region)
    logging.debug(roots)

    print(
        Fore.BLUE + emoji.emojize(":sparkle: List Organizational Units " + Fore.RESET)
    )
    logging.debug("The Organizational Units list ")

    ous = list_organizational_units(parent_id=roots[0]["Id"], region=region, org_client=org_client)
    logging.debug(ous)
    logging.debug("The Organizational Units list with parents info")
    i_ous = index_ous(ous, region=region)
    logging.debug(i_ous)

    print(
        Fore.BLUE
        + emoji.emojize(":sparkle: Getting the Account list info" + Fore.RESET)
    )

    l_accounts = list_accounts(region=region, org_client=org_client)
    logging.debug(l_accounts)
    logging.debug("The Account list with parents info")

    print(
        Fore.YELLOW
        + emoji.emojize(
            f":information:  There are {len(l_accounts)} Accounts in your organization"
            + Fore.RESET
        )
    )

    i_accounts = index_accounts(l_accounts, region=region, org_client=org_client)
    logging.debug(i_accounts)

    file_name = "organizations.json"
    save_results(results=i_accounts, filename=file_name, directory_path=json_path)

    create_mapper(
        template_file=f"{code_path}/{template_file}",
        org=organization,
        root_id=roots[0]["Id"],
        list_ous=ous,
        list_accounts=i_accounts,
    )
    file_name = "organizations_complete.json"
    # view in console
    organizations_complete_f = map_organizations_complete(
        organizations_complete=init_org_complete(
            org=organization, root_id=roots[0]["Id"], list_ous=i_ous
        ),
        llist_accounts=i_accounts,
        list_ous=i_ous,
        reference_outs_list=i_ous.copy(),
    )
    organizations_complete_f = (
        set_accounts_tree(
            llist_accounts=i_accounts,
            organizations_complete=organizations_complete_f,
            list_ous=i_ous,
        ),
    )

    save_results(results=organizations_complete_f, filename=f"{json_path}/{file_name}")

    if auto:
        print(f"{Fore.GREEN}❇️ Creating diagrams in {code_path}")
        command = os.system(f"cd {code_path} && python3 {template_file}")
        if command != 0:
            print(Fore.RED + "❌ Error creating diagrams")
            print(command)

    else:
        print(
            Fore.YELLOW
            + emoji.emojize(
                f":sparkles: Run -> python3 {code_path}/graph_org.py " + Fore.RESET
            )
        )
