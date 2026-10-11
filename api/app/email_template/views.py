"""View models: the only data an email template can see.

Each view declares its fields - name, type, a description in every UI language
and a sample value - and builds a plain dict from an ORM object. Nothing that
isn't declared reaches a template. That declaration also drives the editor's
autocomplete and field browser, the sample data previews render against, and
save-time validation of the paths a template uses.

Never put an ORM object (or anything with attributes worth reading) in a value.
Liquid can't read Python attributes, but a relationship handed over as a dict
would expose whatever it contains - an Organisation's Stripe keys, a user's
password hash.
"""
from datetime import date, datetime
from decimal import Decimal

from app.email_template.engine import MarkdownText, format_date, format_money
from app.utils.language import translation_for


STRING = 'string'
NUMBER = 'number'
BOOLEAN = 'boolean'
DATE = 'date'
URL = 'url'
MARKDOWN = 'markdown'

SCALAR_TYPES = (STRING, NUMBER, BOOLEAN, DATE, URL, MARKDOWN)


class LocalDate(datetime):
    """A datetime that prints as a date in the recipient's language, so
    ``{{ offer.expiry_date }}`` reads well without a filter. The ``date`` filter
    still accepts it for a custom format."""

    language = 'en'

    @classmethod
    def of(cls, value, language):
        if value is None:
            return None
        if isinstance(value, str):
            value = datetime.fromisoformat(value.rstrip('Z'))
        if not isinstance(value, datetime) and isinstance(value, date):
            value = datetime(value.year, value.month, value.day)
        local = cls(value.year, value.month, value.day, value.hour, value.minute, value.second)
        local.language = language
        return local

    def __str__(self):
        return format_date(self, None, self.language)


def _text(en, fr):
    return {'en': en, 'fr': fr}


class Field:
    def __init__(self, type_, description, sample=None, nullable=False):
        # type_ is a scalar type name, a View subclass, or ListOf(...).
        self.type = type_
        self.description = description
        self.sample = sample
        self.nullable = nullable


class ListOf:
    def __init__(self, item):
        self.item = item


def _is_view(type_):
    return isinstance(type_, type) and issubclass(type_, View)


class BuildContext:
    """What every view needs besides its source object: the language to render
    in and the organisation whose system URL links are built on."""

    def __init__(self, language, organisation, event=None):
        self.language = language
        self.organisation = organisation
        self.event = event

    @property
    def base_url(self):
        url = (self.organisation.system_url or '').strip().rstrip('/') if self.organisation else ''
        # Links must be absolute to work in an email client (and to pass the
        # button's scheme check); some organisations store a bare host.
        if url and '://' not in url:
            url = 'https://' + url
        return url

    def url(self, path):
        return '{}/{}'.format(self.base_url, path.lstrip('/'))

    def event_url(self, event, path=''):
        return self.url('{}/{}'.format(event.key, path).rstrip('/'))


def _coerce(field, value, ctx):
    if value is None:
        return None
    if field.type == DATE:
        return LocalDate.of(value, ctx.language)
    if field.type == NUMBER and isinstance(value, Decimal):
        return float(value)
    if field.type == MARKDOWN:
        return MarkdownText(value)
    return value


