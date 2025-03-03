import os
from datetime import datetime, timedelta
import fire
import logging
from village.scripts.utils import setup_logging


def is_backed_up(file_path, backup_dir):
    # Implement your backup check logic here
    backup_path = os.path.join(backup_dir, os.path.relpath(file_path))
    return os.path.exists(backup_path)

def parse_timestamp_from_filename(filename):
    # Assuming the timestamp is in the format ..._..._YYYYMMDD_HHMMSS.something
    try:
        timestamp_str = filename.split('_')[-2] + filename.split('_')[-1].split('.')[0]
        return datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
    except ValueError:
        return None

def remove_old_data(directory, days, backup_dir):
    now = datetime.now()
    cutoff = now - timedelta(days=days)
    something_removed = False

    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_timestamp = parse_timestamp_from_filename(file)

            if file_timestamp and file_timestamp < cutoff:
                if is_backed_up(file_path, backup_dir):
                    os.remove(file_path)
                    something_removed = True
                    logging.info(f"Removed {file_path}")
                else:
                    logging.warning(f"Skipping {file_path}, not backed up")
    if not something_removed:
        logging.info("No files removed")

if __name__ == "__main__":
    log_filename = setup_logging(logs_subdirectory="data_removal_logs")
    logging.info(f"Logging to file: {log_filename}")
    try:
        fire.Fire(remove_old_data)
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
    logging.info("Data removal script completed")
