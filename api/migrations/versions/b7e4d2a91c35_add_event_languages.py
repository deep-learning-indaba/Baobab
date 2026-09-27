"""add event.languages; make event_resource_link.title_en optional

Revision ID: b7e4d2a91c35
Revises: 069d038b4527
Create Date: 2026-09-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7e4d2a91c35'
down_revision = '069d038b4527'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('event', sa.Column('languages', sa.JSON(), nullable=True))
    # Pin existing events to their organisation's current languages, so a language
    # added to the organisation later doesn't retroactively demand translations.
    op.execute("""
        UPDATE event SET languages = (
            SELECT json_agg(COALESCE(lang.value->>'code', lang.value#>>'{}') ORDER BY lang.ordinality)
            FROM organisation o,
                 json_array_elements(o.languages::json) WITH ORDINALITY AS lang(value, ordinality)
            WHERE o.id = event.organisation_id
        )
    """)
    op.alter_column('event_resource_link', 'title_en', existing_type=sa.String(length=160), nullable=True)


def downgrade():
    op.execute("UPDATE event_resource_link SET title_en = title_fr WHERE title_en IS NULL")
    op.alter_column('event_resource_link', 'title_en', existing_type=sa.String(length=160), nullable=False)
    op.drop_column('event', 'languages')
