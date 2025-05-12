import logging
import os
import subprocess
from datetime import datetime, timedelta

import fire

from village.scripts.utils import setup_logging


def check_files_for_backup(
    files, directory, backup_dir, remote_user, remote_host, port=None
) -> list:
    files_to_remove = []
    # Create a single SSH connection to the remote server
    ssh_command = (
        f"ssh {remote_user}@{remote_host} "
        f"'for file in {' '.join([os.path.join(backup_dir, f) for f in files])}; do "
        f"if [ -e $file ]; then echo $file; fi; done'"
    )
    result = subprocess.run(
        ssh_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    backed_up_files = result.stdout.decode().strip().split("\n")

    for file in files:
        backup_path = os.path.join(backup_dir, file)
        if backup_path in backed_up_files:
            files_to_remove.append(os.path.join(directory, file))

    return files_to_remove


def parse_timestamp_from_filename(filename) -> datetime | None:
    # Assuming the timestamp is in the format ..._..._YYYYMMDD_HHMMSS.something
    try:
        timestamp_str = filename.split("_")[-2] + filename.split("_")[-1].split(".")[0]
        return datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
    except ValueError:
        return None


def remove_old_data(
    directory,
    days,
    safe,
    backup_dir=None,
    remote_user=None,
    remote_host=None,
    port=None,
) -> None:
    removed_count = 0
    files_to_check = []
    files_to_remove = []
    now = datetime.now()
    cutoff = now - timedelta(days=days)

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
        if backup_dir:
            files_to_remove = check_files_for_backup(
                files_to_check, directory, backup_dir, remote_user, remote_host, port
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


def remove_file(file_path, removed_count: int) -> int:
    os.remove(file_path)
    logging.info(f"Removed {file_path}")
    return removed_count + 1


def main(
    directory, days, safe, backup_dir, remote_user=None, remote_host=None, port=None
) -> None:
    """
    Main function to remove old data files from a directory

    Parameters:
    - directory: Directory to remove files from
    - days: Number of days to keep files
    - safe: If True, will check for backup files before removing
    - backup_dir: Directory to check for backup files
    - remote_user: Username on remote system
    - remote_host: Remote hostname or IP
    - port: SSH port
    """

    log_file, file_handler = setup_logging(logs_subdirectory="data_removal_logs")
    logging.info(f"Logging to file: {log_file}")
    try:
        remove_old_data(
            directory, days, safe, backup_dir, remote_user, remote_host, port
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