class View:
    """Base class. Subclasses set ``fields`` and implement ``values``."""

    label = _text('', '')
    fields = {}

    @classmethod
    def values(cls, source, ctx):
        raise NotImplementedError

    @classmethod
    def build(cls, source, ctx):
        if source is None:
            return None
        raw = cls.values(source, ctx)
        missing = set(cls.fields) - set(raw)
        if missing:
            raise KeyError('{} did not provide {}'.format(cls.__name__, ', '.join(sorted(missing))))
        result = {}
        for name, field in cls.fields.items():
            value = raw[name]
            if isinstance(field.type, ListOf):
                item = field.type.item
                value = [item.build(v, ctx) if _is_view(item) else _coerce(Field(item, None), v, ctx)
                         for v in (value or [])]
            elif _is_view(field.type):
                value = field.type.build(value, ctx)
            else:
                value = _coerce(field, value, ctx)
            result[name] = value
        return result

    @classmethod
    def sample(cls, ctx):
        result = {}
        for name, field in cls.fields.items():
            if isinstance(field.type, ListOf):
                item = field.type.item
                if _is_view(item):
                    result[name] = [item.sample(ctx) for _ in range(field.sample or 2)]
                else:
                    result[name] = [_coerce(Field(item, None), v, ctx) for v in (field.sample or [])]
            elif _is_view(field.type):
                result[name] = field.type.sample(ctx)
            else:
                result[name] = _coerce(field, field.sample, ctx)
        return result

    @classmethod
    def schema(cls, language):
        def describe(field):
            entry = {
                'description': field.description.get(language) or field.description.get('en'),
                'nullable': field.nullable,
            }
            if isinstance(field.type, ListOf):
                entry['type'] = 'list'
                item = field.type.item
                entry['item'] = ({'type': 'object', 'fields': item.schema(language)['fields']}
                                 if _is_view(item) else {'type': item})
            elif _is_view(field.type):
                entry['type'] = 'object'
                entry['fields'] = field.type.schema(language)['fields']
            else:
                entry['type'] = field.type
                if field.sample is not None and field.type != MARKDOWN:
                    entry['sample'] = field.sample
            return entry

        return {
            'label': cls.label.get(language) or cls.label.get('en'),
            'fields': {name: describe(field) for name, field in cls.fields.items()},
        }


# --------------------------------------------------------------------------- people

class Recipient:
    """Someone to email who may not have a Baobab account (a referee)."""

    def __init__(self, email, firstname='', lastname='', title='', language='en'):
        self.email = email
        self.firstname = firstname or ''
        self.lastname = lastname or ''
        self.user_title = title or ''
        self.language = language

    @property
    def full_name(self):
        return ' '.join(part for part in (self.firstname, self.lastname) if part)

    @property
    def formal_name(self):
        return ' '.join(part for part in (self.user_title, self.firstname, self.lastname) if part)


class PersonView(View):
    label = _text('Person', 'Personne')
    fields = {
        'name': Field(STRING, _text('Full name', 'Nom complet'), 'Thandi Ndlovu'),
        'firstname': Field(STRING, _text('First name', 'Prénom'), 'Thandi'),
        'lastname': Field(STRING, _text('Last name', 'Nom de famille'), 'Ndlovu'),
        'title': Field(STRING, _text('Title, e.g. Dr', 'Titre, p. ex. Dr'), 'Dr'),
        'salutation': Field(STRING, _text('Title, first name and last name',
                                          'Titre, prénom et nom'), 'Dr Thandi Ndlovu'),
        'email': Field(STRING, _text('Email address', 'Adresse électronique'), 'thandi@example.org'),
    }

    @classmethod
    def values(cls, person, ctx):
        return {
            'name': person.full_name,
            'firstname': person.firstname or '',
            'lastname': person.lastname or '',
            'title': person.user_title or '',
            'salutation': person.formal_name,
            'email': person.email,
        }


class RecipientView(PersonView):
    label = _text('Recipient', 'Destinataire')


# --------------------------------------------------------------------------- organisation / event

class OrganisationView(View):
    label = _text('Organisation', 'Organisation')
    fields = {
        'name': Field(STRING, _text('Organisation name', "Nom de l'organisation"), 'Deep Learning Indaba'),
        'system_name': Field(STRING, _text('Name of this system', 'Nom de ce système'), 'Baobab'),
        'url': Field(URL, _text("Organisation's website", "Site web de l'organisation"),
                     'https://deeplearningindaba.com'),
        'system_url': Field(URL, _text('Link to this system', 'Lien vers ce système'),
                            'https://baobab.deeplearningindaba.com'),
        'email_from': Field(STRING, _text('Address emails are sent from', "Adresse d'envoi des courriels"),
                            'info@deeplearningindaba.com', nullable=True),
    }

    @classmethod
    def values(cls, organisation, ctx):
        return {
            'name': organisation.name,
            'system_name': organisation.system_name,
            'url': organisation.url,
            'system_url': ctx.base_url,
            'email_from': organisation.email_from,
        }


