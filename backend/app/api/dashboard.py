"""
GyS CRM — Router del Dashboard Mensual y Métricas Gerenciales
============================================================
Calcula y consolida en tiempo real todos los indicadores clave (KPIs) del taller:
- Ingresos netos del mes y comparativa trimestral
- Alumnos activos, nuevos inscritos y bajas / retiros (churn rate)
- Distribución de ingresos por modalidad de clase y canales de captación
- Alertas de vencimientos a 5 días y recordatorios de CRM
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.dashboard import MonthlyDashboardRead
from backend.app.services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Analytics"])

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("/monthly", response_model=MonthlyDashboardRead)
def get_monthly_dashboard(
    db: DatabaseSession,
    period_month: Annotated[str | None, Query(pattern=r"^\d{4}-\d{2}$")] = None,
    branch: str = "Todas",
) -> MonthlyDashboardRead:
    """
    Obtiene el consolidado mensual de métricas gerenciales y operativas.
    
    Permite filtrar por periodo ('YYYY-MM') y sede ('Todas', 'Los Olivos', 'Comas').
    """
    return DashboardService(db).get_monthly_dashboard(period_month=period_month, branch=branch)
