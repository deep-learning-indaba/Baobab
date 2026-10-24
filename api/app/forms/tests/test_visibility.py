from app import db
from app.forms.models import Form
from app.forms.visibility import VisibilityEvaluator
from app.utils.testing import ApiTestCase


class BlankVisibilityConditionTest(ApiTestCase):
    """A condition with no tag chosen is an unfinished rule, not a restriction.

    The editor creates `{"tag": ""}` as a placeholder as soon as a rule is
    started; if that were evaluated literally it would match nobody.
    """

    def test_blank_tag_is_unrestricted(self):
        self.assertTrue(VisibilityEvaluator.evaluate({'tag': ''}, set()))
        self.assertTrue(VisibilityEvaluator.evaluate({'tag': '  '}, set()))

    def test_blank_tag_is_ignored_inside_groups(self):
        expression = {'operator': 'AND', 'conditions': [{'tag': 'vip'}, {'tag': ''}]}
        self.assertTrue(VisibilityEvaluator.evaluate(expression, {'vip'}))
        self.assertFalse(VisibilityEvaluator.evaluate(expression, set()))

        expression = {'operator': 'OR', 'conditions': [{'tag': ''}, {'tag': 'vip'}]}
        self.assertFalse(VisibilityEvaluator.evaluate(expression, set()))

    def test_group_of_only_blank_conditions_is_unrestricted(self):
        for operator in ('AND', 'OR', 'NOT'):
            expression = {'operator': operator, 'conditions': [{'tag': ''}]}
            self.assertTrue(VisibilityEvaluator.evaluate(expression, set()), operator)
        self.assertTrue(VisibilityEvaluator.evaluate({'operator': 'OR', 'conditions': []}, set()))

    def test_real_conditions_still_restrict(self):
        self.assertFalse(VisibilityEvaluator.evaluate({'tag': 'vip'}, set()))
        self.assertTrue(VisibilityEvaluator.evaluate({'tag': 'vip'}, {'vip'}))
        expression = {'operator': 'NOT', 'conditions': [{'tag': 'blocked'}]}
        self.assertFalse(VisibilityEvaluator.evaluate(expression, {'blocked'}))

    def test_applicant_can_load_form_with_blank_visibility_rule(self):
        event = self.add_event(key='BLANKVIS')
        admin = self.add_user('admin@example.com', password='pw')
        self.add_user('applicant@example.com', password='pw')
        form = Form(
            event_id=event.id, created_by_user_id=admin.id, is_open=True,
            visibility_expression={'tag': ''},
        )
        db.session.add(form)
        db.session.commit()
        form_id = form.id
        headers = self.get_auth_header_for('applicant@example.com', 'pw')

        response = self.app.get('/api/v1/forms/{}/structure'.format(form_id), headers=headers)

        self.assertEqual(response.status_code, 200)