class EventView(View):
    label = _text('Event', 'Événement')
    fields = {
        'name': Field(STRING, _text('Event name', "Nom de l'événement"), 'Deep Learning Indaba 2026'),
        'description': Field(STRING, _text('Event description', "Description de l'événement"),
                             'the Deep Learning Indaba 2026 in Kigali, Rwanda'),
        'key': Field(STRING, _text('Short code used in links', 'Code court utilisé dans les liens'), 'indaba2026'),
        'url': Field(URL, _text("Event's page in this system", "Page de l'événement dans ce système"),
                     'https://baobab.deeplearningindaba.com/indaba2026'),
        'registration_url': Field(URL, _text('Link to the registration form', "Lien vers le formulaire d'inscription"),
                                  'https://baobab.deeplearningindaba.com/indaba2026/registration'),
        'website_url': Field(URL, _text("Event's own website", "Site web de l'événement"),
                             'https://deeplearningindaba.com/2026'),
        'email_from': Field(STRING, _text("Event's contact address", "Adresse de contact de l'événement"),
                            'info@deeplearningindaba.com'),
        'start_date': Field(DATE, _text('First day of the event', "Premier jour de l'événement"), '2026-08-17'),
        'end_date': Field(DATE, _text('Last day of the event', "Dernier jour de l'événement"),
                          '2026-08-22', nullable=True),
        'application_close': Field(DATE, _text('Application deadline', 'Date limite de candidature'),
                                   '2026-04-30', nullable=True),
        'registration_close': Field(DATE, _text('Registration deadline', "Date limite d'inscription"),
                                    '2026-07-15', nullable=True),
        'is_registration_open': Field(BOOLEAN, _text('Whether registration is currently open',
                                                     "Si l'inscription est actuellement ouverte"), True),
        'type': Field(STRING, _text('Kind of event: event, award, call or journal',
                                    "Type d'événement : event, award, call ou journal"), 'event'),
    }

    @classmethod
    def values(cls, event, ctx):
        return {
            'name': event.get_name(ctx.language) or '',
            'description': event.get_description(ctx.language) or '',
            'key': event.key,
            'url': ctx.event_url(event),
            'registration_url': ctx.event_url(event, 'registration'),
            'website_url': event.url,
            'email_from': event.email_from,
            'start_date': event.start_date,
            'end_date': event.end_date,
            'application_close': event.application_close,
            'registration_close': event.registration_close,
            'is_registration_open': bool(event.is_registration_open),
            'type': event.event_type.value if event.event_type else '',
        }


# --------------------------------------------------------------------------- offers

class TagView(View):
    label = _text('Tag', 'Étiquette')
    fields = {
        'name': Field(STRING, _text('Name', 'Nom'), 'Travel grant'),
        'description': Field(STRING, _text('Description', 'Description'),
                             'Return flights to the event', nullable=True),
    }

    @classmethod
    def values(cls, tag, ctx):
        translation = translation_for(tag, ctx.language, 'en')
        return {
            'name': translation.name if translation else '',
            'description': (translation.description if translation else None) or None,
        }


