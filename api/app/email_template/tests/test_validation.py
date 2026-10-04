import unittest

from app.email_template.engine import EmailRenderError
from app.email_template.registry import EMAIL_TYPES
from app.email_template.validation import check_template


OFFER_VIEWS = EMAIL_TYPES['offer'].full_context()


class ValidationTest(unittest.TestCase):

    def assertRejected(self, source, message_part, line=None):
        with self.assertRaises(EmailRenderError) as raised:
            check_template(source, OFFER_VIEWS)
        self.assertIn(message_part, raised.exception.message)
        if line is not None:
            self.assertEqual(raised.exception.line, line)

    def test_valid_paths_pass(self):
        check_template('{{ recipient.salutation }} {{ offer.fee.formatted }} {{ offer.grants.size }} '
                       '{{ offer.grants.first.name }} {{ event.name.size }}', OFFER_VIEWS)

    def test_misspelt_field(self):
        self.assertRejected('Hi\n{{ offer.expiry_dat }}', 'no field "expiry_dat"', line=2)

    def test_field_inside_a_false_branch_is_still_checked(self):
        self.assertRejected('{% if false %}{{ offer.nope }}{% endif %}', 'no field "nope"')

    def test_unknown_root(self):
        self.assertRejected('{{ invoice.number }}', '"invoice" is not available')

    def test_loop_variable_is_checked_against_the_list_item(self):
        check_template('{% for g in offer.grants %}{{ g.name }} {{ forloop.index }}{% endfor %}', OFFER_VIEWS)
        self.assertRejected('{% for g in offer.grants %}{{ g.amount }}{% endfor %}', 'no field "amount"')

    def test_assigned_path_is_followed(self):
        check_template('{% assign fee = offer.fee %}{{ fee.amount }}', OFFER_VIEWS)
        self.assertRejected('{% assign fee = offer.fee %}{{ fee.nope }}', 'no field "nope"')

    def test_orm_relationships_are_not_fields(self):
        self.assertRejected('{{ offer.event.organisation.stripe_api_secret_key }}', 'no field "event"')
        self.assertRejected('{{ recipient.password }}', 'no field "password"')

    def test_button_arguments_are_checked(self):
        self.assertRejected('{% button "Go", offer.link %}', 'no field "link"')

    def test_syntax_error(self):
        with self.assertRaises(EmailRenderError):
            check_template('{% if offer.payment_required %}unclosed', OFFER_VIEWS)
