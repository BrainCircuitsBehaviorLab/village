import logging
import os
import subprocess
from datetime import datetime

import fire


def setup_logging():
    """Configure logging to both file and console"""
    logs_dir = "backup_to_cluster_logs"
    # Create logs directory if it doesn't exist
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Setup logging with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(logs_dir, f"{timestamp}.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_filename), logging.StreamHandler()],
    )
    return log_filename


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
    Main function to sync data to remote cluster using rsync

    Parameters:
    - source: Source directory path
    - destination: Destination path on remote system
    - remote_user: Username on remote system
    - remote_host: Remote hostname or IP
    - port: SSH port (default: 22)
    """
    # Setup logging
    log_file = setup_logging()

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
