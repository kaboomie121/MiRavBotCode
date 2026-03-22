# Set up logging
import os

import logging
from pathlib import Path
from datetime import timedelta, datetime
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Ensure logs folder exists
Path("logs").mkdir(exist_ok=True)

# Set the one of the following levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
loggingLevel = logging.INFO
# Set max amount of logs
MAX_LOGS_AMOUNT = 5

# Create a logger
logger = logging.getLogger()
logger.setLevel(loggingLevel)

# Formatter (used by both handlers)
formatter = logging.Formatter(
    '%(asctime)s - %(relativeCreated)d - %(name)s - %(levelname)s - %(filename)s | %(funcName)s:%(lineno)d - %(message)s'
)

# File handler
def create_file_handler():
    log_file = Path(f'logs/{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log')
    handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    handler.setLevel(loggingLevel)
    handler.setFormatter(formatter)
    return handler

file_handler = create_file_handler()

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(loggingLevel)

console_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# if there are more than 5 log files, delete the oldest one and not _updater logs
def RemoveOldLogs():
    logging.info(f"Checking to delete logs if there are more than {MAX_LOGS_AMOUNT} logs")
    global log_files
    log_files = [f for f in os.listdir('logs') if f.endswith('.log') and not f.endswith('_updater.log')]
    log_files.sort()
    logging.debug(f'We have {len(log_files)} / {MAX_LOGS_AMOUNT} logs')
    while True:
        if len(log_files) > MAX_LOGS_AMOUNT:
            logging.info(f'More than {MAX_LOGS_AMOUNT} log ({len(log_files)}) files found, deleting oldest log file: {log_files[0]}')
            try:
                logging.debug(f'Attempting to remove: {os.path.join('logs', log_files[0])}')
                os.remove(os.path.join('logs', log_files[0]))
            except Exception as e:
                logging.critical(f'Breaking operation; Error while deleting log file: {e}')
                break
            log_files.pop(0)
        else:
            break

RemoveOldLogs()

logging.info('Logging INIT done, starting bot.py')
# Configureable
import re
import asyncio
from asyncio.windows_events import NULL
from json import loads
from operator import truediv
import string
from tkinter import CHAR
from traceback import print_tb

from discord.ext import tasks
import discord.ext
import discord.ext.commands


base_path = Path(__file__).parent
config = loads((base_path / "config.json").read_text())
token = loads((base_path / "token.json").read_text())
versiontxt = (base_path / "version.txt").read_text()

isDevBot = config["devMode"]
hostUser = token["user"]

if isDevBot:
    TOKEN = token["testtoken"]
else:
    TOKEN = token["token"]

LOGGING_CHANNEL = config["loggingChannelId"]
DISCORDGUILD = config["discordGuild"]
TESTDISCORDGUILD = config["testDiscordGuild"]
NOTICELIST_CHANNEL = config["noticeListChannelId"]
SQUADRONMEMBERROLEID = config["squadronMemberRoleId"]

import sys
sys.stdout.reconfigure(encoding='utf-8')
import discord 
from discord import Client, Embed, Interaction, app_commands, ui
from discord.ext import commands
import requests

client = commands.Bot(intents=discord.Intents.all(), command_prefix="thisisnotneeded", help_command=None)


FIRST_DEADLINE = config["firstDeadline"]
FIRST_ACTIVITY_REQUIREMENT = config["firstActivityRequirement"]
SECOND_DEADLINE = config["secondDeadline"]
SECOND_ACTIVITY_REQUIREMENT = config["secondActivityRequirement"]
EXEMPTION_SQ_RATING = config["exemptionSQRating"]

#SQUADRONSTAFFID = config["squadronStaffId"]
#if isDevBot:
#    SQUADRONSTAFFID = 1306031448209363054
COMMUNITYHOST = config["communityHostRoleId"]

botTimeStarted = datetime.now()


DBCHANNELID = config["DBChannelId"]
  
# import all needed helper functions
from helperFunctions.data_helpers import get_squadron_players, get_discord_list, get_discord_exemption_list
from helperFunctions.db import SetupDB, GetFullUserData, Writedata, Removedatakey, GetData
from helperFunctions.helper_functions import IsUserSquadronStaff, IsUserBotOwner
from helperFunctions.version_checker import checkForUpdate
from updater import update


# check for updates, if there are any, update the bot script, only run if not in dev mode and restart the bot
if not isDevBot:
    if checkForUpdate():
        update()

# check for an update every 30 minutes, only run if not in dev mode
@tasks.loop(minutes=30)
async def periodic_update_check():
    if isDevBot:
        logging.warning('Periodic update check called, but bot is in dev mode, skipping update check.')
        return
    logging.info('Running periodic update check...')
    if checkForUpdate():
        logging.info('Update found during periodic check, restarting bot...')
        os.execv(sys.executable, [sys.executable] + sys.argv)
        os._exit(0)
    else:
        logging.info('No update found during periodic check.')



@client.tree.command(description="Starts the next season!")
async def nextseason(ctx:  discord.Interaction):
    if not IsUserBotOwner(ctx.user):
        await ctx.response.send_message('You do not have the requirements for this command.', ephemeral=True)
        return
    await ctx.response.send_message('Next season starting... Transfering data...', ephemeral=False)
    messages = [message async for message in client.get_channel(DBCHANNELID).history(limit=240)]

    for messageMain in messages:
        # we check if they have the "HighestSquadronRating" in the message, if so, get the data, set it to 0 and put it in "PreviousSeasonHighestSquadronRating"
        if messageMain.content.find("HighestSquadronRating") != -1:
            message, data = await GetData(messageMain.content.split("|")[0], "HighestSquadronRating")
            if data == None:
                continue
            await Writedata(message.content.split("|")[0], "PreviousSeasonHighestSquadronRating", data)
            await Writedata(message.content.split("|")[0], "HighestSquadronRating", "0")
    await ctx.response.edit_message(content="All done! Next season started!.")
 
    


    
