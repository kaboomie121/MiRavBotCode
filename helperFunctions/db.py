
if __name__ == "__main__":
    import time
    # Set up logging
    import os
    import logging
    from pathlib import Path
    from datetime import timedelta, datetime
    import sys, subprocess
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
        log_file = Path(f'logs/{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}_DBTEST.log')
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

    logging.info('Logging INIT done, starting db.py as standalone')

else:
    import logging
    from pathlib import Path
    logging.getLogger(__name__)
    logging.info(f'Importing {Path(__file__).name}')

import asyncio


DB_BASE_LOCATION = Path("database")
DB_BASE_LOCATION.mkdir(exist_ok=True)
DB_BASE_LOCATION = str(DB_BASE_LOCATION.absolute())

async def main():
    dblocation = f"{DB_BASE_LOCATION}\\test.sqlite"
    with sqlite3.connect(dblocation) as conn:
            cursor = conn.cursor()
            conn.execute("""
                DROP TABLE IF EXISTS users
            """)
    with sqlite3.connect(dblocation) as conn:
            cursor = conn.cursor()
            conn.execute("""
                DROP TABLE IF EXISTS Exemptions
            """)
    with sqlite3.connect(dblocation) as conn:
            cursor = conn.cursor()
            conn.execute("""
                DROP TABLE IF EXISTS SquadronMemberData
            """)
    db.SetupDB()
    
    db.SquadronMemberData.AddSquadronMember("test", 1, "kaboomie121", 1500, 3600, datetime.now())
    db.SquadronMemberData.AddSquadronMember("test", 1, "notJesse", 200, 3600, datetime.now())
    db.SquadronMemberData.UpdateSquadronMember("test", "kaboomie121") 
    db.SquadronMemberData.UpdateSquadronMember("test", "kaboomie121", sqbPoints = 5)
    

import sqlite3 
from sqlite3 import Error

