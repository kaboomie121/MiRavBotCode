import logging
from pathlib import Path
logging.getLogger(__name__)
logging.info(f'Importing {Path(__file__).name}')

from json import loads

base_path = Path(__file__).parent
config: dict = loads((base_path / "config.json").read_text())


token: dict = loads((base_path / "token.json").read_text())

isDevBot = token.get("devMode", False)