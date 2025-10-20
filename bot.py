# Configureable
import re
from asyncio.windows_events import NULL
from json import loads
from operator import truediv
from pathlib import Path
import string
from tkinter import CHAR
from traceback import print_tb

from discord.ext import tasks
import discord.ext
import discord.ext.commands

base_path = Path(__file__).parent
config = loads((base_path / "config.json").read_text())
token = loads((base_path / "token.json").read_text())

isDevBot = config["devMode"]
hostUser = token["user"]

if isDevBot:
    TOKEN = token["testtoken"]
else:
    TOKEN = token["token"]

DISCORDGUILD = config["discordGuild"]
TESTDISCORDGUILD = config["testDiscordGuild"]
NOTICELIST_CHANNEL = config["noticeListChannelId"]
SQUADRONMEMBERROLEID = config["squadronMemberRoleId"]

# Code

from pprint import pprint
import sys
sys.stdout.reconfigure(encoding='utf-8')
import discord 
from discord import Client, Embed, Interaction, app_commands
from discord.ext import commands
import requests
from datetime import datetime, timedelta

client = discord.Client(intents=discord.Intents.all())

client.tree = discord.app_commands.CommandTree(client)

# position 0 is name, 1 is SQB rating,
# 2 is activity, 3 is role, 4 is join date
async def get_squadron_players():
    # Making a GET request
    r = requests.get('https://warthunder.com/en/community/claninfo/Midnight%20Ravens')

    # check status code for response received
    # success code - 200
    
    # time to pretify
    contentReady = r.content.decode("utf-8").replace(' ', '').replace('\n', '')
    index = contentReady.find('<divclass="squadrons-members__table">')
    lastIndex = contentReady.find('<divclass="socialsocial--footer">')
    
    # find next <
    for counter in range(0,13):
        for i in range (index+2, lastIndex):
            index += 1
            if (contentReady[i] == '<'):
                break
    index += 1
    
    # if type = 0 then number, 1 is name, 2 is 
    isHTML = False
    backSlashCounter = 0
    type = 0
    currentPersonNumber = 0
    currentWord = ' '
    personList = {}
    for i in range(index, lastIndex):
        if (contentReady[i] == '<'):
            isHTML = True
        if (not isHTML):
            currentWord += contentReady[i]
        if (contentReady[i] == '>'):
            isHTML = False
            if (currentWord[len(currentWord)-1] != ' '):
                if (type == 6):
                    type = 0
                    currentPersonNumber += 1
                elif (type != 0):
                    if currentPersonNumber not in personList:
                        personList[currentPersonNumber] = {}  # Initialize as an empty dictionary

                    personList[currentPersonNumber][type-1] = currentWord[1:].replace('@psn', '').replace('@live', '')
                    currentWord = ' '
                    type += 1
                else:
                    type += 1
                    currentWord = ' '
    return personList

FIRST_DEADLINE = config["firstDeadline"]
FIRST_ACTIVITY_REQUIREMENT = config["firstActivityRequirement"]
SECOND_DEADLINE = config["secondDeadline"]
SECOND_ACTIVITY_REQUIREMENT = config["secondActivityRequirement"]
EXEMPTION_SQ_RATING = config["exemptionSQRating"]

SQUADRONSTAFFID = config["squadronStaffId"]
COMMUNITYHOST = config["communityHostRoleId"]
DBCHANNELID = config["DBChannelId"]

timeStarted = datetime.now()


