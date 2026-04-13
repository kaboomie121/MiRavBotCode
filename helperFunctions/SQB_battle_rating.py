import logging
from pathlib import Path
logging.getLogger(__name__)
logging.info(f'Importing {Path(__file__).name}')

from config_loader import config
import discord
import requests

def GetCurrentSquadronSchedule():
    result = requests.get("https://forum.warthunder.com/t/season-schedule-for-squadron-battles/4446")
    if result.status_code == 200:
        logging.info()