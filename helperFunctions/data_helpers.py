import logging
from pathlib import Path
logging.getLogger(__name__)
logging.info(f'Importing {Path(__file__).name}')

import discord
from config_loader import config, isDevBot


import datetime
from datetime import datetime
import requests

DISCORDGUILD = config["discordGuild"]
TESTDISCORDGUILD = config["testDiscordGuild"]
NOTICELIST_CHANNEL = config["noticeListChannelId"]

FIRST_DEADLINE = config["firstDeadline"]
FIRST_ACTIVITY_REQUIREMENT = config["firstActivityRequirement"]
SECOND_DEADLINE = config["secondDeadline"]
SECOND_ACTIVITY_REQUIREMENT = config["secondActivityRequirement"]
EXEMPTION_SQ_RATING = config["exemptionSQRating"]

JOIN_DEADLINE = config["joinDeadline"]

# import all needed helper functions
from helperFunctions.db import GetData

def FindFirstIndex(string, findChar):
    for charNumber_, char in enumerate(string):
        if char == findChar:
            return charNumber_
    return -1

# Will return a list of users that are on notice with the pattern [USERNAME, Condition] where if condition, 0 = all normal, 1 = check notes, 2 = Special case
async def get_notice_list(client : discord.Client):
    print ('Getting notice list...')
    if isDevBot:
        print ('Dev bot is running: Returning empty list')
        return list()
    logging.info('Dev bot is not running: Getting real notice list')
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
    
async def get_discord_exemption_list():
    print ('Getting discord exemption list...')
    _, listExemptions = await GetData("Bot", "ExemptionListDISCORD")
    
    if listExemptions == None:
        listExemptions = ""
        
    return listExemptions.split("§§")

async def get_exemption_list():
    logging.info( 'Getting ingame exemption list...')
    _, listExemptions = await GetData("Bot", "ExemptionListIGN")
    
    if listExemptions == None:
        listExemptions = ""
        
    return listExemptions.split("§§")


async def get_squadron_kickable(bot : discord.client, personList):
    logging.info('Getting kickable squadron members...')
    noticeList = await get_notice_list(bot)
    
    # Convert string to datetime object
    date_format = "%d.%m.%Y"

    # Get today's date
    today = datetime.today()

    logging.info('Comparing squadron members to notice list and activity requirements...')
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
            logging.info(f'Added {personData[0]} to kickable list.')
    

    return returnList

async def get_discord_list(client : discord.Client):
    logging.info('Getting discord member list...')
    if isDevBot:
        return (client.get_guild(TESTDISCORDGUILD)).members
    guild = client.get_guild(DISCORDGUILD)
    return guild.members
  

# position 0 is name, 1 is SQB rating,
# 2 is activity, 3 is role, 4 is join date
async def get_squadron_players():
    logging.info('Getting squadron player list from warthunder.com...')
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
