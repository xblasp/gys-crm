# GyS CRM — Taller de Marinera Garbo & Salero Semillero de Campeones

Sistema CRM y plataforma de gestión operativa y comercial para el **Taller de Marinera Garbo & Salero Semillero de Campeones** (Perú), con soporte integral para sus 2 sedes (**Los Olivos** y **Comas**).

---

## 🎯 Alcance del Sistema (MVP)

El sistema cubre al 100% las necesidades operativas, financieras y comerciales especificadas en el cuestionario de requisitos:

1. **Gestión de Sedes & Turnos**: Soporte para sedes **Los Olivos** y **Comas**, con turnos de lunes a sábado de 4:00 PM a 10:00 PM por niveles y edades.
2. **Alumnos & Apoderados (75% Menores de Edad)**: Ficha de alumnos con detección de menores de edad, registro de apoderados (padre/madre/tutor), DNI (8 dígitos) y comunicación directa por WhatsApp.
3. **Interacciones, CRM & Línea de Tiempo 360°**: Registro de contactos (WhatsApp, visitas presenciales, llamadas, clases de prueba, particulares), resultados, motivos de no inscripción, recordatorios de seguimiento y timeline unificado.
4. **Membresías & Pagos Mensuales**: Control de mensualidades por mes independiente (8 clases al mes, libres, paquetes particulares), cobros con métodos peruanos (**Efectivo, Yape, Plin, Transferencia**), alerta de **vencimiento a 5 días**, y módulo de anulación/devolución auditado.
5. **Promociones & Descuentos**: Descuento de S/ 20 por recomendación de amigos/referidos, exoneración de matrícula y descuentos personalizados.
6. **Dashboard Mensual & Comparativa Trimestral**: KPIs de ingresos, alumnos activos, nuevos y retirados, tendencia de 3 meses, desglose por modalidad de clase y canales de origen.
7. **Usuarios, Roles & Auditoría**: Roles diferenciados (**Administrador General** con control total y **Administrador de Sede** para operaciones locales), con registro inmutable de auditoría.
8. **Futura Web & Captura Automática de Leads**: Endpoints públicos `/public/leads` y `/public/schedule` para alimentar el CRM en tiempo real desde la web oficial.
9. **Frontend Web SPA Integrado**: Interfaz moderna, responsiva y elegante con estética de marinera norteña lista para operar.

---

## 🚀 Inicio Rápido

### Requisitos Previos
- Python 3.13+ (compatible con Python 3.14)
- PostgreSQL (opcional para desarrollo local; se puede usar la base de datos configurada o SQLite en memoria para pruebas)

### 1. Clonar e Instalar Dependencias
```powershell
# Crear y activar entorno virtual
python -m venv .venv
.\.venv\Scripts\activate

# Instalar dependencias del proyecto
pip install -e ".[dev]"
```

### 2. Ejecutar la Aplicación
```powershell
uvicorn backend.app.main:app --reload --port 8000
```
Abrir en el navegador:
- **CRM Web App**: [http://localhost:8000/](http://localhost:8000/)
- **Documentación Interactiva Swagger / OpenAPI**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Ejecutar Pruebas Automatizadas
```powershell
pytest -v
```

---

## 📂 Estructura del Proyecto

```
GyS CRM/
├── backend/
│   ├── app/
│   │   ├── api/             # Endpoints REST (clients, classes, interactions, memberships, payments, dashboard, public, auth)
│   │   ├── core/            # Configuración de variables de entorno y settings
│   │   ├── db/              # Conexión SQLAlchemy y Base declarativa
│   │   ├── models/          # Modelos de base de datos relacionales
│   │   ├── repositories/    # Capa de acceso a datos
│   │   ├── schemas/         # Validación de datos con Pydantic V2
│   │   └── services/        # Lógica de negocio y reglas del estudio
│   └── tests/               # Pruebas unitarias e integrales con Pytest
├── docs/                    # Documentación de arquitectura, base de datos y seguridad
├── frontend/                # Aplicación Web SPA (HTML5, CSS3, JavaScript ES6)
│   ├── css/styles.css       # Sistema de diseño con temática marinera
│   ├── js/app.js            # Lógica reactiva de la interfaz
│   └── index.html           # Estructura de la aplicación
├── migrations/              # Control de versiones de esquema con Alembic
├── docker-compose.yml       # Servicio PostgreSQL para producción/desarrollo
└── pyproject.toml           # Dependencias y configuración de empaquetado
```