class FeeView(View):
    label = _text('Fee', 'Frais')
    fields = {
        'name': Field(STRING, _text('Fee name', 'Nom des frais'), 'Registration fee'),
        'description': Field(STRING, _text('Fee description', 'Description des frais'), None, nullable=True),
        'amount': Field(NUMBER, _text('Amount', 'Montant'), 1500.0),
        'currency': Field(STRING, _text('Currency code', 'Code de la devise'), 'ZAR'),
        'formatted': Field(STRING, _text('Amount with currency, e.g. 1,500.00 ZAR',
                                         'Montant avec devise, p. ex. 1 500,00 ZAR'), '1,500.00 ZAR'),
    }

    @classmethod
    def values(cls, fee, ctx):
        return {
            'name': fee.name,
            'description': fee.description,
            'amount': fee.amount,
            'currency': fee.iso_currency_code,
            'formatted': format_money(fee.amount, fee.iso_currency_code, ctx.language),
        }


class OfferView(View):
    label = _text('Offer', 'Offre')
    fields = {
        'offer_date': Field(DATE, _text('Date the offer was made', "Date de l'offre"), '2026-05-20'),
        'expiry_date': Field(DATE, _text('Last day to accept the offer', "Dernier jour pour accepter l'offre"),
                             '2026-06-05'),
        'payment_required': Field(BOOLEAN, _text('Whether a registration fee is payable',
                                                 "Si des frais d'inscription sont exigés"), True),
        'fee': Field(FeeView, _text('The registration fee, if one is payable',
                                    "Les frais d'inscription, s'il y en a"), nullable=True),
        'grants': Field(ListOf(TagView), _text('Grants included in the offer', "Bourses incluses dans l'offre"),
                        2),
        'notes': Field(ListOf(TagView), _text("Notes attached to the offer", "Notes jointes à l'offre"), 1),
        'url': Field(URL, _text('Link to view, accept or decline the offer',
                                "Lien pour consulter, accepter ou refuser l'offre"),
                     'https://baobab.deeplearningindaba.com/indaba2026/offer'),
        'is_paid': Field(BOOLEAN, _text('Whether the fee has been paid', 'Si les frais ont été payés'), False),
        'invoice_number': Field(STRING, _text('Invoice number, if an invoice was issued',
                                              'Numéro de facture, si une facture a été émise'),
                                'B042', nullable=True),
    }

    @classmethod
    def values(cls, offer, ctx):
        from app.tags.models import TagType
        tags = [offer_tag.tag for offer_tag in offer.offer_tags]
        payment_required = bool(offer.payment_required)
        return {
            'offer_date': offer.offer_date,
            'expiry_date': offer.expiry_date,
            'payment_required': payment_required,
            'fee': offer.event_fee if payment_required and offer.event_fee else None,
            'grants': [tag for tag in tags if tag.tag_type == TagType.GRANT],
            'notes': [tag for tag in tags if tag.tag_type == TagType.OFFER_NOTE],
            'url': ctx.event_url(offer.event, 'offer'),
            'is_paid': bool(offer.is_paid) if payment_required else False,
            'invoice_number': offer.invoice_number,
        }


class InvoiceView(View):
    label = _text('Invoice', 'Facture')
    fields = {
        'number': Field(STRING, _text('Invoice number', 'Numéro de facture'), 'B042'),
        'due_date': Field(DATE, _text('Payment due date', "Date d'échéance du paiement"), '2026-06-05'),
        'total': Field(STRING, _text('Total amount with currency', 'Montant total avec devise'), '1,500.00 ZAR'),
        'payment_url': Field(URL, _text('Link to pay the invoice', 'Lien pour payer la facture'),
                             'https://baobab.deeplearningindaba.com/payment/42'),
    }

    @classmethod
    def values(cls, invoice, ctx):
        return {
            'number': invoice.invoice_number,
            'due_date': invoice.due_date,
            'total': format_money(invoice.total_amount, invoice.iso_currency_code, ctx.language),
            'payment_url': ctx.url('payment/{}'.format(invoice.id)),
        }


# --------------------------------------------------------------------------- applications

class AnswerView(View):
    label = _text('Answer', 'Réponse')
    fields = {
        'question': Field(STRING, _text('Question', 'Question'), 'What is your current role?'),
        'answer': Field(STRING, _text('Answer given', 'Réponse donnée'), 'PhD student'),
    }

    @classmethod
    def values(cls, pair, ctx):
        return {'question': pair['question'], 'answer': pair['answer']}


