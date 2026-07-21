import logging
from pathlib import Path
logging.getLogger(__name__)
logging.info(f'Importing {Path(__file__).name}')

import os
import requests
import base64


VERSION_FILENAME = "version.txt"  # The version file
BOT_FILENAME = "bot.py"  # The script being updated
LOCAL_PATH = os.path.dirname(os.path.abspath(__name__)) +"\\"

GITHUB_API_URL = "https://api.github.com/repos/kaboomie121/MiRavBotCode/contents/"
GITHUB_API_BACKUP_URL = "https://raw.githubusercontent.com/kaboomie121/MiRavBotCode/refs/heads/master/"

def remove_alternate_newlines(s):
    new_str = ""
    newline_count = 0
    for char in s:
        if char == '\n':
            newline_count += 1
            # Skip every 2nd newline (i.e. even occurrences)
            if newline_count % 2 == 0:
                continue
        new_str += char
    return new_str

import subprocess

def get_remote_version():
    result = subprocess.run(
        ["git", "show", "origin/master:version.txt"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        logging.error(result.stderr)
        return None

    return result.stdout.strip()
            

    return None

def get_local_version():
    logging.info("Getting local version from file: " + LOCAL_PATH + VERSION_FILENAME)
    if not os.path.exists(LOCAL_PATH + VERSION_FILENAME):
        return ""  # If bot.py doesn't exist yet, treat it as an empty file
    with open(LOCAL_PATH + VERSION_FILENAME, "r", encoding="utf-8") as f:
        return (f.read().replace('\r', '')).strip()
    
def checkForUpdate():
    logging.info("Checking for updates...")

    fetch = subprocess.run(
        ["git", "fetch", "origin"],
        capture_output=True,
        text=True
    )

    if fetch.returncode != 0:
        logging.error(fetch.stderr)
        return False

    remote_version = get_remote_version()

    if remote_version is None:
        return False

    local_version = get_local_version()

    logging.info(f"Remote version: {remote_version}")
    logging.info(f"Local version : {local_version}")

    return remote_version != local_version
