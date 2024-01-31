"""Describe Organizations."""
import logging
import os

import emoji
from colorama import Fore

from ..dgms.graph_mapper import create_file, create_mapper
from ..dgms.graph_template import graph_template
from ..reports.save_results import save_results
from .describe_sso import client


def describe_organization(region):
    """
    Describe the organization.

    :param region: AWS Region
    :return:
    """
    print(f"{Fore.GREEN}❇️ Describe Organization {Fore.RESET}")
    org_client = client("organizations", region_name=region)
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


def list_organizational_units(parent_id, region, org_units=None):
    """
    List Organizational units.

    :param parent_id:
    :param region:
    :param org_units:
    :return:
    """
    org_client = client("organizations", region_name=region)
    if org_units is None:
        org_units = []
    ous = org_client.list_organizational_units_for_parent(
        ParentId=parent_id,
        MaxResults=20,
    )
    ous = ous["OrganizationalUnits"]

    if len(ous) >= 20:
        logging.info("Paginating ...")
        add_ous = list_organizational_units_pag(
            parent_id, region, next_token=ous["NextToken"]
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
                ous_next = list_organizational_units(
                    ou["Id"], region=region, org_units=org_units
                )
                logging.debug(ous_next)
                if len(ous_next) > 0:
                    logging.debug("Find Netsted")

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


def list_accounts(region):
    """
    List accounts.

    :param region:
    :return:
    """
    org_client = client("organizations", region_name=region)
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


def index_accounts(list_account, region):
    """
    Index accounts.

    :param list_account:
    :param region:
    :return:
    """
    accounts = []
    org_client = client("organizations", region_name=region)
    for a in list_account:
        response = org_client.list_parents(
            ChildId=a["Id"],
        )

        accounts.append(
            {"account": a["Id"], "name": a["Name"], "parents": response["Parents"]}
        )
    return accounts


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

    organization = describe_organization(region=region)
    print(Fore.BLUE + emoji.emojize(":sparkle: Getting Organization Info" + Fore.RESET))
    logging.debug(organization)
    logging.debug("The Roots Info")
    roots = list_roots(region=region)
    logging.debug(roots)

    print(
        Fore.BLUE
        + emoji.emojize(":sparkle: Listing Organizational Units " + Fore.RESET)
    )
    logging.debug("The Organizational Units list ")
    ous = list_organizational_units(parent_id=roots[0]["Id"], region=region)
    logging.debug(ous)
    logging.debug("The Organizational Units list with parents info")
    i_ous = index_ous(ous, region=region)
    logging.debug(i_ous)

    print(
        Fore.BLUE
        + emoji.emojize(":sparkle: Getting the Account list info" + Fore.RESET)
    )
    l_accounts = list_accounts(region=region)
    logging.debug(l_accounts)
    logging.debug("The Account list with parents info")

    print(
        Fore.YELLOW
        + emoji.emojize(
            f":information:  There are {len(l_accounts)} Accounts in your organization"
            + Fore.RESET
        )
    )
    i_accounts = index_accounts(l_accounts, region=region)
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
