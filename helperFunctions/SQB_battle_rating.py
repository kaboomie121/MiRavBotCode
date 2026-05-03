import logging
from pathlib import Path
logging.getLogger(__name__)
logging.info(f'Importing {Path(__file__).name}')

import requests
from datetime import timedelta
from datetime import datetime as datetime


def GetCurrentSquadronSchedule():
    """
    returns either NONE or a dictionary of the combined: "BR"; "StartDate"; "EndDate"
    """
    try:
        result = requests.get("https://forum.warthunder.com/t/season-schedule-for-squadron-battles/4446")
        if result.status_code == 200:
            resultDecoded = result.content.decode("utf-8")
            #print(resultDecoded)
            firstPosition = resultDecoded.find("<div class='post' itemprop='articleBody'>")
            firstPosition = resultDecoded.find("<p>1")+3
            lastPosition = resultDecoded[firstPosition:].find("</p>")
            logging.debug(firstPosition)
            logging.debug(lastPosition)
            listUncodedBrs = resultDecoded[firstPosition:firstPosition+lastPosition].replace("\n","").split("<br>")
            logging.debug(listUncodedBrs)
            listEncodedBrList = list()
            for item in listUncodedBrs:
                processedItem = dict()
                
                # get the BR
                processedItem["BR"] = item[item.find("BR")+2:item.find("(")].strip()

                # Get the dates
                datesUnparsed = item[item.find("(")+1:item.find(")")].replace(" ", "").split("—")

                dateSplit = datesUnparsed[0].split(".")
                processedItem["StartDate"] = datetime(day=int(dateSplit[0]), month=int(dateSplit[1]), hour=9, year=datetime.now().year)
                dateSplit = datesUnparsed[1].split(".")
                processedItem["EndDate"] = datetime(day=int(dateSplit[0]), month=int(dateSplit[1]), hour=9, year=datetime.now().year)

                listEncodedBrList.append(processedItem)
            logging.info(listEncodedBrList)
            return listEncodedBrList
        logging.error("REQUEST HAD AN ERROR")
        return None
    except Exception as e:
        logging.error(f"Got an exception: {e}")
        return None

def GetBRRightNow():
    """
    returns either NONE if schedule failed to grab or string value of BR
    """
    today = datetime.now()
    schedule = GetCurrentSquadronSchedule()

    for BrAndTime in schedule:
        if today > BrAndTime["StartDate"] and today < BrAndTime["EndDate"]:
            logging.info(f"Found date! {BrAndTime["StartDate"]} at br {BrAndTime["BR"]}")
            return BrAndTime["BR"]

if __name__ == "__main__":
    GetBRRightNow()