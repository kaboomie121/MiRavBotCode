import logging
from pathlib import Path
logging.getLogger(__name__)
logging.info(f'Importing {Path(__file__).name}')

import discord
from config_loader import config

