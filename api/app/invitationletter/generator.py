from mailmerge import MailMerge
from app import LOGGER
from config import GCP_CREDENTIALS_DICT, GCP_PROJECT_NAME, GCP_BUCKET_NAME, FILE_SIZE_LIMIT
from config import GCP_BUCKET_NAME
import json
from google.cloud import storage
import os
from app.utils import emailer
from app.utils import pdfconvertor
from app.events.models import Event
from app import db
from app.utils import errors

from google.oauth2 import service_account
from six import string_types


def download_blob(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""

    if GCP_CREDENTIALS_DICT['private_key'] == "dummy":
        LOGGER.debug('Setting dummy storage client')
        storage_client = storage.Client(project=GCP_PROJECT_NAME)
    else:
        LOGGER.debug('Setting GCP storage client')
        credentials = service_account.Credentials.from_service_account_info(
            GCP_CREDENTIALS_DICT
        )
        storage_client = storage.Client(credentials=credentials, project=GCP_PROJECT_NAME)

    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(source_blob_name)

    blob.download_to_filename(destination_file_name)

    print(('Blob {} downloaded to {}.'.format(
        source_blob_name,
        destination_file_name)))

    return source_blob_name

def check_values(template_path, event_id, work_address, addressed_to, residential_address, passport_name,
        passport_no, passport_issued_by, invitation_letter_sent_at, to_date, from_date, country_of_residence,
        nationality, date_of_birth, email, user_title, firstname, lastname, bringing_poster, expiry_date):
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
    assert expiry_date is not None and isinstance(expiry_date, string_types) 


def generate(template_path, event_id, work_address, addressed_to, residential_address, passport_name,
             passport_no, passport_issued_by, invitation_letter_sent_at, to_date, from_date, country_of_residence,
             nationality, date_of_birth, email, user_title, firstname, lastname, bringing_poster, expiry_date, user):

    check_values(template_path, event_id, work_address, addressed_to, residential_address, passport_name,
        passport_no, passport_issued_by, invitation_letter_sent_at, to_date, from_date, country_of_residence,
        nationality, date_of_birth, email, user_title, firstname, lastname, bringing_poster, expiry_date)
    
    event = db.session.query(Event).get(event_id)
    if not event:
        return errors.EVENT_NOT_FOUND

    

    try:
        emailer.email_user(
            'invitation-letter',
            event=event,
            user=user,
            file_name="InvitationLetter.pdf",
            file_path=template_pdf
        )

        LOGGER.debug('successfully sent email...')
        return True
    except ValueError:
        LOGGER.debug('Did not send email...')
        return False

    return False
