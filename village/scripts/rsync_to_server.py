import logging
import os
import subprocess
import time

import fire

from village.scripts.utils import setup_logging


def run_rsync(
    source_path, destination, remote_user, remote_host, port, timeout
) -> bool:
    """
    Run rsync command with specified parameters

    Parameters:
    - source_path: Local path to sync
    - destination: Remote destination path
    - remote_user: Username on remote system
    - remote_host: Remote hostname or IP
    - port: SSH port
    - timeout: Timeout duration in seconds
    """
    # Ensure source path ends with / to copy contents
    source_path = os.path.join(source_path, "")

    # Ensure the destination directory exists
    destination_dir = os.path.dirname(destination)
    subprocess.run(
        [
            "ssh",
            "-p",
            str(port),
            f"{remote_user}@{remote_host}",
            f"mkdir -p {destination_dir}",
        ]
    )

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

        start_time = time.time()
        last_progress_time = start_time

        # Stream output in real-time
        while True:
            if process.stdout:
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break
                if output:
                    logging.info(output.strip())
                    last_progress_time = time.time()  # Reset progress timer

            # Check if the process is still running
            if process.poll() is not None:
                logging.info("rsync completed.")
                break  # Success

            # If no progress for the timeout duration, assume it's stuck
            if time.time() - last_progress_time > timeout:
                logging.warning("rsync seems stuck! Terminating...")
                process.terminate()  # Gracefully stop
                time.sleep(2)
                process.kill()  # Force stop if necessary
                break  # Exit loop

        # Get any errors
        if process.stderr:
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


def main(source, destination, remote_user, remote_host, port=22, timeout=120) -> None:
    """
    Main function to sync data to remote server using rsync

    Parameters:
    - source: Source directory path
    - destination: Destination path on remote system
    - remote_user: Username on remote system
    - remote_host: Remote hostname or IP
    - port: SSH port (default: 22)
    -timeout: Timeout duration in seconds (default: 120)
    """
    # Setup logging
    log_file = setup_logging(logs_subdirectory="rsync_logs")
    logging.info(f"Logging to file: {log_file}")

    # Log start of sync
    logging.info(f"Starting sync from {source} to {remote_host}")

    # Run rsync
    success = run_rsync(source, destination, remote_user, remote_host, port, timeout)

    # Log completion
    if success:
        logging.info(f"Sync completed successfully. Log file: {log_file}")
    else:
        logging.error(f"Sync failed. Check log file for details: {log_file}")

    logging.shutdown()


if __name__ == "__main__":
    fire.Fire(main)
