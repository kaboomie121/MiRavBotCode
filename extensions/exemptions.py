import logging
from pathlib import Path
logging.getLogger(__name__)
logging.info(f'Importing {Path(__file__).name}')

import discord
from config_loader import config, isDevBot

import discord
from discord import app_commands
from discord.ext import commands

from datetime import datetime, timedelta
from asyncio.windows_events import NULL


SQUADRONSTAFFID = config["squadronStaffId"]
if isDevBot:
    SQUADRONSTAFFID = 1306031448209363054

# import all needed helper functions
from helperFunctions.data_helpers import get_exemption_list, get_discord_exemption_list
from helperFunctions.db import Writedata

@app_commands.guild_only()
class ExemptionListGroup(app_commands.Group):
    @app_commands.command(description="Exemption list")
    async def list(self, ctx : discord.Interaction):
        if ((ctx.user.get_role(SQUADRONSTAFFID) == None) and not(ctx.user.id == 259644962876948480)):
            await ctx.response.send_message('You do not have the requirements for this command.', ephemeral=True)
            return
        listExemptions = await get_exemption_list()
        discordListExemptions = await get_discord_exemption_list()
        
        endPrint = "The current people whom are exempt from kicks:\n"
        for exemption in listExemptions:
            endPrint += exemption + "\n"

        endPrint += "\nDiscord members exempt from kicks:\n"
        for exemption in discordListExemptions:
            endPrint += f"<@{exemption}>\n"

        endPrint += f"\nTotal: {len(listExemptions)+ len(discordListExemptions)}"
        await ctx.response.send_message(endPrint)

    #@app_commands.guild_only()
    #@app_commands.command(description="Discord exemption list add")
    #async def discordnameadd(self, ctx : discord.Interaction, discordUser : discord.Member):
    #    if ((ctx.user.get_role(SQUADRONSTAFFID) == None) and not(ctx.user.id == 259644962876948480)):
    #        await ctx.response.send_message('You do not have the requirements for this command.', ephemeral=True)
    #        return
    #    listExemptions = await get_discord_exemption_list()
    #    if discordUser.id in listExemptions:
    #        await ctx.response.send_message(f'"{discordUser.nick.strip()}" is already in the exemption list, you cannot add the same member twice. Did you mean to use "/exemptions remove {discordUser}"?', ephemeral=True)
    #        return
    #    
    #    endPrint = discordUser.id
    #    for exemption in listExemptions:
    #        endPrint += "§§" + exemption
    #    await writedata("Test", "ExemptionListDiscord", endPrint)
    #    await ctx.response.send_message(f'"{discordUser.nick.strip()}" has been added to the exemption list.', ephemeral=True)
    
    @app_commands.command(description="Ingame name exemption list add")
    async def ingamenameadd(self, ctx : discord.Interaction, ingameusername : str):
        if ((ctx.user.get_role(SQUADRONSTAFFID) == None) and not(ctx.user.id == 259644962876948480)):
            await ctx.response.send_message('You do not have the requirements for this command.', ephemeral=True)
            return
        listExemptions = await get_exemption_list()
        if ingameusername.lower() in listExemptions:
            await ctx.response.send_message(f'"{ingameusername.strip()}" is already in the exemption list, you cannot add the same member twice. Did you mean to use "/exemptions remove {ingameusername}"?', ephemeral=True)
            return
        
        endPrint = ingameusername.lower().strip()
        for exemption in listExemptions:
            endPrint += "§§" + exemption
        await Writedata("Bot", "ExemptionListIGN", endPrint)
        await ctx.response.send_message(f'"{ingameusername.strip()}" has been added to the exemption list.', ephemeral=True)
            
    
    @app_commands.command(description="Exemption list remove")
    async def remove(self, ctx : discord.Interaction, ingameusername : str):
        if ((ctx.user.get_role(SQUADRONSTAFFID) == None) and not(ctx.user.id == 259644962876948480)):
            await ctx.response.send_message('You do not have the requirements for this command.', ephemeral=True)
            return
        listExemptions = await get_exemption_list()
        
        if not(ingameusername.lower().strip() in listExemptions):
            await ctx.response.send_message(f'Couldn\'t remove "{ingameusername.strip()}" from the permanent exemption list, they\'re not in the list. Did you mean to use "/exemptions add {ingameusername}"?', ephemeral=True)
            return
        
        finalWritePart = ""
        for username in listExemptions:
            if not (username == ingameusername.lower().strip()):
                finalWritePart += "§§"+ username

        await Writedata("Bot", "ExemptionListIGN", finalWritePart[2:])
            
        await ctx.response.send_message(f'Removed "{ingameusername}" from the permanent exemption list', ephemeral=True)



async def setup(bot : commands.Bot):
    bot.tree.add_command(ExemptionListGroup(name="exemptions", description="Exemptions list"))
    