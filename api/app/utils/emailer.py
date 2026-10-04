import time
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
from flask import g, has_app_context


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
                   sender_name, sender_email, attachments=None, reply_to=None):
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

    attachments = list(attachments or [])
    if file_name and file_path:
        attachments.append((file_name, file_path, 'application/octet-stream'))

    if attachments:
        # An attachment is not an alternative to the body, so it sits alongside it
        # in a mixed container that wraps the alternative pair.
        msg = MIMEMultipart('mixed')
        msg.attach(body)

        for name, path, content_type in attachments:
            maintype, _, subtype = (content_type or 'application/octet-stream').partition('/')
            with open(path, 'rb') as attachment:
                part = MIMEBase(maintype, subtype or 'octet-stream')
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment', filename=name)
            msg.attach(part)
    else:
        msg = body

    msg['Subject'] = subject
    msg['From'] = email.utils.formataddr((sender_name, sender_email))
    msg['To'] = recipient
    if reply_to:
        msg['Reply-To'] = reply_to
    return msg


class SmtpConnection:
    """One authenticated SMTP session, reusable across many messages.

    The TLS handshake and login cost far more than transmitting an individual
    message, so anything sending to more than one recipient must share a single
    connection rather than opening one per message. Sends are also paced:
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
             file_path='', sender_name=None, sender_email=None, attachments=None, reply_to=None):
        sender_name, sender_email = resolve_sender(sender_name, sender_email)

        if DEBUG:
            _log_email(recipient, subject, body_text, body_html, sender_name, sender_email)
            return

        self.open()
        msg = _build_message(recipient, subject, body_text, body_html, charset, file_name,
                             file_path, sender_name, sender_email, attachments, reply_to)
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
