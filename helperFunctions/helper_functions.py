import logging
from pathlib import Path
logging.getLogger(__name__)
logging.info(f'Importing {Path(__file__).name}')

import discord
from config_loader import config, isDevBot


if isDevBot:
    SQUADRONSTAFFID = 1306031448209363054

async def IsUserSquadronStaff(discordUser : discord.Member):
    if (discordUser.get_role(SQUADRONSTAFFID) != None) or discordUser.id == 259644962876948480:
        return True
    return False


async def IsUserBotOwner(discordUser : discord.Member):
    if discordUser.id == 259644962876948480:
        return True
    return False