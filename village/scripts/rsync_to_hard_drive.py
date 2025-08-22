import logging
import os
import signal
import subprocess
import threading
import time

import fire

from village.log import log
from village.scripts.utils import setup_logging


def run_rsync_local(source_path, destination, maximum_sync_time) -> bool:
    """
    Run rsync to sync to a local destination (e.g., external HDD).

    Parameters (for compatibility; only source_path and destination are used):
    - source_path: Local path to sync
    - destination: Local destination path (e.g., /media/pi/mydisk/backup/)
    - maximum_sync_time: Maximum_sync_time in seconds
    """
    # Ensure source path ends with /
    source_path = os.path.join(source_path, "")

    # Ensure destination directory exists
    try:
        os.makedirs(os.path.dirname(destination), exist_ok=True)
    except Exception as e:
        logging.error(f"Failed to create destination directory: {e}")
        return False

    # Build rsync command for local copy
    rsync_cmd = [
        "rsync",
        "-avzP",
        "--update",
        "--safe-links",
        "--timeout=30",
        "--exclude",
        "*.tmp",
        "--exclude",
        "CORRIDOR*",
        "--exclude",
        ".git/",
        source_path,
        destination,
    ]

    logging.info(f"Starting local rsync with command: {' '.join(rsync_cmd)}")

    try:
        # Run rsync with timeout handling
        process = subprocess.Popen(
            rsync_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            preexec_fn=os.setsid,
        )

        start_time = time.time()
        last_progress_time = start_time
        process_running = True

        def check_maximum_sync_time() -> None:
            nonlocal process_running
            time.sleep(maximum_sync_time)
            if process_running and process.poll() is None:
                logging.error(
                    f"Maximum sync time reached ({maximum_sync_time}s). Terminating."
                )
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                except Exception:
                    process.terminate()
                process_running = False

        sync_time_thread = threading.Thread(target=check_maximum_sync_time, daemon=True)
        sync_time_thread.start()

        while process_running:
            if process.stdout:
                try:
                    output = process.stdout.readline()
                    if output == "" and process.poll() is not None:
                        break
                    if output:
                        logging.info(output.strip())
                        last_progress_time = time.time()
                except Exception:
                    pass

            if process.poll() is not None:
                logging.info("rsync completed.")
                process_running = False
                break

            if time.time() - last_progress_time > 60:
                logging.warning("rsync seems stuck! Terminating...")
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                except Exception:
                    process.terminate()
                time.sleep(2)
                if process.poll() is None:
                    try:
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    except Exception:
                        process.kill()
                process_running = False
                break

            time.sleep(0.1)

        if process.stderr:
            try:
                stderr = process.stderr.read()
                if stderr:
                    logging.error(stderr)
            except Exception:
                pass

        if process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=5)
            except Exception:
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                except Exception:
                    process.kill()

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
        try:
            if "process" in locals() and process.poll() is None:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except Exception:
            pass
        return False
    finally:
        try:
            if "process" in locals():
                if process.stdout:
                    process.stdout.close()
                if process.stderr:
                    process.stderr.close()
        except Exception:
            pass


def main(source, destination, maximum_sync_time=1800) -> None:
    """
    Main function to sync data to local disk using rsync.

    Parameters:
    - source: Source directory path
    - destination: Destination path on remote system
    - maximum_sync_time: Maximum sync time duration in seconds (default: 1200)
    """
    log_file, file_handler = setup_logging(logs_subdirectory="rsync_logs")
    logging.info(f"Logging to file: {log_file}")

    logging.info(f"Starting local sync from {source} to {destination}")

    success = run_rsync_local(source, destination, maximum_sync_time)

    if success:
        logging.info(f"Sync completed successfully. Log file: {log_file}")
        log.info("Sync completed successfully")
    else:
        logging.error(f"Sync failed. Check log file for details: {log_file}")
        log.error(f"Sync failed. Check log file for details: {log_file}")

    logging.getLogger().removeHandler(file_handler)
    file_handler.close()
    logging.shutdown()


if __name__ == "__main__":
    fire.Fire(main)
