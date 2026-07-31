"""consolidate duplicate attendance rows and enforce one per event/user

An attendance row accumulates independent facts written by different flows:
indemnity signature, badge export and check-in confirmation. Where more than one
row exists for the same (event_id, user_id), each fact is stranded on whichever
row set it, and readers see only the half their lookup returns. This merges each
group down to a single row that carries the union of those facts, then adds the
constraint that keeps it that way.

Revision ID: c8a1d5e2f7b9
Revises: e7b3a95c1d48
Create Date: 2026-07-31 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'c8a1d5e2f7b9'
down_revision = 'e7b3a95c1d48'
branch_labels = None
depends_on = None


def upgrade():
    # Fold every duplicate group onto its lowest-id row. A fact is true for the
    # attendee if any row in the group asserts it, hence BOOL_OR throughout.
    op.execute(
        """
        WITH consolidated AS (
            SELECT
                a.event_id,
                a.user_id,
                MIN(a.id) AS keep_id,
                BOOL_OR(a.indemnity_signed) AS indemnity_signed,
                BOOL_OR(a.confirmed) AS confirmed,
                BOOL_OR(a.badge_exported) AS badge_exported,
                MAX(a.badge_exported_at) AS badge_exported_at,
                COALESCE(
                    MIN(a."timestamp") FILTER (WHERE a.indemnity_signed),
                    MIN(a."timestamp")
                ) AS ts,
                (ARRAY_AGG(a.updated_by_user_id ORDER BY a.id DESC))[1] AS updated_by_user_id
            FROM attendance a
            GROUP BY a.event_id, a.user_id
            HAVING COUNT(*) > 1
        )
        UPDATE attendance a
        SET indemnity_signed = c.indemnity_signed,
            confirmed = c.confirmed,
            badge_exported = c.badge_exported,
            badge_exported_at = c.badge_exported_at,
            "timestamp" = c.ts,
            updated_by_user_id = c.updated_by_user_id
        FROM consolidated c
        WHERE a.id = c.keep_id;
        """
    )

    op.execute(
        """
        DELETE FROM attendance a
        USING (
            SELECT event_id, user_id, MIN(id) AS keep_id
            FROM attendance
            GROUP BY event_id, user_id
        ) k
        WHERE a.event_id = k.event_id
          AND a.user_id = k.user_id
          AND a.id <> k.keep_id;
        """
    )

    op.create_unique_constraint(
        'uq_attendance_event_user', 'attendance', ['event_id', 'user_id'])


def downgrade():
    op.drop_constraint('uq_attendance_event_user', 'attendance', type_='unique')
