import logging
import os
import subprocess
from datetime import datetime

import fire

from village.scripts.time_utils import time_utils
from village.scripts.utils import setup_logging


def check_files_for_backup_remote(
    files: list[str],
    directory: str,
    backup_dir: str,
    remote_user: str,
    remote_host: str,
    port: int | None,
) -> list[str]:
    """Checks which files have been backed up on a remote server.

    Args:
        files (list[str]): List of filenames to check.
        directory (str): The local directory containing the files.
        backup_dir (str): The remote backup directory.
        remote_user (str): Username on remote system.
        remote_host (str): Remote hostname or IP.
        port (int | None): SSH port.

    Returns:
        list[str]: List of full paths of files that can be safe to remove locally.
    """
    files_to_remove = []
    # Create a single SSH connection to the remote server
    import os

    if port is None:
        ssh_command = (
            f"ssh {remote_user}@{remote_host} "
            f"'for file in {' '.join([os.path.join(backup_dir, f) for f in files])}; do"
            f" if [ -e $file ]; then echo $file; fi; done'"
        )
    else:
        ssh_command = (
            f"ssh -p {port} {remote_user}@{remote_host} "
            f"'for file in {' '.join([os.path.join(backup_dir, f) for f in files])}; do"
            f" if [ -e $file ]; then echo $file; fi; done'"
        )

    try:
        result = subprocess.run(
            ssh_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120,
        )
    except Exception:
        return []

    backed_up_files = result.stdout.decode().strip().split("\n")

    for file in files:
        backup_path = os.path.join(backup_dir, file)
        if backup_path in backed_up_files:
            files_to_remove.append(os.path.join(directory, file))

    return files_to_remove


def check_files_for_backup_local(
    files: list[str], directory: str, backup_dir: str
) -> list[str]:
    """Checks which files have been backed up locally (e.g., external drive).

    Args:
        files (list[str]): List of filenames to check.
        directory (str): The local directory containing the source files.
        backup_dir (str): The local backup directory.

    Returns:
        list[str]: List of full paths of files that can be safe to remove.
    """
    files_to_remove = []
    for file in files:
        try:
            backup_path = os.path.join(backup_dir, file)
            if os.path.exists(backup_path):
                files_to_remove.append(os.path.join(directory, file))
        except Exception:
            pass
    return files_to_remove


def parse_timestamp_from_filename(filename: str) -> datetime | None:
    """Parses a timestamp from a filename.

    Args:
        filename (str): The filename string.

    Returns:
        datetime | None: The parsed datetime object, or None if parsing fails.
    """
    # Assuming the timestamp is in the format ..._..._YYYYMMDD_HHMMSS.something
    try:
        timestamp_str = filename.split("_")[-2] + filename.split("_")[-1].split(".")[0]
        return datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
    except ValueError:
        return None


def remove_old_data(
    directory: str,
    days: int,
    safe: bool,
    backup_dir: str,
    remote_user: str,
    remote_host: str,
    port: int | None,
    remote: bool,
) -> None:
    """Core logic to identify and remove old data files.

    Args:
        directory (str): Directory to clean up.
        days (int): Retention period in days.
        safe (bool): If True, verifies backup before deletion.
        backup_dir (str): Backup directory path.
        remote_user (str): Remote username.
        remote_host (str): Remote host.
        port (int | None): SSH port.
        remote (bool): If True, checks remote backup; otherwise local.
    """
    removed_count = 0
    files_to_check = []
    files_to_remove = []
    cutoff = time_utils.hours_ago(days * 24)

    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            relative_file_path = os.path.relpath(file_path, directory)
            file_timestamp = parse_timestamp_from_filename(file)

            if file_timestamp and file_timestamp < cutoff:
                # if file starts with CORRIDOR_, remove it
                if file.startswith("CORRIDOR_"):
                    removed_count = remove_file(file_path, removed_count)
                elif backup_dir:
                    files_to_check.append(relative_file_path)
                else:
                    removed_count = remove_file(file_path, removed_count)

    if safe:
        if remote:
            files_to_remove = check_files_for_backup_remote(
                files_to_check, directory, backup_dir, remote_user, remote_host, port
            )
        else:
            files_to_remove = check_files_for_backup_local(
                files_to_check, directory, backup_dir
            )
    else:
        logging.info("Safe mode is off, skipping backup check")
        files_to_remove = files_to_check

    for file in files_to_remove:
        removed_count = remove_file(file, removed_count)

    if removed_count == 0:
        logging.info(f"No files removed from {directory}")
    else:
        logging.info(
            f"Removed {removed_count} files older than {days} days from {directory}"
        )


def remove_file(file_path: str, removed_count: int) -> int:
    """Removes a single file and logs the action.

    Args:
        file_path (str): Path to the file.
        removed_count (int): Current count of removed files.

    Returns:
        int: Updated count of removed files.
    """
    os.remove(file_path)
    logging.info(f"Removed {file_path}")
    return removed_count + 1


def main(
    directory: str,
    days: int,
    safe: bool,
    backup_dir: str,
    remote_user: str | None = None,
    remote_host: str | None = None,
    port: int | None = None,
    remote: bool = True,
) -> None:
    """Main function to remove old data files from a directory.

    Args:
        directory (str): Directory to remove files from.
        days (int): Number of days to keep files.
        safe (bool): If True, will check for backup files before removing.
        backup_dir (str): Directory to check for backup files.
        remote_user (str | None): Username on remote system.
        remote_host (str | None): Remote hostname or IP.
        port (int | None): SSH port.
        remote (bool): If True, checks remote backup; otherwise local.
    """

    log_file, file_handler = setup_logging(logs_subdirectory="data_removal_logs")
    logging.info(f"Logging to file: {log_file}")
    try:
        remove_old_data(
            directory, days, safe, backup_dir, remote_user, remote_host, port, remote
        )
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
    logging.info("Data removal script completed")

    # Close the log file handler properly
    logging.getLogger().removeHandler(file_handler)
    file_handler.close()
    logging.shutdown()


if __name__ == "__main__":
    fire.Fire(main)
    # main(
    #     directory="/home/pi/village_projects/visual_and_COT/data/videos",
    #     days=8,
    #     safe=True,
    #     backup_dir="/archive/training_village/visual_and_COT_data/videos",
    #     remote_user="training_village",
    #     remote_host="cluster",
    #     # port=4022,
    # )

