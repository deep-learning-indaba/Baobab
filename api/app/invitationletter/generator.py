from mailmerge import MailMerge
from app import LOGGER
from config import GCP_CREDENTIALS_DICT
from config import GCP_BUCKET_NAME
import json
from google.cloud import storage
import os
<<<<<<< HEAD

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = json.dumps(GCP_CREDENTIALS_DICT)
=======
import requests
from app.utils import emailer
from app.utils import pdfconvertor
from app.events.models import Event
from app import db

OFFER_EMAIL_BODY = """
Dear {user_title} {first_name} {last_name},

Congratulations! You've been selected to attend the {event_name}!

Please see the attached document below for your acceptance of offer: {host}/offer

If you have any queries, please forward them to info@deeplearningindaba.com  

Kind Regards,
The Deep Learning Indaba Team
"""
>>>>>>> 635ac640feabbe20761406986e83fe9c69978477


def download_blob(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(source_blob_name)

    blob.download_to_filename(destination_file_name)

    print('Blob {} downloaded to {}.'.format(
        source_blob_name,
        destination_file_name))

    return source_blob_name


def generate(template_path, event_id, work_address, addressed_to, residential_address, passport_name,
             passport_no, passport_issued_by, invitation_letter_sent_at, to_date, from_date, country_of_residence,
             nationality, date_of_birth, email, user_title, firstname, lastname):

    template = 'app/invitationletter/template/template.docx'

    download_blob(bucket_name=GCP_BUCKET_NAME, source_blob_name=template_path,
                  destination_file_name=template)

    if os.path.exists(template):
        document = MailMerge(template)
        LOGGER.debug("merge-fields.... {} .".format(document.get_merge_fields()))

        document.merge(
            TITLE=user_title,
            FIRSTNAME=firstname,
            SURNAME=lastname,
            WORK_ADDRESS=work_address,
            ADDRESSED_TO=addressed_to,
            RESIDENTIAL_ADDRESS=residential_address,
            PASSPORT_NAME=passport_name,
            PASSPORT_NO=passport_no,
            ISSUED_BY=passport_issued_by,
            EXPIRY_DATE=to_date,
            FROM_DATE=from_date,
            COUNTRY_OF_RESIDENCE=country_of_residence,
            NATIONALITY=nationality,
            DATE_OF_BIRTH=date_of_birth,
            INVITATION_LETTER_SENT_AT=invitation_letter_sent_at
        )

        document.write('app/invitationletter/letter/template_sample.docx')

    # Todo: Convert docx to pdf

<<<<<<< HEAD
    # Todo: Send Email
    return True
=======
    # Todo: converting a generated letter into a pdf
    pdfconvertor.convert_to(folder='app/invitationletter/letter', source=invitation_letter)

    event = db.session.query(Event).get(event_id)
    if not event:
        subject = 'See Attachment'
    else:
        subject = "Invitation to " + event.name
    # Todo: sending an email with the attachment for the event
    try:
        emailer.send_mail(recipient=email, subject=subject, body_html=OFFER_EMAIL_BODY, charset='UTF-8', mail_type='AMZ',
                          file_name=file_name, file_path=invitation_letter)

        LOGGER.debug('successfully sent emeil...')
        return True
    except ValueError:
        LOGGER.debug('Did no send email...')
        return False
>>>>>>> 635ac640feabbe20761406986e83fe9c69978477
