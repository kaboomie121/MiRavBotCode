import os
import time
import hashlib
import requests
import sys
import base64
import subprocess

# GitHub repository details
CHECK_INTERVAL = 600  # Time in seconds between update checks
VERSION_FILENAME = "version.txt"  # The version file
BOT_FILENAME = "bot.py"  # The script being updated
LOCAL_PATH = os.path.dirname(os.path.abspath(__file__)) +"\\"

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

def get_local_script(fileName : str):
    if not os.path.exists(LOCAL_PATH + fileName):
        return "" 
    with open(LOCAL_PATH + "A" + fileName, "r", encoding="utf-8") as f:
        return (f.read().replace('\r', ''))

def get_remote_script(fileName : str):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

    response = requests.get(GITHUB_API_URL + fileName, headers=headers)
    if response.status_code == 200:
        json_response = response.json()
        if "content" in json_response:
            returnContent = base64.b64decode(json_response["content"]).decode("utf-8")

            returnContent = returnContent.replace('\r', '')

            return returnContent
        else:
            print("\033[31mError:\033[0m No content field in GitHub response.")
    elif int(response.status_code) == int(403):
        print("\033[31mFailed\033[0m to fetch the bot script. Status code:", response.status_code, " Error reason: TIMED OUT BY GITHUB")
    else:
        print("\033[31mFailed\033[0m to fetch the bot script. Status code:", response.status_code)
            

    return None

def get_local_version():
    if not os.path.exists(LOCAL_PATH + VERSION_FILENAME):
        return ""  # If bot.py doesn't exist yet, treat it as an empty file
    with open(LOCAL_PATH + VERSION_FILENAME, "r", encoding="utf-8") as f:
        return remove_alternate_newlines(f.read().replace('\r', ''))
    
def get_localA_version():
    if not os.path.exists(LOCAL_PATH + "A" + VERSION_FILENAME):
        return ""  # If bot.py doesn't exist yet, treat it as an empty file
    with open(LOCAL_PATH +"A" + VERSION_FILENAME, "r", encoding="utf-8") as f:
        return (f.read())

def hash_content(content):
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

class ProcessManager:
    def __init__(self):
        self.process = None

    def pollerrors(self):
        if self.process and not(self.process.poll() is None):
            stderr = self.process.stderr.read().decode()
            stdout = self.process.stdout.read().decode()
            print("Bot \033[31mthrew an error\033[0m. Error:\n", stderr)
            print("Bot \033[32moutput:\033[0m.\n", stdout)

    def start(self):
        started = False
        while not started:
            try:
                self.process = subprocess.Popen([sys.executable, LOCAL_PATH + BOT_FILENAME], stderr=subprocess.PIPE)
                time.sleep(2)
                if self.process.poll() is None:
                    print("Bot sub-process started \033[32msuccessfully!\033[0m")
                    started = True
                else:
                    output = self.process.stderr.read().decode()
                    print("Bot \033[31mfailed\033[0m to start. Error:\n", output)
                    started = False

            except Exception as e:
                print("\033[31mERROR\033[0m Try catch in start function has been called. Reason:\n", e)
                started = False
            if not started:
                print("Retrying in 10 seconds...")
                time.sleep(10)
                
                if checkForUpdate():
                    botManager.stop()
                    botManager.start()
                

    def stop(self):
        if not(self.process == None):
            self.process.kill()
        self.process = None

def update_files(files : list[str]):
    files.append("version.txt")

    print("Updating all files!")
    for fileName in files:
        print(f"\033[33mUpdating\033[0m file: {fileName}\n")
        remote_File = get_remote_script(fileName)
        with open(LOCAL_PATH + fileName, "w", encoding="utf-8") as f:
            f.write(remote_File.removesuffix('\n'))

def checkForUpdate():
    print("\nChecking for updates...\n")
    remote_version = get_remote_script(VERSION_FILENAME) #get_remote_script()
    if remote_version:
        local_version = get_local_version()
        if str(remote_version.split('|')[0]) != str(local_version.split('|')[0]):
            print(f"\033[32mUpdate found!\033[0m Updating bot script to new version: {remote_version.split('|')[0]}")
            update_files( (remote_version.split('|')[1]).split(';') )
            return True, (remote_version.split('|')[2].replace('\n', '') == "True")
        else:
            print("\033[33mNo\033[0m updates found.")
            return False, False
    elif remote_version == None: 
        print("\033[33mERROR:\033[0m remote_version returned None")
        return False, False
    return False, False

botManager = ProcessManager()
def main():
    update, restartSelf = checkForUpdate()
    if restartSelf:
        print("Restarting with updated code...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    else:
        print("Self restart not needed.")
    botManager.start()

    while True:
        for i in range(int(CHECK_INTERVAL)):
            time.sleep(1)
            botManager.pollerrors()
        update, restartSelf = checkForUpdate()
        if update:
            if restartSelf:
                print("Restarting with updated code...")
                os.execv(sys.executable, [sys.executable] + sys.argv)
            else:
                print("Self restart not needed.")
            botManager.stop()
            botManager.start()


try:
    main()
except Exception as e:
    try:
        botManager.stop()
    except Exception as e:
        print("")
    print("An \033[31merror\033[0m occured within the main file... Error: \n", e)
finally:
    input("\nPress any key to exit...")