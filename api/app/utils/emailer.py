import traceback
from app import LOGGER
from config import SMTP_USERNAME, SMTP_PASSWORD, SMTP_SENDER_NAME, SMTP_SENDER_EMAIL, SMTP_HOST, SMTP_PORT, DEBUG
import smtplib
import email.utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from flask import g, request
from app.email_template.repository import EmailRepository as email_repository
from app.users.repository import UserRepository as user_repository

def email_user(email_template_key, template_parameters, event_id=None, user_id=None, user=None, subject_parameters=None):
    """Send an email to a specified user using an email template. Handles resolving the correct language."""
    if user_id is None and user is None:
        raise ValueError('You must specify one of user_id or user')
    
    user = user or user_repository.get_by_id(user_id)
    language = user.user_primaryLanguage
    email_template = email_repository.get(event_id, email_template_key, language)
    subject = email_template.subject
    if subject_parameters is not None:
        subject = subject.format(**subject_parameters)
    body_text = email_template.template.format(**template_parameters)
    send_mail(recipient=user.email, subject=subject, body_text=body_text)


def send_mail(recipient, subject, body_text='', body_html='', charset='UTF-8', mail_type='AMZ', file_name='',
              file_path='', sender_name=None, sender_email=None):
    '''[summary]

    Arguments:
        recipient {[type]} -- [description]
        subject {[type]} -- [description]
        body_text {[type]} -- [description]

    Keyword Arguments:
        body_html {[type]} -- [description] (default: {None})
        type {str} -- [description] (default: {'AMZ'})

    Raises:
        e -- [description]
    '''
    sender_name = sender_name or g.organisation.name
    sender_email = sender_email or g.organisation.email_from

    if (not DEBUG):
        if mail_type == 'AMZ':
            try:
                msg = MIMEMultipart()
                msg['Subject'] = subject
                msg['From'] = email.utils.formataddr(
                    (sender_name, sender_email))
                msg['To'] = recipient

                body_part1 = MIMEText(body_text, 'plain', _charset=charset)
                body_part2 = MIMEText(body_html, 'html', _charset=charset)

                if file_name != "" and file_path != "":
                    attachment = open(file_path, "rb")

                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)

                    part.add_header('Content-Disposition', "attachment; filename= %s" % file_name)
                    msg.attach(part)

                msg.attach(body_part1)
                msg.attach(body_part2)

                server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.sendmail(sender_email, recipient, msg.as_string())
                server.close()
            except Exception as e:
                LOGGER.error("Exception {} while trying to send email: {}, {}".format(e, traceback.format_exc()))
                raise e

    else:
        LOGGER.debug('Sender Name: {sender_name}'.format(sender_name=sender_name))
        LOGGER.debug('Sender Email: {sender_email}'.format(sender_email=sender_email))
        LOGGER.debug('Recipient : {recipient}'.format(recipient=recipient))
        LOGGER.debug('Subject : {subject}'.format(subject=subject))
        LOGGER.debug('Body Text : {body}'.format(body=body_text))
        LOGGER.debug('Body HTML : {body}'.format(body=body_html))
