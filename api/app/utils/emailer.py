import time
import traceback
import ssl
from app import LOGGER
from config import (SMTP_USERNAME, SMTP_PASSWORD, SMTP_SENDER_NAME, SMTP_SENDER_EMAIL, SMTP_HOST,
                    SMTP_PORT, SMTP_MAX_SEND_RATE, DEBUG)
import smtplib
import email.utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from flask import g, has_app_context, request
from app.email_template.repository import EmailRepository as email_repository
from app.users.repository import UserRepository as user_repository
from app.events.repository import EventRepository as event_repository

def email_user(
    email_template_key, 
    user, 
    template_parameters=None, 
    event=None,
    subject_parameters=None, 
    file_name='',
    file_path=''
):
    """Send an email to a specified user using an email template. Handles resolving the correct language."""
    if user is None:
        raise ValueError('You must specify a user!')

    language = user.user_primaryLanguage
    email_template = email_repository.get(None if event is None else event.id, email_template_key, language)

    if email_template is None:
        raise ValueError('Could not find email template with key {}'.format(email_template_key))
    
    subject_parameters = subject_parameters or {}
    if event is not None and 'event_name' not in subject_parameters:
        subject_parameters['event_name'] = event.get_name(language) if event.has_specific_translation(language) else event.get_name('en')

    subject = email_template.subject.format(**subject_parameters)

    template_parameters = template_parameters or {}
    if 'title' not in template_parameters:
        template_parameters['title'] = user.user_title
    if 'firstname' not in template_parameters:
        template_parameters['firstname'] = user.firstname
    if 'lastname' not in template_parameters:
        template_parameters['lastname'] = user.lastname
    if event is not None and 'event_name' not in template_parameters:
        template_parameters['event_name'] = event.get_name(language) if event.has_specific_translation(language) else event.get_name('en')

    body_text = email_template.template.format(**template_parameters)
    send_mail(recipient=user.email, subject=subject, body_text=body_text, file_name=file_name, file_path=file_path)


def resolve_sender(sender_name, sender_email):
    """Sender identity: what the caller gave, else this request's organisation,
    else the configured SMTP sender.

    The organisation is not always available — the outbox worker's requests carry
    no Origin header, so nothing resolves one — and email_from is nullable, so
    neither source can be relied on alone. Falling through to SMTP_SENDER_EMAIL
    means an organisation with no email_from still sends rather than failing every
    message in the queue.
    """
    if sender_name and sender_email:
        return sender_name, sender_email

    # g is only reachable inside an app context, and raises rather than returning
    # a default outside one, so this stays callable from a script or worker.
    organisation = getattr(g, 'organisation', None) if has_app_context() else None
    sender_name = sender_name or (organisation.name if organisation else None) or SMTP_SENDER_NAME
    sender_email = (sender_email
                    or (organisation.email_from if organisation else None)
                    or SMTP_SENDER_EMAIL)

    if not sender_email:
        raise ValueError(
            'Cannot send: no sender address. Set the organisation\'s email_from, '
            'or SMTP_SENDER_EMAIL, or pass sender_email explicitly.')
    return sender_name, sender_email


def _log_missing_smtp_config():
    missing_config = [name for name, val in [
        ('SMTP_HOST', SMTP_HOST),
        ('SMTP_PORT', SMTP_PORT),
        ('SMTP_USERNAME', SMTP_USERNAME),
        ('SMTP_PASSWORD', SMTP_PASSWORD),
    ] if not val]
    if missing_config:
        LOGGER.error('SMTP configuration missing for: %s', ', '.join(missing_config))


def _log_email(recipient, subject, body_text, body_html, sender_name, sender_email):
    LOGGER.debug('Sender Name: {sender_name}'.format(sender_name=sender_name))
    LOGGER.debug('Sender Email: {sender_email}'.format(sender_email=sender_email))
    LOGGER.debug('Recipient : {recipient}'.format(recipient=recipient))
    LOGGER.debug('Subject : {subject}'.format(subject=subject))
    LOGGER.debug('Body Text : {body}'.format(body=body_text))
    LOGGER.debug('Body HTML : {body}'.format(body=body_html))


