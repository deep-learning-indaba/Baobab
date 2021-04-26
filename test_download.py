from __future__ import print_function
import os.path
import io

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload, MediaIoBaseUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from PyPDF2 import PdfFileWriter, PdfFileReader

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive']


def main():
    """Shows basic usage of the Docs API.
    Prints the title of a sample document.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    drive_service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        "name": "HTML-test",
        "mimeType": "application/vnd.google-apps.document",
    }

    media = MediaIoBaseUpload(
        io.BytesIO(
            bytes(
                "<!DOCTYPE html> <html> <body> <h1>Hello, </h1> <p>World!</p> </body> </html>", 
                encoding='utf8')
            ), 
        mimetype="text/html", 
        resumable=True
    )

    file = drive_service.files().create(body=file_metadata,
                                        media_body=media,
                                        fields='id').execute()
    
    file_id = file.get('id')

    request = drive_service.files().export_media(fileId=file_id, mimeType='application/pdf')

    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print("Download %d%%." % int(status.progress() * 100))

    pdf_reader = PdfFileReader(fh)
    with open("test.pdf", "wb") as f:
        pdf = PdfFileWriter()
        pdf.appendPagesFromReader(pdf_reader)
        pdf.write(f) 


if __name__ == '__main__':
    main()