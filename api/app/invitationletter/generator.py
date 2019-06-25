from app.utils.emailer import send_mail
from mailmerge import MailMerge
from app import LOGGER
import requests


def get_template(template_path):
    LOGGER.debug("Downloading template......")
    headers = {'Authorization': " authentication"}

    try:
        r = requests.get(template_path)
        file_name = template_path.rsplit('/', 1).pop()
        local_path = 'app/invitationletter/template/' + file_name

        with open(local_path, 'wb') as f:
            f.write(r.content)

        return file_name

    except Exception as e:
        LOGGER.error("failed to fetch template due to {}".format(e))


def generate(template_path, event_id, work_address, addressed_to, residential_address, passport_name,
             passport_no, passport_issued_by, invitation_letter_sent_at, to_date, from_date, country_of_residence,
             nationality, date_of_birth, email, firstname, lastname):

    file_name = get_template(template_path)
    invitation_letter = 'app/invitationletter/letter/' + file_name
    template = 'app/invitationletter/template/' + file_name

    document = MailMerge(template)
    print(document.get_merge_fields())
    LOGGER.debug("merge able fields.... {} .".format(document.get_merge_fields()))

    document.merge(
        firstname=firstname,
        surname=lastname,
        work_address=work_address,
        addressed_to=addressed_to,
        residential_address=residential_address,
        passport_name=passport_name,
        passport_no=passport_no,
        passport_issued_by=passport_issued_by,
        to_date=to_date,
        from_date=from_date,
        country_of_residence=country_of_residence,
        nationality=nationality,
        date_of_birth=date_of_birth,
        invitation_letter_sent_at=invitation_letter_sent_at
    )

    document.write(invitation_letter)

    # Todo: Send Email

    return True
