from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.client import Client
from backend.app.models.client_discount import ClientDiscount
from backend.app.models.membership import Membership
from backend.app.models.payment import Payment
from backend.app.repositories.membership import MembershipRepository
from backend.app.schemas.dashboard import (
    AcquisitionChannelStat,
    MonthlyDashboardRead,
    MonthlySalesComparisonItem,
    RevenueByModality,
)


class DashboardService:
    """Computes operational and managerial analytics as specified in Section 7."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.membership_repo = MembershipRepository(db)

    def get_monthly_dashboard(
        self, period_month: str | None = None, branch: str = "Todas"
    ) -> MonthlyDashboardRead:
        if not period_month:
            period_month = datetime.now().strftime("%Y-%m")

        # 1. Total Revenue for selected month
        payments_query = select(Payment).where(
            Payment.period_month == period_month,
            Payment.status == "completed",
        )
        if branch != "Todas":
            payments_query = payments_query.where(Payment.branch == branch)
        payments = list(self.db.scalars(payments_query))
        total_revenue = sum((p.amount for p in payments), Decimal("0.00"))

        # 2. Clients Statistics for this month
        year_str, month_str = period_month.split("-")
        target_year, target_month = int(year_str), int(month_str)

        clients_query = select(Client)
        if branch != "Todas":
            clients_query = clients_query.where(Client.preferred_branch == branch)
        all_clients = list(self.db.scalars(clients_query))

        active_clients = sum(1 for c in all_clients if c.status == "active" and c.is_active)
        retired_clients = sum(
            1
            for c in all_clients
            if c.status == "retired"
            or (not c.is_active and c.updated_at.year == target_year and c.updated_at.month == target_month)
        )
        new_clients = sum(
            1
            for c in all_clients
            if c.created_at.year == target_year and c.created_at.month == target_month
        )

        # 3. 3-Month Sales and Clients Comparison (Section 7.2, 7.3, 7.4)
        month_names = [
            "",
            "Enero",
            "Febrero",
            "Marzo",
            "Abril",
            "Mayo",
            "Junio",
            "Julio",
            "Agosto",
            "Septiembre",
            "Octubre",
            "Noviembre",
            "Diciembre",
        ]

        three_months_sales: list[MonthlySalesComparisonItem] = []
        for i in range(2, -1, -1):
            m = target_month - i
            y = target_year
            while m <= 0:
                m += 12
                y -= 1
            month_key = f"{y:04d}-{m:02d}"
            name = f"{month_names[m]} {y}"

            m_payments_stmt = select(Payment).where(
                Payment.period_month == month_key,
                Payment.status == "completed",
            )
            if branch != "Todas":
                m_payments_stmt = m_payments_stmt.where(Payment.branch == branch)
            m_payments = list(self.db.scalars(m_payments_stmt))
            m_total = sum((p.amount for p in m_payments), Decimal("0.00"))

            m_new = sum(1 for c in all_clients if c.created_at.year == y and c.created_at.month == m)
            m_ret = sum(
                1
                for c in all_clients
                if c.status == "retired"
                and c.updated_at.year == y
                and c.updated_at.month == m
            )

            three_months_sales.append(
                MonthlySalesComparisonItem(
                    period_month=month_key,
                    month_name=name,
                    total_sales=m_total,
                    clients_new=m_new,
                    clients_retired=m_ret,
                )
            )

        # 4. Revenue by Class Type / Modality (Section 7.5)
        modality_totals: dict[str, dict[str, object]] = {
            "mensualidad": {
                "label": "Mensualidad Grupal (8 clases)",
                "total": Decimal("0.00"),
                "count": 0,
            },
            "clase_libre": {
                "label": "Clase Libre",
                "total": Decimal("0.00"),
                "count": 0,
            },
            "paquete_particular": {
                "label": "Clases Particulares",
                "total": Decimal("0.00"),
                "count": 0,
            },
            "matricula": {
                "label": "Matrícula",
                "total": Decimal("0.00"),
                "count": 0,
            },
            "otro": {
                "label": "Otros Conceptos",
                "total": Decimal("0.00"),
                "count": 0,
            },
        }

        for p in payments:
            c = p.concept
            if c not in modality_totals:
                c = "otro"
            modality_totals[c]["total"] += p.amount
            modality_totals[c]["count"] += 1

        revenue_by_modality: list[RevenueByModality] = []
        for mod, val in modality_totals.items():
            tot = val["total"]
            pct = float((tot / total_revenue * 100)) if total_revenue > 0 else 0.0
            revenue_by_modality.append(
                RevenueByModality(
                    modality=mod,
                    label=str(val["label"]),
                    total_amount=tot,
                    percentage=round(pct, 1),
                    transactions_count=int(val["count"]),
                )
            )

        # 5. Clients by Acquisition Source (Section 7.6)
        source_counts: dict[str, dict[str, object]] = {
            "whatsapp": {"label": "WhatsApp", "count": 0},
            "presencial": {"label": "Presencial / Local", "count": 0},
            "instagram": {"label": "Instagram", "count": 0},
            "tiktok": {"label": "Tik Tok", "count": 0},
            "referral": {"label": "Referidos", "count": 0},
            "web": {"label": "Página Web", "count": 0},
            "other": {"label": "Otros", "count": 0},
        }

        for c in all_clients:
            s = c.acquisition_source
            if s in ["walk_in", "in_person"]:
                s = "presencial"
            elif s in ["social_media"]:
                s = "instagram"
            elif s in ["website"]:
                s = "web"
            elif s not in source_counts:
                s = "other"
            source_counts[s]["count"] += 1

        total_clients_count = len(all_clients)
        acquisition_channels: list[AcquisitionChannelStat] = []
        for src, data in source_counts.items():
            cnt = int(data["count"])
            pct = round((cnt / total_clients_count * 100), 1) if total_clients_count > 0 else 0.0
            acquisition_channels.append(
                AcquisitionChannelStat(
                    source=src,
                    label=str(data["label"]),
                    clients_count=cnt,
                    percentage=pct,
                )
            )

        # 6. Automated Alerts & Queries (Section 7.7)
        expiring = self.membership_repo.list_expiring_soon(days_threshold=5, branch=branch)
        pending_count = self.membership_repo.count_pending_payments(
            period_month=period_month, branch=branch
        )

        discounts_stmt = select(ClientDiscount)
        discounts = list(self.db.scalars(discounts_stmt))
        total_discounts = sum((d.discount_value for d in discounts), Decimal("0.00"))

        return MonthlyDashboardRead(
            period_month=period_month,
            branch_filter=branch,
            new_clients=new_clients,
            active_clients=active_clients,
            retired_clients=retired_clients,
            total_revenue=total_revenue,
            three_months_sales=three_months_sales,
            revenue_by_modality=revenue_by_modality,
            acquisition_channels=acquisition_channels,
            expiring_memberships_count=len(expiring),
            pending_payments_count=pending_count,
            total_discounts_granted=total_discounts,
        )