@client.tree.command(description="A list of the users in the squadron, optionally sorted. (auto on join date)")
@app_commands.choices(sorting=[
    app_commands.Choice(name='Join date', value=0),
    app_commands.Choice(name='League points', value=1),
    app_commands.Choice(name='Activity', value=2)
])
async def allsquadronmembers(ctx:  discord.Interaction, sorting: app_commands.Choice[int]):
    await ctx.response.send_message('Gathering all players...', ephemeral=True)

    squadronList = await get_squadron_players()
    squadronList = list(squadronList.values())
    if sorting.value in [1, 2]:
        # Sorting logic based on list index
        sort_index = {0: 4, 1: 1, 2: 2}[sorting.value]  # Mapping sorting choice to list index

        squadronList.sort(key=lambda player: player[sort_index], reverse=True)


    # change those in notice list to "Notice submitted"        
    printString = f'```cpp\n'
    printString += f'Users: {len(squadronList)}\n'
    printString += f'  Username             | Joined date | League | Activity\n'
    for squadronMember in squadronList:
        printString += f'- {squadronMember[0].ljust(20)} |  {squadronMember[4]} | {squadronMember[1].rjust(6)} | {squadronMember[2].rjust(8)}\n'
        if (len(printString) > 1900):
            printString += '```'
            await ctx.channel.send(printString)
            printString = '```cpp\n'
    printString += '```'
    if (len(printString) > 10):
        await ctx.channel.send(printString)

@client.tree.command(description="Description of squadron battles")
async def squadronbattles(ctx:  discord.Interaction):
    logging.info(f'{ctx.user} ran squadronbattles command')
    embed = discord.Embed(title=f"What is squadron battles?", colour=discord.Colour.random())
    embed.timestamp = datetime.today()
    embed.set_footer(text="kaboomie121")
    embed.add_field(inline=False, name="<:SquadronRating:1268976901196877895> Squadron Battles <:SquadronRating:1268976901196877895>", value="Squadron Battles (SQB) are 8v8 matches where squadrons compete for ranking points.")
    embed.add_field(inline=False, name="How It Works", value="8 players per team (see ⁠events to join).\nLimited spawns:\n- 8 Ground / 4 Air (incl. helicopters)\n- 1 life per player, no vehicle switching.\n- Air players can J out at the airfield when fully repaired.\n- Gameplay is like Ground RB.")

    
    embed.add_field(inline=False,name="When are they held?", value="\nHeld in seasons with BR limits decreasing weekly (e.g., Week 1: BR 12.7 → Week 8: BR 5.7).\nThere are two windows:\n- EU: <t:1738936800:t> - <t:1738965600:t>\n- US: <t:1738890000:t> - <t:1738911600:t>\n-# ^^Adjusted to your timezone^^")
    embed.add_field(inline=False,name="Rules for Attending", value="- Follow event organizers’ instructions.\n- Only speak in battle for important callouts.\n- Use fully modified vehicles (mandatory: Parts, best ammo, fire control upgrades, etc.).\n- Pick a vehicle you perform well in.\n- If lacking a relevant BR vehicle, join as a reserve.")
    embed.add_field(inline=False,name="After the Event", value="- Stay in VC for feedback.\n- Summary discussion is optional but helps improve performance.")

    await ctx.response.send_message(embed = embed)

@client.tree.command(description="How long has the bot been up?")
async def uptime(ctx:  discord.Interaction):
    logging.info(f'{ctx.user} ran uptime command')
    deltatime = datetime.now() - botTimeStarted
    await ctx.response.send_message(f'I\'ve been online since <t:{botTimeStarted.timestamp():.0f}:f>, which is: \n'+
                                    f'{deltatime.days} day(s) and\n' +
                                    f'{deltatime.seconds:.0f} seconds aka\n' +
                                    f'{deltatime.seconds/60:.1f} minutes aka\n' +
                                    f'{deltatime.seconds/60/60:.2f} hours ago\n' +
                                    '')

@client.tree.command(description="Pong!")
async def ping(ctx:  discord.Interaction):
    logging.info(f'{ctx.user} ran ping command')
    await ctx.response.send_message(f'{hostUser}: Pong! {client.latency:.4f}s')


@client.tree.command(description="Verify the users within the discord/squadron.")
async def verifymembers(ctx:  discord.Interaction):
    logging.info(f'{ctx.user} ran verifymembers command')
    if not IsUserSquadronStaff(ctx.user):
        await ctx.response.send_message('You do not have the requirements for this command.', ephemeral=True)
        logging.info(f'{ctx.user} does not have the requirements for verifymembers command')
        return
    
    found = False
    usersChecked = 0
    usersAdded = 0
    usersRemoved = 0
    totalSquadronMembers = 0
    usersNoUTC = 0
    totalOtherSquadrons = 0
    totalRepresentingAllies = 0
    discordMembers = await get_discord_list()
    discordExemptionList = await get_discord_exemption_list()
    squadronMembers = await get_squadron_players()
    otherSquadronRole = discord.utils.get(client.get_guild(DISCORDGUILD).roles, id=1374461613083590667)
    allyRole = discord.utils.get(client.get_guild(DISCORDGUILD).roles, id=1346451233543557121)
    memberRole = discord.utils.get(client.get_guild(DISCORDGUILD).roles, id=1338270607220932639)

    await ctx.response.send_message('Gathered all data... Executing order 66...', ephemeral=True)
    for discordMember in discordMembers:
        logging.debug(f'Checking member: {discordMember.nick} with id: {discordMember.id}')
        if discordMember.id in discordExemptionList:
            logging.debug(f'Member {discordMember.nick} is in the exemption list, skipping.')
            continue
        if discordMember.bot:
            logging.debug(f'Member {discordMember.nick} is a bot, skipping.')
            continue
        found = False
        usersChecked += 1
        if allyRole in discordMember.roles:
            logging.debug(f'Member {discordMember.nick} is representing an ally, skipping.')
            totalRepresentingAllies += 1
            continue
        elif otherSquadronRole in discordMember.roles:
            logging.debug(f'Member {discordMember.nick} is representing another squadron, skipping.')
            totalOtherSquadrons += 1
            continue

        #if (discordMember.nick != None):
        #    logging.info(discordMember.nick[:discordMember.nick.find('[')].replace(' ', '').strip().lower())
        if (discordMember.nick != None and discordMember.nick.strip()[0] == '['):
            logging.debug(f'Member {discordMember.nick} has no name tag, skipping.')
            continue
        for counterB, squadronMember in squadronMembers.items():
            if (discordMember.nick != None):
                logging.debug(f'Comparing with squadron member: {squadronMember.nick}')
                if discordMember.nick[:discordMember.nick.find('[')].replace(' ', '').strip().lower() == squadronMember[0].strip().lower():
                    logging.debug(f'Member {discordMember.nick} found in squadron list as {squadronMember[0]}, marking as found.')
                    found = True
                    break
        
        if found:
            totalSquadronMembers += 1
            logging.debug(f'Member {discordMember.nick} is a squadron member. Now at {totalSquadronMembers}')
        if found and not(memberRole in discordMember.roles):
            await discordMember.add_roles(memberRole)
            usersAdded += 1
            logging.debug(f'Member {discordMember.nick} added to squadron member role. Now at {usersAdded} added users.')
        elif not found and (memberRole in discordMember.roles):
            await discordMember.remove_roles(memberRole)
            usersRemoved += 1
            logging.debug(f'Member {discordMember.nick} removed from squadron member role. Now at {usersRemoved} removed users.')
        elif not found and (discordMember.nick == None or discordMember.nick.find('[') == -1):
            usersNoUTC += 1
            logging.debug(f'Member {discordMember.nick} has no UTC tag and is not found in squadron list, marking as no UTC. Now at {usersNoUTC} users with no UTC.')

    await ctx.channel.send(
        f'All done!\nTotal checked: {usersChecked}\n'+
        f'Total squadron members: {totalSquadronMembers}\n'+
        f'New users: {usersAdded}\n'+
        f'Users removed: {usersRemoved}\n'+
        f'Users with no tags []: {usersNoUTC}\n'+
        f'Total representing allies: {totalRepresentingAllies}\n'+
        f'Total other squadron members: {totalOtherSquadrons}\n'
        )

