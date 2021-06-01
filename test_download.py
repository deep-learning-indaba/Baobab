from __future__ import print_function
import time
import os.path
import io

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload, MediaIoBaseUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from PyPDF2 import PdfFileWriter, PdfFileReader

q_and_a_dict = {"Q1_Name" : "Name Surname", "Q2_Date" : "April 2021", "Q3_Occupation": "Winging it", "Q4_Random_question": "Random Insight"}
requests = [
         {
            'insertText': {
                'location': {
                    'index': 1,
                },
                'text': "<!DOCTYPE html> <html> <body> <h1>Hello,</h1> <p>World!</p> </body> </html>" 
            }
        },
        #          {
        #     'insertText': {
        #         'location': {
        #             'index': 12, # TODO: How does this reconcile with the start and end index 
        #         },
        #         'text': ("B" * 10) + "\n"
        #     }
        # },
        #          {
        #     'insertText': {
        #         'location': {
        #             'index': 75,
        #         },
        #         'text': "C" * 10
        #     }
        # },

    ]

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']

# The ID of a sample document.
DOCUMENT_ID = '195j9eDD3ccgjQRttHhJPymLJUCOUjs-jmwTrekvdjFE'

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
    
    service = build('docs', 'v1', credentials=creds)

    
    title = 'My HTML Document'
    body = {
        'title': title
    }
    doc = service.documents() \
        .create(body=body).execute()
    print('Created document with title: {0}'.format(
        doc.get('title')))


    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token_drive.json'):
        creds = Credentials.from_authorized_user_file('token_drive.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials_drive.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token_drive.json', 'w') as token_drive:
            token_drive.write(creds.to_json())

    file_id = doc.get('documentId')
    result = service.documents().batchUpdate(documentId=file_id, body={'requests': requests}).execute()

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
    print(file_id)

    request = drive_service.files().export_media(fileId=file_id, mimeType='application/pdf')
    # fh = bytes array 
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print("Download %d%%." % int(status.progress() * 100))
    pdf_reader = PdfFileReader(fh)
    with open("testpdf.pdf", "wb") as f:
        pdf = PdfFileWriter()
        pdf.appendPagesFromReader(pdf_reader)
        pdf.write(f) 
    



if __name__ == '__main__':
    main()