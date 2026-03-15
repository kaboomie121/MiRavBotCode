import zipfile
import requests
import os
import shutil
from pathlib import Path
import datetime

# put logs folder then log down

Path('logs').mkdir(exist_ok=True)

import logging
logging.basicConfig(filename=f'logs\\{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}_updater.log', filemode='w', level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s')
# check if there are more than 5 _updater.log files and delete the oldest one
log_files = [f for f in os.listdir('logs') if f.endswith('_updater.log')]
while True:
    if len(log_files) > 5:
        log_files.sort()
        logging.info(f'More than 5 log ({len(log_files)}) files found, deleting oldest log file: {log_files[0]}')
        try:
            os.remove(os.path.join('logs', log_files[0]))
        except Exception as e:
            logging.critical(f'Breaking operation; Error while deleting log file: {e}')
            break
        log_files.pop(0)
    else:
        break

def update():
    logging.info('Starting update process...')
    base_path = str(Path(__file__).parent) + "/"

    headers = {
        "Authorization" : 'token ghp_r5***',
        "Accept": 'application/vnd.github.v3+json'
    #    "Accept": '*.*',
    }
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

    OWNER = 'kaboomie121'
    REPO  = 'miravbotcode'

    REF  = ''      # master/main branch is ref empty, otherwise specify the branch name or tag name

    EXT  = 'zip'
    #EXT  = 'tar'  # it also works
    url = f'https://api.github.com/repos/{OWNER}/{REPO}/{EXT}ball/{REF}'
    logging.info('github url:' + url)

    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        logging.info('size:' + str(len(r.content)))
        # save the file
        try:
            with open(base_path + f'output.{EXT}', 'wb') as fh:
                fh.write(r.content)
                logging.info(f'File {base_path}output.{EXT} saved successfully.')
        except Exception as e:
            logging.critical(f'Error saving the file: {e}')
            return

        # Try to extract the file
        try:
            with zipfile.ZipFile(base_path + f'output.{EXT}', 'r') as zip_ref:
                zip_ref.extractall(base_path)
                logging.info(f'File {base_path}output.{EXT} extracted successfully.')
        except Exception as e:
            logging.critical(f'Error extracting the file: {e}')
            return

        # find the extracted folder (it should be the only one in the base path)
        for file in os.listdir(base_path):
            filepath = os.path.join(base_path, file)
            if os.path.basename(filepath).startswith("kaboomie121-MiRavBotCode"):
                logging.info('extracted folder:' + filepath)
                break
        
        # remove the old files in the base path (except logs and the extracted folder) and move the new files to the base path
        try:
            for file in os.listdir(base_path):
                if (file == "logs" or file == filepath.removeprefix(base_path) or file == "updater.py"):
                    continue
                logging.info(f'Removing file in base path: {file}')
                os.remove(os.path.join(base_path, file))
        except Exception as e:
            logging.critical(f'Error removing file: {e}')
            return
        

        # move the files
        try:
            for file in os.listdir(filepath):
                shutil.move(os.path.join(filepath, file), os.path.join(base_path, file))
                logging.info(f'Moved {os.path.join(filepath, file)} to {os.path.join(base_path, file)}')    
        except Exception as e:
            logging.critical(f'Error moving file: {e}')
            return
        
        # remove the empty extracted folder
        try:
            os.removedirs(filepath)
        except Exception as e:
            logging.critical(f'Error removing empty folder: {e}')
            return
        # All succeeded, start bot and kill myself
        logging.info('Update successful, starting bot...')
        os.system(f'start cmd /c "cd {base_path} && python bot.py"')
        logging.info('Bot start called, exiting updater...')
        os._exit(0)
    else:
        logging.critical(r.text)    

update()