import zipfile
import requests
import os
import shutil
from pathlib import Path
import datetime
import subprocess, sys

# put logs folder then log down

Path('logs').mkdir(exist_ok=True)

import logging
logging.basicConfig(filename=f'logs\\{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}_updater.log', filemode='w', level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s')
# check if there are more than 5 _updater.log files and delete the oldest one
log_files = [f for f in os.listdir('logs') if f.endswith('_updater.log')]
while True:
    if len(log_files) > 5:
        log_files.sort()
        print(f'More than 5 log ({len(log_files)}) files found, deleting oldest log file: {log_files[0]}')
        logging.info(f'More than 5 log ({len(log_files)}) files found, deleting oldest log file: {log_files[0]}')
        try:
            print(f'Deleting log file: {log_files[0]}')
            os.remove(os.path.join('logs', log_files[0]))
        except Exception as e:
            print(f'Error while deleting log file: {e}')
            logging.critical(f'Breaking operation; Error while deleting log file: {e}')
            break
        log_files.pop(0)
    else:
        break

def update():
    base_path = Path(__file__).parent

    logging.info("Pulling latest changes from GitHub...")

    result = subprocess.run(
        ["git", "pull"],
        cwd=base_path,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        logging.critical("git pull failed.")
        logging.critical(result.stderr)
        return False

    logging.info(result.stdout)
    return True

        
if __name__ == "__main__":
    update()