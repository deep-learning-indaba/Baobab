from app import db
from app.applicationModel.models import ApplicationForm
from app.events.models import EventRole
from app.responses.models import Response
from app.users.models import AppUser
from app.invitedGuest.models import InvitedGuest
from app.organisation.models import Organisation
from sqlalchemy import func
from sqlalchemy import or_

class UserRepository():

    @staticmethod
    def get_by_id(user_id):
        return db.session.query(AppUser).get(user_id)

    @staticmethod
    def get_by_id_with_response(user_id):
        return db.session.query(AppUser, Response)\
                         .filter_by(id=user_id)\
                         .join(Response, Response.user_id==AppUser.id)\
                         .first()

    @staticmethod
    def get_by_email(email, organisation_id):
        return db.session.query(AppUser)\
            .filter(func.lower(AppUser.email) == func.lower(email))\
            .filter_by(organisation_id=organisation_id).first()

    @staticmethod
    def get_by_event_admin(user_id, event_admin_user_id):
        return db.session.query(AppUser, Response)\
                         .filter_by(id=user_id)\
                         .join(Response, Response.user_id==AppUser.id)\
                         .join(ApplicationForm, ApplicationForm.id==Response.application_form_id)\
                         .join(EventRole, EventRole.event_id==ApplicationForm.event_id)\
                         .filter_by(user_id=event_admin_user_id, role='admin')\
                         .first()

    @staticmethod
    def _application_responses(event_id):
        """(response model, query of the event's application responses).

        Mirrors app/events/status.py: an event with a form_type='application'
        form in the forms system takes its applications from there; otherwise
        from the legacy application form.
        """
        from app.forms.models import Form, FormResponse
        form_ids = [row[0] for row in db.session.query(Form.id)
                    .filter_by(event_id=event_id, form_type='application').all()]
        if form_ids:
            return FormResponse, db.session.query(FormResponse).filter(FormResponse.form_id.in_(form_ids))
        return Response, (db.session.query(Response)
                          .join(ApplicationForm, ApplicationForm.id == Response.application_form_id)
                          .filter(ApplicationForm.event_id == event_id))

    @staticmethod
    def get_all_with_unsubmitted_response_for(event_id):
        """Active users with an application for this event that is neither
        submitted nor withdrawn - and no submitted one."""
        model, responses = UserRepository._application_responses(event_id)
        unsubmitted = responses.filter(model.is_submitted == False, model.is_withdrawn == False) \
            .with_entities(model.user_id)
        submitted = responses.filter(model.is_submitted == True).with_entities(model.user_id)
        return (db.session.query(AppUser)
                .filter(AppUser.active == True, AppUser.is_deleted == False,
                        AppUser.id.in_(unsubmitted.subquery()),
                        ~AppUser.id.in_(submitted.subquery()))
                .order_by(AppUser.id)
                .all())

    @staticmethod
    def get_all_without_response_for(event):
        """Active users of the event's organisation with no application for it
        at all. Invited guests are left out: they don't apply."""
        model, responses = UserRepository._application_responses(event.id)
        applied = responses.with_entities(model.user_id)
        guests = db.session.query(InvitedGuest.user_id).filter(InvitedGuest.event_id == event.id)
        return (db.session.query(AppUser)
                .filter(AppUser.active == True, AppUser.is_deleted == False,
                        AppUser.organisation_id == event.organisation_id,
                        ~AppUser.id.in_(applied.subquery()),
                        ~AppUser.id.in_(guests.subquery()))
                .order_by(AppUser.id)
                .all())

    @staticmethod
    def get_all_with_responses_for(event_id):
        return db.session.query(AppUser, Response)\
                         .filter_by(active=True, is_deleted=False)\
                         .join(Response, Response.user_id==AppUser.id)\
                         .join(ApplicationForm, ApplicationForm.id==Response.application_form_id)\
                         .filter_by(event_id=event_id)\
                         .all()

    @staticmethod
    def get_all_with_responses_or_invited_guests_for(event_id):
        return (
            db.session.query(AppUser, Response, InvitedGuest)
                .filter_by(active=True, is_deleted=False)
                .join(Response, Response.user_id==AppUser.id, isouter=True)
                .join(InvitedGuest, InvitedGuest.user_id==AppUser.id, isouter=True)
                .filter(or_(InvitedGuest != None, Response != None))
                .join(ApplicationForm, ApplicationForm.id==Response.application_form_id, isouter=True)

                # Since both InvitedGuest and ApplicationForm have an event_id we need to include
                # both in the filter.
                .filter(or_(InvitedGuest.event_id==event_id, ApplicationForm.event_id==event_id))
        ).all()
