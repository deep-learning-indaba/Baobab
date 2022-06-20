from app import db

class Organisation(db.Model):

    __tablename__ = "organisation"

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    system_name = db.Column(db.String(50), nullable=False)
    small_logo = db.Column(db.String(100), nullable=False)
    large_logo = db.Column(db.String(100), nullable=False)
    icon_logo = db.Column(db.String(100), nullable=False)
    domain = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(100), nullable=False)
    email_from = db.Column(db.String(100), nullable=True)
    system_url = db.Column(db.String(100), nullable=False)
    privacy_policy = db.Column(db.String(100), nullable=False)
    languages = db.Column(db.JSON(), nullable=False)
    iso_currency_code = db.Column(db.String(3), nullable=True)
    stripe_api_publishable_key = db.Column(db.String(200), nullable=True)
    stripe_api_secret_key = db.Column(db.String(200), nullable=True)
    stripe_webhook_secret_key = db.Column(db.String(200), nullable=True)

    events = db.relationship('Event')

    def __init__(self, name, system_name, small_logo, large_logo, icon_logo, domain, url, email_from, system_url, privacy_policy, languages):
        self.name = name
        self.small_logo = small_logo
        self.large_logo = large_logo
        self.icon_logo = icon_logo
        self.domain = domain
        self.system_name = system_name
        self.url = url
        self.email_from = email_from
        self.system_url = system_url
        self.privacy_policy = privacy_policy
        self.languages = languages

    def can_accept_payments(self) -> bool:
        return (
            self.iso_currency_code is not None and
            self.stripe_api_publishable_key is not None and
            self.stripe_api_secret_key is not None and
            self.stripe_webhook_secret_key is not None
        )
    
    def set_currency(self, iso_currency_code):
        self.iso_currency_code = iso_currency_code

    def set_stripe_keys(self, publishable_key, secret_key, webhook_secret_key):
        self.stripe_api_publishable_key = publishable_key
        self.stripe_api_secret_key = secret_key
        self.stripe_webhook_secret_key = webhook_secret_key