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

INVITATION_EMAIL_BODY = """
Dear {user_title} {first_name} {last_name},

Your official invitation letter is attached!

If you have any queries, please forward them to info@deeplearningindaba.com  

Kind Regards,
The Deep Learning Indaba Team
"""


def download_blob(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""

    LOGGER.debug('Setting GCP storage client')
    credentials = service_account.Credentials.from_service_account_info(
        GCP_CREDENTIALS_DICT
    )
    storage_client = storage.Client(credentials=credentials, project=GCP_PROJECT_NAME)

    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(source_blob_name)

    blob.download_to_filename(destination_file_name)

    print('Blob {} downloaded to {}.'.format(
        source_blob_name,
        destination_file_name))

    return source_blob_name


def generate(template_path, event_id, work_address, addressed_to, residential_address, passport_name,
             passport_no, passport_issued_by, invitation_letter_sent_at, to_date, from_date, country_of_residence,
             nationality, date_of_birth, email, user_title, firstname, lastname, bringing_poster, expiry_date):

    # Path to store the template locally of merged and unmerged
    template = 'app/invitationletter/template/template.docx'
    template_merged = 'app/invitationletter/letter/template.docx'

    download_blob(bucket_name=GCP_BUCKET_NAME, source_blob_name=template_path,
                  destination_file_name=template)

    if os.path.exists(template):
        document = MailMerge(template)
        LOGGER.debug("merge-fields.... {} .".format(document.get_merge_fields()))

        document.merge(
            TITLE=user_title,
            FIRSTNAME=firstname,
            LASTNAME=lastname,
            WORK_ADDRESS=work_address,
            ADDRESSED_TO=addressed_to,
            RESIDENTIAL_ADDRESS=residential_address,
            PASSPORT_NAME=passport_name,
            PASSPORT_NO=passport_no,
            ISSUED_BY=passport_issued_by,
            EXPIRY_DATE=expiry_date,
            ACCOMODATION_END_DATE=to_date,
            ACCOMODATION_START_DATE=from_date,
            COUNTRY_OF_RESIDENCE=country_of_residence,
            NATIONALITY=nationality,
            DATE_OF_BIRTH=date_of_birth,
            INVITATION_LETTER_SENT_AT=invitation_letter_sent_at,
            BRINGING_POSTER=bringing_poster
        )

        document.write(template_merged)

    # Conversion
    pdfconvertor.convert_to(folder='app/invitationletter/letter', source=template_merged)
    template_pdf = 'app/invitationletter/letter/template.pdf'

    event = db.session.query(Event).get(event_id)
    if not event:
        return errors.EVENT_NOT_FOUND

    subject = "Invitation Letter for " + event.name

    try:
        emailer.send_mail(recipient=email,
                          subject=subject,
                          body_html=INVITATION_EMAIL_BODY.format(
                            user_title=user_title, first_name=firstname, last_name=lastname),
                          file_name=template_path,
                          file_path=template_pdf)

        LOGGER.debug('successfully sent email...')
        return True
    except ValueError:
        LOGGER.debug('Did no send email...')
        return False
    finally:
        # delete files
        os.remove(template)
        os.remove(template_pdf)
        os.remove(template_merged)
