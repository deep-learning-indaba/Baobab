import sys
import subprocess
import os
import io
import tempfile

from app import LOGGER
from config import GCP_CREDENTIALS_DICT

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from google.oauth2.credentials import Credentials

from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials


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


def html_to_pdf(
    file_name,
    html_string,
    ):

    LOGGER.debug('Using Google Drive to convert PDF')

    # If no credentials, return a dummy string for testing.
    if GCP_CREDENTIALS_DICT['private_key'] == 'dummy':
        pdf_bytes = io.BytesIO(b"Hello World, This is not a real PDF")
        return pdf_bytes

    credentials = ServiceAccountCredentials.from_json_keyfile_dict(GCP_CREDENTIALS_DICT)

    drive_service = build('drive', 'v3', credentials=credentials) 

    # Set the upload to be a HTML file
    media = MediaIoBaseUpload(
        io.BytesIO(bytes(html_string, encoding='utf8')), 
        mimetype="text/html",
        resumable=True
    )

    # Create the file, and initiate the conversion to a Docs document
    # This enables the conversion to PDF
    file = drive_service.files().create(
        body={
            "name": file_name,
            "mimeType": "application/vnd.google-apps.document",
            },
        media_body=media,
        fields='id'
    ).execute()

    # Download as a PDF file
    request = drive_service.files().export_media(
        fileId=file.get('id'),
        mimeType='application/pdf'
    )

    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while done is False:
        _, done = downloader.next_chunk()

    # Delete the Docs document afterwards
    drive_service.files().delete(fileId=file.get('id')).execute()

    return buffer