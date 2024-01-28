from colorama import Fore

banner = """Reverse Diagrams 

 #####   ######  #    #  ######  #####    ####   ######
 #    #  #       #    #  #       #    #  #       #
 #    #  #####   #    #  #####   #    #   ####   #####
 #####   #       #    #  #       #####        #  #
 #   #   #        #  #   #       #   #   #    #  #
 #    #  ######    ##    ######  #    #   ####   ######


 #####      #      ##     ####   #####     ##    #    #   ####
 #    #     #     #  #   #    #  #    #   #  #   ##  ##  #
 #    #     #    #    #  #       #    #  #    #  # ## #   ####
 #    #     #    ######  #  ###  #####   ######  #    #       #
 #    #     #    #    #  #    #  #   #   #    #  #    #  #    #
 #####      #    #    #   ####   #    #  #    #  #    #   ####
"""


def get_version(version):
    """
    Get package version.

    :param version:
    :return:
    """
    print(Fore.BLUE + banner)

    print(version + Fore.RESET)

    return version