class SectionView(View):
    label = _text('Form section', 'Section du formulaire')
    fields = {
        'name': Field(STRING, _text('Section name', 'Nom de la section'), 'About you'),
        'answers': Field(ListOf(AnswerView), _text('Questions answered in this section',
                                                   'Questions répondues dans cette section'), 2),
    }

    @classmethod
    def values(cls, section, ctx):
        return {'name': section['name'], 'answers': section['answers']}


class ResponseView(View):
    """Built from {'applicant': AppUser, 'sections': [...]} - see
    app.utils.strings.response_answer_sections."""
    label = _text('Application', 'Candidature')
    fields = {
        'applicant': Field(PersonView, _text('The person who applied', 'La personne qui a postulé')),
        'sections': Field(ListOf(SectionView), _text('Answers, grouped by form section',
                                                     'Réponses, regroupées par section'), 2),
    }

    @classmethod
    def values(cls, response, ctx):
        return {'applicant': response['applicant'], 'sections': response['sections']}


class RegistrationView(View):
    """Built from {'confirmed': bool, 'answers': [...]}."""
    label = _text('Registration', 'Inscription')
    fields = {
        'confirmed': Field(BOOLEAN, _text('Whether the place is confirmed (nothing left to pay)',
                                          'Si la place est confirmée (plus rien à payer)'), True),
        'answers': Field(ListOf(AnswerView), _text('Answers given on the registration form',
                                                   "Réponses au formulaire d'inscription"), 3),
        'url': Field(URL, _text('Link to the registration form', "Lien vers le formulaire d'inscription"),
                     'https://baobab.deeplearningindaba.com/indaba2026/registration'),
    }

    @classmethod
    def values(cls, registration, ctx):
        return {
            'confirmed': bool(registration.get('confirmed')),
            'answers': registration.get('answers') or [],
            'url': ctx.event_url(ctx.event, 'registration'),
        }


class FormView(View):
    label = _text('Form', 'Formulaire')
    fields = {
        'name': Field(STRING, _text('Form name', 'Nom du formulaire'), 'Travel information'),
    }

    @classmethod
    def values(cls, form, ctx):
        return {'name': form['name']}


class ReferenceRequestView(View):
    label = _text('Reference request', 'Demande de référence')
    fields = {
        'url': Field(URL, _text('Link where the referee uploads their letter',
                                'Lien où le référent téléverse sa lettre'),
                     'https://baobab.deeplearningindaba.com/reference/3f2c9a'),
        'relation': Field(STRING, _text("Referee's relationship to the candidate",
                                        'Lien du référent avec le candidat'), 'Supervisor'),
        'deadline': Field(DATE, _text('Date the reference is due', 'Date limite de la référence'),
                          '2026-04-30', nullable=True),
    }

    @classmethod
    def values(cls, reference_request, ctx):
        return {
            'url': ctx.url('reference/{}'.format(reference_request.token)),
            'relation': reference_request.relation or '',
            'deadline': ctx.event.application_close if ctx.event else None,
        }


class NominatorView(View):
    label = _text('Nominator', 'Proposant')
    fields = {
        'name': Field(STRING, _text("Nominator's name", 'Nom du proposant'), 'Prof. Amina Diallo'),
    }

    @classmethod
    def values(cls, name, ctx):
        return {'name': name}


class CandidateView(View):
    label = _text('Candidate', 'Candidat')
    fields = {
        'name': Field(STRING, _text("Candidate's name", 'Nom du candidat'), 'Dr Thandi Ndlovu'),
        'firstname': Field(STRING, _text("Candidate's first name", 'Prénom du candidat'), 'Thandi'),
    }

    @classmethod
    def values(cls, candidate, ctx):
        return {'name': candidate['name'], 'firstname': candidate['firstname']}


