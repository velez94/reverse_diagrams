import boto3
import json


def describe_organization(client=boto3.client('organizations')):
    response = client.describe_organization()
    organization = response["Organization"]
    return organization


def list_accounts(client=boto3.client('organizations')):
    response = client.list_accounts(
        # NextToken='string',
        # MaxResults=123
    )

    return response["Accounts"]


def index_accounts(list_account):
    accounts = []
    client = boto3.client('organizations')
    for a in list_account:
        response = client.list_parents(
            ChildId=a["Id"],
            # NextToken='string',
            # MaxResults=123
        )
        print(response)

        accounts.append({"account": a["Id"], "name": a["Name"], "parents": response["Parents"]})
    return accounts


def get_ous(accounts):
    ous = []
    root = ""
    for p in accounts:
        for a in p["parents"]:
            if a["Id"] in ous and a["Type"] != "ROOT":
                continue

            elif (a["Id"] in ous) == False and a["Type"] == "ROOT":
                root = a["Id"]
            else:
                ous.append(a["Id"])
    return ous, root
