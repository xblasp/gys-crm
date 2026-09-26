from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class RevenueByModality(BaseModel):
    modality: str  # mensualidad_grupal, clase_libre, particulares, matricula, otros
    label: str
    total_amount: Decimal
    percentage: float
    transactions_count: int


class AcquisitionChannelStat(BaseModel):
    source: str
    label: str
    clients_count: int
    percentage: float


class MonthlySalesComparisonItem(BaseModel):
    period_month: str  # YYYY-MM
    month_name: str
    total_sales: Decimal
    clients_new: int
    clients_retired: int


class MonthlyDashboardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    period_month: str
    branch_filter: str
    
    # 4 Key Monthly Metrics (Section 7.1)
    new_clients: int
    active_clients: int
    retired_clients: int
    total_revenue: Decimal

    # 3-Month Sales Comparison (Section 7.2)
    three_months_sales: list[MonthlySalesComparisonItem]

    # Revenue by Class Type / Modality (Section 7.5)
    revenue_by_modality: list[RevenueByModality]

    # Clients by Acquisition Source (Section 7.6)
    acquisition_channels: list[AcquisitionChannelStat]

    # Automated Answers / Alerts (Section 7.7)
    expiring_memberships_count: int  # Vencen en próximos 5 días
    pending_payments_count: int
    total_discounts_granted: Decimal
