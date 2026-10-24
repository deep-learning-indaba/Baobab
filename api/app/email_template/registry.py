"""Every kind of email the system sends, and what each one's template can use.

Every template also gets ``recipient`` and ``organisation``, and ``event`` when
the type is event-scoped; ``context`` lists what a type adds on top. Adding a
type means adding it here, writing its defaults in ``defaults/<key>.<lang>.md``,
and calling ``queue_email('<key>', ...)`` with exactly the declared context.
"""
from app.email_template import views as v


class Scope:
    #: Not tied to an event (account emails). Only organisation-level
    #: templates and layouts apply, and only system admins may edit them.
    ORGANISATION = 'organisation'
    EVENT = 'event'


class Group:
    ACCOUNT = 'account'
    APPLICATIONS = 'applications'
    REFERENCES = 'references'
    REVIEWS = 'reviews'
    OUTCOMES = 'outcomes'
    REGISTRATION = 'registration'
    GUESTS = 'guests'
    ATTENDANCE = 'attendance'
    DOCUMENTS = 'documents'
    MESSAGES = 'messages'


class EmailType:
    def __init__(self, key, name, description, group, scope, context=None, sensitive=False,
                 default_key=None):
        self.key = key
        self.name = name
        self.description = description
        self.group = group
        self.scope = scope
        # {name: View subclass}; a View may be wrapped in Optional to allow None.
        self.context = context or {}
        # The body can carry a login, password-reset or verification code. Such
        # bodies are hidden from admins and deleted once the message is sent.
        self.sensitive = sensitive
        # Defaults are read from this key's files (lets an alias share them).
        self.default_key = default_key or key

    @property
    def is_event_scoped(self):
        return self.scope == Scope.EVENT

    def implicit_context(self):
        implicit = {'recipient': v.RecipientView, 'organisation': v.OrganisationView}
        if self.is_event_scoped:
            implicit['event'] = v.EventView
        return implicit

    def full_context(self):
        return dict(self.implicit_context(), **{name: _view(spec) for name, spec in self.context.items()})

    def nullable(self, name):
        return isinstance(self.context.get(name), Optional)

    def alias(self, key):
        """The same type under another key - see DOCUMENT_EMAIL_TYPE."""
        return EmailType(key, self.name, self.description, self.group, self.scope, self.context,
                         self.sensitive, default_key=self.default_key)


class Optional:
    """Marks a context entry that may be None, e.g. a nominator on a self-nomination."""

    def __init__(self, view):
        self.view = view


def _view(spec):
    return spec.view if isinstance(spec, Optional) else spec


def _t(en, fr):
    return {'en': en, 'fr': fr}


