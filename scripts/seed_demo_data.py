"""Realistic demonstration dataset generator for GyS CRM.

Populates last 3 months (Junio, Julio, Agosto 2026):
- Los Olivos: 6 inscriptions in June, 10 in July, 2 in August.
- Comas (inverted): 2 inscriptions in June, 10 in July, 6 in August.
- Generates recurring memberships and completed payments for history.
- Generates pending memberships expiring in <= 5 days for August demo.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import delete
from sqlalchemy.orm import Session

from backend.app.db.base import Base
from backend.app.db.session import SessionLocal, engine
from backend.app.models.class_session import ClassSession
from backend.app.models.client import Client
from backend.app.models.enrollment import Enrollment
from backend.app.models.interaction import Interaction
from backend.app.models.membership import Membership
from backend.app.models.payment import Payment
from backend.app.models.promotion import Promotion
from backend.app.models.user import User
from backend.app.services.auth import AuthService


def clear_and_seed_database(db: Session | None = None) -> None:
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        Base.metadata.create_all(bind=engine)

        # 1. Clear existing dynamic data
        db.execute(delete(Enrollment))
        db.execute(delete(Interaction))
        db.execute(delete(Payment))
        db.execute(delete(Membership))
        db.execute(delete(Client))
        db.execute(delete(ClassSession))
        db.execute(delete(Promotion))
        db.commit()

        # 2. Seed Users
        auth_service = AuthService(db)
        auth_service.seed_initial_users_if_empty()

        # 3. Seed Promotions
        promos = [
            Promotion(
                name="Descuento de S/ 20 por recomendación",
                description="Descuento aplicado al alumno por traer un amigo/familiar referido.",
                discount_type="fixed_amount",
                discount_value=Decimal("20.00"),
                is_active=True,
            ),
            Promotion(
                name="Exoneración de Matrícula",
                description="Matrícula 100% gratuita por campaña promocional.",
                discount_type="enrollment_fee_waiver",
                discount_value=Decimal("0.00"),
                is_active=True,
            ),
            Promotion(
                name="Descuento 10% Hermanos",
                description="10% de descuento para el segundo hermano matriculado.",
                discount_type="percentage",
                discount_value=Decimal("10.00"),
                is_active=True,
            ),
        ]
        db.add_all(promos)
        db.commit()

        # 4. Seed Classes for both branches
        now = datetime.now()
        cls_olivos_1 = ClassSession(
            name="Marinera Infantil Semillero (4-11 años)",
            class_type="group",
            branch="Los Olivos",
            level="inicial",
            age_group="infantil",
            shift_time="Lunes y Miércoles 4:00 - 5:30 PM",
            starts_at=now + timedelta(days=1, hours=16),
            ends_at=now + timedelta(days=1, hours=17, minutes=30),
            capacity=15,
            price=Decimal("150.00"),
            instructor_name="Prof. Carlos Mendoza",
            notes="Sede Los Olivos - Salón Principal",
        )
        cls_olivos_2 = ClassSession(
            name="Marinera Juvenil & Adultos (12+ años)",
            class_type="group",
            branch="Los Olivos",
            level="intermedio",
            age_group="juvenil",
            shift_time="Martes y Jueves 6:30 - 8:00 PM",
            starts_at=now + timedelta(days=2, hours=18, minutes=30),
            ends_at=now + timedelta(days=2, hours=20),
            capacity=18,
            price=Decimal("150.00"),
            instructor_name="Prof. Andrea Benavides",
            notes="Sede Los Olivos",
        )
        cls_comas_1 = ClassSession(
            name="Marinera Infantil & Juvenil Comas",
            class_type="group",
            branch="Comas",
            level="inicial",
            age_group="infantil",
            shift_time="Lunes y Miércoles 5:00 - 6:30 PM",
            starts_at=now + timedelta(days=1, hours=17),
            ends_at=now + timedelta(days=1, hours=18, minutes=30),
            capacity=16,
            price=Decimal("150.00"),
            instructor_name="Prof. Carlos Mendoza",
            notes="Sede Comas - Av. Túpac Amaru",
        )
        cls_comas_2 = ClassSession(
            name="Marinera Campeones Concurso (Avanzado)",
            class_type="group",
            branch="Comas",
            level="campeones",
            age_group="todas las edades",
            shift_time="Sábados 4:00 - 6:30 PM",
            starts_at=now + timedelta(days=3, hours=16),
            ends_at=now + timedelta(days=3, hours=18, minutes=30),
            capacity=14,
            price=Decimal("180.00"),
            instructor_name="Prof. Andrea Benavides",
            notes="Sede Comas - Preparación intensiva",
        )
        db.add_all([cls_olivos_1, cls_olivos_2, cls_comas_1, cls_comas_2])
        db.commit()

        # =========================================================================
        # 5. STUDENTS DEFINITIONS
        # =========================================================================
        # LOS OLIVOS: 6 in June, 10 in July, 2 in August = 18 students
        olivos_students_data = [
            # --- JUNIO (6) ---
            {
                "first_name": "Lucía", "last_name": "García Torres", "dni": "74892154", "birth_year": 2015,
                "is_minor": True, "guardian_name": "Carmen Torres", "guardian_phone": "+51 987654321", "guardian_relationship": "Madre",
                "phone": "+51 987654321", "whatsapp": "+51 987654321", "source": "whatsapp", "join_month": 6, "join_day": 3,
                "aug_paid": True,
            },
            {
                "first_name": "Mateo", "last_name": "Rojas Quispe", "dni": "71239845", "birth_year": 2013,
                "is_minor": True, "guardian_name": "Luis Rojas", "guardian_phone": "+51 999888777", "guardian_relationship": "Padre",
                "phone": "+51 999888777", "whatsapp": "+51 999888777", "source": "referral", "referrer_name": "Carmen Torres",
                "referrer_phone": "+51 987654321", "join_month": 6, "join_day": 5, "discount": Decimal("20.00"),
                "aug_paid": True,
            },
            {
                "first_name": "Camila", "last_name": "Fernández Soto", "dni": "76543219", "birth_year": 2017,
                "is_minor": True, "guardian_name": "Elena Soto", "guardian_phone": "+51 977112233", "guardian_relationship": "Madre",
                "phone": "+51 977112233", "whatsapp": "+51 977112233", "source": "instagram", "join_month": 6, "join_day": 10,
                "aug_paid": True,
            },
            {
                "first_name": "Diego Alonso", "last_name": "Morales Castro", "dni": "72114455", "birth_year": 2002,
                "is_minor": False, "phone": "+51 966554433", "whatsapp": "+51 966554433", "source": "tiktok", "join_month": 6, "join_day": 14,
                "aug_paid": True,
            },
            {
                "first_name": "Antonella", "last_name": "Prado Huamán", "dni": "78990011", "birth_year": 2014,
                "is_minor": True, "guardian_name": "Rosa Huamán", "guardian_phone": "+51 955332211", "guardian_relationship": "Madre",
                "phone": "+51 955332211", "whatsapp": "+51 955332211", "source": "presencial", "join_month": 6, "join_day": 18,
                "aug_paid": True,
            },
            {
                "first_name": "Joaquín", "last_name": "Silva Carranza", "dni": "73445566", "birth_year": 2011,
                "is_minor": True, "guardian_name": "Jorge Silva", "guardian_phone": "+51 944221100", "guardian_relationship": "Padre",
                "phone": "+51 944221100", "whatsapp": "+51 944221100", "source": "whatsapp", "join_month": 6, "join_day": 22,
                "aug_paid": True,
            },

            # --- JULIO (10) ---
            {
                "first_name": "Valeria", "last_name": "Mendoza Vega", "dni": "70998877", "birth_year": 2004,
                "is_minor": False, "phone": "+51 933110099", "whatsapp": "+51 933110099", "source": "instagram", "join_month": 7, "join_day": 2,
                "aug_paid": True,
            },
            {
                "first_name": "Rodrigo", "last_name": "Salazar Benítez", "dni": "75667788", "birth_year": 2013,
                "is_minor": True, "guardian_name": "Patricia Benítez", "guardian_phone": "+51 922009988", "guardian_relationship": "Madre",
                "phone": "+51 922009988", "whatsapp": "+51 922009988", "source": "whatsapp", "join_month": 7, "join_day": 4,
                "aug_paid": True,
            },
            {
                "first_name": "Sofía", "last_name": "Castro Navarro", "dni": "77889900", "birth_year": 2016,
                "is_minor": True, "guardian_name": "Gladys Navarro", "guardian_phone": "+51 911998877", "guardian_relationship": "Madre",
                "phone": "+51 911998877", "whatsapp": "+51 911998877", "source": "presencial", "join_month": 7, "join_day": 6,
                "aug_paid": True,
            },
            {
                "first_name": "Franco", "last_name": "Villanueva Peña", "dni": "74332211", "birth_year": 2012,
                "is_minor": True, "guardian_name": "Manuel Villanueva", "guardian_phone": "+51 988776655", "guardian_relationship": "Padre",
                "phone": "+51 988776655", "whatsapp": "+51 988776655", "source": "referral", "referrer_name": "Rosa Huamán",
                "referrer_phone": "+51 955332211", "join_month": 7, "join_day": 8, "discount": Decimal("20.00"),
                "aug_paid": True,
            },
            {
                "first_name": "Mia Valentina", "last_name": "Paredes Ruiz", "dni": "79112233", "birth_year": 2018,
                "is_minor": True, "guardian_name": "Silvia Paredes", "guardian_phone": "+51 977665544", "guardian_relationship": "Madre",
                "phone": "+51 977665544", "whatsapp": "+51 977665544", "source": "instagram", "join_month": 7, "join_day": 11,
                "aug_paid": True,
            },
            {
                "first_name": "Sebastián", "last_name": "Ríos Chávez", "dni": "71887766", "birth_year": 2005,
                "is_minor": False, "phone": "+51 966443322", "whatsapp": "+51 966443322", "source": "tiktok", "join_month": 7, "join_day": 14,
                "aug_paid": True,
            },
            {
                "first_name": "Daniela", "last_name": "Cáceres Medina", "dni": "76223344", "birth_year": 2014,
                "is_minor": True, "guardian_name": "Teresa Medina", "guardian_phone": "+51 955221100", "guardian_relationship": "Madre",
                "phone": "+51 955221100", "whatsapp": "+51 955221100", "source": "whatsapp", "join_month": 7, "join_day": 17,
                "aug_paid": True,
            },
            {
                "first_name": "Gabriel", "last_name": "Luna Córdova", "dni": "73119988", "birth_year": 2012,
                "is_minor": True, "guardian_name": "Andrés Luna", "guardian_phone": "+51 944110099", "guardian_relationship": "Padre",
                "phone": "+51 944110099", "whatsapp": "+51 944110099", "source": "presencial", "join_month": 7, "join_day": 20,
                "aug_paid": True,
            },
            {
                "first_name": "Kiara", "last_name": "Zúñiga Farfán", "dni": "78445566", "birth_year": 2015,
                "is_minor": True, "guardian_name": "Norma Farfán", "guardian_phone": "+51 933009988", "guardian_relationship": "Madre",
                "phone": "+51 933009988", "whatsapp": "+51 933009988", "source": "instagram", "join_month": 7, "join_day": 23,
                "aug_paid": False,  # EXPIRING SOON PENDING DEMO
            },
            {
                "first_name": "Leonardo", "last_name": "Tello Palacios", "dni": "70556677", "birth_year": 1999,
                "is_minor": False, "phone": "+51 922998877", "whatsapp": "+51 922998877", "source": "whatsapp", "join_month": 7, "join_day": 26,
                "aug_paid": False,  # EXPIRING SOON PENDING DEMO
            },

            # --- AGOSTO (2) ---
            {
                "first_name": "Flavia", "last_name": "Hurtado Quiroz", "dni": "77112244", "birth_year": 2016,
                "is_minor": True, "guardian_name": "Mónica Quiroz", "guardian_phone": "+51 911887766", "guardian_relationship": "Madre",
                "phone": "+51 911887766", "whatsapp": "+51 911887766", "source": "whatsapp", "join_month": 8, "join_day": 4,
                "aug_paid": False,  # EXPIRING SOON PENDING DEMO
            },
            {
                "first_name": "Matías", "last_name": "Cornejo Del Solar", "dni": "74889911", "birth_year": 2004,
                "is_minor": False, "phone": "+51 988665544", "whatsapp": "+51 988665544", "source": "instagram", "join_month": 8, "join_day": 9,
                "aug_paid": False,  # EXPIRING SOON PENDING DEMO
            },
        ]

        # COMAS (Inverted): 2 in June, 10 in July, 6 in August = 18 students
        comas_students_data = [
            # --- JUNIO (2) ---
            {
                "first_name": "Bianca Estefanía", "last_name": "Rivas Castillo", "dni": "75112233", "birth_year": 2014,
                "is_minor": True, "guardian_name": "Laura Rivas", "guardian_phone": "+51 977554433", "guardian_relationship": "Madre",
                "phone": "+51 977554433", "whatsapp": "+51 977554433", "source": "whatsapp", "join_month": 6, "join_day": 6,
                "aug_paid": True,
            },
            {
                "first_name": "Christian", "last_name": "Barrenechea Ruiz", "dni": "71334455", "birth_year": 2001,
                "is_minor": False, "phone": "+51 966332211", "whatsapp": "+51 966332211", "source": "presencial", "join_month": 6, "join_day": 12,
                "aug_paid": True,
            },

            # --- JULIO (10) ---
            {
                "first_name": "Yamila", "last_name": "Sánchez Balbín", "dni": "78223344", "birth_year": 2015,
                "is_minor": True, "guardian_name": "Rocío Balbín", "guardian_phone": "+51 955110099", "guardian_relationship": "Madre",
                "phone": "+51 955110099", "whatsapp": "+51 955110099", "source": "instagram", "join_month": 7, "join_day": 2,
                "aug_paid": True,
            },
            {
                "first_name": "Fabricio", "last_name": "Ramos Dávila", "dni": "73990011", "birth_year": 2012,
                "is_minor": True, "guardian_name": "César Ramos", "guardian_phone": "+51 944009988", "guardian_relationship": "Padre",
                "phone": "+51 944009988", "whatsapp": "+51 944009988", "source": "tiktok", "join_month": 7, "join_day": 5,
                "aug_paid": True,
            },
            {
                "first_name": "Luciana", "last_name": "Alarcón Pineda", "dni": "77445566", "birth_year": 2017,
                "is_minor": True, "guardian_name": "Carmen Pineda", "guardian_phone": "+51 933998877", "guardian_relationship": "Madre",
                "phone": "+51 933998877", "whatsapp": "+51 933998877", "source": "referral", "referrer_name": "Laura Rivas",
                "referrer_phone": "+51 977554433", "join_month": 7, "join_day": 7, "discount": Decimal("20.00"),
                "aug_paid": True,
            },
            {
                "first_name": "Gianfranco", "last_name": "Meza Osorio", "dni": "70889900", "birth_year": 2000,
                "is_minor": False, "phone": "+51 922887766", "whatsapp": "+51 922887766", "source": "whatsapp", "join_month": 7, "join_day": 10,
                "aug_paid": True,
            },
            {
                "first_name": "Andrea", "last_name": "Paucar Espinoza", "dni": "76112244", "birth_year": 2013,
                "is_minor": True, "guardian_name": "Juana Espinoza", "guardian_phone": "+51 911776655", "guardian_relationship": "Madre",
                "phone": "+51 911776655", "whatsapp": "+51 911776655", "source": "presencial", "join_month": 7, "join_day": 13,
                "aug_paid": True,
            },
            {
                "first_name": "Ariana Belén", "last_name": "Guizado Tello", "dni": "79556677", "birth_year": 2016,
                "is_minor": True, "guardian_name": "Kelly Guizado", "guardian_phone": "+51 988554433", "guardian_relationship": "Madre",
                "phone": "+51 988554433", "whatsapp": "+51 988554433", "source": "instagram", "join_month": 7, "join_day": 16,
                "aug_paid": True,
            },
            {
                "first_name": "Bruno", "last_name": "Santillán Vílchez", "dni": "72667788", "birth_year": 2011,
                "is_minor": True, "guardian_name": "Raúl Santillán", "guardian_phone": "+51 977443322", "guardian_relationship": "Padre",
                "phone": "+51 977443322", "whatsapp": "+51 977443322", "source": "whatsapp", "join_month": 7, "join_day": 19,
                "aug_paid": True,
            },
            {
                "first_name": "Luana Nicole", "last_name": "Chumpitaz Arias", "dni": "78778899", "birth_year": 2018,
                "is_minor": True, "guardian_name": "Sonia Chumpitaz", "guardian_phone": "+51 966221100", "guardian_relationship": "Madre",
                "phone": "+51 966221100", "whatsapp": "+51 966221100", "source": "tiktok", "join_month": 7, "join_day": 22,
                "aug_paid": True,
            },
            {
                "first_name": "Gonzalo", "last_name": "Rueda Bustamante", "dni": "71445566", "birth_year": 2004,
                "is_minor": False, "phone": "+51 955009988", "whatsapp": "+51 955009988", "source": "presencial", "join_month": 7, "join_day": 25,
                "aug_paid": False,  # EXPIRING SOON PENDING DEMO
            },
            {
                "first_name": "Romina", "last_name": "Delgado Cárdenas", "dni": "75889911", "birth_year": 2014,
                "is_minor": True, "guardian_name": "Isabel Cárdenas", "guardian_phone": "+51 944998877", "guardian_relationship": "Madre",
                "phone": "+51 944998877", "whatsapp": "+51 944998877", "source": "whatsapp", "join_month": 7, "join_day": 28,
                "aug_paid": False,  # EXPIRING SOON PENDING DEMO
            },

            # --- AGOSTO (6) ---
            {
                "first_name": "Micaela", "last_name": "Viteri Holguín", "dni": "74223344", "birth_year": 2015,
                "is_minor": True, "guardian_name": "Diana Holguín", "guardian_phone": "+51 933887766", "guardian_relationship": "Madre",
                "phone": "+51 933887766", "whatsapp": "+51 933887766", "source": "whatsapp", "join_month": 8, "join_day": 2,
                "aug_paid": False,  # EXPIRING SOON PENDING DEMO
            },
            {
                "first_name": "Esteban", "last_name": "Gamarra Lozano", "dni": "77556677", "birth_year": 2012,
                "is_minor": True, "guardian_name": "Percy Gamarra", "guardian_phone": "+51 922776655", "guardian_relationship": "Padre",
                "phone": "+51 922776655", "whatsapp": "+51 922776655", "source": "instagram", "join_month": 8, "join_day": 5,
                "aug_paid": False,  # EXPIRING SOON PENDING DEMO
            },
            {
                "first_name": "Nicole", "last_name": "Arévalo Poma", "dni": "70112233", "birth_year": 2017,
                "is_minor": True, "guardian_name": "Yolanda Poma", "guardian_phone": "+51 911665544", "guardian_relationship": "Madre",
                "phone": "+51 911665544", "whatsapp": "+51 911665544", "source": "tiktok", "join_month": 8, "join_day": 8,
                "aug_paid": False,  # EXPIRING SOON PENDING DEMO
            },
            {
                "first_name": "Álvaro", "last_name": "Céspedes Cueva", "dni": "76667788", "birth_year": 2003,
                "is_minor": False, "phone": "+51 988443322", "whatsapp": "+51 988443322", "source": "presencial", "join_month": 8, "join_day": 11,
                "aug_paid": False,  # EXPIRING SOON PENDING DEMO
            },
            {
                "first_name": "Pamela", "last_name": "Luján Calderón", "dni": "73778899", "birth_year": 2013,
                "is_minor": True, "guardian_name": "Miriam Calderón", "guardian_phone": "+51 977332211", "guardian_relationship": "Madre",
                "phone": "+51 977332211", "whatsapp": "+51 977332211", "source": "whatsapp", "join_month": 8, "join_day": 14,
                "aug_paid": False,  # EXPIRING SOON PENDING DEMO
            },
            {
                "first_name": "Salvador", "last_name": "Vera Carrión", "dni": "79889900", "birth_year": 2016,
                "is_minor": True, "guardian_name": "Walter Vera", "guardian_phone": "+51 966110099", "guardian_relationship": "Padre",
                "phone": "+51 966110099", "whatsapp": "+51 966110099", "source": "referral", "referrer_name": "Laura Rivas",
                "referrer_phone": "+51 977554433", "join_month": 8, "join_day": 17, "discount": Decimal("20.00"),
                "aug_paid": False,  # EXPIRING SOON PENDING DEMO
            },
        ]

        def process_branch_students(students_list: list[dict], branch_name: str, group_class: ClassSession) -> None:
            for s in students_list:
                join_date = datetime(2026, s["join_month"], s["join_day"], 16, 0, 0)
                client = Client(
                    first_name=s["first_name"],
                    last_name=s["last_name"],
                    dni=s.get("dni"),
                    phone=s.get("phone"),
                    whatsapp=s.get("whatsapp"),
                    email=f"{s['first_name'].lower().replace(' ', '')}@gmail.com",
                    birth_year=s.get("birth_year"),
                    is_minor=s.get("is_minor", False),
                    guardian_name=s.get("guardian_name"),
                    guardian_phone=s.get("guardian_phone"),
                    guardian_relationship=s.get("guardian_relationship"),
                    preferred_branch=branch_name,
                    status="active",
                    acquisition_source=s.get("source", "whatsapp"),
                    referrer_name=s.get("referrer_name"),
                    referrer_phone=s.get("referrer_phone"),
                    notes=f"Inscrito en {branch_name} ({join_date.strftime('%d/%m/%Y')}).",
                    created_at=join_date,
                    is_active=True,
                )
                db.add(client)
                db.flush()

                # Enroll in class
                enrollment = Enrollment(
                    class_session_id=group_class.id,
                    client_id=client.id,
                    status="booked",
                    created_at=join_date,
                )
                db.add(enrollment)

                # Initial Interaction (Welcome)
                inter = Interaction(
                    client_id=client.id,
                    channel=s.get("source", "whatsapp"),
                    motive="matricula",
                    summary=f"Matrícula e inscripción confirmada en la sede {branch_name}.",
                    result="se_matriculo",
                    attended_by="Directora General",
                    created_at=join_date,
                )
                db.add(inter)

                # Generate history of memberships & payments for active months
                # Months from join_month up to 8 (August)
                for month_num in range(s["join_month"], 9):
                    p_month = f"2026-0{month_num}"
                    m_start = date(2026, month_num, 1)
                    m_end = date(2026, month_num, 30 if month_num == 6 else 31)

                    # For August, set expiration to today+3 to today+5 to trigger alerts nicely
                    if month_num == 8:
                        # 2026-08-28 to 2026-08-31
                        m_end = date(2026, 8, 28)

                    base_price = Decimal("150.00")
                    disc = s.get("discount", Decimal("0.00")) if month_num == s["join_month"] else Decimal("0.00")
                    final_price = base_price - disc

                    is_paid = True
                    if month_num == 8:
                        is_paid = s.get("aug_paid", True)

                    mem = Membership(
                        client_id=client.id,
                        branch=branch_name,
                        class_type="grupal_mensual",
                        plan_name="Marinera Norteña Mensual (8 clases)",
                        period_month=p_month,
                        start_date=m_start,
                        end_date=m_end,
                        classes_total=8,
                        classes_attended=6 if is_paid else 2,
                        price=base_price,
                        discount_applied=disc,
                        final_price=final_price,
                        payment_status="paid" if is_paid else "pending",
                        status="active",
                        is_recurring=True,
                        auto_renew=True,
                        is_active=True,
                        created_at=datetime(2026, month_num, 1, 10, 0, 0),
                    )
                    db.add(mem)
                    db.flush()

                    if is_paid:
                        pay_day = s["join_day"] if month_num == s["join_month"] else 5
                        pay_method = "yape" if (client.id.int % 2 == 0) else "transferencia"
                        payment = Payment(
                            client_id=client.id,
                            membership_id=mem.id,
                            amount=final_price,
                            payment_date=datetime(2026, month_num, pay_day, 11, 30, 0),
                            period_month=p_month,
                            concept="mensualidad",
                            shift_detail=group_class.shift_time,
                            payment_method=pay_method,
                            transaction_reference=f"{pay_method.upper()}-{20260000 + (client.id.int % 90000)}",
                            branch=branch_name,
                            registered_by="Directora General",
                            status="completed",
                            created_at=datetime(2026, month_num, pay_day, 11, 30, 0),
                        )
                        db.add(payment)

        # Process both branches
        process_branch_students(olivos_students_data, "Los Olivos", cls_olivos_1)
        process_branch_students(comas_students_data, "Comas", cls_comas_1)

        # 6. Seed Interested Leads (Prospects with pending reminders)
        interested_leads = [
            {
                "first_name": "Renato", "last_name": "Barrios Vega", "phone": "+51 987112233", "whatsapp": "+51 987112233",
                "branch": "Los Olivos", "source": "instagram", "motive": "precios_y_horarios", "summary": "Interesado en clases para su hijo de 6 años. Se coordinará clase de prueba.",
                "result": "lo_pensara", "reminder_in_days": 2,
            },
            {
                "first_name": "Valeria", "last_name": "Espinoza Quintana", "phone": "+51 976223344", "whatsapp": "+51 976223344",
                "branch": "Comas", "source": "tiktok", "motive": "clase_de_prueba", "summary": "Vio video en TikTok de campeones. Desea probar clase juvenil este sábado.",
                "result": "vino_a_probarse", "reminder_in_days": 1,
            },
            {
                "first_name": "Gonzalo", "last_name": "Pacheco Cárdenas", "phone": "+51 965334455", "whatsapp": "+51 965334455",
                "branch": "Los Olivos", "source": "whatsapp", "motive": "precios_y_horarios", "summary": "Preguntó por costo de matrícula y si hay descuentos por hermanos.",
                "result": "pidio_informacion", "reminder_in_days": 3,
            },
            {
                "first_name": "Mariana", "last_name": "Zavala Ortiz", "phone": "+51 954445566", "whatsapp": "+51 954445566",
                "branch": "Comas", "source": "web", "motive": "precios_y_horarios", "summary": "Registro automático desde el simulador web. Interés en Marinera Infantil.",
                "result": "pidio_informacion", "reminder_in_days": 1,
            },
        ]

        for lead in interested_leads:
            cl = Client(
                first_name=lead["first_name"],
                last_name=lead["last_name"],
                phone=lead["phone"],
                whatsapp=lead["whatsapp"],
                preferred_branch=lead["branch"],
                status="interested",
                acquisition_source=lead["source"],
                notes=lead["summary"],
                is_active=True,
            )
            db.add(cl)
            db.flush()

            it = Interaction(
                client_id=cl.id,
                channel=lead["source"],
                motive=lead["motive"],
                summary=lead["summary"],
                result=lead["result"],
                attended_by="Directora General",
                next_followup_date=now + timedelta(days=lead["reminder_in_days"]),
                reminder_active=True,
                created_at=now - timedelta(days=1),
            )
            db.add(it)

        # 7. Seed Retired Students (with exit reasons for analytics & reactivation demo)
        retired_students = [
            {
                "first_name": "Diego", "last_name": "Huamán Rivas", "dni": "72334455", "phone": "+51 943556677", "whatsapp": "+51 943556677",
                "branch": "Los Olivos", "source": "presencial", "reason": "cruce_horarios", "notes": "Cambio de horario escolar. Posible retorno en verano.",
            },
            {
                "first_name": "Ximena", "last_name": "Torres Arana", "dni": "75445566", "phone": "+51 932667788", "whatsapp": "+51 932667788",
                "branch": "Comas", "source": "whatsapp", "reason": "distancia_mudanza", "notes": "Se mudó a San Miguel. Muy agradecida con los profesores.",
            },
            {
                "first_name": "Mauricio", "last_name": "Castro Benites", "dni": "71556677", "phone": "+51 921778899", "whatsapp": "+51 921778899",
                "branch": "Los Olivos", "source": "instagram", "reason": "economico_precio", "notes": "Dificultad económica temporal.",
            },
        ]

        for ret in retired_students:
            cl_ret = Client(
                first_name=ret["first_name"],
                last_name=ret["last_name"],
                dni=ret["dni"],
                phone=ret["phone"],
                whatsapp=ret["whatsapp"],
                preferred_branch=ret["branch"],
                status="retired",
                acquisition_source=ret["source"],
                uninterested_reason=ret["reason"],
                retired_at=now - timedelta(days=15),
                notes=ret["notes"],
                is_active=True,
            )
            db.add(cl_ret)
            db.flush()

            it_ret = Interaction(
                client_id=cl_ret.id,
                channel="whatsapp",
                motive="otro",
                summary=f"Baja / Retiro registrado: {ret['reason']}. {ret['notes']}",
                result="no_respondio",
                uninterested_reason=ret["reason"],
                attended_by="Directora General",
                created_at=now - timedelta(days=15),
            )
            db.add(it_ret)

        db.commit()
        print("[OK] Base de datos ficticia para los ultimos 3 meses generada exitosamente.")
    finally:
        if should_close:
            db.close()


if __name__ == "__main__":
    clear_and_seed_database()
