import logging
from pathlib import Path
logging.getLogger(__name__)
logging.info(f'Importing {Path(__file__).name}')

import discord
from config_loader import config, isDevBot


SQUADRONSTAFFID = config["squadronStaffId"]
if isDevBot:
    SQUADRONSTAFFID = 1306031448209363054

def IsUserSquadronStaff(discordUser : discord.Member):
    logging.info(f"Checking discord user for squadron staff: {discordUser}")
    if (discordUser.get_role(SQUADRONSTAFFID) != None):# or discordUser.id == 259644962876948480:
        logging.info("User is squadron staff")
        return True
    logging.info("User is NOT squadron staff")
    return False


def IsUserBotOwner(discordUser : discord.Member):
    if discordUser.id == 259644962876948480:
        return True
    return False