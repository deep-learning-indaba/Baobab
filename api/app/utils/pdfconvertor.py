import sys
import subprocess
import re
from app import LOGGER
import os

def convert_to(folder, source, output):
    LOGGER.debug('...beginning conversion to pdf...')
    args = [libreoffice_exec(), '--headless', '--convert-to', 'pdf', '--outdir', folder, source]

    process = subprocess.call(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if os.path.exists(output):
        LOGGER.debug('Successfully converted to pdf...')
        return True
    LOGGER.debug('Did not successfully convert to pdf...')
    return False

def libreoffice_exec():
    if sys.platform == 'linux':
        return '/lib/libreoffice/program/soffice'
    return 'libreoffice'


class LibreOfficeError(Exception):
    def __init__(self, output):
        self.output = output