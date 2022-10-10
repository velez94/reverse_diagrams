
from diagrams import Diagram, Cluster

from diagrams.aws.management import Organizations, OrganizationsAccount, OrganizationsOrganizationalUnit
from diagrams.aws.general import Users, User

with Diagram("Organizations-SSO-State", show=False, direction="TB"):
    ou = OrganizationsOrganizationalUnit("OU")
    oa = OrganizationsAccount("Account")
    gg = Users("Group")
    uu= User("User")

    with Cluster('Organizations'):

        oo = Organizations('o-9tlhkjyoii\n029921763173\nr-w3ow')

        ou_Research= OrganizationsOrganizationalUnit("ou-w3ow-oegm0al0\nResearch")

        oo>> ou_Research

        ou_Dev= OrganizationsOrganizationalUnit("ou-w3ow-k24p2opx\nDev")

        oo>> ou_Dev

        ou_Core= OrganizationsOrganizationalUnit("ou-w3ow-93hiq3zr\nCore")

        oo>> ou_Core

        ou_Custom= OrganizationsOrganizationalUnit("ou-w3ow-5qsqi8b5\nCustom")

        oo>> ou_Custom

        ou_Shared= OrganizationsOrganizationalUnit("ou-w3ow-w7dzhzcz\nShared")

        oo>> ou_Shared

        ou_NetstedOU= OrganizationsOrganizationalUnit("ou-w3ow-i9xzgb9x\nNetstedOU")

        ou_Custom>> ou_NetstedOU

        ou_Core>> OrganizationsAccount("884478634998\nLog archive")

        ou_Custom>> OrganizationsAccount("582441254763\nProd")

        ou_Core>> OrganizationsAccount("895882538541\nAudit")

        ou_Shared>> OrganizationsAccount("105171185823\nDevSecOps")

        ou_Dev>> OrganizationsAccount("994261317734\nLabVelCT")

        ou_Shared>> OrganizationsAccount("155794986228\nSharedServices")

        oo >> OrganizationsAccount("029921763173\nAlejandro Velez")

        ou_Dev>> OrganizationsAccount("571340586587\nDev")