class ReviewAssignmentView(View):
    label = _text('Review assignment', 'Attribution de révisions')
    fields = {
        'count': Field(NUMBER, _text('Number of reviews just assigned', 'Nombre de révisions attribuées'), 5),
        'url': Field(URL, _text('Link to the review list', 'Lien vers la liste des révisions'),
                     'https://baobab.deeplearningindaba.com/indaba2026/reviewlist'),
    }

    @classmethod
    def values(cls, count, ctx):
        return {'count': count, 'url': ctx.event_url(ctx.event, 'reviewlist')}


# --------------------------------------------------------------------------- guests / attendance

class GuestView(View):
    label = _text('Invited guest', 'Invité')
    fields = {
        'role': Field(STRING, _text("Guest's role, e.g. Speaker", "Rôle de l'invité, p. ex. Speaker"), 'Speaker'),
        'registration_url': Field(URL, _text('Link to the guest registration form',
                                             "Lien vers le formulaire d'inscription des invités"),
                                  'https://baobab.deeplearningindaba.com/indaba2026/registration'),
    }

    @classmethod
    def values(cls, role, ctx):
        return {'role': role or '', 'registration_url': ctx.event_url(ctx.event, 'registration')}


class AccountSetupView(View):
    label = _text('Account setup', 'Création du compte')
    fields = {
        'set_password_url': Field(URL, _text('Link to set a password (contains a one-time code)',
                                             'Lien pour définir un mot de passe (contient un code à usage unique)'),
                                  'https://baobab.deeplearningindaba.com/resetPassword?resetToken=abc123'),
        'profile_url': Field(URL, _text('Link to the profile page', 'Lien vers la page de profil'),
                             'https://baobab.deeplearningindaba.com/profile'),
    }

    @classmethod
    def values(cls, reset_code, ctx):
        return {
            'set_password_url': ctx.url('resetPassword?resetToken={}'.format(reset_code)),
            'profile_url': ctx.url('profile'),
        }


class IndemnityView(View):
    label = _text('Indemnity', 'Décharge')
    fields = {
        'text': Field(STRING, _text('Full text of the signed form', 'Texte complet du formulaire signé'),
                      'I, Thandi Ndlovu, agree to ...'),
    }

    @classmethod
    def values(cls, text, ctx):
        return {'text': text}


class DocumentView(View):
    label = _text('Document', 'Document')
    fields = {
        'name': Field(STRING, _text('Document name', 'Nom du document'), 'Invitation letter'),
        'filename': Field(STRING, _text('Attached file name', 'Nom du fichier joint'), 'invitation-letter.pdf'),
        'url': Field(URL, _text('Link to download it from this system',
                                'Lien pour le télécharger depuis ce système'),
                     'https://baobab.deeplearningindaba.com/indaba2026/documents'),
    }

    @classmethod
    def values(cls, document, ctx):
        return {
            'name': document['name'],
            'filename': document['filename'],
            'url': ctx.event_url(ctx.event, 'documents'),
        }


# --------------------------------------------------------------------------- accounts

class LinkView(View):
    label = _text('Link', 'Lien')
    fields = {
        'url': Field(URL, _text('The link (contains a one-time code)', 'Le lien (contient un code à usage unique)'),
                     'https://baobab.deeplearningindaba.com/verifyEmail?token=abc123'),
    }

    @classmethod
    def values(cls, url, ctx):
        return {'url': url}


class MessageView(View):
    label = _text('Message', 'Message')
    fields = {
        'subject': Field(STRING, _text('Subject the sender wrote', "Objet rédigé par l'expéditeur"),
                         'Your visa appointment'),
        'body': Field(MARKDOWN, _text('Message the sender wrote', "Message rédigé par l'expéditeur"),
                      'Please bring your passport to the registration desk.'),
    }

    @classmethod
    def values(cls, message, ctx):
        return {'subject': message['subject'], 'body': message['body']}