def _build_message(recipient, subject, body_text, body_html, charset, file_name, file_path,
                   sender_name, sender_email):
    # The plain text and the HTML are two renderings of one message, so they go in a
    # multipart/alternative and the client displays whichever it prefers — normally
    # the HTML. Under multipart/mixed a client shows every part instead, one after
    # the other, which reads as the message having been sent twice.
    body = MIMEMultipart('alternative')
    # Least preferred first, which is what tells a client the HTML supersedes it.
    body.attach(MIMEText(body_text, 'plain', _charset=charset))
    if body_html:
        # Attached only when there is one: an empty HTML part is still the
        # alternative a client prefers, so it would render as a blank message.
        body.attach(MIMEText(body_html, 'html', _charset=charset))

    if file_name and file_path:
        # An attachment is not an alternative to the body, so it sits alongside it
        # in a mixed container that wraps the alternative pair.
        msg = MIMEMultipart('mixed')
        msg.attach(body)

        with open(file_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment; filename= %s" % file_name)
        msg.attach(part)
    else:
        msg = body

    msg['Subject'] = subject
    msg['From'] = email.utils.formataddr((sender_name, sender_email))
    msg['To'] = recipient
    return msg


class SmtpConnection:
    """One authenticated SMTP session, reusable across many messages.

    The TLS handshake and login cost far more than transmitting an individual
    message, so anything sending to more than one recipient must share a single
    connection rather than calling send_mail in a loop. Sends are also paced:
    SES enforces a per-second limit by rejecting messages above it.

    Under DEBUG no connection is opened and messages are only logged.
    """

    def __init__(self, max_send_rate=None):
        self._max_send_rate = SMTP_MAX_SEND_RATE if max_send_rate is None else max_send_rate
        self._server = None
        self._last_send_at = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()
        return False

    def open(self):
        if DEBUG or self._server is not None:
            return

        _log_missing_smtp_config()
        LOGGER.info('Connecting to SMTP server %s:%s', SMTP_HOST, SMTP_PORT)
        context = ssl.create_default_context()
        server = smtplib.SMTP(SMTP_HOST, int(SMTP_PORT), timeout=30)
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        LOGGER.info('TLS established, logging in as %s', SMTP_USERNAME)
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        self._server = server

    def close(self):
        if self._server is None:
            return
        try:
            self._server.quit()
        except Exception as e:  # noqa: BLE001 - a failed teardown must not mask the work done
            LOGGER.warning('Error closing SMTP connection: %s', e)
        finally:
            self._server = None

    def _wait_for_rate_limit(self):
        if not self._max_send_rate or self._last_send_at is None:
            return
        minimum_interval = 1.0 / self._max_send_rate
        elapsed = time.monotonic() - self._last_send_at
        if elapsed < minimum_interval:
            time.sleep(minimum_interval - elapsed)

    def send(self, recipient, subject, body_text='', body_html='', charset='UTF-8', file_name='',
             file_path='', sender_name=None, sender_email=None):
        sender_name, sender_email = resolve_sender(sender_name, sender_email)

        if DEBUG:
            _log_email(recipient, subject, body_text, body_html, sender_name, sender_email)
            return

        self.open()
        msg = _build_message(recipient, subject, body_text, body_html, charset, file_name,
                             file_path, sender_name, sender_email)
        self._wait_for_rate_limit()
        try:
            self._server.sendmail(sender_email, recipient, msg.as_string())
        except (smtplib.SMTPServerDisconnected, smtplib.SMTPConnectError):
            # SES drops connections that have been idle or open a long time.
            # Reconnecting once keeps that from failing the rest of a batch.
            LOGGER.warning('SMTP connection dropped, reconnecting to send to %s', recipient)
            self.close()
            self.open()
            self._server.sendmail(sender_email, recipient, msg.as_string())
        finally:
            self._last_send_at = time.monotonic()
        LOGGER.info('Email sent successfully to %s', recipient)


def send_mail(recipient, subject, body_text='', body_html='', charset='UTF-8', mail_type='AMZ', file_name='',
              file_path='', sender_name=None, sender_email=None):
    """Send a single email over a connection opened and closed for it alone.

    Sending to many recipients must go through the outbox (or share one
    SmtpConnection) instead of calling this in a loop — connection setup
    dominates, and a few thousand recipients will not fit inside a request.
    """
    sender_name, sender_email = resolve_sender(sender_name, sender_email)
    _log_missing_smtp_config()

    if DEBUG:
        _log_email(recipient, subject, body_text, body_html, sender_name, sender_email)
        return

    if mail_type != 'AMZ':
        return

    try:
        with SmtpConnection() as connection:
            connection.send(
                recipient=recipient,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                charset=charset,
                file_name=file_name,
                file_path=file_path,
                sender_name=sender_name,
                sender_email=sender_email,
            )
    except Exception as e:
        LOGGER.error("Exception {} while trying to send email: {}".format(e, traceback.format_exc()))
        raise e