async def get_squadron_kickable(personList):
    noticeList = await get_notice_list()
    
    # Convert string to datetime object
    date_format = "%d.%m.%Y"

    # Get today's date
    today = datetime.today()

    returnList = {}
    for personNumber, personData in personList.items():
        given_date = datetime.strptime(personData[4], date_format)
        found = False
        for noticePerson in noticeList:
            if noticePerson[0] == personData[0].lower().replace(' ', ''):
                # we found a match! Check if type
                if noticePerson[1] == 1:
                    personData[5] = 'Marked for inactivity & notice expired. Verify notice list.'
                    break
                else:
                    found = True
                    break
        if found:
            continue
        if (int(personData[1]) < EXEMPTION_SQ_RATING and int(personData[2]) < FIRST_ACTIVITY_REQUIREMENT and -(given_date.date() - today.date()).days >= FIRST_DEADLINE ) or (int(personData[1]) < EXEMPTION_SQ_RATING and int(personData[2]) < SECOND_ACTIVITY_REQUIREMENT and -(given_date.date() - today.date()).days >= SECOND_DEADLINE ) :
            returnList[len(returnList)] = personData
    

    return returnList

async def get_discord_list():
    if isDevBot:
        return (client.get_guild(TESTDISCORDGUILD)).members
    guild = client.get_guild(DISCORDGUILD)
    return guild.members
  

def FindFirstIndex(string, findChar):
    for charNumber_, char in enumerate(string):
        if char == findChar:
            return charNumber_
    return -1

# Will return a list of users that are on notice with the pattern [USERNAME, Condition] where if condition, 0 = all normal, 1 = check notes, 2 = Special case
async def get_notice_list():
    if isDevBot:
        return list()
    messages = [message async for message in client.get_channel(NOTICELIST_CHANNEL).history(limit=123)]
    returnList = list()
    for message in messages:
        messageSplit = message.content.splitlines()
        name = ''
        for text in messageSplit[0].split()[1:]:
            name += text + ' '
        today = round(datetime.now().timestamp()-1)
        # no dates
        if FindFirstIndex(messageSplit[2], '<') == -1:
            # Alert to check list
            returnList.append([name.strip().replace(' ', '').lower(), 2])
        # Two dates
        elif messageSplit[2].count('<') == 2:
            index = FindFirstIndex(messageSplit[2], '<') +3
            secondIndex = FindFirstIndex(messageSplit[2], '>')-2
            # if it is in the future, skip and don't alert as he's not needed yet
            if today < int(messageSplit[2][index:secondIndex]):
                continue
            
            index = FindFirstIndex(messageSplit[2][secondIndex:], '<') + secondIndex+3
            secondIndex = FindFirstIndex(messageSplit[2][index:], '>') + index-2
            # if end date is in the past, skip
            if today > int(messageSplit[2][index:secondIndex]):
                returnList.append([name.strip().replace(' ', '').lower(), 1])
                continue
            returnList.append([name.strip().replace(' ', '').lower(), 0])
        # One dates
        elif messageSplit[2].count('<') == 1:
            index = FindFirstIndex(messageSplit[2], '<')+3
            secondIndex = FindFirstIndex(messageSplit[2], '>')-2
            # if end date is in the future, add
            if today < int(messageSplit[2][index:secondIndex]):
                returnList.append([name.strip().replace(' ', '').lower(), 0])
            # if end date is in the the past then alert he's still on the list
            else:
                returnList.append([name.strip().replace(' ', '').lower(), 1])
        else:
            # Alert someone is on the list
            returnList.append([name.strip().replace(' ', '').lower(), 1])

    return returnList
    
async def get_exemption_list():
    _, listExemptions = await getData("Bot", "ExemptionListIGN")
    
    if listExemptions == None:
        listExemptions = ""
        
    return listExemptions.split("§§")

@app_commands.guild_only()
class ExemptionListGroup(app_commands.Group):
    @app_commands.command(description="Exemption list")
    @commands.has_role(SQUADRONSTAFFID)
    async def list(self, ctx : discord.Interaction):
        if ((ctx.user.get_role(SQUADRONSTAFFID) == None) and not(ctx.user.id == 259644962876948480)):
            await ctx.response.send_message('You do not have the requirements for this command.', ephemeral=True)
            return
        listExemptions = await get_exemption_list()
        
        endPrint = "The current people whom are exempt from kicks:\n"
        for exemption in listExemptions:
            endPrint += exemption + "\n"
        await ctx.response.send_message(endPrint)

    @commands.has_role(SQUADRONSTAFFID)
    @app_commands.command(description="Exemption list add")
    async def add(self, ctx : discord.Interaction, ingameusername : str):
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
        await writedata("Bot", "ExemptionListIGN", endPrint)
        await ctx.response.send_message(f'"{ingameusername.strip()}" has been added to the exemption list.', ephemeral=True)
            
    
    @app_commands.command(description="Exemption list remove")
    @commands.has_role(SQUADRONSTAFFID)
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

        await writedata("Bot", "ExemptionListIGN", finalWritePart[2:])
            
        await ctx.response.send_message(f'Removed "{ingameusername}" from the permanent exemption list', ephemeral=True)


