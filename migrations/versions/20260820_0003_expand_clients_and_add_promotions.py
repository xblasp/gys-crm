"""expand clients and add promotions

Revision ID: 20260820_0003
Revises: 20260820_0002
Create Date: 2026-08-20

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260820_0003"
down_revision: str | Sequence[str] | None = "20260820_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("clients", sa.Column("dni", sa.String(length=8), nullable=True))
    op.add_column("clients", sa.Column("whatsapp", sa.String(length=30), nullable=True))
    op.add_column("clients", sa.Column("birth_year", sa.Integer(), nullable=True))
    op.add_column(
        "clients",
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="interested",
            nullable=False,
        ),
    )
    op.add_column("clients", sa.Column("referrer_phone", sa.String(length=30), nullable=True))
    op.execute("UPDATE clients SET status = 'retired' WHERE is_active = false")
    op.create_index("ix_clients_dni", "clients", ["dni"], unique=True)
    op.create_index("ix_clients_status", "clients", ["status"], unique=False)
    op.create_check_constraint(
        "ck_clients_status",
        "clients",
        "status IN ('interested', 'active', 'retired')",
    )

    op.create_table(
        "promotions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("discount_type", sa.String(length=30), nullable=False),
        sa.Column("discount_value", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "discount_type IN ('fixed_amount', 'percentage', 'enrollment_fee_waiver')",
            name="ck_promotions_discount_type",
        ),
        sa.CheckConstraint(
            "(discount_type = 'enrollment_fee_waiver' AND discount_value = 0) "
            "OR (discount_type != 'enrollment_fee_waiver' AND discount_value > 0)",
            name="ck_promotions_discount_value",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_promotions_name"),
    )
    op.create_index("ix_promotions_is_active", "promotions", ["is_active"], unique=False)

    op.create_table(
        "client_discounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.Uuid(), nullable=False),
        sa.Column("promotion_id", sa.Uuid(), nullable=True),
        sa.Column("promotion_name", sa.String(length=150), nullable=False),
        sa.Column("discount_type", sa.String(length=30), nullable=False),
        sa.Column("discount_value", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("applies_to", sa.String(length=30), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("applied_by", sa.String(length=150), nullable=False),
        sa.Column(
            "applied_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "discount_type IN ('fixed_amount', 'percentage', 'enrollment_fee_waiver')",
            name="ck_client_discounts_discount_type",
        ),
        sa.CheckConstraint(
            "(discount_type = 'enrollment_fee_waiver' AND discount_value = 0) "
            "OR (discount_type != 'enrollment_fee_waiver' AND discount_value > 0)",
            name="ck_client_discounts_discount_value",
        ),
        sa.CheckConstraint(
            "applies_to IN ('enrollment', 'membership', 'other')",
            name="ck_client_discounts_applies_to",
        ),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["promotion_id"], ["promotions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_client_discounts_client_id", "client_discounts", ["client_id"], unique=False)
    op.create_index(
        "ix_client_discounts_promotion_id", "client_discounts", ["promotion_id"], unique=False
    )
    op.create_index(
        "ix_client_discounts_applied_at", "client_discounts", ["applied_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_client_discounts_applied_at", table_name="client_discounts")
    op.drop_index("ix_client_discounts_promotion_id", table_name="client_discounts")
    op.drop_index("ix_client_discounts_client_id", table_name="client_discounts")
    op.drop_table("client_discounts")
    op.drop_index("ix_promotions_is_active", table_name="promotions")
    op.drop_table("promotions")
    op.drop_constraint("ck_clients_status", "clients", type_="check")
    op.drop_index("ix_clients_status", table_name="clients")
    op.drop_index("ix_clients_dni", table_name="clients")
    op.drop_column("clients", "referrer_phone")
    op.drop_column("clients", "status")
    op.drop_column("clients", "birth_year")
    op.drop_column("clients", "whatsapp")
    op.drop_column("clients", "dni")
