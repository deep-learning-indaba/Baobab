import csv
import io
import json
from unittest.mock import patch

from app import db
from app.forms.models import (
    Form, FormTranslation, FormSection, FormSectionTranslation,
    FormQuestion, FormQuestionTranslation,
    FormResponse, FormAnswer
)
from app.documents.google_client import GoogleApiError
from app.utils.testing import ApiTestCase


class _FakeSheetsClient:
    def __init__(self, url='https://docs.google.com/spreadsheets/d/fake123/edit', error=None):
        self.calls = []
        self._url = url
        self._error = error

    def create_spreadsheet(self, title, rows, share_with_email):
        self.calls.append({'title': title, 'rows': rows, 'share_with_email': share_with_email})
        if self._error:
            raise self._error
        return self._url


class TestFormResponseExportAPI(ApiTestCase):

    def seed_static_data(self):
        # Capture ids before any request - db.session detaches after.
        admin = self.add_user('admin@example.com', 'Admin', 'User', password='password123')
        self.admin_id = admin.id
        event = self.add_event()
        self.event_id = event.id
        self.add_event_role('admin', admin.id, event.id)
        other_user = self.add_user('nonadmin@example.com', 'Non', 'Admin', password='password123')
        self.other_user_id = other_user.id

        self.admin_headers = self.get_auth_header_for('admin@example.com', 'password123')
        self.other_headers = self.get_auth_header_for('nonadmin@example.com', 'password123')

    def _create_form_with_questions(self):
        form = Form(event_id=self.event_id, created_by_user_id=self.admin_id, is_open=True)
        db.session.add(form)
        db.session.flush()
        db.session.add(FormTranslation(form_id=form.id, language='en', name='Application'))

        section = FormSection(form_id=form.id, order=1, key='main')
        db.session.add(section)
        db.session.flush()
        db.session.add(FormSectionTranslation(
            form_section_id=section.id, language='en', name='Main'
        ))

        text_question = FormQuestion(
            form_id=form.id, section_id=section.id, order=1,
            question_type='short-text', is_required=True, key='reason'
        )
        db.session.add(text_question)
        db.session.flush()
        db.session.add(FormQuestionTranslation(
            form_question_id=text_question.id, language='en', headline='Reason for applying'
        ))

        choice_question = FormQuestion(
            form_id=form.id, section_id=section.id, order=2,
            question_type='dropdown', is_required=True, key='country'
        )
        db.session.add(choice_question)
        db.session.flush()
        choice_translation = FormQuestionTranslation(
            form_question_id=choice_question.id, language='en', headline='Country'
        )
        choice_translation.options = [
            {'value': 'za', 'label': 'South Africa'},
            {'value': 'ke', 'label': 'Kenya'},
        ]
        db.session.add(choice_translation)

        db.session.commit()
        return form, text_question, choice_question

    def _add_response(self, form, user, text_question, choice_question,
                       text_value, choice_value, is_submitted=True):
        response = FormResponse(form_id=form.id, user_id=user.id)
        response.is_submitted = is_submitted
        db.session.add(response)
        db.session.flush()
        db.session.add(FormAnswer(response_id=response.id, question_id=text_question.id, value=text_value))
        db.session.add(FormAnswer(response_id=response.id, question_id=choice_question.id, value=choice_value))
        db.session.commit()
        return response

    def _rows_from_csv(self, response_data):
        return list(csv.reader(io.StringIO(response_data.decode('utf-8'))))

    def test_csv_export_includes_all_questions_and_resolves_option_labels(self):
        self.seed_static_data()
        form, text_question, choice_question = self._create_form_with_questions()

        applicant = self.add_user('applicant@example.com', 'Ada', 'Lovelace', password='password123')
        self._add_response(
            form, applicant, text_question, choice_question,
            text_value='Because I love ML', choice_value='za'
        )

        resp = self.app.get(
            f'/api/v1/forms/{form.id}/responses/export?event_id={self.event_id}&format=csv',
            headers=self.admin_headers
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, 'text/csv')
        self.assertIn('attachment', resp.headers.get('Content-Disposition', ''))

        rows = self._rows_from_csv(resp.data)
        header = rows[0]
        self.assertIn('Reason for applying', header)
        self.assertIn('Country', header)

        data_row = rows[1]
        row_dict = dict(zip(header, data_row))
        self.assertEqual(row_dict['Email'], 'applicant@example.com')
        self.assertEqual(row_dict['Status'], 'Submitted')
        self.assertEqual(row_dict['Reason for applying'], 'Because I love ML')
        # 'za' should resolve to its option label.
        self.assertEqual(row_dict['Country'], 'South Africa')

    def test_csv_export_respects_email_filter(self):
        self.seed_static_data()
        form, text_question, choice_question = self._create_form_with_questions()

        matching_user = self.add_user('match@example.com', 'Match', 'Me', password='password123')
        other_user = self.add_user('someoneelse@different.com', 'No', 'Match', password='password123')
        self._add_response(form, matching_user, text_question, choice_question, 'A', 'za')
        self._add_response(form, other_user, text_question, choice_question, 'B', 'ke')

        resp = self.app.get(
            f'/api/v1/forms/{form.id}/responses/export?event_id={self.event_id}&format=csv&email=match@',
            headers=self.admin_headers
        )

        self.assertEqual(resp.status_code, 200)
        rows = self._rows_from_csv(resp.data)
        self.assertEqual(len(rows), 2)  # header + one matching response
        self.assertEqual(rows[1][1], 'match@example.com')

    def test_csv_export_streams_every_row_without_loss_at_moderate_scale(self):
        # Streaming shouldn't drop/duplicate/reorder rows.
        self.seed_static_data()
        form, text_question, choice_question = self._create_form_with_questions()

        expected_emails = []
        for i in range(40):
            user = self.add_user(f'bulk{i}@example.com', f'First{i}', 'Last', password='password123')
            self._add_response(form, user, text_question, choice_question, f'Answer {i}', 'za')
            expected_emails.append(f'bulk{i}@example.com')

        resp = self.app.get(
            f'/api/v1/forms/{form.id}/responses/export?event_id={self.event_id}&format=csv',
            headers=self.admin_headers
        )

        self.assertEqual(resp.status_code, 200)
        rows = self._rows_from_csv(resp.data)
        self.assertEqual(len(rows), 41)  # header + 40 responses

        email_col = rows[0].index('Email')
        exported_emails = sorted(row[email_col] for row in rows[1:])
        self.assertEqual(exported_emails, sorted(expected_emails))

    def test_export_requires_event_admin(self):
        self.seed_static_data()
        form, text_question, choice_question = self._create_form_with_questions()

        resp = self.app.get(
            f'/api/v1/forms/{form.id}/responses/export?event_id={self.event_id}&format=csv',
            headers=self.other_headers
        )
        self.assertEqual(resp.status_code, 403)

    def test_invalid_format_returns_400(self):
        self.seed_static_data()
        form, text_question, choice_question = self._create_form_with_questions()

        resp = self.app.get(
            f'/api/v1/forms/{form.id}/responses/export?event_id={self.event_id}&format=pdf',
            headers=self.admin_headers
        )
        self.assertEqual(resp.status_code, 400)

    def test_sheets_export_creates_and_shares_spreadsheet(self):
        self.seed_static_data()
        form, text_question, choice_question = self._create_form_with_questions()

        applicant = self.add_user('applicant2@example.com', 'Ada', 'Lovelace', password='password123')
        self._add_response(form, applicant, text_question, choice_question, 'Because', 'ke')

        fake_client = _FakeSheetsClient()
        with patch('app.documents.google_client.build_default_client', return_value=fake_client):
            resp = self.app.get(
                f'/api/v1/forms/{form.id}/responses/export?event_id={self.event_id}&format=sheets',
                headers=self.admin_headers
            )

        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data['url'], fake_client._url)

        self.assertEqual(len(fake_client.calls), 1)
        call = fake_client.calls[0]
        self.assertEqual(call['share_with_email'], 'admin@example.com')
        self.assertIn('Reason for applying', call['rows'][0])
        self.assertEqual(call['rows'][1][1], 'applicant2@example.com')

    def test_sheets_export_google_error_returns_502(self):
        self.seed_static_data()
        form, text_question, choice_question = self._create_form_with_questions()

        fake_client = _FakeSheetsClient(error=GoogleApiError(500, 'boom'))
        with patch('app.documents.google_client.build_default_client', return_value=fake_client):
            resp = self.app.get(
                f'/api/v1/forms/{form.id}/responses/export?event_id={self.event_id}&format=sheets',
                headers=self.admin_headers
            )

        self.assertEqual(resp.status_code, 502)
