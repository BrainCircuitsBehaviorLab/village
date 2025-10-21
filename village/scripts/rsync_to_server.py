import logging
import os
import select
import signal
import subprocess
import threading
import time

import fire

from village.scripts.log import log
from village.scripts.time_utils import time_utils
from village.scripts.utils import setup_logging


def run_rsync(
    source_path,
    destination,
    remote_user,
    remote_host,
    port,
    maximum_sync_time,
    cancel_event=None,
) -> bool:
    """
    Run rsync command with specified parameters

    Parameters:
    - source_path: Local path to sync
    - destination: Remote destination path
    - remote_user: Username on remote system
    - remote_host: Remote hostname or IP
    - port: SSH port
    - maximum_sync_time: Maximum_sync_time in seconds
    - cancel_event: threading.Event to signal cancellation
    """

    if cancel_event is None:
        cancel_event = threading.Event()

    # Ensure source path ends with / to copy contents
    source_path = os.path.join(source_path, "")
    destination_dir = os.path.dirname(destination)

    try:
        if port is None:
            subprocess.run(
                [
                    "ssh",
                    "-o",
                    "ConnectTimeout=10",
                    f"{remote_user}@{remote_host}",
                    f"mkdir -p {destination_dir}",
                ],
                timeout=30,
                check=True,
            )
        else:
            subprocess.run(
                [
                    "ssh",
                    "-p",
                    str(port),
                    "-o",
                    "ConnectTimeout=10",
                    f"{remote_user}@{remote_host}",
                    f"mkdir -p {destination_dir}",
                ],
                timeout=30,
                check=True,
            )
    except subprocess.TimeoutExpired:
        logging.error(
            "SSH connection timed out (mkdir). Remote host may be unreachable."
        )
        return False
    except subprocess.CalledProcessError as e:
        logging.error(f"SSH command failed: {e}")
        return False

    # Construct the rsync command with safe options
    if port is None:
        rsync_cmd = [
            "rsync",
            "-avP",  # archive, verbose, compress, show progress
            "--update",  # skip files that are newer on receiver
            "--safe-links",  # ignore symlinks that point outside the tree
            "--timeout=30",  # I/O timeout for rsync
            "--exclude",
            "*.tmp",  # exclude temporary files
            "--exclude",
            "CORRIDOR*",  # exclude CORRIDOR videos and data
            "--exclude",
            ".git/",  # exclude git directory
            source_path,
            f"{remote_user}@{remote_host}:{destination}",
        ]
    else:
        rsync_cmd = [
            "rsync",
            "-avP",  # archive, verbose, compress, show progress
            "--update",  # skip files that are newer on receiver
            "--safe-links",  # ignore symlinks that point outside the tree
            "--timeout=30",  # I/O timeout for rsync
            "--exclude",
            "*.tmp",  # exclude temporary files
            "--exclude",
            "CORRIDOR*",  # exclude CORRIDOR videos and data
            "--exclude",
            ".git/",  # exclude git directory
            "-e",
            f"ssh -p {port}",  # specify ssh port
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
            preexec_fn=os.setsid,  # new process group for signal handling
            bufsize=1,  # line-buffered
        )

        start_time = time_utils.get_time_monotonic()
        last_progress_time = start_time

        process_running = True

        def _terminate(reason: str):
            nonlocal process_running
            logging.error(reason)
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            except Exception:
                process.terminate()
            try:
                if process.stdout:
                    process.stdout.close()
            except Exception:
                pass
            try:
                if process.stderr:
                    process.stderr.close()
            except Exception:
                pass
            process_running = False

        def check_maximum_sync_time():
            nonlocal process_running
            fired = cancel_event.wait(timeout=maximum_sync_time)
            if process_running and process.poll() is None:
                if fired:
                    text = "External cancel requested. "
                else:
                    text = f"Maximum sync time reached ({maximum_sync_time}s). "
                _terminate(text + "Terminating rsync process.")

        # Launching a thread to check for maximum_sync_time
        sync_time_thread = threading.Thread(target=check_maximum_sync_time, daemon=True)
        sync_time_thread.start()

        # Stream output in (almost) real-time
        while process_running:
            if process.stdout:
                try:
                    ready, _, _ = select.select([process.stdout], [], [], 0.1)
                    if ready:
                        line = process.stdout.readline()
                        if line:
                            logging.info(line.strip())
                            last_progress_time = time_utils.get_time_monotonic()
                except Exception:
                    pass

            # Check if the process is still running
            if process.poll() is not None:
                logging.info("rsync completed.")
                process_running = False
                break  # Success

            # If no progress for the timeout duration, assume it's stuck
            if (
                time_utils.get_time_monotonic() - last_progress_time > 600
            ):  # 60s no progress
                logging.warning("rsync seems stuck! Terminating...")
                try:
                    # kill process group
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                except Exception:
                    process.terminate()  # Gracefully stop
                time.sleep(2)
                if process.poll() is None:
                    try:
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    except Exception:
                        process.kill()  # Force stop if necessary
                process_running = False
                break  # Exit loop

            # small pause to prevent busy CPU
            time.sleep(0.1)

        # Get any errors
        if process.stderr:
            try:
                stderr = process.stderr.read()
                if stderr:
                    logging.error(stderr)
            except Exception:
                pass

        # make sure process is terminated
        if process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=5)
            except Exception:
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                except Exception:
                    process.kill()

        # Check return code
        if process.returncode != 0 and process.returncode is not None:
            logging.error(f"Rsync failed with return code: {process.returncode}")
            return False

        if process.returncode == 0:
            logging.info("Rsync completed successfully")
            return True
        else:
            return False

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        # try to kill the process if it is still running
        try:
            if "process" in locals() and process.poll() is None:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except Exception:
            pass
        return False
    finally:
        # close streams
        try:
            if "process" in locals():
                if process.stdout:
                    process.stdout.close()
                if process.stderr:
                    process.stderr.close()
        except Exception:
            pass


def main(
    source,
    destination,
    remote_user,
    remote_host,
    port=None,
    maximum_sync_time=1200,
    cancel_event=None,
) -> None:
    """
    Main function to sync data to remote server using rsync

    Parameters:
    - source: Source directory path
    - destination: Destination path on remote system
    - remote_user: Username on remote system
    - remote_host: Remote hostname or IP
    - port: SSH port (default: None)
    - maximum_sync_time: Maximum sync time duration in seconds (default: 1200)
    - cancel_event: threading.Event to signal cancellation (optional)
    """
    # Setup logging
    log_file, file_handler = setup_logging(logs_subdirectory="rsync_logs")
    logging.info(f"Logging to file: {log_file}")

    # Log start of sync
    logging.info(f"Starting sync from {source} to {remote_host}")

    # Run rsync
    success = run_rsync(
        source,
        destination,
        remote_user,
        remote_host,
        port,
        maximum_sync_time,
        cancel_event,
    )

    # Log completion
    if success:
        logging.info(f"Sync completed successfully. Log file: {log_file}")
        log.info("Sync completed successfully")
    else:
        logging.error(f"Sync failed. Check log file for details: {log_file}")
        log.error(f"Sync failed. Check log file for details: {log_file}")

    # Close the log file handler properly
    logging.getLogger().removeHandler(file_handler)
    file_handler.close()
    logging.shutdown()


if __name__ == "__main__":
    fire.Fire(main)
