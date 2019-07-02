from app import db


class InvitationTemplate(db.Model):

    __tablename__ = "invitation_template"

    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey("event.id"), nullable=False)
    template_path = db.Column(db.String(), nullable=False)
    send_for_travel_award_only = db.Column(db.Boolean(), nullable=False)
    send_for_accommodation_award_only = db.Column(db.Boolean(), nullable=False)
    send_for_both_travel_accommodation = db.Column(db.Boolean(), nullable=False)


class InvitationLetterRequest(db.Model):

    __tablename__ = "invitation_letter_request"

    id = db.Column(db.Integer(), primary_key=True)
    registration_id = db.Column(db.Integer(), db.ForeignKey("registration.id"), nullable=False)
    event_id = db.Column(db.Integer(), db.ForeignKey("event.id"), nullable=False)
    work_address = db.Column(db.String(), nullable=False)
    addressed_to = db.Column(db.String(), nullable=False)
    residential_address = db.Column(db.String(), nullable=False)
    passport_name = db.Column(db.String(), nullable=False)
    passport_no = db.Column(db.String(), nullable=False)
    passport_issued_by = db.Column(db.String(), nullable=False)
    passport_expiry_date = db.Column(db.DateTime(), nullable=False)
    invitation_letter_sent_at = db.Column(db.String(), nullable=False)
    to_date = db.Column(db.DateTime(), nullable=False)
    from_date = db.Column(db.DateTime(), nullable=False)
