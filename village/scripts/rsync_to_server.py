import logging
import os
import subprocess
from village.scripts.utils import setup_logging

import fire


def run_rsync(source_path, destination, remote_user, remote_host, port=22):
    """
    Run rsync command with specified parameters

    Parameters:
    - source_path: Local path to sync
    - destination: Remote destination path
    - remote_user: Username on remote system
    - remote_host: Remote hostname or IP
    - port: SSH port (default: 22)
    """
    # Ensure source path ends with / to copy contents
    source_path = os.path.join(source_path, "")

    # Ensure the destination directory exists
    destination_dir = os.path.dirname(destination)
    subprocess.run(["ssh", "-p", str(port), f"{remote_user}@{remote_host}", f"mkdir -p {destination_dir}"])

    # Construct the rsync command with safe options
    rsync_cmd = [
        "rsync",
        "-avzP",  # archive, verbose, compress, show progress
        "--update",  # skip files that are newer on receiver
        "--safe-links",  # ignore symlinks that point outside the tree
        "-e",
        f"ssh -p {port}",  # specify ssh port
        "--exclude",
        "*.tmp",  # exclude temporary files
        "--exclude",
        "CORRIDOR*",  # exclude CORRIDOR videos and data
        "--exclude",
        ".git/",  # exclude git directory
        source_path,
        f"{remote_user}@{remote_host}:{destination}",
    ]

    logging.info(f"Starting rsync with command: {' '.join(rsync_cmd)}")

    try:
        # Run rsync command and capture output
        process = subprocess.Popen(
            rsync_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

        # Stream output in real-time
        while True:
            output = process.stdout.readline()
            if output == "" and process.poll() is not None:
                break
            if output:
                logging.info(output.strip())

        # Get any errors
        stderr = process.stderr.read()
        if stderr:
            logging.error(stderr)

        # Check return code
        if process.returncode != 0:
            logging.error(f"Rsync failed with return code: {process.returncode}")
            return False

        logging.info("Rsync completed successfully")
        return True

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return False


def main(source, destination, remote_user, remote_host, port=22):
    """
    Main function to sync data to remote server using rsync

    Parameters:
    - source: Source directory path
    - destination: Destination path on remote system
    - remote_user: Username on remote system
    - remote_host: Remote hostname or IP
    - port: SSH port (default: 22)
    """
    # Setup logging
    log_file = setup_logging(logs_subdirectory="rsync_logs")
    logging.info(f"Logging to file: {log_file}")

    # Log start of sync
    logging.info(f"Starting sync from {source} to {remote_host}")

    # Run rsync
    success = run_rsync(source, destination, remote_user, remote_host, port)

    # Log completion
    if success:
        logging.info(f"Sync completed successfully. Log file: {log_file}")
    else:
        logging.error(f"Sync failed. Check log file for details: {log_file}")


if __name__ == "__main__":
    fire.Fire(main)
