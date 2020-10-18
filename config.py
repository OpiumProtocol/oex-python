from pathlib import Path
import logging
import os

import yaml

logger = logging.getLogger(__name__)

project_root = os.getenv('opium_project_root', '')


def read_config(param: str):
    try:
        with open(Path(project_root, 'creds.yaml')) as f:
            return yaml.load(f, Loader=yaml.SafeLoader).get(param)
    except FileNotFoundError as ex:
        logger.error(ex)
