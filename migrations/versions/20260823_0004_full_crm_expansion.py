"""full crm expansion for marinera dance studio

Revision ID: 20260823_0004
Revises: 20260820_0003
Create Date: 2026-08-23

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260823_0004"
down_revision: str | Sequence[str] | None = "20260820_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Expand clients
    op.add_column("clients", sa.Column("is_minor", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("clients", sa.Column("guardian_name", sa.String(length=200), nullable=True))
    op.add_column("clients", sa.Column("guardian_phone", sa.String(length=30), nullable=True))
    op.add_column("clients", sa.Column("guardian_relationship", sa.String(length=50), nullable=True))
    op.add_column("clients", sa.Column("guardian_dni", sa.String(length=8), nullable=True))
    op.add_column("clients", sa.Column("preferred_branch", sa.String(length=50), server_default="Los Olivos", nullable=True))
    op.add_column("clients", sa.Column("uninterested_reason", sa.String(length=100), nullable=True))

    # 2. Expand class_sessions
    op.add_column("class_sessions", sa.Column("branch", sa.String(length=50), server_default="Los Olivos", nullable=False))
    op.add_column("class_sessions", sa.Column("level", sa.String(length=50), server_default="intermedio", nullable=False))
    op.add_column("class_sessions", sa.Column("age_group", sa.String(length=50), server_default="todas las edades", nullable=False))
    op.add_column("class_sessions", sa.Column("shift_time", sa.String(length=50), nullable=True))
    op.add_column("class_sessions", sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=True))
    op.create_index("ix_class_sessions_branch", "class_sessions", ["branch"], unique=False)

    # 3. Create interactions
    op.create_table(
        "interactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.Uuid(), nullable=False),
        sa.Column("interaction_date", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("channel", sa.String(length=50), nullable=False),
        sa.Column("motive", sa.String(length=150), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("result", sa.String(length=50), nullable=False),
        sa.Column("uninterested_reason", sa.String(length=100), nullable=True),
        sa.Column("attended_by", sa.String(length=150), nullable=False),
        sa.Column("next_followup_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reminder_active", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_interactions_client_id", "interactions", ["client_id"], unique=False)
    op.create_index("ix_interactions_interaction_date", "interactions", ["interaction_date"], unique=False)
    op.create_index("ix_interactions_reminder_active", "interactions", ["reminder_active"], unique=False)

    # 4. Create memberships
    op.create_table(
        "memberships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.Uuid(), nullable=False),
        sa.Column("branch", sa.String(length=50), server_default="Los Olivos", nullable=False),
        sa.Column("class_type", sa.String(length=50), nullable=False),
        sa.Column("plan_name", sa.String(length=150), nullable=False),
        sa.Column("period_month", sa.String(length=7), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("classes_total", sa.Integer(), server_default="8", nullable=False),
        sa.Column("classes_attended", sa.Integer(), server_default="0", nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("discount_applied", sa.Numeric(precision=10, scale=2), server_default="0.00", nullable=False),
        sa.Column("final_price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("payment_status", sa.String(length=30), server_default="pending", nullable=False),
        sa.Column("status", sa.String(length=30), server_default="active", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_memberships_client_id", "memberships", ["client_id"], unique=False)
    op.create_index("ix_memberships_period_month", "memberships", ["period_month"], unique=False)
    op.create_index("ix_memberships_end_date", "memberships", ["end_date"], unique=False)
    op.create_index("ix_memberships_branch", "memberships", ["branch"], unique=False)

    # 5. Create payments
    op.create_table(
        "payments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.Uuid(), nullable=False),
        sa.Column("membership_id", sa.Uuid(), nullable=True),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("payment_date", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("period_month", sa.String(length=7), nullable=False),
        sa.Column("concept", sa.String(length=100), nullable=False),
        sa.Column("shift_detail", sa.String(length=100), nullable=True),
        sa.Column("payment_method", sa.String(length=30), nullable=False),
        sa.Column("transaction_reference", sa.String(length=100), nullable=True),
        sa.Column("branch", sa.String(length=50), server_default="Los Olivos", nullable=False),
        sa.Column("registered_by", sa.String(length=150), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="completed", nullable=False),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("cancelled_by", sa.String(length=150), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["membership_id"], ["memberships.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payments_client_id", "payments", ["client_id"], unique=False)
    op.create_index("ix_payments_period_month", "payments", ["period_month"], unique=False)
    op.create_index("ix_payments_branch", "payments", ["branch"], unique=False)
    op.create_index("ix_payments_payment_method", "payments", ["payment_method"], unique=False)
    op.create_index("ix_payments_status", "payments", ["status"], unique=False)

    # 6. Create users
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=30), server_default="admin_sede", nullable=False),
        sa.Column("branch", sa.String(length=50), server_default="Todas", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username", name="uq_users_username"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    # 7. Create audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.String(length=100), nullable=False),
        sa.Column("performed_by", sa.String(length=150), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"], unique=False)
    op.create_index("ix_audit_logs_performed_by", "audit_logs", ["performed_by"], unique=False)


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("users")
    op.drop_table("payments")
    op.drop_table("memberships")
    op.drop_table("interactions")
    op.drop_column("class_sessions", "price")
    op.drop_column("class_sessions", "shift_time")
    op.drop_column("class_sessions", "age_group")
    op.drop_column("class_sessions", "level")
    op.drop_column("class_sessions", "branch")
    op.drop_column("clients", "uninterested_reason")
    op.drop_column("clients", "preferred_branch")
    op.drop_column("clients", "guardian_dni")
    op.drop_column("clients", "guardian_relationship")
    op.drop_column("clients", "guardian_phone")
    op.drop_column("clients", "guardian_name")
    op.drop_column("clients", "is_minor")
