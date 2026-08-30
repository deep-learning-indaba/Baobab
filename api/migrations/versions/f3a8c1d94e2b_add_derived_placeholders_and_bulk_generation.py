"""add derived placeholders and bulk generation

Revision ID: f3a8c1d94e2b
Revises: 9d623a4d3509
Create Date: 2026-08-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'f3a8c1d94e2b'
down_revision = '9d623a4d3509'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'document_derived_placeholder',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('event_id', sa.Integer(), sa.ForeignKey('event.id'), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('event_id', 'key', name='uq_derived_placeholder_event_key'),
    )

    op.create_table(
        'document_derived_placeholder_rule',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('derived_placeholder_id', sa.Integer(),
                  sa.ForeignKey('document_derived_placeholder.id'), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('condition_expression', sa.JSON(), nullable=True),
    )

    op.create_table(
        'document_derived_placeholder_rule_translation',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('rule_id', sa.Integer(),
                  sa.ForeignKey('document_derived_placeholder_rule.id'), nullable=False),
        sa.Column('language', sa.String(length=2), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.UniqueConstraint('rule_id', 'language', name='uq_derived_placeholder_rule_translation'),
    )

    op.create_table(
        'document_generation_job',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('event_id', sa.Integer(), sa.ForeignKey('event.id'), nullable=False),
        sa.Column('document_template_id', sa.Integer(),
                  sa.ForeignKey('document_template.id'), nullable=False),
        sa.Column('requested_by_user_id', sa.Integer(), sa.ForeignKey('app_user.id'), nullable=False),
        sa.Column('language', sa.String(length=2), nullable=False, server_default='en'),
        sa.Column('override_eligibility', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('recipient_selection', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=24), nullable=False, server_default='pending'),
        sa.Column('total_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('succeeded_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )

    op.add_column('generated_document',
                   sa.Column('job_id', sa.Integer(), sa.ForeignKey('document_generation_job.id'),
                             nullable=True))
    op.add_column('generated_document',
                   sa.Column('language', sa.String(length=2), nullable=False, server_default='en'))
    op.add_column('generated_document',
                   sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('generated_document', sa.Column('claimed_at', sa.DateTime(), nullable=True))
    op.add_column('generated_document', sa.Column('claim_token', sa.String(length=36), nullable=True))

    op.create_index('idx_generated_document_job', 'generated_document', ['job_id'])
    op.create_index('ix_generated_document_claimable', 'generated_document', ['status', 'job_id'])


def downgrade():
    op.drop_index('ix_generated_document_claimable', table_name='generated_document')
    op.drop_index('idx_generated_document_job', table_name='generated_document')
    op.drop_column('generated_document', 'claim_token')
    op.drop_column('generated_document', 'claimed_at')
    op.drop_column('generated_document', 'attempts')
    op.drop_column('generated_document', 'language')
    op.drop_column('generated_document', 'job_id')

    op.drop_table('document_generation_job')
    op.drop_table('document_derived_placeholder_rule_translation')
    op.drop_table('document_derived_placeholder_rule')
    op.drop_table('document_derived_placeholder')
