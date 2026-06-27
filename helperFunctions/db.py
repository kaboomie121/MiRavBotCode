import logging
from pathlib import Path
logging.getLogger(__name__)
logging.info(f'Importing {Path(__file__).name}')

import discord
from config_loader import config

DBCHANNELID = config["DBChannelId"]

client = ""

async def SetupDB(_client : discord.Client):
    global client
    client = _client


async def GetFullUserData(userkey:str):
    logging.info(f'Getting full data for userkey: {userkey}')
    dbChannel = client.get_channel(DBCHANNELID)
    #find first
    async for message in dbChannel.history(limit= None):
        founduserkey, data = message.content.split("|")
        if founduserkey == userkey:
            return message, str(data)
    return None, None

async def GetAllDataFromOneKey(datakey:str):
    logging.info(f'Getting all data for datakey: {datakey}')
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
        for data in (userData.split(";")):
            if data.split(":")[0] in datakey:
                returnList.append([DBuserkey, userData.split(":")[1]])
    return returnList

async def GetData(userkey:str, datakey:str):
    logging.info(f'Getting data for userkey: {userkey} and datakey: {datakey}')
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
            for data in (userData.split(";")):
                if data.split(":")[0] == datakey:
                    return message, str(data.split(":")[1])
    return None, None
    
async def Removedatakey(userkey:str, datakey:str):
    logging.info(f'Removing data for userkey: {userkey} and datakey: {datakey}')
    # find first
    message, fullData = await GetFullUserData(userkey)
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

async def Writedata(userkey:str, datakey:str, data:str):
    logging.info(f'Writing data for userkey: {userkey} and datakey: {datakey} with data: {data}')
    dbChannel = client.get_channel(DBCHANNELID)
    # find first
    message, fullData = await GetFullUserData(userkey)
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
 