@client.tree.command(description="Check if the username is found in the squadron.")
async def checkmembername(ctx :  discord.Interaction, name: str):
    found = False
    squadronMembers = await get_squadron_players()
    squadronMemberFound = ''
    for counterB, squadronMember in squadronMembers.items():
        if name.strip().lower().replace(' ', '') == squadronMember[0].strip().lower().replace(' ', ''):
            squadronMemberFound = squadronMember
            found = True
            break 
    if found:
        await ctx.response.send_message(f':white_check_mark: Member found with the name ``{squadronMemberFound[0]}``; activity: {squadronMemberFound[2]}, league points: {squadronMemberFound[1]}')
    else:
        await ctx.response.send_message(f':x: Couldn\'t find a user with the name: ``{name}``')

    if ctx.author == client.user:
        return
    
    if ctx.content.startswith('&test'):
        embed = discord.Embed(title="test List", colour=discord.Colour.red())
        embed.add_field(name="Field 1", value="Value 1")
        embed.add_field(name="Field 2", value="Value 2")
        embed.add_field(name="Field 3", value="Value 3")
        embed.add_field(name="Field 4", value="Value 4")
        embed.add_field(name="Field 5", value="Value 5")
        embed.add_field(name="Field 6", value="Value 6")
        embed.timestamp = datetime.today()
        embed.set_footer(text="kaboomie121")
        await ctx.channel.send(embed = embed)



