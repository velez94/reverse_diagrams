import boto3
import json


def describe_organization(client=boto3.client('organizations')):
    organization = client.describe_organization()
    organization = organization["Organization"]
    return organization


def list_roots(client=boto3.client('organizations')):
    roots = client.list_roots(

    )
    return roots["Roots"]


def list_organizational_units(parent_id, client=boto3.client('organizations'), org_units=None):
    ous = client.list_organizational_units_for_parent(
        ParentId=parent_id,

    )
    for o in ous["OrganizationalUnits"]:
        org_units.append(o)
    print("The parent Id is: ", parent_id)
    print(ous)
    if len(ous) > 0:
        for ou in ous["OrganizationalUnits"]:
            print(ou)
            if "Id" in ou.keys():
                print("Search nested for: ", ou["Name"])
                ous_next = list_organizational_units(ou["Id"], client=client, org_units=org_units)
                print(ous_next)
                if len(ous_next) > 0:
                    print("Find NetsteD")

    return org_units


def list_parents(child_id, client=boto3.client('organizations')):
    response = client.list_parents(
        ChildId=child_id,

    )
    return response["Parents"]


def index_ous(list_ous, client=boto3.client('organizations')):
    for ou in list_ous:
        if "Id" in ou.keys() and len(ou) > 0:
            response = client.list_parents(
                ChildId=ou["Id"],

            )
            print(response["Parents"])
            ou["Parents"] = response["Parents"]
    return list_ous


def list_accounts(client=boto3.client('organizations')):
    accounts = client.list_accounts(

    )

    return accounts["Accounts"]


def index_accounts(list_account):
    accounts = []
    client = boto3.client('organizations')
    for a in list_account:
        response = client.list_parents(
            ChildId=a["Id"],

        )

        accounts.append({"account": a["Id"], "name": a["Name"], "parents": response["Parents"]})
    return accounts
