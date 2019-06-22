"""Populate registration form.

Revision ID: 3ab678fc66cd
Revises: a5480ca6646b
Create Date: 2019-06-20 21:34:45.822651

"""

# revision identifiers, used by Alembic.
revision = '3ab678fc66cd'
down_revision = 'a5480ca6646b'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


def upgrade():
    op.alter_column('registration_section', 'show_for_travel_award',
               nullable=True)
    op.alter_column('registration_section', 'show_for_accommodation_award',
               nullable=True)
    op.alter_column('registration_section', 'show_for_payment_required',
               nullable=True)

    reg_form = table('registration_form',
            column('id', sa.Integer()),
            column('event_id', sa.Integer()))

    section = table('registration_section',
            column('id', sa.Integer()),
            column('registration_form_id', sa.Integer()),
            column('name', sa.String()),
            column('description', sa.String()),
            column('order', sa.Integer()),
            column('show_for_travel_award', sa.Boolean()),
            column('show_for_accommodation_award', sa.Boolean()),
            column('show_for_payment_required', sa.Boolean()))

    question = table('registration_question',
            column('id', sa.Integer()),
            column('registration_form_id', sa.Integer()),
            column('section_id', sa.Integer()),
            column('type', sa.String()),
            column('description', sa.String()),
            column('headline', sa.String()),
            column('placeholder', sa.String()),
            column('validation_regex', sa.String()),
            column('validation_text', sa.String()),
            column('order', sa.Integer()),
            column('options', sa.JSON()),
            column('is_required', sa.Boolean()),
            column('depends_on_question_id', sa.Integer()),
            column('hide_for_dependent_value', sa.String()),
            column('required_value', sa.String())
            )

    op.bulk_insert(
        reg_form,
        [
            {
                'id': 1,
                'event_id': 1
            }
        ]
    )

    op.bulk_insert(
        section,
        [
            {
                'id': 1,
                'registration_form_id': 1,
                'name': 'Personal Details',
                'description': '''This is the registration form for candidates who have been accepted  to attend the Deep Learning Indaba 2019. It should take about 5 minutes to complete.

Data usage: We will use the information you provide in this form for registration and coordination purposes for the Deep Learning Indaba 2019. This may involve sharing your contact details with third-party service providers for the purposes of event management and organisation. 

Due Date: Please complete and submit this form by 20 July 2019.''',
                'order': 1,
                'show_for_travel_award': None,
                'show_for_accommodation_award': None,
                'show_for_payment_required': None
            },
            {
                'id': 2,
                'registration_form_id': 1,
                'name': 'Code of Conduct',
                'description': '''We ask that you recall a central principle of African philosophy, whether you know it as ujamaa (Swahili), umuntu (Chichewa), ubuntu (Zulu), unhu (Shona), djema'a (Arabic), or through the many other words used across our continent: the philosophy of familyhood and unity. Our duty, as we come together at the Indaba, is to create a familyhood of people and cultures and learning, built on the principles of freedom, equality and unity; and towards the aim of strengthening African machine learning. 

This means that every participant is responsible for providing a safe experience for all participants, regardless of gender, gender identity and expression, sexual orientation, ability, physical appearance, body size, race, ethnicity, nationality, age, religion, or socioeconomic status. As organisers, we are committed to these responsibilities and will not tolerate harassment of Indaba participants in any form.

Every participant of the Indaba must fiercely defend these principles, and make it their responsibility to uphold the spirit of togetherness. 

If a participant engages in behaviour that breaks this code of conduct, the organisers retain the right to take any actions needed to keep the Indaba a welcoming environment for all participants. You can report a concern or an incident through an anonymous report, or in person.

For details of expected conduct, unacceptable behaviour, how to report an incident, how we maintain a respectful community, and how we enforce these standards, please go to deeplearningindaba.com/conduct or send a message to conduct@deeplearningindaba.com.''',
                'order': 2,
                'show_for_travel_award': None,
                'show_for_accommodation_award': None,
                'show_for_payment_required': None
            },
            {
                'id': 3,
                'registration_form_id': 1,
                'name': 'Posters',
                'description': 'If you would like to showcase some of the work you have been doing at your institution and solicit feedback from leading researchers and industry experts, we encourage you to take part in our poster sessions! ',
                'order': 3,
                'show_for_travel_award': None,
                'show_for_accommodation_award': None,
                'show_for_payment_required': None
            },
            {
                'id': 4,
                'registration_form_id': 1,
                'name': 'Attendance Information',
                'description': 'Some more information to help our planning.',
                'order': 10,
                'show_for_travel_award': None,
                'show_for_accommodation_award': None,
                'show_for_payment_required': None
            },
            {
                'id': 5,
                'registration_form_id': 1,
                'name': 'Registration Fee',
                'description': '''To reduce the barrier to participation, we ask no registration fees for students. We do charge a registration fee of USD 350 for participants from industry and academic faculty.

Payments will be taken through a secure payment portal, and receipts provided for all payments. Payment details will be sent in a separate email, or you can check for deeplearningindaba.com/payments for updates.''',
                'order': 5,
                'show_for_travel_award': None,
                'show_for_accommodation_award': None,
                'show_for_payment_required': True
            },
            {
                'id': 6,
                'registration_form_id': 1,
                'name': 'Registration Fee',
                'description': 'To reduce the barrier to participation, we ask no registration fees for students. We do charge a registration fee of USD 350 for participants from industry and academic faculty. ',
                'order': 6,
                'show_for_travel_award': None,
                'show_for_accommodation_award': None,
                'show_for_payment_required': False
            },
            {
                'id': 7,
                'registration_form_id': 1,
                'name': 'Travel Award',
                'description': 'You have accepted a travel award and the Indaba will fund your travel to and from Nairobi. We will book these flights on your behalf. AIrport transfers will also be available for those arriving on certain days, more information about this will be available on the website closer to the event. If you choose to travel on different dates you will be responsibile for your own airport transfers.',
                'order': 7,
                'show_for_travel_award': True,
                'show_for_accommodation_award': None,
                'show_for_payment_required': None
            },
            {
                'id': 8,
                'registration_form_id': 1,
                'name': 'Accommodation Award',
                'description': 'You have accepted an accommodation award in a shared room at Nyayo Hostel on the Kenyatta University Campus. You will only share with someone of the same gender as indicated in your user profile. The Indaba will provide accommodation for the nights of the 25th of August to the 31st of August. You will be responsible for your own accommodation outside of these dates should you decide to arrive earlier or leave later. ',
                'order': 8,
                'show_for_travel_award': None,
                'show_for_accommodation_award': False,
                'show_for_payment_required': None
            },
        ]
    )

    op.bulk_insert(
        question,
        [
            {
                'id': 1,
                'registration_form_id': 1,
                'section_id': 1,
                'type': 'short-text',
                'description': 'Including country code.',
                'headline': 'Cellphone Number',
                'placeholder': 'Cellphone Number',
                'validation_regex': None,
                'validation_text': None,
                'order': 1,
                'options': None,
                'is_required': True,
                'depends_on_question_id': None,
                'hide_for_dependent_value': None,
                'required_value': None, 
            },
            {
                'id': 2,
                'registration_form_id': 1,
                'section_id': 2,
                'type': 'single-choice',
                'description': '',
                'headline': 'I have read, understood and agree with the Code of Conduct',
                'placeholder': '',
                'validation_regex': '1',
                'validation_text': 'You must agree to the Code of Conduct.',
                'order': 1,
                'options': None,
                'is_required': True,
                'depends_on_question_id': None,
                'hide_for_dependent_value': None,
                'required_value': '1', 
            },
            {
                'id': 3,
                'registration_form_id': 1,
                'section_id': 3,
                'type': 'multi-choice',
                'description': '',
                'headline': 'Will you be bringing a poster?',
                'placeholder': '',
                'validation_regex': None,
                'validation_text': None,
                'order': 1,
                'options': [{"value": "yes", "label": "Yes"}, {"value": "no", "label": "No"}],
                'is_required': True,
                'depends_on_question_id': None,
                'hide_for_dependent_value': None,
                'required_value': None, 
            },
            {
                'id': 4,
                'registration_form_id': 1,
                'section_id': 3,
                'type': 'short-text',
                'description': "You can come back and complete this later if you don't have a title yet.",
                'headline': 'What is the provisional title of your poster?',
                'placeholder': 'Poster Title',
                'validation_regex': None,
                'validation_text': None,
                'order': 2,
                'options': None,
                'is_required': False,
                'depends_on_question_id': 3,
                'hide_for_dependent_value': 'no',
                'required_value': None, 
            },
            {
                'id': 5,
                'registration_form_id': 1,
                'section_id': 3,
                'type': 'file',
                'description': "",
                'headline': 'Upload your poster PDF',
                'placeholder': '',
                'validation_regex': None,
                'validation_text': None,
                'order': 3,
                'options': None,
                'is_required': False,
                'depends_on_question_id': 3,
                'hide_for_dependent_value': 'no',
                'required_value': None, 
            },
            {
                'id': 6,
                'registration_form_id': 1,
                'section_id': 4,
                'type': 'multi-choice',
                'description': "",
                'headline': 'Do you have any dietary requirements?',
                'placeholder': '',
                'validation_regex': None,
                'validation_text': None,
                'order': 1,  
                'options': [{"value": "vegetarian", "label": "Vegetarian"}, {"value": "vegan", "label": "Vegan"}, {"value": "halaal", "label": "Halaal"}, {"value": "kosher", "label": "Kosher"}, {"value": "gluten-free", "label": "Gluten Free"}, {"value": "other", "label": "Other"}],
                'is_required': False,
                'depends_on_question_id': None,
                'hide_for_dependent_value': None,
                'required_value': None, 
            },
            {
                'id': 7,
                'registration_form_id': 1,
                'section_id': 4,
                'type': 'short-text',
                'description': 'If you answered "Other" to the dietary requirements question, please give us more details.',
                'headline': 'Other Details',
                'placeholder': '',
                'validation_regex': None,
                'validation_text': None,
                'order': 2,  
                'options': None,
                'is_required': False,
                'depends_on_question_id': None,
                'hide_for_dependent_value': None,
                'required_value': None, 
            },
            {
                'id': 8,
                'registration_form_id': 1,
                'section_id': 4,
                'type': 'multi-choice',
                'description': '',
                'headline': 'T-Shirt Size',
                'placeholder': '',
                'validation_regex': None,
                'validation_text': None,
                'order': 3,  
                'options': [{"value": "S", "label": "S"}, {"value": "M", "label": "M"}, {"value": "L", "label": "L"}, {"value": "XL", "label": "XL"}],
                'is_required': True,
                'depends_on_question_id': None,
                'hide_for_dependent_value': None,
                'required_value': None, 
            },
            {
                'id': 9,
                'registration_form_id': 1,
                'section_id': 5,
                'type': 'single-choice',
                'description': '',
                'headline': 'I agree to the payment of a USD 350 registration fee.',
                'placeholder': '',
                'validation_regex': '1',
                'validation_text': 'You must agree to the payment of USD 350 in order to register.',
                'order': 1,  
                'options': None,
                'is_required': True,
                'depends_on_question_id': None,
                'hide_for_dependent_value': None,
                'required_value': '1', 
            },
            {
                'id': 10,
                'registration_form_id': 1,
                'section_id': 6,
                'type': 'single-choice',
                'description': 'In order to waive the registration fee, please confirm that you are currently a STUDENT or Unemployed. If your status has changed, please get in touch with us at info@deeplearningindaba.com',
                'headline': 'Are you currently a student or unemployed?',
                'placeholder': '',
                'validation_regex': '1',
                'validation_text': 'You must confirm you are student or contact us at info@deeplearningindaba.com',
                'order': 1,  
                'options': None,
                'is_required': True,
                'depends_on_question_id': None,
                'hide_for_dependent_value': None,
                'required_value': None, 
            },
            {
                'id': 11,
                'registration_form_id': 1,
                'section_id': 7,
                'type': 'file',
                'description': '',
                'headline': 'Upload a copy of the photo page of your passport',
                'placeholder': '',
                'validation_regex': None,
                'validation_text': None,
                'order': 1,  
                'options': None,
                'is_required': True,
                'depends_on_question_id': None,
                'hide_for_dependent_value': None,
                'required_value': None, 
            },
            {
                'id': 12,
                'registration_form_id': 1,
                'section_id': 7,
                'type': 'short-text',
                'description': '(e.g. O.R. Tambo International Airport)',
                'headline': 'Please confirm your chosen airport of departure.',
                'placeholder': 'Airport of Departure',
                'validation_regex': None,
                'validation_text': None,
                'order': 2,  
                'options': None,
                'is_required': True,
                'depends_on_question_id': None,
                'hide_for_dependent_value': None,
                'required_value': None, 
            },
            {
                'id': 13,
                'registration_form_id': 1,
                'section_id': 7,
                'type': 'date',
                'description': "If you'd like to stay in Nairobi for longer, and not arrive on Sunday the 25th of August, please indicate your preferred arrival date.",
                'headline': 'Preferred Arrival Date in Nairobi.',
                'placeholder': 'Arrival Date',
                'validation_regex': None,
                'validation_text': None,
                'order': 3,  
                'options': None,
                'is_required': False,
                'depends_on_question_id': None,
                'hide_for_dependent_value': None,
                'required_value': None, 
            },
            {
                'id': 14,
                'registration_form_id': 1,
                'section_id': 7,
                'type': 'date',
                'description': "If you'd like to stay in Nairobi for longer, and not depart on Saturday 31st August, please indicate your preferred departure date.",
                'headline': 'Preferred Departure Date.',
                'placeholder': 'Departure Date',
                'validation_regex': None,
                'validation_text': None,
                'order': 4,  
                'options': None,
                'is_required': False,
                'depends_on_question_id': None,
                'hide_for_dependent_value': None,
                'required_value': None, 
            },
            {
                'id': 15,
                'registration_form_id': 1,
                'section_id': 8,
                'type': 'long-text',
                'description': "",
                'headline': 'Please let us know if you have any special needs relating to your accommodation that we should be aware of?',
                'placeholder': 'Special Accommodation Requirements',
                'validation_regex': None,
                'validation_text': None,
                'order': 1,  
                'options': None,
                'is_required': False,
                'depends_on_question_id': None,
                'hide_for_dependent_value': None,
                'required_value': None, 
            },
        ]
    )

    op.get_bind().execute("""SELECT setval('registration_form_id_seq', (SELECT max(id) FROM registration_form));""")
    op.get_bind().execute("""SELECT setval('registration_section_id_seq', (SELECT max(id) FROM registration_section));""")
    op.get_bind().execute("""SELECT setval('registration_question_id_seq', (SELECT max(id) FROM registration_question));""")


def downgrade():
    op.get_bind().execute('DELETE FROM registration_question; DELETE FROM registration_section; DELETE FROM registration_form;')

    op.get_bind().execute("""SELECT setval('registration_form_id_seq', (SELECT max(id) FROM registration_form));""")
    op.get_bind().execute("""SELECT setval('registration_section_id_seq', (SELECT max(id) FROM registration_section));""")
    op.get_bind().execute("""SELECT setval('registration_question_id_seq', (SELECT max(id) FROM registration_question));""")

    op.alter_column('registration_section', 'show_for_travel_award',
               nullable=False)
    op.alter_column('registration_section', 'show_for_accommodation_award',
               nullable=False)
    op.alter_column('registration_section', 'show_for_payment_required',
               nullable=False)
