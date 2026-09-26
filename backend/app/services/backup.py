import csv
import io
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.app.models.class_session import ClassSession
from backend.app.models.client import Client
from backend.app.models.client_discount import ClientDiscount
from backend.app.models.enrollment import Enrollment
from backend.app.models.interaction import Interaction
from backend.app.models.membership import Membership
from backend.app.models.payment import Payment
from backend.app.models.promotion import Promotion
from backend.app.models.user import User


class BackupService:
    """Service to export and import full database backups and client CSV spreadsheets."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def export_full_database(self) -> dict[str, Any]:
        """Serializes all CRM tables into a portable JSON snapshot."""
        now = datetime.now()

        clients = list(self.db.scalars(select(Client)))
        interactions = list(self.db.scalars(select(Interaction)))
        classes = list(self.db.scalars(select(ClassSession)))
        enrollments = list(self.db.scalars(select(Enrollment)))
        memberships = list(self.db.scalars(select(Membership)))
        payments = list(self.db.scalars(select(Payment)))
        promotions = list(self.db.scalars(select(Promotion)))
        discounts = list(self.db.scalars(select(ClientDiscount)))
        users = list(self.db.scalars(select(User)))

        def serialize_val(val: Any) -> Any:
            if isinstance(val, uuid.UUID):
                return str(val)
            if isinstance(val, (datetime, date)):
                return val.isoformat()
            if isinstance(val, Decimal):
                return float(val)
            return val

        def model_to_dict(obj: Any) -> dict[str, Any]:
            res = {}
            for col in obj.__table__.columns:
                res[col.name] = serialize_val(getattr(obj, col.name))
            return res

        return {
            "metadata": {
                "version": "1.0",
                "application": "GyS CRM — Garbo & Salero Semillero de Campeones",
                "exported_at": now.isoformat(),
                "counts": {
                    "clients": len(clients),
                    "interactions": len(interactions),
                    "class_sessions": len(classes),
                    "enrollments": len(enrollments),
                    "memberships": len(memberships),
                    "payments": len(payments),
                    "promotions": len(promotions),
                    "client_discounts": len(discounts),
                    "users": len(users),
                },
            },
            "data": {
                "users": [model_to_dict(u) for u in users],
                "promotions": [model_to_dict(p) for p in promotions],
                "clients": [model_to_dict(c) for c in clients],
                "interactions": [model_to_dict(i) for i in interactions],
                "class_sessions": [model_to_dict(cl) for cl in classes],
                "enrollments": [model_to_dict(e) for e in enrollments],
                "memberships": [model_to_dict(m) for m in memberships],
                "payments": [model_to_dict(p) for p in payments],
                "client_discounts": [model_to_dict(d) for d in discounts],
            },
        }

    def import_full_database(self, data: dict[str, Any], mode: str = "merge") -> dict[str, Any]:
        """Restores a JSON snapshot into the database."""
        raw_data = data.get("data", data)
        imported_stats: dict[str, int] = {}

        def parse_dt(v: Any) -> datetime | None:
            if not v:
                return None
            try:
                return datetime.fromisoformat(v)
            except Exception:
                return None

        def parse_d(v: Any) -> date | None:
            if not v:
                return None
            try:
                return date.fromisoformat(v) if isinstance(v, str) else v
            except Exception:
                return None

        def parse_uuid(v: Any) -> uuid.UUID | None:
            if not v:
                return None
            return uuid.UUID(str(v)) if not isinstance(v, uuid.UUID) else v

        def parse_dec(v: Any) -> Decimal:
            if v is None:
                return Decimal("0.00")
            return Decimal(str(v))

        # 1. Promotions
        for p_dict in raw_data.get("promotions", []):
            p_id = parse_uuid(p_dict.get("id")) or uuid.uuid4()
            existing = self.db.get(Promotion, p_id)
            if not existing:
                existing = self.db.scalar(select(Promotion).where(Promotion.name == p_dict.get("name")))
            if not existing:
                p = Promotion(
                    id=p_id,
                    name=p_dict["name"],
                    description=p_dict.get("description"),
                    discount_type=p_dict.get("discount_type", "fixed_amount"),
                    discount_value=parse_dec(p_dict.get("discount_value", 0)),
                    is_active=p_dict.get("is_active", True),
                )
                self.db.add(p)
                imported_stats["promotions"] = imported_stats.get("promotions", 0) + 1

        # 2. Clients
        for c_dict in raw_data.get("clients", []):
            c_id = parse_uuid(c_dict.get("id")) or uuid.uuid4()
            existing = self.db.get(Client, c_id)
            if not existing and c_dict.get("dni"):
                existing = self.db.scalar(select(Client).where(Client.dni == c_dict.get("dni")))
            if not existing:
                c = Client(
                    id=c_id,
                    first_name=c_dict.get("first_name", "Sin Nombre"),
                    last_name=c_dict.get("last_name", "Sin Apellido"),
                    dni=c_dict.get("dni"),
                    phone=c_dict.get("phone"),
                    whatsapp=c_dict.get("whatsapp") or c_dict.get("phone"),
                    email=c_dict.get("email"),
                    birth_year=c_dict.get("birth_year"),
                    is_minor=c_dict.get("is_minor", False),
                    guardian_name=c_dict.get("guardian_name"),
                    guardian_phone=c_dict.get("guardian_phone"),
                    guardian_relationship=c_dict.get("guardian_relationship"),
                    guardian_dni=c_dict.get("guardian_dni"),
                    preferred_branch=c_dict.get("preferred_branch", "Los Olivos"),
                    status=c_dict.get("status", "interested"),
                    acquisition_source=c_dict.get("acquisition_source", "other"),
                    referrer_name=c_dict.get("referrer_name"),
                    referrer_phone=c_dict.get("referrer_phone"),
                    uninterested_reason=c_dict.get("uninterested_reason"),
                    notes=c_dict.get("notes"),
                    is_active=c_dict.get("is_active", True),
                )
                self.db.add(c)
                imported_stats["clients"] = imported_stats.get("clients", 0) + 1

        self.db.flush()

        # 3. Class Sessions
        for cl_dict in raw_data.get("class_sessions", []):
            cl_id = parse_uuid(cl_dict.get("id")) or uuid.uuid4()
            existing = self.db.get(ClassSession, cl_id)
            if not existing:
                cl = ClassSession(
                    id=cl_id,
                    name=cl_dict["name"],
                    class_type=cl_dict.get("class_type", "group"),
                    branch=cl_dict.get("branch", "Los Olivos"),
                    level=cl_dict.get("level", "intermedio"),
                    age_group=cl_dict.get("age_group", "todas las edades"),
                    shift_time=cl_dict.get("shift_time"),
                    starts_at=parse_dt(cl_dict.get("starts_at")) or datetime.now(),
                    ends_at=parse_dt(cl_dict.get("ends_at")),
                    capacity=cl_dict.get("capacity", 15),
                    price=parse_dec(cl_dict.get("price")) if cl_dict.get("price") else None,
                    instructor_name=cl_dict.get("instructor_name"),
                    notes=cl_dict.get("notes"),
                    is_cancelled=cl_dict.get("is_cancelled", False),
                )
                self.db.add(cl)
                imported_stats["class_sessions"] = imported_stats.get("class_sessions", 0) + 1

        # 4. Enrollments
        for e_dict in raw_data.get("enrollments", []):
            e_id = parse_uuid(e_dict.get("id")) or uuid.uuid4()
            if not self.db.get(Enrollment, e_id):
                en = Enrollment(
                    id=e_id,
                    client_id=parse_uuid(e_dict["client_id"]),
                    class_session_id=parse_uuid(e_dict["class_session_id"]),
                    status=e_dict.get("status", "booked"),
                    notes=e_dict.get("notes"),
                )
                self.db.add(en)
                imported_stats["enrollments"] = imported_stats.get("enrollments", 0) + 1

        # 5. Memberships
        for m_dict in raw_data.get("memberships", []):
            m_id = parse_uuid(m_dict.get("id")) or uuid.uuid4()
            if not self.db.get(Membership, m_id):
                mem = Membership(
                    id=m_id,
                    client_id=parse_uuid(m_dict["client_id"]),
                    branch=m_dict.get("branch", "Los Olivos"),
                    class_type=m_dict.get("class_type", "grupal_mensual"),
                    plan_name=m_dict.get("plan_name", "Plan Mensual"),
                    period_month=m_dict.get("period_month", datetime.now().strftime("%Y-%m")),
                    start_date=parse_d(m_dict.get("start_date")) or date.today(),
                    end_date=parse_d(m_dict.get("end_date")) or date.today(),
                    classes_total=m_dict.get("classes_total", 8),
                    classes_attended=m_dict.get("classes_attended", 0),
                    price=parse_dec(m_dict.get("price", 150)),
                    discount_applied=parse_dec(m_dict.get("discount_applied", 0)),
                    final_price=parse_dec(m_dict.get("final_price", 150)),
                    payment_status=m_dict.get("payment_status", "pending"),
                    status=m_dict.get("status", "active"),
                    notes=m_dict.get("notes"),
                    is_active=m_dict.get("is_active", True),
                )
                self.db.add(mem)
                imported_stats["memberships"] = imported_stats.get("memberships", 0) + 1

        # 6. Payments
        for p_dict in raw_data.get("payments", []):
            pay_id = parse_uuid(p_dict.get("id")) or uuid.uuid4()
            if not self.db.get(Payment, pay_id):
                payment = Payment(
                    id=pay_id,
                    client_id=parse_uuid(p_dict["client_id"]),
                    membership_id=parse_uuid(p_dict.get("membership_id")),
                    amount=parse_dec(p_dict.get("amount", 0)),
                    payment_date=parse_dt(p_dict.get("payment_date")) or datetime.now(),
                    period_month=p_dict.get("period_month", datetime.now().strftime("%Y-%m")),
                    concept=p_dict.get("concept", "mensualidad"),
                    shift_detail=p_dict.get("shift_detail"),
                    payment_method=p_dict.get("payment_method", "yape"),
                    transaction_reference=p_dict.get("transaction_reference"),
                    branch=p_dict.get("branch", "Los Olivos"),
                    registered_by=p_dict.get("registered_by", "Administrador"),
                    status=p_dict.get("status", "completed"),
                    cancellation_reason=p_dict.get("cancellation_reason"),
                    cancelled_by=p_dict.get("cancelled_by"),
                    cancelled_at=parse_dt(p_dict.get("cancelled_at")),
                    notes=p_dict.get("notes"),
                )
                self.db.add(payment)
                imported_stats["payments"] = imported_stats.get("payments", 0) + 1

        # 7. Interactions
        for i_dict in raw_data.get("interactions", []):
            i_id = parse_uuid(i_dict.get("id")) or uuid.uuid4()
            if not self.db.get(Interaction, i_id):
                interaction = Interaction(
                    id=i_id,
                    client_id=parse_uuid(i_dict["client_id"]),
                    interaction_date=parse_dt(i_dict.get("interaction_date")) or datetime.now(),
                    channel=i_dict.get("channel", "whatsapp"),
                    motive=i_dict.get("motive", "precios_y_horarios"),
                    summary=i_dict.get("summary", "Registro importado"),
                    result=i_dict.get("result", "pidio_informacion"),
                    uninterested_reason=i_dict.get("uninterested_reason"),
                    attended_by=i_dict.get("attended_by", "Administrador"),
                    next_followup_date=parse_dt(i_dict.get("next_followup_date")),
                    reminder_active=i_dict.get("reminder_active", False),
                )
                self.db.add(interaction)
                imported_stats["interactions"] = imported_stats.get("interactions", 0) + 1

        self.db.commit()
        return {
            "status": "success",
            "message": "Base de datos cargada y sincronizada exitosamente.",
            "imported_counts": imported_stats,
        }

    def export_clients_csv(self) -> str:
        """Generates a CSV string of all clients with UTF-8 BOM support for Excel."""
        output = io.StringIO()
        writer = csv.writer(output, delimiter=",", quoting=csv.QUOTE_MINIMAL)

        writer.writerow([
            "Nombres",
            "Apellidos",
            "DNI",
            "WhatsApp",
            "Telefono",
            "Email",
            "Anio_Nacimiento",
            "Es_Menor",
            "Nombre_Apoderado",
            "Telefono_Apoderado",
            "Parentesco_Apoderado",
            "DNI_Apoderado",
            "Sede_Preferida",
            "Estado",
            "Origen_Captacion",
            "Referido_Por_Nombre",
            "Referido_Por_Telefono",
            "Notas",
        ])

        clients = list(self.db.scalars(select(Client).order_by(Client.last_name, Client.first_name)))
        for c in clients:
            writer.writerow([
                c.first_name,
                c.last_name,
                c.dni or "",
                c.whatsapp or "",
                c.phone or "",
                c.email or "",
                c.birth_year or "",
                "SI" if c.is_minor else "NO",
                c.guardian_name or "",
                c.guardian_phone or "",
                c.guardian_relationship or "",
                c.guardian_dni or "",
                c.preferred_branch or "Los Olivos",
                c.status or "interested",
                c.acquisition_source or "other",
                c.referrer_name or "",
                c.referrer_phone or "",
                c.notes or "",
            ])

        return output.getvalue()

    def import_clients_csv(self, csv_content: str) -> dict[str, Any]:
        """Parses a CSV string, automatically mapping headers and creating clients."""
        # Detect delimiter (comma, semicolon or tab)
        first_line = csv_content.splitlines()[0] if csv_content.splitlines() else ""
        delimiter = ";" if ";" in first_line else ("\t" if "\t" in first_line else ",")

        f = io.StringIO(csv_content.strip())
        reader = csv.reader(f, delimiter=delimiter)
        rows = list(reader)
        if not rows:
            return {"status": "error", "message": "El archivo CSV está vacío."}

        headers = [h.strip().lower().replace(" ", "_").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n") for h in rows[0]]

        # Map header indices
        def find_idx(*aliases: str) -> int:
            for alias in aliases:
                for idx, h in enumerate(headers):
                    if alias in h:
                        return idx
            return -1

        idx_fname = find_idx("nombre", "first_name", "nombres")
        idx_lname = find_idx("apellido", "last_name", "apellidos")
        idx_dni = find_idx("dni", "documento", "cedula")
        idx_wsp = find_idx("whatsapp", "wsp", "celular", "movil")
        idx_phone = find_idx("telefono", "phone", "fijo")
        idx_email = find_idx("email", "correo")
        idx_year = find_idx("nacimiento", "anio", "edad", "birth")
        idx_minor = find_idx("menor", "is_minor")
        idx_gname = find_idx("nombre_apoderado", "apoderado", "tutor", "padre", "madre")
        idx_gphone = find_idx("telefono_apoderado", "celular_apoderado", "wsp_apoderado")
        idx_grel = find_idx("parentesco", "relacion")
        idx_gdni = find_idx("dni_apoderado", "doc_apoderado")
        idx_branch = find_idx("sede", "sucursal", "local", "branch")
        idx_status = find_idx("estado", "status")
        idx_source = find_idx("origen", "canal", "fuente", "medio", "source")
        idx_ref_name = find_idx("referido_nombre", "recomendado_por", "referido_por", "referrer")
        idx_ref_phone = find_idx("referido_telefono", "telefono_referido", "contacto_referido")
        idx_notes = find_idx("nota", "observacion", "comentario")

        if idx_fname == -1:
            return {"status": "error", "message": "No se encontró la columna de Nombres en el archivo CSV."}

        imported_count = 0
        updated_count = 0
        current_year = datetime.now().year

        for row in rows[1:]:
            if not row or not any(field.strip() for field in row):
                continue

            def get_val(idx: int, default: str = "") -> str:
                if idx != -1 and idx < len(row):
                    return row[idx].strip()
                return default

            first_name = get_val(idx_fname)
            last_name = get_val(idx_lname, " ")
            if not first_name:
                continue

            dni_val = get_val(idx_dni) or None
            if dni_val:
                dni_val = "".join(filter(str.isdigit, dni_val))[:8] or None

            phone_val = get_val(idx_phone) or None
            wsp_val = get_val(idx_wsp) or phone_val

            year_val = None
            raw_year = get_val(idx_year)
            if raw_year and raw_year.isdigit():
                val = int(raw_year)
                if 1900 <= val <= 2026:
                    year_val = val
                elif 1 <= val <= 90:  # age given instead of year
                    year_val = current_year - val

            is_minor_val = False
            raw_minor = get_val(idx_minor).upper()
            if raw_minor in ["SI", "S", "TRUE", "1", "YES", "Y"] or (year_val and (current_year - year_val) < 18):
                is_minor_val = True

            branch_val = get_val(idx_branch, "Los Olivos")
            if "comas" in branch_val.lower():
                branch_val = "Comas"
            else:
                branch_val = "Los Olivos"

            status_val = get_val(idx_status, "interested").lower()
            if "act" in status_val or "matriculad" in status_val:
                status_val = "active"
            elif "ret" in status_val or "inact" in status_val or "baja" in status_val:
                status_val = "retired"
            else:
                status_val = "interested"

            source_val = get_val(idx_source, "other").lower()
            if "what" in source_val: source_val = "whatsapp"
            elif "pres" in source_val or "local" in source_val: source_val = "presencial"
            elif "insta" in source_val: source_val = "instagram"
            elif "tik" in source_val: source_val = "tiktok"
            elif "ref" in source_val or "recom" in source_val: source_val = "referral"
            elif "web" in source_val: source_val = "web"
            else: source_val = "other"

            # Check existing by DNI or phone
            existing_client = None
            if dni_val:
                existing_client = self.db.scalar(select(Client).where(Client.dni == dni_val))
            if not existing_client and wsp_val:
                existing_client = self.db.scalar(select(Client).where(Client.whatsapp == wsp_val))

            if existing_client:
                existing_client.first_name = first_name
                existing_client.last_name = last_name or existing_client.last_name
                existing_client.phone = phone_val or existing_client.phone
                existing_client.whatsapp = wsp_val or existing_client.whatsapp
                existing_client.preferred_branch = branch_val
                existing_client.status = status_val
                if is_minor_val:
                    existing_client.is_minor = True
                    existing_client.guardian_name = get_val(idx_gname) or existing_client.guardian_name
                    existing_client.guardian_phone = get_val(idx_gphone) or existing_client.guardian_phone
                updated_count += 1
            else:
                new_client = Client(
                    first_name=first_name,
                    last_name=last_name,
                    dni=dni_val,
                    phone=phone_val,
                    whatsapp=wsp_val,
                    email=get_val(idx_email) or None,
                    birth_year=year_val,
                    is_minor=is_minor_val,
                    guardian_name=get_val(idx_gname) or None,
                    guardian_phone=get_val(idx_gphone) or None,
                    guardian_relationship=get_val(idx_grel) or None,
                    guardian_dni=get_val(idx_gdni) or None,
                    preferred_branch=branch_val,
                    status=status_val,
                    acquisition_source=source_val,
                    referrer_name=get_val(idx_ref_name) or None,
                    referrer_phone=get_val(idx_ref_phone) or None,
                    notes=get_val(idx_notes) or "Importado masivamente vía CSV",
                    is_active=(status_val != "retired"),
                )
                self.db.add(new_client)
                imported_count += 1

        self.db.commit()
        return {
            "status": "success",
            "message": f"Proceso completado: {imported_count} alumnos nuevos importados, {updated_count} alumnos actualizados.",
            "imported_count": imported_count,
            "updated_count": updated_count,
            "total_processed": imported_count + updated_count,
        }
