import logging
from pathlib import Path
logging.getLogger(__name__)
logging.info(f'Importing {Path(__file__).name}')

from config_loader import config, isDevBot

import discord
from discord import app_commands
from discord.ext import commands

from datetime import datetime, timedelta
from asyncio.windows_events import NULL

SQUADRONMEMBERROLEID = config["squadronMemberRoleId"]
FIRST_DEADLINE = config["firstDeadline"]
FIRST_ACTIVITY_REQUIREMENT = config["firstActivityRequirement"]
SECOND_DEADLINE = config["secondDeadline"]
SECOND_ACTIVITY_REQUIREMENT = config["secondActivityRequirement"]
EXEMPTION_SQ_RATING = config["exemptionSQRating"]

SQUADRONSTAFFID = config["squadronStaffId"]

if isDevBot:
    SQUADRONSTAFFID = 1306031448209363054
COMMUNITYHOST = config["communityHostRoleId"]
DBCHANNELID = config["DBChannelId"]
JOIN_DEADLINE = config["joinDeadline"]

# import all needed helper functions
from helperFunctions.data_helpers import get_squadron_kickable, get_squadron_players, get_discord_list, get_exemption_list
from helperFunctions.db import GetFullUserData


async def GetKicklistVariantBoth(bot, today, exemptionKickList, squadronList):
    logging.info('Gathering kickable squadron player list')
    kickAble = await get_squadron_kickable(bot, squadronList)
    logging.info('Marking inactivity reasons...')
    for numbera, squadronMember in kickAble.items():
        if squadronMember.get(5, NULL) == NULL:
            squadronMember[5] = 'Inactivity'

    logging.info('Gathering discord member list')
    discordMemberList = await get_discord_list(bot)
    
    logging.info('Gathered all data... Processing kicklist...')
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
        squadronMember[5] = 'Inactivity'
        if (not found and (today - datetime.strptime(squadronMember[4], "%d.%m.%Y")).days > JOIN_DEADLINE):
            squadronMember[5] = 'Not in discord'
            notInDiscordList[len(notInDiscordList)] = squadronMember
            logging.debug(f'Marked {squadronMember[0]} as not in discord.')

    logging.info('Comparing not in discord list to kickable list...')
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
    
    logging.info('Filtering final kicklist based on exemptions and squadron points...')
    finalList = {}
    for numbera, squadronMember in secondfinalList.items():
        logging.info(f'Checking exemption for {squadronMember[0]}')
        if not (squadronMember[0].lower() in exemptionKickList):
            logging.info(f'{squadronMember[0]} is not exempt. Type: {squadronMember[5]}')
            if squadronMember[5] == 'Inactivity':
                logging.info("Checking sqb points for possible for " + squadronMember[0])
                # now one last check if he has points
                message, data = await GetFullUserData(squadronMember[0])
                # if they don't have any userdata, add them
                if data == None:
                    finalList[len(finalList)] = squadronMember #
                    logging.info("Adding " + squadronMember[0] + " to kick list due to no squadron points.")
                    continue

                hasPointsThisOrLastSeason = False
                # check if they have previous season points...
                if data.find("PreviousSeasonHighestSquadronRating") != -1:
                    logging.info("PreviousSeasonHighestSquadronRating: " + data[data.find("PreviousSeasonHighestSquadronRating"):].split(":")[1].split(";")[0])
                    if data[data.find("PreviousSeasonHighestSquadronRating"):].split(":")[1][0] != "0":
                        hasPointsThisOrLastSeason = True
                # check if they have current season points
                if data.find("HighestSquadronRating") != -1:
                    logging.info("HighestSquadronRating: " + data[data.find("HighestSquadronRating"):].split(":")[1].split(";")[0])
                    if data[data.find("HighestSquadronRating"):].split(":")[1][0] != "0":
                        hasPointsThisOrLastSeason = True

                # if they have no points in this or last season, add them to the kick list
                if not hasPointsThisOrLastSeason:
                    finalList[len(finalList)] = squadronMember #
                    logging.info("Adding " + squadronMember[0] + " to kick list due to no squadron points.")
                else:
                    # they have points!
                    logging.info(squadronMember[0] + " has points.")
            else:
                # Not in Discord or other reasons:
                finalList[len(finalList)] = squadronMember #

    logging.info('Sorting final kicklist...')        
    # Convert date strings to datetime objects for sorting
    for key, value in finalList.items():
        value[4] = datetime.strptime(value[4], "%d.%m.%Y")  # Convert date to datetime
    # Sort finalList based on (date, name)
    sortedItems = sorted(finalList.items(), key=lambda x: x[1][0].lower())
    logging.debug(sortedItems)

    finalSortedList = {i + 1: item[1] for i, item in enumerate(sortedItems)}
    logging.debug(finalSortedList)
    return finalSortedList

