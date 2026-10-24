"""Every default template, in every language, against every branch it can take."""
import itertools
import os
import unittest

from app.email_template import engine
from app.email_template.registry import EMAIL_TYPES
from app.email_template.repository import DEFAULTS_DIR, load_default
from app.email_template.service import sample_context
from app.email_template.validation import check_template
from app.email_template.views import BOOLEAN, ListOf, _is_view

LANGUAGES = ('en', 'fr')


def branch_points(email_type):
    """Dotted paths whose value changes which branch a template takes, each
    with the alternative value to try: booleans flipped, lists emptied,
    optional values removed."""
    points = []
    for name, view in email_type.full_context().items():
        if email_type.nullable(name):
            points.append((name, None))
        for field_name, field in view.fields.items():
            path = '{}.{}'.format(name, field_name)
            if field.type == BOOLEAN:
                points.append((path, False))
            elif isinstance(field.type, ListOf):
                points.append((path, 0))
            elif _is_view(field.type) and field.nullable:
                points.append((path, None))
            elif field.nullable:
                points.append((path, None))
    return points


def scenarios(email_type):
    points = branch_points(email_type)
    yield {}
    for count in range(1, min(len(points), 3) + 1):
        for combination in itertools.combinations(points, count):
            yield dict(combination)


class DefaultTemplatesTest(unittest.TestCase):

    def test_every_type_has_a_default_in_every_language(self):
        for key in EMAIL_TYPES:
            for language in LANGUAGES:
                self.assertIsNotNone(load_default(key, language), '{}.{}.md is missing'.format(key, language))

    def test_no_default_without_a_type(self):
        keys = {name.split('.')[0] for name in os.listdir(DEFAULTS_DIR) if name.endswith('.md')}
        self.assertEqual(keys - set(EMAIL_TYPES), set())

    def test_defaults_only_use_declared_fields(self):
        for key, email_type in EMAIL_TYPES.items():
            views = email_type.full_context()
            for language in LANGUAGES:
                subject, body = load_default(key, language)
                with self.subTest(key=key, language=language):
                    check_template(subject, views, field='subject')
                    check_template(body, views)

    def test_defaults_render_in_every_branch(self):
        for key, email_type in EMAIL_TYPES.items():
            for language in LANGUAGES:
                subject, body = load_default(key, language)
                for overrides in scenarios(email_type):
                    values = sample_context(email_type, None, None, language, overrides)
                    with self.subTest(key=key, language=language, overrides=overrides):
                        rendered_subject = engine.render_subject(subject, values, language, strict=True)
                        self.assertTrue(rendered_subject.strip())
                        html = engine.render_html_fragment(body, values, language, '#000000', strict=True)
                        text = engine.render_text_fragment(body, values, language, strict=True)
                        self.assertTrue(html.strip())
                        self.assertTrue(text.strip())
                        self.assertNotIn('{{', text)
                        self.assertNotIn('{%', text)