JOIN_DEADLINE = config["joinDeadline"]
@client.tree.command(description="A list of players who need to be kicked from the ingame squadron")
@app_commands.choices(type=[
    app_commands.Choice(name='Both', value=0),
    app_commands.Choice(name='Inactivity', value=1),
    app_commands.Choice(name='Not in discord', value=2)
])
@commands.has_role(SQUADRONSTAFFID)
async def kicklist(ctx :  discord.Interaction, type: app_commands.Choice[int]):
    if ((ctx.user.get_role(SQUADRONSTAFFID) == None) and not(ctx.user.id == 259644962876948480)):
        await ctx.response.send_message('You do not have the requirements for this command.', ephemeral=True)
        return
    await ctx.response.send_message('Gathering the list for you!', ephemeral=True)
    
    today = datetime.today()
    exemptionKickList = await get_exemption_list()
    squadronList = await get_squadron_players()
    kickAble = await get_squadron_kickable(squadronList)
    for numbera, squadronMember in kickAble.items():
        if squadronMember.get(5, NULL) == NULL:
            squadronMember[5] = 'Inactivity'
    
    discordMemberList = await get_discord_list()

    filteredMemberList = {}
    for member in discordMemberList: 
        if (member.nick != None):
            filteredMemberList[len(filteredMemberList)] = member.nick[:member.nick.find('[')].strip()
    notInDiscordList = {}
    # compare each member in discord to the squadron
    for numberb, squadronMember in squadronList.items():
        found = False
        for numbera, member in filteredMemberList.items():
            #compare nickname
            if member.replace(' ', '').lower() == squadronMember[0].lower():
                found = True
                #break list to skip to next user
                break
        if (not found and (today - datetime.strptime(squadronMember[4], "%d.%m.%Y")).days > JOIN_DEADLINE):
            squadronMember[5] = 'Not in discord'
            notInDiscordList[len(notInDiscordList)] = squadronMember

    secondfinalList = notInDiscordList.copy()
    for numbera, squadronMember in kickAble.items():
        found = False
        for numberb, member in notInDiscordList.items():
            #compare nickname
            if member[0].lower() == squadronMember[0].lower():
                found = True
                #break list to skip to next user
                break
        if not found:
            secondfinalList[len(secondfinalList)] = squadronMember
    
    finalList = {}
    for numbera, squadronMember in secondfinalList.items():
        if not (squadronMember[0].lower() in exemptionKickList):
            finalList[len(finalList)] = squadronMember

            
    # Convert date strings to datetime objects for sorting
    for key, value in finalList.items():
        value[4] = datetime.strptime(value[4], "%d.%m.%Y")  # Convert date to datetime
    # Sort finalList based on (date, name)
    sortedItems = sorted(finalList.items(), key=lambda x: x[1][0].lower())

    finalSortedList = {i + 1: item[1] for i, item in enumerate(sortedItems)}
    #print(sortedItems)
    #print(finalSortedList)
    #embed = discord.Embed(title=f"Member number 1", description=f"**{finalSortedList[1][0]}**", color=discord.Color.blue())
    #await message.channel.send(embed=embed, view=MemberView(finalSortedList))

    # change those in notice list to "Notice submitted"        
    printString = f'```ansi\n'
    amountToKick = "ERROR N/A"
    if (type.value == 0):
        amountToKick = len(finalSortedList)
    else:
        NIDToKick = 0
        INACToKick = 0
        for number, squadronMember in finalSortedList.items():
            if squadronMember[5] == 'Not in discord':
                NIDToKick += 1
            elif squadronMember[5] == 'Inactivity':
                INACToKick += 1
        if type.value == 1: #Inactivity
            amountToKick = INACToKick
        elif type.value == 2: #Not in discord
            amountToKick = NIDToKick
        
    printString += f'Users to kick: \u001b[1;31m{amountToKick}\u001b[0m\n'
    printString += f'  Username             | Date joined | Reason\n'
    for number, squadronMember in finalSortedList.items():
        if ((type.value == 1 and squadronMember[5] == 'Not in discord') or (type.value == 2 and squadronMember[5] == 'Inactivity')):
            continue
        
        if squadronMember[5] == 'Not in discord':
            printString += f'- \u001b[33m{squadronMember[0].ljust(20)}\u001b[0m |  \u001b[34m{squadronMember[4].strftime("%d.%m.%Y")}\u001b[0m | \u001b[33m{squadronMember.get(5, "N/A")}\u001b[0m\n'
        elif squadronMember[5] == 'Inactivity':
            printString += f'- \u001b[36m{squadronMember[0].ljust(20)}\u001b[0m |  \u001b[34m{squadronMember[4].strftime("%d.%m.%Y")}\u001b[0m | \u001b[36m{squadronMember.get(5, "N/A")}\u001b[0m\n'
        else:
            printString += f'- {squadronMember[0].ljust(20)} |  \u001b[34m{squadronMember[4].strftime("%d.%m.%Y")}\u001b[0m | {squadronMember.get(5, "N/A")}\n'
        if (len(printString) > 1900):
            printString += '```'
            await ctx.channel.send(printString)
            printString = '```ansi\n'
    printString += '```'
    if (len(printString) > 15):
        await ctx.channel.send(printString)
    
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
    deltatime = datetime.now() - timeStarted
    await ctx.response.send_message(f'I\'ve been online since <t:{timeStarted.timestamp():.0f}:f>, which is: \n'+
                                    f'{deltatime.days} day(s) and\n' +
                                    f'{deltatime.seconds:.0f} seconds aka\n' +
                                    f'{deltatime.seconds/60:.1f} minutes aka\n' +
                                    f'{deltatime.seconds/60/60:.2f} hours ago\n' +
                                    '')