_TYPES = [
    # ------------------------------------------------------------------ account
    EmailType('verify-email', _t('Verify email address', "Vérification de l'adresse électronique"),
              _t('Sent when someone creates an account or changes their email address.',
                 "Envoyé lors de la création d'un compte ou d'un changement d'adresse électronique."),
              Group.ACCOUNT, Scope.ORGANISATION, {'verification': v.LinkView}, sensitive=True),
    EmailType('password-reset', _t('Password reset', 'Réinitialisation du mot de passe'),
              _t('Sent when someone asks to reset their password.',
                 'Envoyé lorsqu’une personne demande à réinitialiser son mot de passe.'),
              Group.ACCOUNT, Scope.ORGANISATION, {'reset': v.LinkView}, sensitive=True),

    # ------------------------------------------------------------------ applications
    EmailType('application-submitted', _t('Application received', 'Candidature reçue'),
              _t('Sent to an applicant when they submit, with a copy of their answers.',
                 'Envoyé au candidat lorsqu’il soumet sa candidature, avec une copie de ses réponses.'),
              Group.APPLICATIONS, Scope.EVENT, {'response': v.ResponseView}),
    EmailType('withdrawal', _t('Application withdrawn', 'Candidature retirée'),
              _t('Sent when an applicant withdraws their application.',
                 'Envoyé lorsqu’un candidat retire sa candidature.'),
              Group.APPLICATIONS, Scope.EVENT),
    EmailType('form-response-deleted', _t('Form response deleted', 'Réponse au formulaire supprimée'),
              _t("Sent when an organiser deletes someone's response to a form.",
                 'Envoyé lorsqu’un organisateur supprime la réponse d’une personne à un formulaire.'),
              Group.APPLICATIONS, Scope.EVENT, {'form': v.FormView}),
    EmailType('application-not-submitted', _t('Reminder: application not submitted',
                                              'Rappel : candidature non soumise'),
              _t('Sent by an organiser to people who started an application but did not submit it.',
                 'Envoyé par un organisateur aux personnes ayant commencé une candidature sans la soumettre.'),
              Group.APPLICATIONS, Scope.EVENT),
    EmailType('application-not-started', _t('Reminder: application not started',
                                            'Rappel : candidature non commencée'),
              _t('Sent by an organiser to people with an account who have not started an application.',
                 'Envoyé par un organisateur aux personnes ayant un compte sans avoir commencé de candidature.'),
              Group.APPLICATIONS, Scope.EVENT),

    # ------------------------------------------------------------------ references
    EmailType('reference-request', _t('Reference request', 'Demande de référence'),
              _t('Sent to a referee an applicant has named, with a link to upload their letter.',
                 'Envoyé au référent désigné par un candidat, avec un lien pour téléverser sa lettre.'),
              Group.REFERENCES, Scope.EVENT,
              {'reference': v.ReferenceRequestView, 'candidate': v.CandidateView,
               'nominator': Optional(v.NominatorView)}),

    # ------------------------------------------------------------------ reviews
    EmailType('reviews-assigned', _t('Reviews assigned', 'Révisions attribuées'),
              _t('Sent to a reviewer when applications are assigned to them.',
                 'Envoyé à un évaluateur lorsque des candidatures lui sont attribuées.'),
              Group.REVIEWS, Scope.EVENT, {'reviews': v.ReviewAssignmentView}),

    # ------------------------------------------------------------------ outcomes / offers
    EmailType('outcome-rejected', _t('Application unsuccessful', 'Candidature non retenue'),
              _t('Sent when an application is rejected.', 'Envoyé lorsqu’une candidature est refusée.'),
              Group.OUTCOMES, Scope.EVENT),
    EmailType('outcome-waitlist', _t('Application waitlisted', "Candidature sur liste d'attente"),
              _t('Sent when an applicant is put on the waiting list.',
                 "Envoyé lorsqu’un candidat est placé sur la liste d'attente."),
              Group.OUTCOMES, Scope.EVENT),
    EmailType('offer', _t('Offer of a place', "Offre d'une place"),
              _t('Sent when an applicant is made an offer. Covers fees, grants and offer notes.',
                 "Envoyé lorsqu'une offre est faite à un candidat. Couvre les frais, bourses et notes."),
              Group.OUTCOMES, Scope.EVENT, {'offer': v.OfferView}),
    EmailType('offer-reset', _t('Offer reset', 'Offre réinitialisée'),
              _t('Sent when an organiser resets an offer so it can be answered again.',
                 "Envoyé lorsqu'un organisateur réinitialise une offre pour qu'on puisse y répondre à nouveau."),
              Group.OUTCOMES, Scope.EVENT, {'offer': v.OfferView}),
    EmailType('offer-paid', _t('Payment received', 'Paiement reçu'),
              _t('Sent when the registration fee for an offer has been paid.',
                 "Envoyé lorsque les frais d'inscription d'une offre ont été payés."),
              Group.OUTCOMES, Scope.EVENT, {'offer': v.OfferView}),
    EmailType('invoice', _t('Invoice', 'Facture'),
              _t('Sent with the invoice PDF attached when an invoice is issued for an offer.',
                 "Envoyé avec la facture en pièce jointe lorsqu'une facture est émise pour une offre."),
              Group.OUTCOMES, Scope.EVENT, {'invoice': v.InvoiceView, 'offer': v.OfferView}),

    # ------------------------------------------------------------------ registration
    EmailType('registration-received', _t('Registration received', 'Inscription reçue'),
              _t('Sent when someone completes the registration form, with a copy of their answers.',
                 "Envoyé lorsqu'une personne remplit le formulaire d'inscription, avec une copie de ses réponses."),
              Group.REGISTRATION, Scope.EVENT, {'registration': v.RegistrationView}),
    EmailType('registration-confirmed', _t('Registration confirmed', 'Inscription confirmée'),
              _t('Sent when a registration is confirmed (any payment completed).',
                 'Envoyé lorsqu’une inscription est confirmée (paiement effectué).'),
              Group.REGISTRATION, Scope.EVENT),

    # ------------------------------------------------------------------ guests
    EmailType('guest-invitation', _t('Guest invitation', "Invitation d'un invité"),
              _t('Sent when an existing user is added to the guest list.',
                 "Envoyé lorsqu'un utilisateur existant est ajouté à la liste des invités."),
              Group.GUESTS, Scope.EVENT, {'guest': v.GuestView}),
    EmailType('new-guest', _t('Guest invitation (new account)', "Invitation d'un invité (nouveau compte)"),
              _t('Sent when a guest is invited who has no account yet; includes a link to set a password.',
                 "Envoyé lorsqu'un invité sans compte est invité ; inclut un lien pour définir un mot de passe."),
              Group.GUESTS, Scope.EVENT, {'guest': v.GuestView, 'account': v.AccountSetupView},
              sensitive=True),
    EmailType('guest-removal', _t('Removed from guest list', 'Retiré de la liste des invités'),
              _t('Sent when a guest is removed from the guest list.',
                 "Envoyé lorsqu'un invité est retiré de la liste des invités."),
              Group.GUESTS, Scope.EVENT, {'guest': v.GuestView}),
    EmailType('guest-registration-confirmation', _t('Guest registration received',
                                                    "Inscription de l'invité reçue"),
              _t('Sent when a guest completes the guest registration form.',
                 "Envoyé lorsqu'un invité remplit le formulaire d'inscription des invités."),
              Group.GUESTS, Scope.EVENT, {'registration': v.RegistrationView}),

    # ------------------------------------------------------------------ attendance
    EmailType('attendance-confirmation', _t('Checked in', 'Enregistrement'),
              _t('Sent when someone is checked in at the event.',
                 "Envoyé lorsqu'une personne est enregistrée à l'événement."),
              Group.ATTENDANCE, Scope.EVENT),
    EmailType('indemnity-signed', _t('Indemnity signed', 'Décharge signée'),
              _t('Sent with a copy of the indemnity form when it is signed.',
                 'Envoyé avec une copie de la décharge lorsqu’elle est signée.'),
              Group.ATTENDANCE, Scope.EVENT, {'indemnity': v.IndemnityView}),

    # ------------------------------------------------------------------ documents
    EmailType('invitation-letter', _t('Invitation letter (legacy)', "Lettre d'invitation (ancienne version)"),
              _t('Sent with the letter attached by the legacy invitation letter generator.',
                 "Envoyé avec la lettre en pièce jointe par l'ancien générateur de lettres d'invitation."),
              Group.DOCUMENTS, Scope.EVENT),
    EmailType('generated-document', _t('Generated document', 'Document généré'),
              _t('Sent when a document is generated for someone. A document template can use its '
                 'own email instead of this one.',
                 "Envoyé lorsqu'un document est généré. Un modèle de document peut utiliser son propre courriel."),
              Group.DOCUMENTS, Scope.EVENT, {'document': v.DocumentView}),

    # ------------------------------------------------------------------ messages
    EmailType('admin-message', _t('Message from an organiser', "Message d'un organisateur"),
              _t('Wraps a one-off message an organiser writes to an individual.',
                 "Enveloppe un message ponctuel qu'un organisateur écrit à une personne."),
              Group.MESSAGES, Scope.EVENT, {'message': v.MessageView}),
]

EMAIL_TYPES = {email_type.key: email_type for email_type in _TYPES}

#: Document templates may name their own email key; any such key behaves as
#: this type, with its defaults.
DOCUMENT_EMAIL_TYPE = 'generated-document'


class UnknownEmailType(KeyError):
    pass


def get_email_type(key, event_id=None):
    """The type for a key. A key that isn't registered is accepted only if a
    document template of the given event uses it as its email key."""
    if key in EMAIL_TYPES:
        return EMAIL_TYPES[key]
    if event_id is not None and key in document_email_keys(event_id):
        return EMAIL_TYPES[DOCUMENT_EMAIL_TYPE].alias(key)
    raise UnknownEmailType(key)


def document_email_keys(event_id):
    from app import db
    from app.documents.models import DocumentTemplate
    rows = (db.session.query(DocumentTemplate.email_template_key)
            .filter(DocumentTemplate.event_id == event_id,
                    DocumentTemplate.email_template_key.isnot(None),
                    DocumentTemplate.email_template_key != '')
            .distinct().all())
    return {row[0] for row in rows if row[0] not in EMAIL_TYPES}
