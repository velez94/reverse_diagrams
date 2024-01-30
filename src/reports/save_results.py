"""Save results."""
import json
import logging
from pathlib import Path

from colorama import Fore


def save_results(results, filename, directory_path="."):
    """
    Save results to a file.

    :param directory_path:
    :param results:
    :param filename:

    :return: None. Saves results to a file.
    """
    if not Path.exists(Path(directory_path)):
        Path.mkdir(Path(directory_path))
        logging.debug(f"Directory {directory_path} created")
    with open(f"{directory_path}/{filename}", "w") as f:
        json.dump(results, fp=f, indent=4)
        print(
            f"{Fore.YELLOW}ℹ️  The accounts are stored in {directory_path}/{filename} {Fore.RESET}"
        )