@client.tree.command(description="Pong!")
async def ping(ctx:  discord.Interaction):
    await ctx.response.send_message(f'{hostUser}: Pong! {client.latency:.4f}s')

    

@client.tree.command(description="Verify the users within the discord/squadron.")
async def verifymembers(ctx:  discord.Interaction):
    if ((ctx.user.get_role(SQUADRONSTAFFID) == None) and not(ctx.user.id == 259644962876948480)):
        await ctx.response.send_message('You do not have the requirements for this command.', ephemeral=True)
        return
    found = False
    usersChecked = 0
    usersAdded = 0
    usersRemoved = 0
    totalSquadronMembers = 0
    usersNoUTC = 0
    totalAllies = 0
    newAllies = 0
    discordMembers = await get_discord_list()
    squadronMembers = await get_squadron_players()
    allyRole = discord.utils.get(client.get_guild(DISCORDGUILD).roles, id=1346451233543557121)
    role = discord.utils.get(client.get_guild(DISCORDGUILD).roles, id=1338270607220932639)
    await ctx.response.send_message('Gathered all data... Executing order 66...', ephemeral=True)
    for discordMember in discordMembers:
        if discordMember.bot:
            continue
        found = False
        usersChecked += 1
        #if (discordMember.nick != None):
        #    print(discordMember.nick[:discordMember.nick.find('[')].replace(' ', '').strip().lower())
        if (discordMember.nick != None and discordMember.nick.strip()[0] == '['):
            if not(allyRole in discordMember.roles):
                await discordMember.add_roles(allyRole)
                newAllies += 1
            totalAllies += 1
            continue
        for counterB, squadronMember in squadronMembers.items():
            if (discordMember.nick != None):
                if discordMember.nick[:discordMember.nick.find('[')].replace(' ', '').strip().lower() == squadronMember[0].strip().lower():
                    found = True
                    break
        
        if found:
            totalSquadronMembers += 1
        if found and not(role in discordMember.roles):
            await discordMember.add_roles(role)
            usersAdded += 1
        elif not found and (role in discordMember.roles):
            await discordMember.remove_roles(role)
            usersRemoved += 1
        elif not found and (discordMember.nick == None or discordMember.nick.find('[') == -1):
            usersNoUTC += 1

    await ctx.channel.send(
        f'All done!\nTotal checked: {usersChecked}\n'+
        f'Total squadron members: {totalSquadronMembers}\n'+
        f'New users: {usersAdded}\n'+
        f'Users removed: {usersRemoved}\n'+
        f'Users with no tags []: {usersNoUTC}\n'+
        f'Total allies: {totalAllies}\n'+
        f'New allies: {newAllies}')

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
            printedListReserve += f'{str(user.nick).split('[')[0]} | <@{user.id}>\n'

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
            print("⚠️ Something went wrong when editing message to an event")
        finally:
            try:
                super().stop()
            except:
                print("⚠️ Something went wrong when deleting an event")
            finally:
                await removedatakey("OngoingEvents", f"{self.message.channel.id}-{self.message.id}")

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
        if not(isDevBot) and ((ctx.user.get_role(SQUADRONSTAFFID) == None and ctx.user.get_role(COMMUNITYHOST) == None) and not(ctx.user.id == 259644962876948480 or ctx.user.id == 490216540331966485)):
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
        newHour = hour-int(time)+2
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
        await writedata("OngoingEvents", f'{myView.message.channel.id}-{myView.message.id}', int(hostDate.timestamp()))
        myView.id = today.timestamp()
        myView.owner = ctx.user
        client.add_view(view=myView, message_id=myView.message.id)
        

    @app_commands.command(description="A command to host SQB at a specified BR and hour")
    async def stop(self, ctx : discord.Interaction, messageid : str = None):
        if not(isDevBot) and ((ctx.user.get_role(SQUADRONSTAFFID) == None and ctx.user.get_role(COMMUNITYHOST) == None) and not(ctx.user.id == 259644962876948480 or ctx.user.id == 490216540331966485)):
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
        if not(isDevBot) and ((ctx.user.get_role(SQUADRONSTAFFID) == None and ctx.user.get_role(COMMUNITYHOST) == None) and not(ctx.user.id == 259644962876948480 or ctx.user.id == 490216540331966485)):
            await ctx.response.send_message('⚠️ You do not have the requirements for this command.', ephemeral=True)
            return
        viewAmount = 0
        for view in client.persistent_views:
            viewAmount += 1
        if viewAmount == 0:
            await ctx.response.send_message("Not detecting any ongoing events...", ephemeral=True)
            return
        
        if (hours < 0 or minutes < 0) and not isDevBot:
            await ctx.response.send_message("You can't delay the event by negative amount, edit the event instead if this was on purpose.", ephemeral=True)
            return

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
        if not(isDevBot) and ((ctx.user.get_role(SQUADRONSTAFFID) == None and ctx.user.get_role(COMMUNITYHOST) == None) and not(ctx.user.id == 259644962876948480 or ctx.user.id == 490216540331966485)):
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
        newHour = hour-int(time)+2
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
        await writedata("OngoingEvents", f'{myView.message.channel.id}-{myView.message.id}', int(hostDate.timestamp()))
        myView.id = today.timestamp()
        myView.owner = ctx.user
        client.add_view(view=myView, message_id=myView.message.id)


@client.tree.command(description="Testing")
async def test(ctx : discord.Interaction):
    if not isDevBot:
        await ctx.response.send_message(f'This is a test command for testing!')
        return
    print("Test comamnd called")
    # devbot test code
    if not client.persistent_views:
        print("No persistent views registered.")
    else:
        print("Persistent Views:")
        for view in client.persistent_views:
            print(f"- {view.__class__.__name__} | {view.id} (timeout={view.timeout}, children={len(view.children)})")
            for child in view.children:
                print(f"- {child.__class__.__name__} | {child}")
            print(view.primary)
            

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
            print(f"{guildmember.name} is in here for a year")
        else:
            print(f"{guildmember.name} is NOT in here for a year")

async def getFullUserData(userkey:str):
    dbChannel = client.get_channel(DBCHANNELID)
    #find first
    async for message in dbChannel.history(limit= None):
        founduserkey, data = message.content.split("|")
        if founduserkey == userkey:
            return message, str(data)
    return None, None

async def getAllDataFromOneKey(datakey:str):
    dbChannel = client.get_channel(DBCHANNELID)
    #find first
    returnList = []
    async for message in dbChannel.history(limit= None):
        DBuserkey, userData = message.content.split("|")
        userData += " "
        # if userdata is only one ; then check if it's correct and return or continue
        if userData.count(';') == 1:
            if userData.split(":")[0] in datakey:
                returnList.append([DBuserkey, userData.split(":")[1]])
            continue
        # if we have more than 1 then:
        async for data in (userData.split(";")):
            if data.split(":")[0] in datakey:
                returnList.append([DBuserkey, userData.split(":")[1]])
    return returnList

async def getData(userkey:str, datakey:str):
    dbChannel = client.get_channel(DBCHANNELID)
    #find first
    async for message in dbChannel.history(limit= None):
        DBuserkey, userData = message.content.split("|")
        if DBuserkey == userkey:
            userData += " "
            # if userdata is only one ; then check if it's correct and return or continue
            if userData.count(';') == 1:
                if userData.split(":")[0] == datakey:
                    return message, str((userData)[:len(userData)-2].split(":")[1])
                continue
            # if we have more than 1 then:
            async for data in (userData.split(";")):
                if data.split(":")[0] == datakey:
                    return message, str(data.split(":")[1])
    return None, None
    
async def removedatakey(userkey:str, datakey:str):
    dbChannel = client.get_channel(DBCHANNELID)
    # find first
    message, fullData = await getFullUserData(userkey)
    if fullData is None:
        # didn't find userkey
        return
    else:
        # found a key
        splitdata = fullData.split(";")
        #find correct datakey
        for singulardata in splitdata:
            if singulardata.split(":")[0] == datakey:
                splitdata.remove(singulardata)
                strData = ""
                for dataToAdd in splitdata:
                    if not(dataToAdd == ""):
                        strData += dataToAdd + ";" 
                await message.edit(content=f"{userkey}|{strData}")
    
async def writedata(userkey:str, datakey:str, data:str):
    dbChannel = client.get_channel(DBCHANNELID)
    # find first
    message, fullData = await getFullUserData(userkey)
    if fullData is None:
        # didn't find userkey
        await dbChannel.send(f"{userkey}|{datakey}:{data};")
    else:
        # didn't found a key
        splitdata = fullData.split(";")
        #find correct datakey
        for singulardata in splitdata:
            if singulardata.split(":")[0] == datakey:
                splitdata.remove(singulardata)
                strData = ""
                for dataToAdd in splitdata:
                    if not(dataToAdd == ""):
                        strData += dataToAdd + ";" 
                await message.edit(content=f"{userkey}|{strData}{datakey}:{data};")
                return
        # if didn't find the correct datakey
        await message.edit(content=f"{userkey}|{fullData}{datakey}:{data};")
 
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

# Checks if 6hours have passed since the start of the event, if so, stop the event.
@tasks.loop(minutes=1)
async def task_end_old_events():
    print(f'{datetime.now()} | Running "task_end_old_events", 1m has passed.')

    if client.persistent_views:
        for view in client.persistent_views:
            print(view.hostdate)
            time_until_event = view.hostdate - datetime.now()
            print(time_until_event)

            if time_until_event < -timedelta(hours=6):
                print("Ended!")
                await view.stop()
                
            elif time_until_event < timedelta(seconds=0):
                print("Event started!")
                if not(view.started):
                    view.started = True
                    await view.start()

    print(f'{datetime.now()} | Task "task_end_old_events" done')

@tasks.loop(hours=12)
async def task_check_join_date():
    guild = client.get_guild(TESTDISCORDGUILD)
    guildmembers = guild.members
    today = datetime.today()
    oneyearago = today
    oneyearago.replace(year=oneyearago.year-1)

    for guildmember in guildmembers:
        if guildmember.joined_at.timestamp()-oneyearago.timestamp() > 0:
            print(f"{guildmember.name} is in here for a year")
        else:
            print(f"{guildmember.name} is NOT in here for a year")

@tasks.loop(hours=6)
async def task_write_squadron_highest_SQBrating():
    print(f'{datetime.now()} | Running "task_write_squadron_highest_SQBrating", 6h have passed.')

    squadronPlayers = await get_squadron_players()

    for _number_, personData in squadronPlayers.items():
        if int(personData[1]) == 0:
            continue
        message, squadronRating = await getData(str(personData[0]), "HighestSquadronRating")
        if squadronRating == None or int(squadronRating) < int(personData[1]):
            await writedata(personData[0], "HighestSquadronRating", personData[1])

    print(f'{datetime.now()} | Task "task_write_squadron_highest_SQBrating" done')

@client.event
async def on_ready():
    print('Syncing...')
    if not isDevBot:
        client.tree.copy_global_to(guild=discord.Object(id=DISCORDGUILD))
        await client.tree.sync(guild=discord.Object(id=DISCORDGUILD))
        print('MiRav done!')
    client.tree.copy_global_to(guild=discord.Object(id=TESTDISCORDGUILD))
    await client.tree.sync(guild=discord.Object(id=TESTDISCORDGUILD))

    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="MiRav Discord", url="https://youtu.be/0-cyS4inY_c", details_url="https://youtu.be/0-cyS4inY_c", state_url="https://youtu.be/0-cyS4inY_c"))
    print(f'We have logged in as {client.user}')
    timeStarted = datetime.now()    

    print('Attempting to load ongoing events...')




    # if there is currently no persistent views upon start, do this...
    print(client.persistent_views)
    if len(client.persistent_views) == 0:
        # Check all events, if they are valid
        _, eventData = await getFullUserData("OngoingEvents")
        if not (eventData == None):
            events = str(eventData).split(";")
            eventsPassedString = ""
            for event in events:
                # Get the time left untill event
                if event == "":
                    continue
                try:
                    print(f"Searching for the channelID: \"{(event.split(":")[0]).split("-")[0]}\"")
                    channel = await client.fetch_channel((event.split(":")[0]).split("-")[0])

                    # Get the message
                    print(f"Searching for messageID: \"{(event.split(":")[0]).split("-")[1]}\"")
                    message = await channel.fetch_message((event.split(":")[0]).split("-")[1])
                    
                    # Get embed
                    oldEmbed = message.embeds[0]
                    
                    # Get host date
                    print(f"Finding host date...")
                    front = oldEmbed.description.lstrip().find('<')+3
                    back  = oldEmbed.description.lstrip().find('>')-2
                    print(f"Found host timestamp at: ind(f):{front} | ind(b):{back} | Result: {int(oldEmbed.description.lstrip()[front:back])}")
                    hostDate = datetime.fromtimestamp(int(oldEmbed.description.lstrip()[front:back]))

                    # Get the Primary list back!
                    print(f"Gathering old member list...")
                    primaryList = []
                    if oldEmbed.fields[0].value != "":
                        oldMainListNames = oldEmbed.fields[0].value.split('\n')
                        print(f"Raw list main with size: {len(oldMainListNames)} | {oldMainListNames}")
                        if len(oldMainListNames) > 0:
                            for value in oldMainListNames:
                                print(f"Processing main attendee: {value}")
                                if value == "":
                                    continue
                                split = (value.split('|')[1]).strip()
                                userID = split[2:len(split)-1]
                                attendee = await channel.guild.fetch_member(userID)
                                primaryList.append(attendee)

                    print(f"Gathering old reserve member list...")
                    reserveList = []
                    try:
                        if oldEmbed.fields[1].value != "":
                            oldReserveListNames = oldEmbed.fields[1].value.split('\n')
                            print("Raw list reserve: ", oldReserveListNames)
                            if len(oldReserveListNames) > 0:
                                for value in oldReserveListNames:
                                    print(f"Processing reserve attendee: {value}")
                                    if value == "":
                                        continue
                                    split = (value.split('|')[1]).strip()
                                    userID = split[2:len(split)-1]
                                    attendee = await channel.guild.fetch_member(userID)
                                    reserveList.append(attendee)
                    except:
                        print(f"No reserve list detected or something went wrong... Treating as only main list...")
                        reserveList = None

                    # Get user
                    user = oldEmbed.author.name[10:].strip()
                    discordList = await get_discord_list()
                    found = False
                    print(f"Searching for host of event: \"{oldEmbed.title}\"")
                    for discordUser in discordList:
                        if discordUser.nick == None:
                            continue
                        if user == (discordUser.nick[:discordUser.nick.find('[')].strip()):
                            user = discordUser
                            found = True
                            print("User found!")
                            break
                    if not(found):
                        print("User not found...")
                        # Presume user got kicked and cancel event
                        continue
                    
                    # Find the max amount of people that can enter!
                    print("Finding max people...")
                    maxAttendees = -1
                    oldAttendeeName = oldEmbed.fields[0].name.strip()
                    maxIndex = oldAttendeeName.find("max")
                    if maxIndex == -1:
                        print("Couldn't find max, infinite assumed...")
                        # max Attendees is already -1 thuss no need to change
                    else:
                        try:
                            maxAttendees = int(oldAttendeeName[maxIndex + 4:len(oldAttendeeName)-2])
                        except:
                            print("Something went from extracting an int from: ", oldAttendeeName[maxIndex + 4:len(oldAttendeeName)-2], " |  Will assume the max is infinite...")
                            maxAttendees = -1
                        print("Max attendees = ", maxAttendees)
                        
                    
                    print("Searching for if only squadron members are allowed...")
                    squadronMembersOnly = False
                    if oldEmbed.author.name[0] == "​":
                        # invisible character to notify if it's squadron members only
                        squadronMembersOnly = True

                    # Event can continue!
                    myView = EventView(oldEmbed, user, hostDate, squadronMembersOnly, maxAttendees, reserveList!=None, primaryList, reserveList)
                    myView.message = await message.edit( content=message.content, embed=oldEmbed, view=myView)
                    #await writedata("OngoingEvents", f'{myView.message.channel.id}-{myView.message.id}', int(hostDate.timestamp()))
                    myView.id = datetime.today().timestamp()
                    myView.owner = user
                    client.add_view(view=myView, message_id=myView.message.id)
                    print("Event done!")
                except:
                    print("Error, something went wrong with loading event:", event, "This event won't be able to restart anymore... Deleting...")
                    await removedatakey("OngoingEvents", event.split(":")[0])
                    print("Deleted")


    print('Done loading! Starting tasks\n\n')
    if not task_end_old_events.is_running():
        print(f'Task "{(task_end_old_events.start()).get_name()}" is running...')
          
    if not isDevBot:
        if not task_write_squadron_highest_SQBrating.is_running():
            print(f'Task "{(task_write_squadron_highest_SQBrating.start()).get_name()}" is running...')


client.tree.add_command(EventGroup(name="event", description="Manage events"))
client.tree.add_command(ExemptionListGroup(name="exemptions", description="Exemptions list"))

print(f'Starting')
client.run(TOKEN)