class db:
    """Class that manages all the data to and from the databases"""
    def SetupDB():
        logging.info(f"Setup db called for base location: {DB_BASE_LOCATION}")
        return
    
    class Config:
        """
        """

    
    class Events:
        """
        Data in the form of\n
        """


    
    class SquadronMemberData:
        """
        Data in the form of\n

        "id" : **key** int
        "gaijinID" : int
        "usernameIngame" : str
        "previousSeasonSqbPoints" : int
        "activity" : int
        "joinDate" : str <-- stored as isoformat
        """
        @staticmethod
        def GetAll(serverID : str):
            dblocation = f"{DB_BASE_LOCATION}\\{serverID}.sqlite"
            
            logging.info(f"{__class__.__name__} Getting all squadron-member data for {serverID}")
            with sqlite3.connect(dblocation) as conn:
                cursor = conn.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{__class__.__name__}'")
                # check if the table actually exists
                if cursor.fetchone():
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute(f"SELECT * FROM {__class__.__name__}")
                    # check if the table actually exists
                    return [dict(row) for row in cursor.fetchall()]
                else:
                    logging.warning(f"No such table ({__class__.__name__}) exist... ignored request")
            return []
        
        @staticmethod
        def GetUser(serverID : str, usernameIngame : str):
            dblocation = f"{DB_BASE_LOCATION}\\{serverID}.sqlite"
            
            logging.info(f"{__class__.__name__} Getting all squadron-member data for {serverID}")
            with sqlite3.connect(dblocation) as conn:
                cursor = conn.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{__class__.__name__}'")
                # check if the table actually exists
                if cursor.fetchone():
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute(f"SELECT * FROM {__class__.__name__}")

                    conn.execute(f"SELECT FROM {__class__.__name__} WHERE usernameIngame = ?", (usernameIngame))
                    return [dict(row) for row in cursor.fetchone()]
                else:
                    logging.warning(f"No such table ({__class__.__name__}) exists... ignored request")
            return None
        
        @staticmethod
        def AddSquadronMember(serverID : str, gaijinID : str , usernameIngame : str, sqbPoints : int, activity : int, joinDate : datetime) -> None:
            dblocation = f"{DB_BASE_LOCATION}\\{serverID}.sqlite"
            
            logging.info(f"{__class__.__name__} Adding squadron member named {usernameIngame} for {serverID}")
            with sqlite3.connect(dblocation) as conn:
                conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {__class__.__name__} (
                        id INTEGER PRIMARY KEY,
                        gaijinID int,
                        usernameIngame TEXT,
                        sqbPoints int,
                        previousSeasonSqbPoints int,
                        activity int,
                        joinDate int
                    )
                """)
                conn.execute(f"""INSERT INTO {__class__.__name__} (gaijinID, usernameIngame, sqbPoints, previousSeasonSqbPoints, activity, joinDate)
                             VALUES (?, ?, ?, ?, ?, ?)""", (gaijinID, usernameIngame, sqbPoints, 0, activity, joinDate.isoformat()))
            return None
        
        @staticmethod
        def UpdateSquadronMember(serverID : str, usernameIngame : str, sqbPoints : int = None, previousSeasonSqbPoints : int = None, activity : int = None) -> None:
            dblocation = f"{DB_BASE_LOCATION}\\{serverID}.sqlite"
            
            logging.info(f"{__class__.__name__} Updating squadron member named {usernameIngame} for {serverID}")
            with sqlite3.connect(dblocation) as conn:
                cursor = conn.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{__class__.__name__}'")
                # check if the table actually exists
                if cursor.fetchone():
                    fields = []
                    values = []

                    if sqbPoints is not None:
                        fields.append("sqbPoints = ?")
                        values.append(sqbPoints)

                    if previousSeasonSqbPoints is not None:
                        fields.append("previousSeasonSqbPoints = ?")
                        values.append(previousSeasonSqbPoints)

                    if activity is not None:
                        fields.append("activity = ?")
                        values.append(activity)
                        
                    if not fields:
                        logging.critical(f"{__class__.__name__} Called update without ANY updated values, ensure atleast one value is updated")
                        return
                    
                    values.append(usernameIngame)

                    conn.execute(f"""UPDATE {__class__.__name__}
                                SET {", ".join(fields)}
                                WHERE usernameIngame = ?""", values)
                else:
                    logging.warning(f"No such table ({__class__.__name__}) exists... ignored request")
            return

        @staticmethod
        def RemoveSquadronMember(serverID : str, usernameIngame : str = None) -> None:
            dblocation = f"{DB_BASE_LOCATION}\\{serverID}.sqlite"
            
            logging.info(f"{__class__.__name__} Deleting IGN: {usernameIngame} for {serverID}")
            with sqlite3.connect(dblocation) as conn:
                cursor = conn.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{__class__.__name__}'")
                # check if the table actually exists
                if cursor.fetchone():
                    cursor = conn.execute(f"SELECT * FROM {__class__.__name__}")

                    conn.execute(f"DELETE FROM {__class__.__name__} WHERE usernameIngame = ?", (usernameIngame))
                else:
                    logging.warning(f"No such table ({__class__.__name__}) exists... ignored request")
            return

    class Exemptions:
        """
        Data in the form of\n

        "id" : **key** int
        "usernameIngame" : str
        "discordID" : int
        """
        @staticmethod
        def GetAll(serverID : str):
            dblocation = f"{DB_BASE_LOCATION}\\{serverID}.sqlite"
            
            logging.info(f"{__class__.__name__} Getting all {__class__.__name__} for {serverID}")
            with sqlite3.connect(dblocation) as conn:
                cursor = conn.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{__class__.__name__}'")
                # check if the table actually exists
                if cursor.fetchone():
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute(f"SELECT * FROM {__class__.__name__}")
                    # check if the table actually exists
                    return [dict(row) for row in cursor.fetchall()]
                else:
                    logging.warning(f"No such table ({__class__.__name__}) exist... ignored request")
            return []
        
        @staticmethod
        def AddUser(serverID : str, usernameIngame : str, discordID : int) -> None:
            dblocation = f"{DB_BASE_LOCATION}\\{serverID}.sqlite"
            
            logging.info(f"{__class__.__name__} Adding IGN: {usernameIngame} and discID: {discordID} for {serverID}")
            with sqlite3.connect(dblocation) as conn:
                conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {__class__.__name__} (
                        id INTEGER PRIMARY KEY,
                        usernameIngame TEXT,
                        discordID INTEGER
                    )
                """)
                conn.execute(f"INSERT INTO {__class__.__name__} (usernameIngame, discordID) VALUES (?, ?)", (usernameIngame, discordID))
            return
        
        @staticmethod
        def RemoveUser(serverID : str, usernameIngame : str = None, discordID : int = None) -> None:
            dblocation = f"{DB_BASE_LOCATION}\\{serverID}.sqlite"
            
            logging.info(f"{__class__.__name__} Deleting IGN: {usernameIngame} and/or discID: {discordID} for {serverID}")
            with sqlite3.connect(dblocation) as conn:
                cursor = conn.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{__class__.__name__}'")
                # check if the table actually exists
                if cursor.fetchone():
                    if usernameIngame != None and discordID != None:
                        logging.debug(f"Using ingameusername and discordid")
                        conn.execute(f"DELETE FROM {__class__.__name__} WHERE usernameIngame = ? AND discordID = ?", (usernameIngame, discordID))
                    elif usernameIngame != None:
                        logging.debug(f"Using ingameusername")
                        conn.execute(f"DELETE FROM {__class__.__name__} WHERE usernameIngame = ?", (usernameIngame,))
                    elif discordID != None:
                        logging.debug(f"Using discordid")
                        conn.execute(f"DELETE FROM {__class__.__name__} WHERE discordID = ?", (discordID,))
                else:
                    logging.warning(f"No such table ({__class__.__name__}) exists... ignored request")
            return
        
        
if __name__ == "__main__":
    asyncio.run(main())