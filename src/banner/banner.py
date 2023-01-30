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
    print(Fore.BLUE + banner )

    print(version + Fore.RESET)

    return version
