import re
import unittest
from unittest.mock import patch

from app.email_template.registry import EMAIL_TYPES
from app.email_template.repository import load_default
from app.email_template.translate import TranslationUnavailable, translate_template
from app.email_template.validation import check_template


def fake_service(texts, target, source, format_='text'):
    """Upper-cases everything outside tags, the way a translation service
    changes words but (for translate="no" spans) not markup."""
    def translate(text):
        parts = re.split(r'(<span translate="no">\d+</span>|<[^>]+>|&\w+;)', text)
        return ''.join(p if p.startswith(('<', '&')) else p.upper() for p in parts)
    return [translate(t) for t in texts]


class TranslateTemplateTest(unittest.TestCase):

    def translate(self, text, service=fake_service):
        with patch('app.utils.translation.TranslationService.translate_many', side_effect=service):
            return translate_template(text, 'en', 'fr')

    def test_liquid_is_untouched_and_prose_translated(self):
        out, kept = self.translate('Dear {{ recipient.salutation }}, see {{ offer.url }} now.')
        self.assertEqual(out, 'DEAR {{ recipient.salutation }}, SEE {{ offer.url }} NOW.')
        self.assertEqual(kept, 0)

    def test_spacing_around_placeholders_is_kept_as_written(self):
        def padding(texts, *args, **kwargs):
            return [re.sub(r'(<span translate="no">\d+</span>)', r' \1 ', t) for t in texts]
        out, _ = self.translate('Dear {{ recipient.salutation }}, the fee{% if offer.fee %} of X{% endif %}.', padding)
        self.assertEqual(out, 'Dear {{ recipient.salutation }}, the fee{% if offer.fee %} of X{% endif %}.')

    def test_control_flow_lines_are_not_sent(self):
        out, _ = self.translate('{% if offer.payment_required %}\nPay up.\n{% endif %}')
        self.assertEqual(out, '{% if offer.payment_required %}\nPAY UP.\n{% endif %}')

    def test_button_label_translated_but_tag_kept(self):
        out, _ = self.translate('{% button "View my offer", offer.url, style: "secondary" %}')
        self.assertEqual(out, '{% button "VIEW MY OFFER", offer.url, style: "secondary" %}')

    def test_button_label_quotes_cannot_break_the_tag(self):
        def quoting(texts, *args, **kwargs):
            return [t.replace('Go', 'Allez "vite"') for t in texts]
        out, _ = self.translate('{% button "Go", offer.url %}', quoting)
        self.assertEqual(out, '{% button "Allez \'vite\'", offer.url %}')

    def test_markdown_survives(self):
        out, _ = self.translate('- **Bold** and _soft_ with [a link]({{ offer.url }}) & more')
        self.assertEqual(out, '- **BOLD** AND _SOFT_ WITH [A LINK]({{ offer.url }}) & MORE')

    def test_heading_and_numbered_prefixes_kept(self):
        out, _ = self.translate('### Fees\n1. Pay')
        self.assertEqual(out, '### FEES\n1. PAY')

    def test_line_with_lost_placeholder_is_kept_in_source_language(self):
        def lossy(texts, *args, **kwargs):
            return [re.sub(r'<span translate="no">\d+</span>', '', t) for t in texts]
        out, kept = self.translate('Hi {{ recipient.firstname }}\nThanks', lossy)
        self.assertEqual(out, 'Hi {{ recipient.firstname }}\nThanks')
        self.assertEqual(kept, 1)

    def test_service_unavailable(self):
        with self.assertRaises(TranslationUnavailable):
            self.translate('Hello', lambda *a, **k: None)

    def test_every_default_template_still_validates_after_translation(self):
        for key, email_type in EMAIL_TYPES.items():
            subject, body = load_default(key, 'en')
            for source in (subject, body):
                out, kept = self.translate(source)
                self.assertEqual(kept, 0, key)
                check_template(out, email_type.full_context())
