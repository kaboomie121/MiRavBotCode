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

def get_remote_script(fileName : str):
    # Idk bro
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

    response = requests.get(GITHUB_API_URL + fileName, headers=headers)
    if response.status_code == 200:
        json_response = response.json()
        if "content" in json_response:
            returnContent = base64.b64decode(json_response["content"]).decode("utf-8")

            returnContent = returnContent.replace('\r', '')

            return returnContent
        else:
            logging.error("\033[31mError:\033[0m No content field in GitHub response.")
    elif int(response.status_code) == int(403):
        logging.error("Failed to fetch the bot script. Status code: %s. Error reason: TIMED OUT BY GITHUB", response.status_code)
    else:
        logging.error("Failed to fetch the bot script. Status code: %s", response.status_code)
            

    return None

def get_local_version():
    logging.info("Getting local version from file: " + LOCAL_PATH + VERSION_FILENAME)
    if not os.path.exists(LOCAL_PATH + VERSION_FILENAME):
        return ""  # If bot.py doesn't exist yet, treat it as an empty file
    with open(LOCAL_PATH + VERSION_FILENAME, "r", encoding="utf-8") as f:
        return remove_alternate_newlines(f.read().replace('\r', ''))
    
def checkForUpdate():
    logging.info("Checking for updates...")
    remote_version = get_remote_script(VERSION_FILENAME) #get_remote_script()
    if remote_version:
        local_version = get_local_version()
        logging.info(f"Remote version: {str(remote_version).strip()}")
        logging.info(f"Local version: {str(local_version).strip()}")
        if str(remote_version).strip() != str(local_version).strip():
            logging.info(f"\033[32mUpdate found!\033[0m New version: {str(remote_version).strip()}")
            return True
        else:
            logging.info("\033[33mNo updates found.\033[0m")
            return False
    elif remote_version == None:
        logging.error("\033[33mERROR:\033[0m remote_version returned None")
        return False
    return False
