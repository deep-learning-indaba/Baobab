"""Event app: core tables (schema migration A).

Revision ID: c1a2b3d4e5f6
Revises: 496db296e680
Create Date: 2026-06-14 10:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = 'c1a2b3d4e5f6'
down_revision = '496db296e680'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # --- event: add timezone and checkin_mode ---
    op.add_column('event', sa.Column('timezone', sa.String(length=64), nullable=True))
    op.execute("UPDATE event SET timezone = 'UTC' WHERE timezone IS NULL")
    op.alter_column('event', 'timezone', nullable=False, server_default='UTC')

    op.add_column('event', sa.Column('checkin_mode', sa.String(length=16), nullable=True))
    op.execute("UPDATE event SET checkin_mode = 'per_event' WHERE checkin_mode IS NULL")
    op.alter_column('event', 'checkin_mode', nullable=False, server_default='per_event')

    # --- event_qr_token ---
    op.create_table(
        'event_qr_token',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['event.id']),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token'),
        sa.UniqueConstraint('event_id', 'user_id', name='uq_qrtoken_event_user'),
    )

    # --- checkin ---
    op.create_table(
        'checkin',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('checked_in_at', sa.DateTime(), nullable=False),
        sa.Column('checked_in_by_user_id', sa.Integer(), nullable=True),
        sa.Column('method', sa.String(length=16), nullable=False),
        sa.Column('day', sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['event.id']),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id']),
        sa.ForeignKeyConstraint(['checked_in_by_user_id'], ['app_user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id', 'user_id', 'day', name='uq_checkin_event_user_day'),
    )

    # --- member_profile ---
    op.create_table(
        'member_profile',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('headline', sa.String(length=160), nullable=True),
        sa.Column('about', sa.String(length=2000), nullable=True),
        sa.Column('pronouns', sa.String(length=40), nullable=True),
        sa.Column('name_pronunciation', sa.String(length=120), nullable=True),
        sa.Column('city', sa.String(length=120), nullable=True),
        sa.Column('photo_url', sa.String(length=512), nullable=True),
        sa.Column('visibility', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )

    # --- member_profile_link ---
    op.create_table(
        'member_profile_link',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('link_type', sa.String(length=40), nullable=False),
        sa.Column('url', sa.String(length=512), nullable=False),
        sa.ForeignKeyConstraint(['profile_id'], ['member_profile.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('profile_id', 'link_type', name='uq_profile_link_type'),
    )

    # --- member_profile_interest ---
    op.create_table(
        'member_profile_interest',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id']),
        sa.ForeignKeyConstraint(['tag_id'], ['tag.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'tag_id', name='uq_member_interest'),
    )

    # --- user_consent ---
    op.create_table(
        'user_consent',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=True),
        sa.Column('consent_type', sa.String(length=40), nullable=False),
        sa.Column('consent_version', sa.String(length=20), nullable=False),
        sa.Column('granted', sa.Boolean(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id']),
        sa.ForeignKeyConstraint(['event_id'], ['event.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- connection ---
    op.create_table(
        'connection',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('from_user_id', sa.Integer(), nullable=False),
        sa.Column('to_user_id', sa.Integer(), nullable=False),
        sa.Column('method', sa.String(length=16), nullable=False),
        sa.Column('status', sa.Enum('scanned', 'pending', 'connected', 'rejected', 'blocked', 'withdrawn', name='connection_status'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['event.id']),
        sa.ForeignKeyConstraint(['from_user_id'], ['app_user.id']),
        sa.ForeignKeyConstraint(['to_user_id'], ['app_user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id', 'from_user_id', 'to_user_id', name='uq_connection_edge'),
    )

    # --- connection_report ---
    op.create_table(
        'connection_report',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('reporter_user_id', sa.Integer(), nullable=False),
        sa.Column('reported_user_id', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['event.id']),
        sa.ForeignKeyConstraint(['reporter_user_id'], ['app_user.id']),
        sa.ForeignKeyConstraint(['reported_user_id'], ['app_user.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- programme_session ---
    op.create_table(
        'programme_session',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('session_type_id', sa.Integer(), nullable=True),
        sa.Column('venue', sa.String(length=160), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['event.id']),
        sa.ForeignKeyConstraint(['session_type_id'], ['tag.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- programme_session_translation ---
    op.create_table(
        'programme_session_translation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('language', sa.String(length=2), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('description', sa.String(length=4000), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['programme_session.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'language', name='uq_session_lang'),
    )

    # --- programme_speaker ---
    op.create_table(
        'programme_speaker',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('photo_url', sa.String(length=512), nullable=True),
        sa.Column('bio', sa.String(length=2000), nullable=True),
        sa.Column('linked_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['event.id']),
        sa.ForeignKeyConstraint(['linked_user_id'], ['app_user.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- programme_session_speaker ---
    op.create_table(
        'programme_session_speaker',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('speaker_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['programme_session.id']),
        sa.ForeignKeyConstraint(['speaker_id'], ['programme_speaker.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'speaker_id', name='uq_session_speaker'),
    )

    # --- programme_session_tag ---
    op.create_table(
        'programme_session_tag',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['programme_session.id']),
        sa.ForeignKeyConstraint(['tag_id'], ['tag.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'tag_id', name='uq_session_tag'),
    )

    # --- announcement ---
    op.create_table(
        'announcement',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('send_at', sa.DateTime(), nullable=True),
        sa.Column('expiry_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['event.id']),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['app_user.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- announcement_translation ---
    op.create_table(
        'announcement_translation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('announcement_id', sa.Integer(), nullable=False),
        sa.Column('language', sa.String(length=2), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('body_markdown', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['announcement_id'], ['announcement.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('announcement_id', 'language', name='uq_announcement_lang'),
    )

    # --- announcement_receipt ---
    op.create_table(
        'announcement_receipt',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('announcement_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('opened_at', sa.DateTime(), nullable=True),
        sa.Column('channel', sa.String(length=16), nullable=True),
        sa.ForeignKeyConstraint(['announcement_id'], ['announcement.id']),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('announcement_id', 'user_id', name='uq_receipt_announcement_user'),
    )

    # --- push_subscription ---
    op.create_table(
        'push_subscription',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('endpoint', sa.String(length=1024), nullable=False),
        sa.Column('p256dh', sa.String(length=256), nullable=False),
        sa.Column('auth', sa.String(length=256), nullable=False),
        sa.Column('user_agent', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('endpoint'),
    )

    # --- engagement_event ---
    op.create_table(
        'engagement_event',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organisation_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=40), nullable=False),
        sa.Column('event_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisation.id']),
        sa.ForeignKeyConstraint(['event_id'], ['event.id']),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_engagement_event_type_event', 'engagement_event', ['event_id', 'event_type'])


def downgrade():
    op.drop_index('ix_engagement_event_type_event', table_name='engagement_event')
    op.drop_table('engagement_event')
    op.drop_table('push_subscription')
    op.drop_table('announcement_receipt')
    op.drop_table('announcement_translation')
    op.drop_table('announcement')
    op.drop_table('programme_session_tag')
    op.drop_table('programme_session_speaker')
    op.drop_table('programme_speaker')
    op.drop_table('programme_session_translation')
    op.drop_table('programme_session')
    op.drop_table('connection_report')
    op.drop_table('connection')
    op.execute("DROP TYPE IF EXISTS connection_status")
    op.drop_table('user_consent')
    op.drop_table('member_profile_interest')
    op.drop_table('member_profile_link')
    op.drop_table('member_profile')
    op.drop_table('checkin')
    op.drop_table('event_qr_token')
    op.drop_column('event', 'checkin_mode')
    op.drop_column('event', 'timezone')
