import sys
import subprocess
import re
from app import LOGGER


def convert_to(folder, source):
    LOGGER.debug('...beginning conversion to pdf...')
    args = [libreoffice_exec(), '--headless', '--convert-to', 'pdf', '--outdir', folder, source]

    process = subprocess.call(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    filename = re.search('-> (.*?) using filter', process.stdout.decode())

    LOGGER.debug('successfully converted to pdf...')
    if filename is None:
        raise LibreOfficeError(process.stdout.decode())
    else:
        return filename.group(1)


def libreoffice_exec():
    if sys.platform == 'linux':
        return '/lib/libreoffice/program/soffice'
    return 'libreoffice'


class LibreOfficeError(Exception):
    def __init__(self, output):
        self.output = output