async def GetKicklistVariantDidntPlayLastSeason(exemptionKickList, squadronList):
    logging.info("Checking who should be exempt from kicking")
    # Remove exemptions from the list
    peopleToCheck = dict()
    logging.debug(squadronList)
    logging.debug(exemptionKickList)
    for _, member in squadronList.items():
        logging.debug(member)
        if not (member[0].lower() in exemptionKickList):
            logging.info(f"Adding, {member[0]}")
            indx = len(peopleToCheck)
            peopleToCheck[indx] = member
            peopleToCheck[indx][5] = "Didn't play last season"
            peopleToCheck[indx][4] = datetime.strptime(member[4], "%d.%m.%Y")
    
    logging.info("Making the final list!")
    finalList = dict()
    # Now check and add to a final list
    for _, member in peopleToCheck.items():
        member[0]
        hasPointsThisOrLastSeason = False
        message, data = await GetFullUserData(member[0])
        # if they don't have any userdata, add them
        if data == None:
            finalList[len(finalList)] = member #
            logging.info("Adding " + member[0] + " to kick list due to no squadron points.")
            continue

        # check if they have previous season points...
        if data.find("PreviousSeasonHighestSquadronRating") != -1:
            logging.info("PreviousSeasonHighestSquadronRating: " + data[data.find("PreviousSeasonHighestSquadronRating"):].split(":")[1].split(";")[0])
            if data[data.find("PreviousSeasonHighestSquadronRating"):].split(":")[1][0] != "0":
                hasPointsThisOrLastSeason = True
        # check if they have current season points
        if data.find("HighestSquadronRating") != -1:
            logging.info("HighestSquadronRating: " + data[data.find("HighestSquadronRating"):].split(":")[1].split(";")[0])
            if data[data.find("HighestSquadronRating"):].split(":")[1][0] != "0":
                hasPointsThisOrLastSeason = True

        if not hasPointsThisOrLastSeason:
            finalList[len(finalList)] = member #
            logging.info("Adding " + member[0] + " to kick list due to no squadron points.")
        else:
            # they have points!
            logging.info(member[0] + " has points.")

    logging.info("Done!")
    return finalList


async def setup(bot : commands.Bot):
    @bot.tree.command(description="A list of players who need to be kicked from the ingame squadron")
    @app_commands.choices(type=[
        app_commands.Choice(name='Both', value=0),
        app_commands.Choice(name='Inactivity', value=1),
        app_commands.Choice(name='Not in discord', value=2),
        app_commands.Choice(name='Didn\'t play last season', value=3)
    ])
    async def kicklist(ctx :  discord.Interaction, type: app_commands.Choice[int]):
        logging.info('kicklist called')
        if ((ctx.user.get_role(SQUADRONSTAFFID) == None) and not(ctx.user.id == 259644962876948480)):
            await ctx.response.send_message('You do not have the requirements for this command.', ephemeral=True)
            return
        await ctx.response.send_message('Gathering the list for you!', ephemeral=True)
        logging.info('Generating kicklist...')
        today = datetime.today()
        logging.info('Getting exemption list')
        exemptionKickList = await get_exemption_list()
        logging.info('Gathering squadron player list')
        squadronList = await get_squadron_players()

        try:
            if type.value < 3:
                finalSortedList = await GetKicklistVariantBoth(bot, today, exemptionKickList, squadronList)
            # If it's didn't play last season, then only do that one
            elif type.value == 3:
                finalSortedList = await GetKicklistVariantDidntPlayLastSeason(exemptionKickList, squadronList)
        except:
            finalSortedList = dict()
            finalSortedList[0] = dict()
            finalSortedList[0][0] = "Error occured when generating list"
            finalSortedList[0][4] = datetime.now()
            finalSortedList[0][5] = "ERR"
       
        timeEnd = datetime.today()
        timeTaken = timeEnd - today
        logging.info(f'Kicklist generated in {timeTaken.total_seconds():.2f} seconds.')
        # Count people
        printString = f'```ansi\n'
        amountToKick = "ERROR N/A"
        if (type.value == 0 or type.value == 3):
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
            
        printString += f'Users to kick: \u001b[1;31m{amountToKick}\u001b[0m   Time taken: {timeTaken.total_seconds():.2f} seconds\n'
        
        # If didn't play
        if type.value == 3:
            printString += f'Note: notice list is NOT checked in this list'

        printString += f'  Username             | Date joined | Reason\n'
        for number, squadronMember in finalSortedList.items():
            if ((type.value == 1 and squadronMember[5] == 'Not in discord') or (type.value == 2 and squadronMember[5] == 'Inactivity')):
                continue
            logging.info(f'Preparing kicklist entry for {squadronMember[0]}')
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