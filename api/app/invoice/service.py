from app.offer.models import Offer
from app.events.models import EventFee
from app.invoice.models import Invoice, InvoiceLineItem, InvoicePaymentStatus, PaymentStatus
from app.invoice.repository import InvoiceRepository as invoice_repository
from app.invoice import generator
from flask import g
from typing import Sequence
from datetime import datetime
from app.email_template.service import Attachment, queue_email, upload_attachment
from app.utils import storage
from app import LOGGER, db
import os


INVOICE_BUCKET = "indaba-invoices"  # TODO: Replace bucket name with config from organisation


class OfferAlreadyHasInvoiceError(ValueError):
    def __init__(self):
        super().__init__("Offer already has an invoice")


class EventFeesMustHaveSameCurrencyError(ValueError):
    def __init__(self):
        super().__init__("Event fees must have the same currency")


class DueDateInThePastError(ValueError):
    def __init__(self):
        super().__init__("Due date is in the past")


class InvoiceNegativeError(ValueError):
    def __init__(self):
        super().__init__("Invoice total amount cannot be negative")


def issue_invoice_for_offer(offer: Offer, event_fees: Sequence[EventFee], due_date: datetime, issuing_user_id: int):
    if offer.has_valid_invoice():
        raise OfferAlreadyHasInvoiceError()
    if due_date < datetime.now():
        raise DueDateInThePastError()
    
    iso_currency_codes = set([event_fee.iso_currency_code for event_fee in event_fees])
    if len(iso_currency_codes) > 1:
        raise EventFeesMustHaveSameCurrencyError()
    iso_currency_code = list(iso_currency_codes)[0]

    total_amount = sum([event_fee.amount for event_fee in event_fees])
    if total_amount < 0:
        raise InvoiceNegativeError()

    line_items = []
    for event_fee in event_fees:
        line_item = InvoiceLineItem(event_fee.name, event_fee.description, event_fee.amount)
        line_items.append(line_item)

    invoice = Invoice(
        offer.user.email,
        offer.user.full_name,
        iso_currency_code,
        due_date,
        line_items,
        issuing_user_id,
        str(offer.user_id)
    )
    invoice.link_offer(offer.id)

    if invoice.total_amount == 0:
        paid_status = InvoicePaymentStatus.from_baobab(PaymentStatus.PAID, issuing_user_id)
        invoice.add_invoice_payment_status(paid_status)

    invoice_repository.add(invoice)

    invoice_pdf, invoice_number = generator.from_invoice_model(invoice, g.organisation)
    filename = f"invoice_{invoice_number}.pdf"
    try:
        with open(invoice_pdf, 'rb') as file:
            bytes_file = file.read()

        # Saved to its own bucket to keep a copy; the email attaches that copy.
        try:
            bucket = storage.get_storage_bucket(INVOICE_BUCKET)
            bucket.blob(filename).upload_from_string(bytes_file, content_type="application/pdf")
            attachment = Attachment(filename, filename, bucket=INVOICE_BUCKET)
        except Exception as e:
            LOGGER.error("Could not upload invoice to cloud storage: " + str(e))
            attachment = upload_attachment(bytes_file, filename)

        queue_email('invoice', offer.user, event=offer.event, attachments=[attachment],
                    context={'invoice': invoice, 'offer': offer})
        db.session.commit()
    finally:
        os.remove(invoice_pdf)

    return invoice
