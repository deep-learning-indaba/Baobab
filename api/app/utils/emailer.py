import traceback
from app import LOGGER
from config import SMTP_USERNAME, SMTP_PASSWORD, SMTP_SENDER_NAME, SMTP_SENDER_EMAIL, SMTP_HOST, SMTP_PORT, DEBUG
import smtplib
import email.utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_mail(recipient, subject, body_text, body_html='', charset='UTF-8', mail_type='AMZ'):
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
    if (not DEBUG):
        if mail_type == 'AMZ':
            configuration_set = 'ConfigSet'
            try:
                msg = MIMEMultipart()
                msg['Subject'] = subject
                msg['From'] = email.utils.formataddr(
                    (SMTP_SENDER_NAME, SMTP_SENDER_EMAIL))
                msg['To'] = recipient
                msg.add_header('X-SES-CONFIGURATION-SET', configuration_set)

                body_part1 = MIMEText(body_text, 'plain', _charset=charset)
                body_part2 = MIMEText(body_html, 'html', _charset=charset)

                msg.attach(body_part1)
                msg.attach(body_part2)

                server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.sendmail(SMTP_SENDER_EMAIL, recipient, msg.as_string())
                server.close()
            except Exception as e:
                raise e
    else:
        LOGGER.debug('Recipient : {recipient}'.format(recipient=recipient))
        LOGGER.debug('Subject : {subject}'.format(subject=subject))
        LOGGER.debug('Body : {body}'.format(body=body_text))
