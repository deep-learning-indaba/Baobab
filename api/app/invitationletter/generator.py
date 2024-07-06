from app import LOGGER
from config import GCP_CREDENTIALS_DICT, GCP_PROJECT_NAME
from google.cloud import storage
from app.utils import emailer
from app.events.models import Event
from app import db
from app.utils import errors
from google.auth import default
from googleapiclient.discovery import build
from google.oauth2 import service_account
import re
from google.oauth2 import service_account
from six import string_types
import uuid
import os


SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']


def check_values(template_path, event_id, work_address, addressed_to, residential_address, passport_name,
        passport_no, passport_issued_by, invitation_letter_sent_at, to_date, from_date, country_of_residence,
        nationality, date_of_birth, email, user_title, firstname, lastname, bringing_poster, bringing_poster_fr, expiry_date):
    assert template_path is not None and isinstance(template_path, string_types) 
    assert event_id is not None and isinstance(event_id, int) 
    assert work_address is not None and isinstance(work_address, string_types) 
    assert addressed_to is not None and isinstance(addressed_to, string_types) 
    assert residential_address is not None and isinstance(residential_address, string_types) 
    assert passport_name is not None and isinstance(passport_name, string_types) 
    assert passport_no is not None and isinstance(passport_no, string_types) 
    assert passport_issued_by is not None and isinstance(passport_issued_by, string_types) 
    assert invitation_letter_sent_at is not None and isinstance(invitation_letter_sent_at, string_types) 
    assert to_date is not None and isinstance(to_date, string_types) 
    assert from_date is not None and isinstance(from_date, string_types) 
    assert country_of_residence is not None and isinstance(country_of_residence, string_types) 
    assert nationality is not None and isinstance(nationality, string_types) 
    assert date_of_birth is not None and isinstance(date_of_birth, string_types) 
    assert email is not None and isinstance(email, string_types) 
    assert user_title is not None and isinstance(user_title, string_types) 
    assert firstname is not None and isinstance(firstname, string_types) 
    assert lastname is not None and isinstance(lastname, string_types) 
    assert bringing_poster is not None and isinstance(bringing_poster, string_types) 
    assert bringing_poster_fr is not None and isinstance(bringing_poster_fr, string_types)
    assert expiry_date is not None and isinstance(expiry_date, string_types) 


def _create_doc_service():
    if GCP_CREDENTIALS_DICT['private_key'] == 'dummy':
        # Running on GCP, use App Engine credentials
        credentials, _ = default()
    else:
        # Create credentials to access from anywhere
        private_key = GCP_CREDENTIALS_DICT['private_key'].replace('\\n', '\n')
        GCP_CREDENTIALS_DICT["private_key"] = private_key
        credentials = service_account.Credentials.from_service_account_info(
            GCP_CREDENTIALS_DICT
        )

    docs_service = build('docs', 'v1', credentials=credentials)
    return docs_service

def _create_drive_service():
    if GCP_CREDENTIALS_DICT['private_key'] == 'dummy':
        # Running on GCP, use App Engine credentials
        credentials, _ = default()
    else:
        # Create credentials to access from anywhere
        private_key = GCP_CREDENTIALS_DICT['private_key'].replace('\\n', '\n')
        GCP_CREDENTIALS_DICT["private_key"] = private_key
        credentials = service_account.Credentials.from_service_account_info(
            GCP_CREDENTIALS_DICT
        )
    drive_service = build('drive', 'v3', credentials=credentials)
    return drive_service


def generate(template_path, event_id, work_address, addressed_to, residential_address, passport_name,
             passport_no, passport_issued_by, invitation_letter_sent_at, to_date, from_date, country_of_residence,
             nationality, date_of_birth, email, user_title, firstname, lastname, bringing_poster, bringing_poster_fr, expiry_date, user):

    check_values(template_path, event_id, work_address, addressed_to, residential_address, passport_name,
        passport_no, passport_issued_by, invitation_letter_sent_at, to_date, from_date, country_of_residence,
        nationality, date_of_birth, email, user_title, firstname, lastname, bringing_poster, bringing_poster_fr, expiry_date)
    
    event = db.session.query(Event).get(event_id)
    if not event:
        return errors.EVENT_NOT_FOUND

    # Create credentials to access from anywhere
    document_id = template_path
    doc_service = _create_doc_service()
    drive_service = _create_drive_service()

    copied_document = drive_service.files().copy(fileId=document_id, body={'name': f"Copy of {document_id}"}).execute()
    copied_document_id = copied_document.get('id')

    replace_variables = {
        '%WORK_ADDRESS%': work_address,
        '%ADDRESSED_TO%': addressed_to,
        '%RESIDENTIAL_ADDRESS%': residential_address,
        '%PASSPORT_NAME%': passport_name,
        '%PASSPORT_NO%': passport_no,
        '%PASSPORT_ISSUED_BY%': passport_issued_by,
        '%INVITATION_LETTER_SENT_AT%': invitation_letter_sent_at,
        '%TO_DATE%': to_date,
        '%FROM_DATE%': from_date,
        '%COUNTRY_OF_RESIDENCE%': country_of_residence,
        '%NATIONALITY%': nationality,
        '%DATE_OF_BIRTH%': date_of_birth,
        '%EMAIL%': email,
        '%USER_TITLE%': user_title,
        '%FIRSTNAME%': firstname,
        '%LASTNAME%': lastname,
        '%BRINGING_POSTER%': bringing_poster,
        '%BRINGING_POSTER_FR%': bringing_poster_fr,
        '%EXPIRY_DATE%': expiry_date
    }

    # Iterate through variables and perform replacements
    replace_requests = []
    for key, value in replace_variables.items():
        replace_requests.append({
            'replaceAllText': {
                'containsText': {"text": key, "matchCase": True},
                "replaceText": value
            }
        })

    # Batch update the document with replacements
    if replace_requests:
        batch = doc_service.documents().batchUpdate(documentId=copied_document_id, body={'requests': replace_requests}).execute()
    
    export_request = drive_service.files().export(fileId=copied_document_id, mimeType='application/pdf').execute()
    output_file = str(uuid.uuid4()) + ".pdf"

    with open(output_file, "wb") as f:
        f.write(export_request)

    try:
        emailer.email_user(
            'invitation-letter',
            event=event,
            user=user,
            file_name="InvitationLetter.pdf",
            file_path=output_file
        )

        LOGGER.debug('successfully sent email...')
        return True
    except ValueError:
        LOGGER.debug('Did not send email...')
        return False
    finally:
        os.remove(output_file)
        drive_service.files().delete(fileId=copied_document_id).execute()
