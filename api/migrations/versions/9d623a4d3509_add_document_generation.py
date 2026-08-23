"""add document generation tables

Revision ID: 9d623a4d3509
Revises: 80393b25a1bb
Create Date: 2026-08-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '9d623a4d3509'
down_revision = '80393b25a1bb'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'document_template',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('event_id', sa.Integer(), sa.ForeignKey('event.id'), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('self_service', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('eligibility_expression', sa.JSON(), nullable=True),
        sa.Column('delivery_mode', sa.String(length=16), nullable=False, server_default='attachment'),
        sa.Column('email_template_key', sa.String(length=50), nullable=True),
        sa.Column('filename_pattern', sa.String(length=255), nullable=True),
        sa.Column('allow_blank_values', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_user_id', sa.Integer(), sa.ForeignKey('app_user.id'), nullable=False),
        sa.UniqueConstraint('event_id', 'key', name='uq_document_template_event_key'),
    )

    op.create_table(
        'document_template_translation',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('document_template_id', sa.Integer(),
                  sa.ForeignKey('document_template.id'), nullable=False),
        sa.Column('language', sa.String(length=2), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.UniqueConstraint('document_template_id', 'language',
                             name='uq_document_template_translation'),
    )

    op.create_table(
        'document_template_variant',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('document_template_id', sa.Integer(),
                  sa.ForeignKey('document_template.id'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('google_file_id', sa.String(length=255), nullable=False),
        sa.Column('google_file_type', sa.String(length=16), nullable=False),
        sa.Column('google_file_name', sa.String(length=500), nullable=True),
        sa.Column('language', sa.String(length=2), nullable=True),
        sa.Column('selection_expression', sa.JSON(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('detected_placeholders', sa.JSON(), nullable=True),
        sa.Column('access_status', sa.String(length=32), nullable=True),
        sa.Column('access_checked_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    op.create_table(
        'document_template_form',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('document_template_id', sa.Integer(),
                  sa.ForeignKey('document_template.id'), nullable=False),
        sa.Column('form_id', sa.Integer(), sa.ForeignKey('form.id'), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('requirement', sa.String(length=16), nullable=False, server_default='none'),
        sa.UniqueConstraint('document_template_id', 'form_id', name='uq_document_template_form'),
    )

    op.create_table(
        'document_template_form_translation',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('document_template_form_id', sa.Integer(),
                  sa.ForeignKey('document_template_form.id'), nullable=False),
        sa.Column('language', sa.String(length=2), nullable=False),
        sa.Column('prompt_message', sa.Text(), nullable=False),
        sa.UniqueConstraint('document_template_form_id', 'language',
                             name='uq_document_template_form_translation'),
    )

    op.create_table(
        'user_event_data',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('event_id', sa.Integer(), sa.ForeignKey('event.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('app_user.id'), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('updated_by_user_id', sa.Integer(), sa.ForeignKey('app_user.id'), nullable=False),
        sa.UniqueConstraint('event_id', 'user_id', 'key', name='uq_user_event_data'),
    )
    op.create_index('idx_user_event_data_lookup', 'user_event_data', ['event_id', 'user_id'])

    op.create_table(
        'generated_document',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('event_id', sa.Integer(), sa.ForeignKey('event.id'), nullable=False),
        sa.Column('document_template_id', sa.Integer(),
                  sa.ForeignKey('document_template.id'), nullable=False),
        sa.Column('variant_id', sa.Integer(),
                  sa.ForeignKey('document_template_variant.id'), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('app_user.id'), nullable=False),
        sa.Column('requested_by_user_id', sa.Integer(), sa.ForeignKey('app_user.id'), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False, server_default='pending'),
        sa.Column('storage_blob_name', sa.String(length=255), nullable=True),
        sa.Column('filename', sa.String(length=255), nullable=True),
        sa.Column('placeholder_snapshot', sa.JSON(), nullable=True),
        sa.Column('error_code', sa.String(length=64), nullable=True),
        sa.Column('error_detail', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('generated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('idx_generated_document_lookup', 'generated_document',
                     ['document_template_id', 'user_id'])


def downgrade():
    op.drop_index('idx_generated_document_lookup', table_name='generated_document')
    op.drop_table('generated_document')
    op.drop_index('idx_user_event_data_lookup', table_name='user_event_data')
    op.drop_table('user_event_data')
    op.drop_table('document_template_form_translation')
    op.drop_table('document_template_form')
    op.drop_table('document_template_variant')
    op.drop_table('document_template_translation')
    op.drop_table('document_template')
