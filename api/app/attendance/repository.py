from app import db
from app.attendance.models import Attendance, EventIndemnity
from app.invitedGuest.models import InvitedGuest
from app.invoice.models import InvoicePaymentStatus, OfferInvoice, PaymentStatus
from app.offer.models import Offer
from app.users.models import AppUser
from sqlalchemy import and_, case
from sqlalchemy.sql import func
from sqlalchemy.dialects import postgresql

class AttendanceRepository():

    @staticmethod
    def get(event_id, user_id):
        return db.session.query(Attendance)\
                         .filter_by(event_id=event_id, user_id=user_id)\
                         .first()

    @staticmethod
    def add(attendance):
        db.session.add(attendance)
    
    @staticmethod
    def save():
        db.session.commit()

    @staticmethod
    def delete(attendance):
        db.session.delete(attendance)
        db.session.commit()

    @staticmethod
    def get_all_guests_for_event(event_id):
        # All users who either accepted an offer or are invited guests for the event.
        # We LEFT JOIN Attendance so we still include users without an Attendance record.

        # Subquery to check for paid status
        
        # This subquery determines if an offer's payment is confirmed by replicating the logic of the
        # Offer.is_paid property, which in turn depends on the Invoice.current_payment_status property.

        # 1. Subquery to get the latest payment status for each invoice
        latest_payment_status_subquery = (
            db.session.query(
                InvoicePaymentStatus.invoice_id,
                func.max(InvoicePaymentStatus.created_at_unix).label('max_created_at')
            )
            .group_by(InvoicePaymentStatus.invoice_id)
            .subquery()
        )

        current_payment_status_subquery = (
            db.session.query(
                InvoicePaymentStatus.invoice_id,
                InvoicePaymentStatus.payment_status
            )
            .join(
                latest_payment_status_subquery,
                and_(
                    InvoicePaymentStatus.invoice_id == latest_payment_status_subquery.c.invoice_id,
                    InvoicePaymentStatus.created_at_unix == latest_payment_status_subquery.c.max_created_at
                )
            )
            .subquery()
        )

        # 2. Subquery to determine if an offer is considered paid.
        # An offer is paid if all its 'valid' invoices are paid.
        # A 'valid' invoice is one with a status of UNPAID, PAID, or FAILED.
        offer_paid_status_subquery = (
            db.session.query(
                OfferInvoice.offer_id,
                case([
                    (
                        func.count(OfferInvoice.invoice_id) == 0, True
                    ),
                    (
                        func.sum(case([
                            (current_payment_status_subquery.c.payment_status == PaymentStatus.PAID.value, 1)
                        ], else_=0)) == func.count(OfferInvoice.invoice_id),
                        True
                    )
                ], else_=False).label('is_payment_confirmed')
            )
            .join(current_payment_status_subquery, current_payment_status_subquery.c.invoice_id == OfferInvoice.invoice_id)
            .filter(current_payment_status_subquery.c.payment_status.in_([
                PaymentStatus.UNPAID.value,
                PaymentStatus.PAID.value,
                PaymentStatus.FAILED.value
            ]))
            .group_by(OfferInvoice.offer_id)
            .subquery()
        )



        offers = (
            db.session.query(AppUser, Attendance)
            .join(Offer, Offer.user_id == AppUser.id)
            .outerjoin(offer_paid_status_subquery, offer_paid_status_subquery.c.offer_id == Offer.id)
            .outerjoin(
                Attendance,
                and_(
                    Attendance.user_id == AppUser.id,
                    Attendance.event_id == event_id,
                ),
            )
            .filter(
                Offer.event_id == event_id,
                Offer.candidate_response == True,
                case(
                    [
                        (Offer.payment_required == False, True),
                        (Offer.payment_required == True, offer_paid_status_subquery.c.is_payment_confirmed == True)
                    ],
                    else_=False
                )
            )
        )

        invited = (
            db.session.query(AppUser, Attendance)
            .join(InvitedGuest, InvitedGuest.user_id == AppUser.id)
            .outerjoin(
                Attendance,
                and_(
                    Attendance.user_id == AppUser.id,
                    Attendance.event_id == event_id,
                ),
            )
            .filter(
                InvitedGuest.event_id == event_id,
            )
        )

        query = offers.union(invited)
        return query.all()



    @staticmethod
    def get_confirmed_attendees(event_id):
        return (db.session.query(Attendance)
                    .filter_by(event_id=event_id, confirmed=True))

    @staticmethod
    def get_confirmed_attendee_users(event_id):
        return (db.session.query(AppUser)
                    .join(Attendance, Attendance.user_id == AppUser.id)
                    .filter_by(event_id=event_id, confirmed=True))

    @staticmethod
    def get_invited_guest(event_id, user_id):
        return (db.session.query(InvitedGuest)
                .filter_by(event_id=event_id, user_id=user_id)
                .first())

    @staticmethod
    def get_offer(event_id, user_id):
        return (db.session.query(Offer)
                .filter_by(event_id=event_id, user_id=user_id)
                .first())


class IndemnityRepository():
    @staticmethod
    def get(event_id):
        return (db.session.query(EventIndemnity)
                .filter_by(event_id=event_id)
                .first())