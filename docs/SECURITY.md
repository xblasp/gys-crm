# Políticas de Seguridad y Permisos — GyS CRM

Lineamientos de seguridad, control de acceso basado en roles (RBAC) y auditoría para el Taller de Marinera Garbo & Salero.

## 1. Modelo de Roles y Permisos

El sistema establece una separación estricta de responsabilidades (Sección 8 del cuestionario):

### Rol: `admin_general` (Dirección General)
- Acceso a todas las sedes (**Los Olivos**, **Comas** y consolidado **Todas**).
- Permiso exclusivo para **anular o devolver pagos** (con motivo obligatorio).
- Creación y modificación de promociones y descuentos globales.
- Acceso al Dashboard comparativo consolidado e informes de ingresos.
- Creación y administración de cuentas de usuario.

### Rol: `admin_sede` (Administración de Sede / Recepción)
- Operación diaria limitada a su sede asignada.
- Registro y actualización de clientes y apoderados.
- Registro de contactos e interacciones en el CRM.
- Registro de cobros y emisión de recibos digitales.
- Control de asistencias e inscripciones a clases de su sede.
- Consulta de recordatorios y alertas de vencimientos de su sede.
- **Sin permisos** para anular transacciones de pago sin autorización de la Dirección.

## 2. Pista de Auditoría (`audit_logs`)
Todas las operaciones sensibles generan un registro inmutable que captura:
- `action`: Tipo de evento (`PAYMENT_CREATED`, `PAYMENT_CANCELLED`, `DISCOUNT_APPLIED`, `CLIENT_STATUS_CHANGED`).
- `entity_type` y `entity_id`: Recurso afectado.
- `performed_by`: Nombre y usuario del colaborador que ejecutó la acción.
- `created_at`: Marca de tiempo con zona horaria.
- `details`: Justificación y datos de contexto (por ejemplo, motivo de la anulación).

## 3. Manejo de Datos Financieros & Pagos Online
- En cumplimiento de las buenas prácticas de seguridad (Sección 10), el CRM **nunca almacena números de tarjeta de crédito o códigos CVV**.
- Para cobros locales se registran únicamente el método (**Yape, Plin, Transferencia, Efectivo**) y el número de referencia/operación.
- Para futuras pasarelas web, la tokenización y cobro se delegan completamente al proveedor de pagos mediante webhooks seguros.
