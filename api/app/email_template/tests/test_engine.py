import unittest

from app.email_template import engine
from app.email_template.engine import EmailRenderError, MarkdownText


CONTEXT = {
    'user': {'name': '*Bob* <b>x</b> [a](b) a_b'},
    'offer': {
        'url': 'https://example.org/a_b/offer?x=1&y=2',
        'fee': {'amount': 1500, 'currency': 'ZAR'},
        'grants': [{'name': 'Travel'}, {'name': 'Accommodation'}, {'name': 'Meals'}],
    },
}


def html(source, context=CONTEXT, language='en', strict=False):
    return engine.render_html_fragment(source, context, language, '#123456', strict)


def text(source, context=CONTEXT, language='en'):
    return engine.render_text_fragment(source, context, language)


class EscapingTest(unittest.TestCase):

    def test_values_are_escaped_for_html_and_markdown(self):
        out = html('Dear {{ user.name }},')
        self.assertIn('*Bob* &lt;b&gt;x&lt;/b&gt; [a](b) a_b', out)
        self.assertNotIn('<em>', out)
        self.assertNotIn('<b>', out)
        self.assertNotIn('href="b"', out)

    def test_values_survive_plain_text_conversion_verbatim(self):
        self.assertEqual(text('Dear {{ user.name }},'), 'Dear *Bob* <b>x</b> [a](b) a_b,')

    def test_template_markdown_is_formatted(self):
        self.assertIn('<strong>bold</strong>', html('**bold**'))
        self.assertEqual(text('**bold** and [a link](https://x.org)'), 'bold and a link (https://x.org)')

    def test_admin_html_is_sanitised(self):
        out = html('<script>alert(1)</script><a href="javascript:alert(1)">x</a><img src=x onerror=alert(1)>')
        self.assertNotIn('<script', out)
        self.assertNotIn('javascript:', out)
        self.assertNotIn('onerror', out)

    def test_raw_html_is_dropped_from_text(self):
        self.assertEqual(text('Hello <b>there</b>'), 'Hello there')

    def test_markdown_text_keeps_its_formatting_but_not_html(self):
        context = {'message': {'body': MarkdownText('**Important** <script>x</script>')}}
        out = html('{{ message.body }}', context)
        self.assertIn('<strong>Important</strong>', out)
        self.assertNotIn('<script', out)

    def test_bare_urls_become_links(self):
        out = html('Visit {{ offer.url }} now.')
        self.assertIn('<a href="https://example.org/a_b/offer?x=1&amp;y=2"', out)

    def test_subject_is_one_unescaped_line(self):
        subject = engine.render_subject('{{ user.name }}\n  update', CONTEXT, 'en')
        self.assertEqual(subject, '*Bob* <b>x</b> [a](b) a_b update')


class ButtonTest(unittest.TestCase):

    def test_button_renders_a_table_in_the_brand_colour(self):
        out = html('{% button "Accept <now>", offer.url %}')
        self.assertTrue(out.startswith('<table role="presentation"'))
        self.assertIn('background:#123456', out)
        self.assertIn('href="https://example.org/a_b/offer?x=1&amp;y=2"', out)
        self.assertIn('Accept &lt;now&gt;', out)
        self.assertNotIn('<p><table', out)

    def test_secondary_style(self):
        self.assertIn('border:2px solid #123456', html('{% button "View", offer.url, style: "secondary" %}'))

    def test_button_in_text_is_label_and_url(self):
        self.assertEqual(text('{% button "Accept <now>", offer.url %}'),
                         'Accept <now>: https://example.org/a_b/offer?x=1&y=2')

    def test_unsafe_link_is_rejected_with_position(self):
        with self.assertRaises(EmailRenderError) as raised:
            html('Hi\n{% button "Click", "javascript:alert(1)" %}')
        self.assertEqual(raised.exception.line, 2)

    def test_value_cannot_forge_a_button_token(self):
        # The token is per-render and random, so a value can't predict it.
        out = html('{{ user.name }} {% button "Go", offer.url %}',
                   {'user': {'name': 'BTN00000000000000000000000000000000N0X'}, 'offer': CONTEXT['offer']})
        self.assertEqual(out.count('<table'), 1)


class FilterTest(unittest.TestCase):

    def test_date_in_french(self):
        self.assertEqual(engine.format_date('2026-10-04', '%A %-d %B %Y', 'fr'), 'dimanche 4 octobre 2026')

    def test_date_filter_uses_render_language(self):
        self.assertEqual(text('{{ d | date }}', {'d': '2026-01-05'}, 'fr'), '5 janvier 2026')

    def test_money(self):
        self.assertIn('1,500.00 ZAR', html('{{ offer.fee | money }}'))
        self.assertEqual(text('{{ offer.fee | money }}', language='fr'), '1 500,00 ZAR')

    def test_list(self):
        self.assertEqual(text('{{ offer.grants | map: "name" | list }}'), 'Travel, Accommodation and Meals')
        self.assertEqual(text('{{ offer.grants | map: "name" | list }}', language='fr'),
                         'Travel, Accommodation et Meals')


class ErrorTest(unittest.TestCase):

    def test_undefined_in_strict_mode_reports_position(self):
        with self.assertRaises(EmailRenderError) as raised:
            html('ok\n {{ user.nme }}', strict=True)
        self.assertEqual((raised.exception.line, raised.exception.column), (2, 5))

    def test_undefined_renders_empty_when_lenient(self):
        self.assertEqual(text('[{{ user.nme }}]'), '[]')

    def test_unknown_filter(self):
        with self.assertRaises(EmailRenderError):
            html('{{ user.name | nope }}')

    def test_python_attributes_are_unreachable(self):
        class Secret:
            password = 'hunter2'
        self.assertNotIn('hunter2', text('{{ s.password }}{{ s.__class__ }}', {'s': Secret()}))

    def test_runaway_loop_is_stopped(self):
        with self.assertRaises(EmailRenderError):
            html('{% for i in (1..100000) %}{% for j in (1..100000) %}x{% endfor %}{% endfor %}')
