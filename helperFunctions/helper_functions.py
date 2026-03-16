from json import loads
from pathlib import Path
import discord as Discord

base_path = Path(__file__).parent.parent
config = loads((base_path / "config.json").read_text())

SQUADRONSTAFFID = config["squadronStaffId"]
isDevBot = config["devMode"]
if isDevBot:
    SQUADRONSTAFFID = 1306031448209363054

async def IsUserSquadronStaff(discordUser : Discord.Member):
    if (discordUser.get_role(SQUADRONSTAFFID) != None) or discordUser.id == 259644962876948480:
        return True
    return False


async def IsUserBotOwner(discordUser : Discord.Member):
    if discordUser.id == 259644962876948480:
        return True
    return False