async def WriteAttendanceLists(self, embed, printReserveList):
    printedList = ''
    for user in self.primary:
        printedList += f'{str(user.nick).split('[')[0]} | <@{user.id}>\n'
    
    maxMembers = ""

    if self.maxmembers != -1:
        maxMembers = f" (max {self.maxmembers})"

    if len(self.primary) == 1:
        embed.set_field_at(0, name=f'1 Attendee{maxMembers}:', value=printedList, inline=True)
    else:
        embed.set_field_at(0, name=f'{len(self.primary)} Attendees{maxMembers}:', value=printedList, inline=True)

    if printReserveList:
        printedListReserve = ''
        for user in self.reserve:
            printedListReserve += f'{str(user.nick).split("[")[0]} | <@{user.id}>\n'

        if len(self.reserve) == 1:
            embed.set_field_at(1, name=f'1 Reserve:', value=printedListReserve, inline=True)
        else:
            embed.set_field_at(1, name=f'{len(self.reserve)} Reserves:', value=printedListReserve, inline=True)

class EventView(discord.ui.View):
    def __init__(self, embed : Embed, host, endDate : datetime, squadronmembersonly : bool, maxmembers : int, twolistsystem: bool,
                 primaryList = None, reserveList = None):
        super().__init__(timeout=None)

        if primaryList != None:
            self.primary = primaryList
        else:
            self.primary = [host]

        if reserveList != None:
            self.reserve = reserveList
        else:
            self.reserve = []

        self.embed = embed
        self.squadronmembersonly = squadronmembersonly
        self.twolistsystem = twolistsystem
        self.maxmembers = maxmembers
        self.hostdate = endDate
        self.started = False
        if not twolistsystem:
            for item in self.children:
                if isinstance(item, discord.ui.Button) and item.custom_id == "reservebutton":
                    item.disabled = True

    async def getembed(self):
        return self.embed
    
    async def delay(self, minutes, hours):
        delayTime = timedelta(hours=hours, minutes=minutes)
        newDate = self.hostdate + delayTime
        
        self.embed.description = self.embed.description.replace(str(int(self.hostdate.timestamp())), str(int(newDate.timestamp())))
        
        self.hostdate = newDate
        await self.message.edit(view=self, embed=self.embed)
        await self.message.reply(content=f"**{self.embed.title.replace('*', '')}** delayed to <t:{str(int(self.hostdate.timestamp()))}:t>")
        

    async def edit(self, newembed = None, disabled = None, newcontent = None):
        if not(disabled == None):
            for item in self.children:
                item.disabled = disabled

        if not(newembed == None):
            self.embed = newembed

        if newcontent == None:
            await self.message.edit(view=self, embed=self.embed)
        else:
            await self.message.edit(view=self, embed=self.embed, content=newcontent)
    
    async def start(self):
        await self.message.edit(view=self, embed=self.embed, content="Event started! ||<@&1338270607220932639>||")

    async def stop(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self, embed=self.embed, content="This event has ended")
        except:
            logging.exception("⚠️ Something went wrong when editing message to an event")
        finally:
            try:
                super().stop()
            except:
                logging.exception("⚠️ Something went wrong when deleting an event")
            finally:
                await Removedatakey("OngoingEvents", f"{self.message.channel.id}-{self.message.id}")

    @discord.ui.button(label="Attend", style=discord.ButtonStyle.green, custom_id="primarybutton")
    async def button_primary(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.squadronmembersonly and not isDevBot and (interaction.user.get_role(SQUADRONMEMBERROLEID) == None or interaction.user.nick.find('[') == -1):
            await interaction.response.send_message("⚠️ You are not a squadron member! Become one by applying in <#1303841412684447805>", ephemeral=True)
            return
        
        if interaction.user in self.primary:
            self.primary.pop(self.primary.index(interaction.user))
            await interaction.response.send_message("❌ You are no longer attending.", ephemeral=True)
        else:
            if len(self.primary) >= self.maxmembers and not (self.maxmembers == -1):
                if interaction.user in self.reserve:
                    await interaction.response.send_message("❌ Primary list is full! You cannot switch to primary!", ephemeral=True)
                    return
                if self.twolistsystem:
                    self.reserve.append(interaction.user)
                    await interaction.response.send_message("✅ Primary list full! You're now attending as reserve!", ephemeral=True)
                else:
                    await interaction.response.send_message("❌ The event is full! You can not attend!", ephemeral=True)

                await WriteAttendanceLists(self, self.embed, self.twolistsystem)
                await interaction.message.edit(embed=self.embed)
                return
            # people can still attend!
            if interaction.user in self.reserve:
                self.reserve.pop(self.reserve.index(interaction.user))
                self.primary.append(interaction.user)
                
                
                await WriteAttendanceLists(self, self.embed, self.twolistsystem)
                await interaction.message.edit(embed=self.embed)
                await interaction.response.send_message("✅ You have switched to primary.", ephemeral=True)
                return

            self.primary.append(interaction.user)
            await interaction.response.send_message("✅ You're now attending!", ephemeral=True)
        
        await WriteAttendanceLists(self, self.embed, self.twolistsystem)
        await interaction.message.edit(embed=self.embed)
    
    @discord.ui.button(label="Attend as reserve", style=discord.ButtonStyle.blurple, custom_id="reservebutton")
    async def button_reserve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isDevBot and (interaction.user.get_role(SQUADRONMEMBERROLEID) == None or interaction.user.nick.find('[') == -1):
            await interaction.response.send_message("⚠️ You are not a squadron member! Become one by applying in <#1303841412684447805>", ephemeral=True)
            return
        
        if interaction.user in self.primary:
            self.primary.pop(self.primary.index(interaction.user))
            self.reserve.append(interaction.user)
            
            await WriteAttendanceLists(self, self.embed, self.twolistsystem)
            await interaction.message.edit(embed=self.embed)
            await interaction.response.send_message("✅ You have switched to reserve.", ephemeral=True)
            return

        if interaction.user in self.reserve:
            self.reserve.pop(self.reserve.index(interaction.user))
            await interaction.response.send_message("❌ You are no longer attending.", ephemeral=True)
        else:
            self.reserve.append(interaction.user)
            await interaction.response.send_message("✅ You're now attending as reserve!", ephemeral=True)

        
        await WriteAttendanceLists(self, self.embed, self.twolistsystem)
        await interaction.message.edit(embed=self.embed)

@app_commands.guild_only()
class EventGroup(app_commands.Group):
    @app_commands.command(description="A command to host SQB at a specified BR and hour")
    @app_commands.choices(whotoping=[
    app_commands.Choice(name='Squadron members only', value=0),
    app_commands.Choice(name='Event ping only', value=1),
    app_commands.Choice(name='Both pings', value=2)
    ])
    async def host(self, ctx : discord.Interaction, title : str, hour : int, minute : int, description : str = "", maxmainattendees : int = -1, hasreservelist : bool = False, whotoping : app_commands.Choice[int] = 0):
        if not(isDevBot) and (not IsUserSquadronStaff(ctx.user) and ctx.user.get_role(COMMUNITYHOST) == None) and not(IsUserBotOwner(ctx.user) or ctx.user.id == 490216540331966485):
            await ctx.response.send_message('⚠️ You do not have the requirements for this command.', ephemeral=True)
            return
        if maxmainattendees < 1 and maxmainattendees != -1:
            await ctx.response.send_message(content='❌ You cannot have less than 1 main attendee! Leave empty or type -1 if infinite', ephemeral=True)
            return
        
        if hour == 24:
            hour = 0
        elif not (0 <= hour <= 24):
            await ctx.response.send_message("⚠️ Hour must be between 0 and 24.", ephemeral=True)
            return
        if not (0 <= minute <= 59):
            await ctx.response.send_message("⚠️ Minute must be between 0 and 59.", ephemeral=True)
            return
        
        if ctx.user.nick.find('[') == -1:
            await ctx.response.send_message('⚠️ You do not have a UTC tag! Get one by putting [UTC+XX] in your nickname (replace +XX with your timezone in utc)', ephemeral=True)
            return
        
        squadronmembersonly = True
        if whotoping != 0:
            squadronmembersonly = False
        await ctx.response.send_message(content='✅ Starting event!', ephemeral=True)

        time = ctx.user.nick[ctx.user.nick.find('[')+4:len(ctx.user.nick)-1]
        today = datetime.today()
        newHour = hour-int(time)+1
        if (newHour < 0):
            newHour += 24
        elif (newHour > 23):
            newHour -= 24

        hostDate = today.replace(hour=newHour, minute=minute, second=0, microsecond=0)

        if (hostDate < today):
            hostDate = hostDate + timedelta(days=1)

        description =  f"<t:{int(hostDate.timestamp())}:R> | <t:{int(hostDate.timestamp())}:t>\n" +(description.replace('\\n ', '\n')).replace('\\n', '\n')

        embed = discord.Embed(color=int("696969", 16), title=title,
            description=description)
        
        embed.set_author(name=f'Hosted by {ctx.user.nick[:ctx.user.nick.find('[')]}', icon_url=ctx.user.display_avatar)
        
        if maxmainattendees == -1:
            embed.add_field(name='1 Attendee:', value=f'{str(ctx.user.nick).split('[')[0]} | <@{ctx.user.id}>\n', inline=True)
        else:
            embed.add_field(name=f'1 Attendee(max {maxmainattendees}):', value=f'{str(ctx.user.nick).split('[')[0]} | <@{ctx.user.id}>\n', inline=True)

        if hasreservelist:
            embed.add_field(name='0 Reserves:', value=f'', inline=True)

        if squadronmembersonly:
            # Invisible character that saves if squadron member only
            embed.set_author(name=f'​Hosted by {ctx.user.nick[:ctx.user.nick.find('[')]}', icon_url=ctx.user.display_avatar)
        else:
            # NO invisible character that saves NOT squadron member only
            embed.set_author(name=f'Hosted by {ctx.user.nick[:ctx.user.nick.find('[')]}', icon_url=ctx.user.display_avatar)
        
        myView = EventView(embed, ctx.user, hostDate, squadronmembersonly, maxmainattendees, hasreservelist)

        if whotoping == 0:
            whotopingText = "<@&1338270607220932639>" # Squadron members
        elif whotoping == 1:
            whotopingText = "<@&1300018031002652754>" # Events ping
        else:
            whotopingText = "<@&1338270607220932639> and <@&1300018031002652754>" # Both pings

        myView.message = await ctx.channel.send(whotopingText, embed=embed, view=myView)
        await Writedata("OngoingEvents", f'{myView.message.channel.id}-{myView.message.id}', int(hostDate.timestamp()))
        myView.id = today.timestamp()
        myView.owner = ctx.user
        client.add_view(view=myView, message_id=myView.message.id)
        

    @app_commands.command(description="A command to host SQB at a specified BR and hour")
    async def stop(self, ctx : discord.Interaction, messageid : str = None):
        if not(isDevBot) and (not IsUserSquadronStaff(ctx.user) and ctx.user.get_role(COMMUNITYHOST) == None) and not(ctx.user.id == 259644962876948480 or ctx.user.id == 490216540331966485):
            await ctx.response.send_message('⚠️ You do not have the requirements for this command.', ephemeral=True)
            return
        viewAmount = 0
        for view in client.persistent_views:
            viewAmount += 1
        if viewAmount == 0:
            await ctx.response.send_message("Not detecting any ongoing events...", ephemeral=True)
            return
        
        if messageid == None:
            await ctx.response.send_message("Stopping your event most recent event!", ephemeral=True)
            # Try to find a event with same owner, if it exists.
            foundEvent = None
            allEventNames = ""
            viewAmount = 0
            selectListOptions = []
            for view in client.persistent_views:
                if view.owner.id == ctx.user.id:
                    viewAmount += 1
                    foundEvent = view
                    allEventNames += f'ID: {view.message.id} | HostDate: <t:{int((view.hostdate).timestamp())}:f> | {(view.embed.title).replace('\n', '')}\n'
                    selectListOptions.append( discord.SelectOption(value=view.message.id, label=view.embed.title.replace('\n', '').replace('*', ''), description=f"Hosted on {(view.hostdate).ctime()}") )

                    
            if viewAmount > 1:
                class StopSelect(discord.ui.Select):
                    def __init__(self, options):
                        super().__init__(placeholder="Choose an option...", min_values=1, max_values=1, options=options)

                    async def callback(self, ctx: discord.Interaction):
                        if self.disabled:
                            return
                        self.disabled = True
                        messageid = self.values[0]
                        await ctx.response.edit_message(view=None, content=f"Stopping the event with id: {messageid}")
                        # find event
                        foundEvent = None
                        for view in client.persistent_views:
                            if int(view.message.id) == int(messageid):
                                foundEvent = view
                                break
                                
                        # end if it exists
                        if foundEvent != None:
                            await foundEvent.stop()

                # delay view setup
                stopView = discord.ui.View(timeout = 300)
                stopView.add_item(StopSelect(selectListOptions))

                await ctx.edit_original_response(view=stopView, content=f"You have multiple ({viewAmount}) events ongoing, specify with a message ID or select via the menu below. All current ongoing events:\n{allEventNames}")
                return


            # End if it exists
            if foundEvent != None:
                await ctx.edit_original_response(content=f"Found a event with the title \"{(foundEvent.embed.title).replace('\n', '')}\"")
                await foundEvent.stop()
            else:
                await ctx.edit_original_response(content="You have no events ongoing...!")
        # If a messageID is specified
        else:
            try:
                messageid = int(messageid)
            except ValueError:
                await ctx.response.send_message("Message ID must be numeric.")
                return
            
            # find event
            await ctx.response.send_message(f"Stopping the event with id: {messageid}", ephemeral=True)
            foundEvent = None
            for view in client.persistent_views:
                if view.message.id == messageid:
                    foundEvent = view
                    break
                    
            # end if it exists
            if foundEvent != None:
                await ctx.edit_original_response(content=f"Stopping a event with the title {(foundEvent.embed.title).replace('\n', '')}")
                await foundEvent.stop()
            else:
                await ctx.edit_original_response(content=f"There is no event with the ID: {messageid}")

            
    #@app_commands.command(description="A command to host SQB at a specified BR and hour")
    #async def edit(self, ctx : discord.Interaction, messageid : int = None, title : str = None, description : str = None, smalldescription : str = None, hassecondlist : bool = None):
    #    if messageid == None:
    #        await ctx.response.send_message("Opening modal with event most recent event!", ephemeral=True)
    #    else:
    #        await ctx.response.send_message(f"Opening a modal with event id: {messageid}!", ephemeral=True)
    

    @app_commands.command(description="A command to host SQB at a specified BR and hour")
    async def delay(self, ctx : discord.Interaction, minutes : int = 0, hours : int = 0, messageid : str = None):
        if not(isDevBot) and ((not IsUserSquadronStaff(ctx.user) and ctx.user.get_role(COMMUNITYHOST) == None) and not(ctx.user.id == 259644962876948480 or ctx.user.id == 490216540331966485)):
            await ctx.response.send_message('⚠️ You do not have the requirements for this command.', ephemeral=True)
            return
        viewAmount = 0
        for view in client.persistent_views:
            viewAmount += 1
        if viewAmount == 0:
            await ctx.response.send_message("Not detecting any ongoing events...", ephemeral=True)
            return
        
        #if (hours < 0 or minutes < 0) and not isDevBot:
        #    await ctx.response.send_message("You can't delay the event by negative amount, edit the event instead if this was on purpose.", ephemeral=True)
        #    return

        if messageid == None:
            await ctx.response.send_message("Delaying your event most recent event!", ephemeral=True)
            # Try to find a event with same owner, if it exists.
            foundEvent = None
            allEventNames = ""
            viewAmount = 0
            selectListOptions = []
            for view in client.persistent_views:
                if view.owner == ctx.user:
                    viewAmount += 1
                    foundEvent = view
                    allEventNames += f'ID: {view.message.id} | HostDate: <t:{int((view.hostdate).timestamp())}:f> | {(view.embed.title).replace('\n', '')}\n'
                    selectListOptions.append( discord.SelectOption(value=view.message.id, label=view.embed.title.replace('\n', '').replace('*', ''), description=f"Hosted on {(view.hostdate).ctime()}") )
                    
            if viewAmount > 1:
                # Delay select list
                class DelaySelect(discord.ui.Select):
                    def __init__(self, options):
                        super().__init__(placeholder="Choose an option...", min_values=1, max_values=1, options=options)

                    async def callback(self, ctx: discord.Interaction):
                        if self.disabled:
                            return
                        self.disabled = True
                        messageid = self.values[0]
                        await ctx.response.edit_message(view=None, content=f"Delaying the event with id: {messageid}")
                        # find event
                        foundEvent = None
                        for view in client.persistent_views:
                            if int(view.message.id) == int(messageid):
                                foundEvent = view
                                
                        # end if it exists
                        if foundEvent != None:
                            await foundEvent.delay(minutes, hours)

                # delay view setup
                selectView = discord.ui.View( timeout = 300)
                selectView.add_item(DelaySelect(selectListOptions))
                await ctx.edit_original_response(view=selectView, content=f"You have multiple ({viewAmount}) events ongoing, specify with a message ID or use the provided dropdown below (within 5 minutes). All current ongoing events:\n{allEventNames}")

                return
            # Delay if it exists
            if foundEvent != None:
                await ctx.edit_original_response(content=f"Found a event with the title \"{(foundEvent.embed.title).replace('\n', '')}\"")
                await foundEvent.delay(minutes, hours)
            else:
                await ctx.edit_original_response(content="You have no events ongoing...!")
        # If a messageID is specified
        else:
            try:
                messageid = int(messageid)
            except ValueError:
                await ctx.response.send_message("Message ID must be numeric.")
                return
            
            # find event
            await ctx.response.send_message(f"Delaying the event with id: {messageid}", ephemeral=True)
            foundEvent = None
            for view in client.persistent_views:
                if view.message.id == messageid:
                    foundEvent = view
                    
            # end if it exists
            if foundEvent != None:
                await ctx.edit_original_response(content=f"Delaying the event with the title {(foundEvent.embed.title).replace('\n', '')}")
                await foundEvent.delay(minutes, hours)
            else:
                await ctx.edit_original_response(content=f"There is no event with the ID: {messageid}")

        

    @app_commands.describe(
    battlerating="Choose the battle rating (e.g., 6.7, 7.3, 8.0)",
    hour="Hour of the event in 24 hour notation (0-24), in your local time, the bot will automatically convert it",
    minute="Minute of the event 0-59"
    )
    @app_commands.command(description="A command to host SQB at a specified BR and hour")
    async def squadronbattle(self, ctx : discord.Interaction, battlerating : str, hour : int, minute : int):
        if not(isDevBot) and ((not IsUserSquadronStaff(ctx.user) and ctx.user.get_role(COMMUNITYHOST) == None) and not(ctx.user.id == 259644962876948480 or ctx.user.id == 490216540331966485)):
            await ctx.response.send_message('⚠️ You do not have the requirements for this command.', ephemeral=True)
            return
        if len(battlerating.strip()) == 0:
            await ctx.response.send_message('⚠️ Battle rating cannot be empty', ephemeral=True)
            return
        pattern = r"^(?:[0-9]|1[0-9]|20)\.(0|3|7)$"
        if not bool(re.fullmatch(pattern, battlerating)):
            await ctx.response.send_message('⚠️ Battle rating is incorrect! Please verify! It can only be numbers 0.0 to 20.7 with .0, .3, .7', ephemeral=True)
            return
        if hour == 24:
            hour = 0
        elif not (0 <= hour <= 24):
            await ctx.response.send_message("⚠️ Hour must be between 0 and 24.", ephemeral=True)
            return
        if not (0 <= minute <= 59):
            await ctx.response.send_message("⚠️ Minute must be between 0 and 59.", ephemeral=True)
            return

        if ctx.user.nick.find('[') == -1:
            await ctx.response.send_message('⚠️ You do not have a UTC tag! Get one by putting [UTC+XX] in your nickname (replace +XX with your timezone in utc)', ephemeral=True)
            return
        
        await ctx.response.send_message('✅ Starting squadron battles!', ephemeral=True)

        time = ctx.user.nick[ctx.user.nick.find('[')+4:len(ctx.user.nick)-1]
        today = datetime.today()
        newHour = hour-int(time)+1
        if (newHour < 0):
            newHour += 24
        elif (newHour > 23):
            newHour -= 24
        hostDate = today.replace(hour=newHour, minute=minute, second=0, microsecond=0)

        if (hostDate < today):
            hostDate = hostDate + timedelta(days=1)

        embed = discord.Embed(color=int("696969", 16), title=f'**Squadron Battles [MAX BR {battlerating}]**\n',
                            description=f'<t:{int(hostDate.timestamp())}:R> | <t:{int(hostDate.timestamp())}:t>\n' +
                            '**Min. required checks: 8**\n' +
                            '-# - Don\'t fake check, this will result in punishments!\n' +
                            '-# - Make sure you check on time!\n' +
                            '-# - <:MidnightRavens:1233397037110919220> Make sure your vehicles are spaded!\n')
        
        embed.set_author(name=f'​Hosted by {ctx.user.nick[:ctx.user.nick.find('[')]}', icon_url=ctx.user.display_avatar)
        
        embed.add_field(name='1 Attendee (max 8):', value=f'{str(ctx.user.nick).split('[')[0]} | <@{ctx.user.id}>\n', inline=True)
        embed.add_field(name='0 Reserves:', value=f'', inline=True)
                
        myView = EventView(embed, ctx.user, hostDate, True, 8, True)
        myView.message = await ctx.channel.send('<@&1338270607220932639>', embed=embed, view=myView)
        await Writedata("OngoingEvents", f'{myView.message.channel.id}-{myView.message.id}', int(hostDate.timestamp()))
        myView.id = today.timestamp()
        myView.owner = ctx.user
        client.add_view(view=myView, message_id=myView.message.id)


@client.tree.command(description="Shows the version of the bot")
async def version(ctx :  discord.Interaction):
    await ctx.response.send_message(versiontxt)

@client.tree.command(description="Testing")
async def test(ctx : discord.Interaction):
    if not isDevBot:
        await ctx.response.send_message(f'This is a test command for testing!')
        return
    logging.info("Test comamnd called")
    # devbot test code
    if not client.persistent_views:
        logging.info("No persistent views registered.")
    else:
        logging.info("Persistent Views:")
        for view in client.persistent_views:
            logging.info(f"- {view.__class__.__name__} | {view.id} (timeout={view.timeout}, children={len(view.children)})")
            for child in view.children:
                logging.info(f"- {child.__class__.__name__} | {child}")
            logging.info(view.primary)
            

    return
    guild = client.get_guild(TESTDISCORDGUILD)
    guildmembers = guild.members
    today = datetime.today()
    oneyear = today
    oneyear.replace(year=oneyear.year-1)

    if (oneyear.month == 13):
        oneyear.replace(month=1, year= oneyear.year +1)
    for guildmember in guildmembers:
        if guildmember.joined_at.timestamp()-oneyear.timestamp() > 0:
            logging.info(f"{guildmember.name} is in here for a year")
        else:
            logging.info(f"{guildmember.name} is NOT in here for a year")

@client.tree.command(description="statistics such as total utc per type!")
async def stats(message):
    # Get the list of discord members
    discord_members = await get_discord_list()

    # make a list of all timezones too
    utcList = []
    utcListCounter = {}
    
    
    for player in discord_members:
        if player.bot or player.nick is None:
            continue
        positionofstart = player.nick.find('UTC')
        if positionofstart == -1:
            continue
        timezone = float(player.nick[positionofstart+3:player.nick[positionofstart].find(']')].replace(',', '.'))
        if timezone is not None:
            utcListCounter[timezone] = utcListCounter.get(timezone, 0) + 1
            if timezone not in utcList:
                utcList.append(timezone)
                
    utcList.sort()
    # Create an embed message
    text = "UTC List:\n"
    
    for utctime in utcList:
        if utcListCounter[utctime] > 0:
            text += f"UTC {"{0}".format(str(round(utctime, 1) if utctime % 1 else int(utctime)))}: {utcListCounter[utctime]} members\n"

    await message.response.send_message(text)

class WTGuessrView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)  # 3 minutes timeout
        self.message = None
        self.owner = None
        self.currentImage = None
        self.currentAnswer = None
        self.score = 0
        self.round = 0
        self.started = False
        self.starttime = datetime.now()
    
    async def start(self):
        await self.next_round()

    async def next_round(self):
        if self.round >= 5:
            await self.message.edit(content=f"Game over! Your final score is {self.score}/5", view=None)
            await self.stop()
            return
        
        # Fetch a new image and answer
        self.currentImage, self.currentAnswer = None, None
        
        if self.currentImage is None or self.currentAnswer is None:
            await self.message.edit(content="Error fetching image. Please try again later.", view=None)
            await self.stop()
            return
        
        embed = discord.Embed(title=f"Warthunder Guessr - Round {self.round + 1}/5", description="Guess the location of the Warthunder screenshot!", color=0x00ff00)
        embed.set_image(url=self.currentImage)
        embed.set_footer(text="You have 3 minutes to guess the location!")
        
        await self.message.edit(content=None, embed=embed)
        self.round += 1

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.red, custom_id="guess_location")
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.owner:
            await interaction.response.send_message("Only the game host can use this button.", ephemeral=True)
            return
        
        super().stop()
        return


@client.tree.command(description="WarthunderGuessr!")
@app_commands.choices(difficulty=[
    app_commands.Choice(name='Easy', value=0),
    app_commands.Choice(name='Hard', value=1)
    ])
async def warthunderguessr(ctx: discord.Interaction, difficulty: app_commands.Choice[int] = 0):
    if not isDevBot:
        await ctx.response.send_message("This command is only available in the dev bot.", ephemeral=True)
        return
    await ctx.response.send_message("Starting WarthunderGuessr!", ephemeral=True)
    view = WTGuessrView()
    message = await ctx.channel.send("WarthunderGuessr started! You have 3 minutes to guess the location by using the buttons below!", view=view)
    view.message = message
    view.owner = ctx.user
    

# Checks if 6hours have passed since the start of the event, if so, stop the event.
@tasks.loop(minutes=1)
async def task_end_old_events():
    logging.info(f'Running "task_end_old_events", 1m has passed.')

    if client.persistent_views:
        for view in client.persistent_views:
            logging.info(view.hostdate)
            time_until_event = view.hostdate - datetime.now()
            logging.info(time_until_event)

            if time_until_event < -timedelta(hours=6):
                logging.info("Ended!")
                await view.stop()
                
            elif time_until_event < timedelta(seconds=0):
                logging.info("Event started!")
                if not(view.started):
                    view.started = True
                    await view.start()

    logging.info(f'Task "task_end_old_events" done')

@tasks.loop(hours=12)
async def task_check_join_date():
    guild = client.get_guild(TESTDISCORDGUILD)
    guildmembers = guild.members
    today = datetime.today()
    oneyearago = today
    oneyearago.replace(year=oneyearago.year-1)

    for guildmember in guildmembers:
        if guildmember.joined_at.timestamp()-oneyearago.timestamp() > 0:
            logging.info(f"{guildmember.name} is in here for a year")
        else:
            logging.info(f"{guildmember.name} is NOT in here for a year")

skipFirstUploadTaskRun = True
@tasks.loop(hours=48)
async def task_upload_last_log():
    global skipFirstUploadTaskRun
    if skipFirstUploadTaskRun == True:
        logging.info('Skipping first upload run...')
        skipFirstUploadTaskRun = False
        return
    logging.info(f'Running "task_upload_logs", 48h have passed.')
    global file_handler

    # stop logs
    logging.info("Stopping filelogs for upload...")
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            logger.removeHandler(handler)
            handler.close()

    file_handler = create_file_handler()
    logger.addHandler(file_handler)
    logging.info("Logging initialised!")
    logging.info(client.user.name)

    # handlers done
    RemoveOldLogs()

    log_file = log_files[-2]
    channel = client.get_channel(LOGGING_CHANNEL)
    logging.info('Attempting to send past log to discord')
    try:
        await channel.send(file=discord.File(os.path.join("logs", log_file)))
    except Exception as e:
        logging.warning(f"Failed to send current log: {e}")



@tasks.loop(hours=6)
async def task_write_squadron_highest_SQBrating():
    logging.info(f'Running "task_write_squadron_highest_SQBrating", 6h have passed.')

    squadronPlayers = await get_squadron_players()
    logging.info(f"Got squadron players: {squadronPlayers}")

    for _number_, personData in squadronPlayers.items():
        if int(personData[1]) == 0:
            continue
        message, squadronRating = await GetData(str(personData[0]), "HighestSquadronRating")
        if squadronRating == None or int(squadronRating) < int(personData[1]):
            await Writedata(personData[0], "HighestSquadronRating", personData[1])

    logging.info(f'Task "task_write_squadron_highest_SQBrating" done')

@client.event
async def on_ready():
    logging.info('Setup DB')
    await SetupDB(client)
    
    logging.info('Syncing...')
    if not isDevBot:
        client.tree.copy_global_to(guild=discord.Object(id=DISCORDGUILD))
        await client.tree.sync(guild=discord.Object(id=DISCORDGUILD))
        logging.info('MiRav done!')
    client.tree.copy_global_to(guild=discord.Object(id=TESTDISCORDGUILD))
    await client.tree.sync(guild=discord.Object(id=TESTDISCORDGUILD))

    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="MiRav Discord", url="https://youtu.be/0-cyS4inY_c", details_url="https://youtu.be/0-cyS4inY_c", state_url="https://youtu.be/0-cyS4inY_c"))
    logging.info(f'We have logged in as {client.user}')
    timeStarted = datetime.now()    

    logging.info('Attempting to load ongoing events...')
    # if there is currently no persistent views upon start, do this...
    logging.info(f"Persistent views: {client.persistent_views}")
    if len(client.persistent_views) == 0 and not isDevBot:
        # Check all events, if they are valid
        _, eventData = await GetFullUserData("OngoingEvents")
        if not (eventData == None):
            events = str(eventData).split(";")
            for event in events:
                # Get the time left untill event
                if event == "":
                    continue
                try:
                    logging.info(f"Searching for the channelID: \"{(event.split(":")[0]).split("-")[0]}\"")
                    channel = await client.fetch_channel((event.split(":")[0]).split("-")[0])

                    # Get the message
                    logging.info(f"Searching for messageID: \"{(event.split(":")[0]).split("-")[1]}\"")
                    message = await channel.fetch_message((event.split(":")[0]).split("-")[1])
                    
                    # Get embed
                    oldEmbed = message.embeds[0]
                    
                    # Get host date
                    logging.info(f"Finding host date...")
                    front = oldEmbed.description.lstrip().find('<')+3
                    back  = oldEmbed.description.lstrip().find('>')-2
                    logging.info(f"Found host timestamp at: ind(f):{front} | ind(b):{back} | Result: {int(oldEmbed.description.lstrip()[front:back])}")
                    hostDate = datetime.fromtimestamp(int(oldEmbed.description.lstrip()[front:back]))

                    # Get the Primary list back!
                    logging.info(f"Gathering old member list...")
                    primaryList = []
                    if oldEmbed.fields[0].value != "":
                        oldMainListNames = oldEmbed.fields[0].value.split('\n')
                        logging.info(f"Raw list main with size: {len(oldMainListNames)} | {oldMainListNames}")
                        if len(oldMainListNames) > 0:
                            for value in oldMainListNames:
                                logging.info(f"Processing main attendee: {value}")
                                if value == "":
                                    continue
                                split = (value.split('|')[1]).strip()
                                userID = split[2:len(split)-1]
                                attendee = await channel.guild.fetch_member(userID)
                                primaryList.append(attendee)

                    logging.info(f"Gathering old reserve member list...")
                    reserveList = []
                    try:
                        if oldEmbed.fields[1].value != "":
                            oldReserveListNames = oldEmbed.fields[1].value.split('\n')
                            logging.info("Raw list reserve: ", oldReserveListNames)
                            if len(oldReserveListNames) > 0:
                                for value in oldReserveListNames:
                                    logging.info(f"Processing reserve attendee: {value}")
                                    if value == "":
                                        continue
                                    split = (value.split('|')[1]).strip()
                                    userID = split[2:len(split)-1]
                                    attendee = await channel.guild.fetch_member(userID)
                                    reserveList.append(attendee)
                    except:
                        logging.warning(f"No reserve list detected or something went wrong... Treating as only main list...")
                        reserveList = None

                    # Get user
                    user = oldEmbed.author.name[10:].strip()
                    discordList = await get_discord_list()
                    found = False
                    logging.info(f"Searching for host of event: \"{oldEmbed.title}\"")
                    for discordUser in discordList:
                        if discordUser.nick == None:
                            continue
                        if user == (discordUser.nick[:discordUser.nick.find('[')].strip()):
                            user = discordUser
                            found = True
                            logging.info("User found!")
                            break
                    if not(found):
                        logging.warning("User not found...")
                        # Presume user got kicked and cancel event
                        continue
                    
                    # Find the max amount of people that can enter!
                    logging.info("Finding max people...")
                    maxAttendees = -1
                    oldAttendeeName = oldEmbed.fields[0].name.strip()
                    maxIndex = oldAttendeeName.find("max")
                    if maxIndex == -1:
                        logging.warning("Couldn't find max, or max is -1, infinite assumed...")
                        # max Attendees is already -1 thuss no need to change
                    else:
                        try:
                            maxAttendees = int(oldAttendeeName[maxIndex + 4:len(oldAttendeeName)-2])
                        except:
                            logging.warning("Something went from extracting an int from: ", oldAttendeeName[maxIndex + 4:len(oldAttendeeName)-2], " |  Will assume the max is infinite...")
                            maxAttendees = -1
                        logging.info("Max attendees = ", maxAttendees)
                        
                    
                    logging.info("Searching for if only squadron members are allowed...")
                    squadronMembersOnly = False
                    if oldEmbed.author.name[0] == "​":
                        # invisible character to notify if it's squadron members only
                        squadronMembersOnly = True

                    # Event can continue!
                    myView = EventView(oldEmbed, user, hostDate, squadronMembersOnly, maxAttendees, reserveList!=None, primaryList, reserveList)
                    myView.message = await message.edit( content=message.content, embed=oldEmbed, view=myView)
                    #await Writedata("OngoingEvents", f'{myView.message.channel.id}-{myView.message.id}', int(hostDate.timestamp()))
                    myView.id = datetime.today().timestamp()
                    myView.owner = user
                    client.add_view(view=myView, message_id=myView.message.id)
                    logging.info("Event done!")
                except:
                    logging.error("Something went wrong with loading event:", event, "This event won't be able to restart anymore... Deleting...")
                    await Removedatakey("OngoingEvents", event.split(":")[0])
                    logging.info("Deleted")
    logging.info('Done loading events!')

    channel = client.get_channel(LOGGING_CHANNEL)
    logging.info('Attempting to send previous log to discord')
    try:
        await channel.send(file=discord.File(os.path.join("logs", log_files[-2])))
    except Exception as e:
        logging.warning(f"Failed to send previous log: {e}")



    logging.info(f'Attempting to start tasks...')
    if not task_end_old_events.is_running():
        logging.info(f'Task "{(task_end_old_events.start()).get_name()}" is running...')

    if not task_upload_last_log.is_running():
        logging.info(f'Task "{(task_upload_last_log.start()).get_name()}" is running...')
          
    if not isDevBot:
        if not task_write_squadron_highest_SQBrating.is_running():
            logging.info(f'Task "{(task_write_squadron_highest_SQBrating.start()).get_name()}" is running...')
            
        if not periodic_update_check.is_running():
            logging.info(f'Task "{(periodic_update_check.start()).get_name()}" is running...')


client.tree.add_command(EventGroup(name="event", description="Manage events"))


async def main():
    for file in os.listdir("./extensions"):
        if file.endswith(".py"):
            await client.load_extension(f"extensions.{file[:-3]}")
    await client.start(TOKEN)

logging.info(f'Starting bot')
asyncio.run(main())