"""backfill checkin from confirmed attendance

Makes the `checkin` table the single source of truth for check-in status.
Historically, manual check-ins only set `attendance.confirmed = True` and never
created a `checkin` row, while QR check-ins created both. This backfills a
`checkin` row for every confirmed `attendance` that does not already have one,
so the unified check-in view reflects all historical check-ins.

Revision ID: a3c7e1f2b9d4
Revises: f9e8d7c6b5a4
Create Date: 2026-06-18 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'a3c7e1f2b9d4'
down_revision = 'f9e8d7c6b5a4'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        INSERT INTO checkin (event_id, user_id, checked_in_at, checked_in_by_user_id, method, day)
        SELECT a.event_id, a.user_id, a.timestamp, a.updated_by_user_id, 'manual', NULL
        FROM attendance a
        WHERE a.confirmed = true
        AND NOT EXISTS (
            SELECT 1 FROM checkin c
            WHERE c.event_id = a.event_id AND c.user_id = a.user_id
        );
        """
    )


def downgrade():
    # Data backfill is not safely reversible: removing 'manual' check-ins could
    # delete legitimate manual check-ins created after this migration ran.
    pass
