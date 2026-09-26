# 📖 MANUAL DE USUARIO Y OPERACIONES
## GyS CRM — Taller de Marinera Garbo & Salero "Semillero de Campeones"
### Sedes: Los Olivos & Comas

---

## 📌 Tabla de Contenidos
1. [Introducción y Acceso al Sistema](#1-introducción-y-acceso-al-sistema)
2. [Barra Superior y Controles Globales (Sedes y Roles)](#2-barra-superior-y-controles-globales)
3. [Módulo 1: Dashboard & Analítica Gerencial](#3-módulo-1-dashboard--analítica-gerencial)
4. [Módulo 2: Alumnos & Apoderados (Gestión 360°)](#4-módulo-2-alumnos--apoderados-gestión-360)
5. [Módulo 3: Interacciones & Seguimiento Comercial](#5-módulo-3-interacciones--seguimiento-comercial)
6. [Módulo 4: Horarios, Clases & Control de Aforos](#6-módulo-4-horarios-clases--control-de-aforos)
7. [Módulo 5: Membresías & Facturación Recurrente Automática](#7-módulo-5-membresías--facturación-recurrente-automática)
8. [Módulo 6: Cobranzas, Flujo de Caja & Recibos Digitales](#8-módulo-6-cobranzas-flujo-de-caja--recibos-digitales)
9. [Módulo 7: Catálogo de Promociones & Descuentos](#9-módulo-7-catálogo-de-promociones--descuentos)
10. [Módulo 8: Simulador de Captación Web (Leads en Vivo)](#10-módulo-8-simulador-de-captación-web-leads-en-vivo)
11. [Módulo 9: Respaldo, Restauración & Carga Masiva (Excel / CSV)](#11-módulo-9-respaldo-restauración--carga-masiva-excel--csv)
12. [Preguntas Frecuentes y Solución de Problemas](#12-preguntas-frecuentes-y-solución-de-problemas)

---

## 1. Introducción y Acceso al Sistema

El **GyS CRM** es la plataforma integral de gestión comercial, académica y financiera diseñada exclusivamente para el **Taller de Marinera Garbo & Salero**. Permite centralizar la información de alumnos (adultos y menores con apoderados), automatizar las cuotas mensuales, controlar asistencias y aforos en las sedes de Los Olivos y Comas, emitir recibos digitales y generar respaldos completos.

### 🚀 Cómo iniciar el sistema en su computadora:
1. Abra su terminal o PowerShell en la carpeta del proyecto.
2. Ejecute el siguiente comando para iniciar el servidor local:
   ```powershell
   & .\.venv_win\Scripts\python.exe -m uvicorn backend.app.main:app --reload --port 8000
   ```
3. Abra su navegador web (Google Chrome, Edge, Firefox) e ingrese a:
   👉 **`http://localhost:8000`**

---

## 2. Barra Superior y Controles Globales

La barra superior permanece visible en todas las pantallas y le permite configurar el contexto de trabajo:

* **Selector de Sede (`Todas`, `Los Olivos`, `Comas`):**
  * Al cambiar de sede, todas las tablas, métricas del Dashboard, clases y listas de alumnos se filtran automáticamente para mostrar únicamente la información del local seleccionado.
* **Perfil y Conmutador de Roles (`Directora General` / `Administrador de Sede`):**
  * Muestra el usuario activo.
  * **Directora General:** Acceso total, incluyendo reportes financieros consolidados, anulación de pagos y restauración de base de datos.
  * **Administrador de Sede:** Operación diaria de registro de alumnos, cobros, asistencia y seguimiento.

---

## 3. Módulo 1: Dashboard & Analítica Gerencial

El Dashboard es el panel principal de control que resume la salud del negocio en el mes seleccionado.

### 📊 Componentes y Opciones:
1. **Filtro de Mes del Periodo:** Permite consultar métricas de meses anteriores o del mes en curso (`YYYY-MM`).
2. **Tarjetas de KPIs:**
   * **Ingresos Totales (S/):** Dinero efectivamente cobrado en el periodo.
   * **Alumnos Activos:** Total de estudiantes con matrícula vigente asistiendo a clases.
   * **Nuevos Alumnos:** Estudiantes inscritos por primera vez en el mes.
   * **Alumnos Retirados:** Total de bajas registradas en el periodo.
3. **Banner de Alertas Urgentes de Cobranza:**
   * Muestra un recuadro amarillo preventivo si existen membresías que vencen en los próximos **5 días**, con acceso directo para gestionar el cobro.
4. **Gráfico de Tendencia de Ventas (3 Meses):**
   * Gráfico comparativo que muestra la evolución de ingresos en Soles (barras doradas) versus la cantidad de nuevos alumnos matriculados (línea azul).
5. **Gráfico de Distribución de Ingresos por Modalidad:**
   * Gráfico circular que desglosa los ingresos generados por: *Grupal Mensual (8 clases)*, *Clases Libres*, *Paquetes Particulares* y *Matrículas*.
6. **Canales de Captación:**
   * Indicadores de efectividad comercial (% de alumnos captados por WhatsApp, Instagram, TikTok, Referidos o Presencial).
7. **Tablas de Acción Inmediata:**
   * **Próximos Vencimientos:** Lista de alumnos con cuotas por vencer en ≤ 5 días con botón directo de **Cobrar**.
   * **Recordatorios de Seguimiento:** Lista de prospectos que solicitaron información y tienen llamadas o mensajes pendientes para hoy.

---

## 4. Módulo 2: Alumnos & Apoderados (Gestión 360°)

Este módulo centraliza el padrón de alumnos y prospectos.

### ➕ 4.1 Registrar un Nuevo Alumno
1. Haga clic en el botón azul **`+ Nuevo Alumno`**.
2. Complete la información básica:
   * **Nombres y Apellidos** (Obligatorio).
   * **DNI:** Documento de 8 dígitos (el sistema valida duplicados).
   * **WhatsApp / Teléfono:** Número con formato peruano (ej. `+51 987654321`).
   * **Año de Nacimiento:** Permite calcular automáticamente la edad.
   * **Sede Preferida:** Los Olivos o Comas.
   * **Estado Inicial:** *Interesado (Prospecto)* o *Activo (Matriculado)*.
3. **Sección de Menor de Edad (75% del alumnado):**
   * Si marca la casilla **`¿Es menor de edad?`**, se desplegarán los campos para registrar al **Apoderado**:
     * Nombre del padre/madre/tutor.
     * Teléfono / WhatsApp del apoderado (clave para los grupos de WhatsApp de la sede).
     * Parentesco (*Madre*, *Padre*, *Tutor*).
     * DNI del apoderado.
4. **Canal de Captación y Referidos:**
   * Indique cómo conoció la academia (*WhatsApp, Instagram, Presencial, Referido, etc.*).
   * Si selecciona **`Referido / Recomendación`**, ingrese el nombre y teléfono de quien lo recomendó para otorgarle su bono/descuento de S/ 20.
5. Haga clic en **`Guardar Alumno`**.

---

### 🔍 4.2 Ficha 360° y Línea de Tiempo del Alumno
Al hacer clic en el nombre de cualquier alumno o en el botón de **Ojo (Ver)**:
* **Columna Izquierda:** Ficha con todos los datos personales, apoderado, sede y estado.
* **Contacto Directo por WhatsApp:**
  * Seleccione una plantilla predeterminada (*Aviso de vencimiento*, *Bienvenida al grupo*, *Clase de prueba*, *Seguimiento*) y haga clic en **`Abrir WhatsApp Web`** para enviar el mensaje con el texto ya redactado.
* **Columna Derecha (Línea de Tiempo 360°):**
  * Historial cronológico con cada interacción, clase asistida, cobro realizado, descuento aplicado y cambios de estado.

---

### 🚪 4.3 Flujo de Baja / Retiro de Alumnos
Cuando un alumno o apoderado comunique que no continuará:
1. En la tabla de alumnos o en la Ficha 360°, haga clic en el botón rojo **`Dar de Baja / Retirar`** (icono de usuario con signo menos).
2. Se abrirá el modal de retiro solicitando obligatoriamente el **Motivo Principal de Retiro**:
   * ⏰ *Cruce de Horarios (Colegio / Universidad / Trabajo)*
   * 💰 *Precio / Situación Económica*
   * 📍 *Distancia / Cambio de Domicilio*
   * 🏥 *Salud o Lesión*
   * ✈️ *Viaje o Ausencia Temporal*
   * 🎓 *Culminó Temporada / Vacaciones*
   * ⚠️ *Insatisfacción con la Clase o Servicio*
   * 👨‍👩‍👧 *Motivos Personales / Familiares*
   * 📝 *Otro Motivo*
3. Ingrese observaciones adicionales si lo desea (ej. *"Madre indicó que retomará en verano"*).
4. Haga clic en **`Confirmar Retiro del Alumno`**.
5. **Efectos automáticos del sistema:**
   * El alumno pasa a estado **Retirado**.
   * Sus cuotas o membresías pendientes del mes quedan **canceladas automáticamente**.
   * Se detiene la generación de cuotas futuras recurrentes.
   * Se registra el evento en su Línea de Tiempo 360° y en la Auditoría.

---

### 🔄 4.4 Reactivación de un Alumno Retirado
Si un alumno retirado decide volver a entrenar:
1. Localice al alumno en la tabla (usando el filtro de estado *Retirados* o buscando por nombre).
2. Haga clic en el botón verde **`Reactivar Alumno`** (icono de usuario con signo más).
3. Confirme la acción. El sistema cambiará su estado a **Activo** y generará automáticamente su cuota del mes vigente.

---

## 5. Módulo 3: Interacciones & Seguimiento Comercial

Permite hacer seguimiento riguroso a prospectos para evitar que se pierdan consultas.

### 📝 Cómo registrar una interacción:
1. Haga clic en **`+ Registrar Interacción`**.
2. Seleccione el alumno o interesado.
3. Elija el **Canal** (*WhatsApp, Llamada, Presencial, Instagram, TikTok*).
4. Elija el **Motivo** (*Consulta de Horarios, Clase de Prueba, Reclamo, Seguimiento, etc.*).
5. Escriba un **Resumen** de lo conversado.
6. Registre el **Resultado** (*Pidió información, Asistió a clase de prueba, Se matriculó, No interesado*).
7. **Próximo Seguimiento:** Configure una fecha y hora futura si debe volver a contactarlo; el sistema le enviará un recordatorio en el Dashboard.

---

## 6. Módulo 4: Horarios, Clases & Control de Aforos

Permite gestionar la programación académica y controlar la capacidad física de cada salón.

### 📅 Opciones disponibles:
1. **Crear Nuevo Horario / Clase (`+ Programar Clase`):**
   * Nombre de la clase (ej. *Marinera Norteña Infantil Inicial*).
   * Modalidad (*Grupal 8 clases, Clase Libre, Particular*).
   * Sede (*Los Olivos* o *Comas*).
   * Nivel (*Inicial/Semillero, Intermedio, Avanzado, Campeones/Concurso*).
   * Grupo de Edad (*Infantil 4-11 años, Juvenil 12-17 años, Adultos 18+*).
   * Aforo Máximo (ej. *15 alumnos*).
   * Profesor asignado y días habituales (ej. *Lunes y Miércoles 6:00 - 7:30 PM*).
2. **Semáforo de Aforo:**
   * La barra de capacidad muestra el % de ocupación en tiempo real. Si la clase se llena, el sistema alertará que no hay cupos disponibles.
3. **Inscribir Alumno a la Clase:**
   * Haga clic en **`Inscribir Alumno`** dentro de la tarjeta de la clase y elija al estudiante.

---

## 7. Módulo 5: Membresías & Facturación Recurrente Automática

Este módulo elimina la necesidad de renovar cuotas manualmente mes a mes.

### ⚡ 7.1 Cómo funciona el cobro mensual recurrente:
* **Cálculo Automático:** Para todos los alumnos activos, el sistema calcula automáticamente las cuotas mensuales (1er día al último día del mes correspondiente, con 8 clases base).
* **Botón `⚡ Sincronizar Cuotas del Mes`:**
  * Al inicio de cada mes, puede pulsar este botón en la barra superior de Membresías para asegurar y pre-generar las cuotas pendientes de todos los alumnos activos de la sede en un solo clic.
* **Asignación Manual de Plan (`Asignar Plan`):**
  * Útil para casos especiales (ej. paquetes de clases particulares o modalidades sueltas). Permite definir precio base, descuento y estado de pago.

---

## 8. Módulo 6: Cobranzas, Flujo de Caja & Recibos Digitales

Permite registrar ingresos de dinero, emitir comprobantes y controlar devoluciones.

### 💵 8.1 Registrar un Cobro
1. Haga clic en **`Registrar Cobro`** (o pulse el botón **`Cobrar`** en cualquier cuota pendiente).
2. Seleccione el alumno y el concepto (*Mensualidad 8 clases, Matrícula, Clase Libre, etc.*).
3. Ingrese el monto en Soles (S/).
4. Seleccione el **Método de Pago:** *Yape*, *Plin*, *Transferencia Bancaria* o *Efectivo*.
5. Ingrese el N° de Operación / Referencia (ej. *Op. 482910*).
6. Haga clic en **`Emitir Recibo & Guardar`**.

---

### 🧾 8.2 Recibo Digital y Envío por WhatsApp
Al registrar el pago o hacer clic en el botón de **Recibo**:
1. Se abre el comprobante oficial numerado con formato institucional (`REC-XXXXXXXX`).
2. Muestra el detalle del alumno, DNI, sede, concepto, periodo, fecha exacta, método de pago y monto total.
3. Haga clic en el botón verde **`Compartir por WhatsApp`**:
   * Abrirá automáticamente WhatsApp con el mensaje formal de agradecimiento y el desglose del recibo listo para enviar al apoderado.

---

### ⚠️ 8.3 Anulación / Devolución de Pagos (Auditoría)
* Exclusivo para la **Directora General**.
* Si un pago se registró por error o duplicado, pulse el botón rojo de anulación en la tabla de pagos.
* Debe ingresar obligatoriamente el **Motivo de Anulación** y el nombre del autorizador.
* El sistema anulará el recibo, revertirá la membresía a pendiente y guardará un registro inmutable en el log de auditoría.

---

## 9. Módulo 7: Catálogo de Promociones & Descuentos

Permite aplicar beneficios comerciales de forma ordenada y transparente.

### 🎁 Promociones Predeterminadas:
1. **Descuento por Recomendación (S/ 20.00):** Se aplica automáticamente cuando un alumno refiere a un nuevo inscrito.
2. **Exoneración de Matrícula (S/ 0.00):** Aplica para campañas promocionales de inicio de temporada.
3. **Descuento Familiar / Hermanos:** Reducción porcentual o fija para familias con más de 2 alumnos.

### 📌 Cómo aplicar un descuento:
* En la Ficha 360° del alumno, pulse **`Aplicar Descuento`**, seleccione la promoción y confirme. El descuento quedará registrado de forma inmutable en el historial del alumno.

---

## 10. Módulo 8: Simulador de Captación Web (Leads en Vivo)

Permite simular o conectar el formulario de la página web del taller para recibir prospectos en tiempo real.

* Al completar el formulario público con los datos de un interesado (padre o adulto), el sistema:
  1. Registra automáticamente al prospecto en la base de datos de la sede elegida.
  2. Genera una interacción inicial de canal *Web*.
  3. Muestra una alerta en el feed en vivo del CRM para que el administrador de sede lo contacte de inmediato por WhatsApp.

---

## 11. Módulo 9: Respaldo, Restauración & Carga Masiva (Excel / CSV)

Protege la información de la academia y facilita la migración de datos.

### 📥 11.1 Carga Masiva de Clientes desde Excel o CSV
Si ya cuenta con una lista de alumnos en Excel:
1. Diríjase a la pestaña **`Respaldos & Carga Masiva`**.
2. Haga clic en **`Descargar Plantilla CSV Oficial`** para conocer el formato sugerido.
3. Guarde su Excel como archivo **`.CSV (delimitado por comas)`**.
4. Arrastre el archivo a la zona de carga y haga clic en **`Cargar e Importar Alumnos al CRM`**.
5. El sistema procesará cada fila, detectará alumnos y apoderados, y los incorporará al CRM indicando la cantidad de registros importados exitosamente.

---

### 💾 11.2 Descargar Backup Completo (.JSON)
* Haga clic en **`Descargar Backup (.JSON)`**.
* Se descargará un archivo con toda la base de datos completa: alumnos, apoderados, interacciones, mensualidades, pagos, clases y registros de auditoría.
* **Recomendación:** Descargar un respaldo semanal o mensual y guardarlo en Google Drive o un disco externo.

---

### 🔄 11.3 Restaurar Base de Datos desde Backup
1. En la tarjeta *Restaurar Base de Datos*, seleccione el archivo `.json` de respaldo previamente descargado.
2. Haga clic en **`Restaurar / Cargar Base de Datos`**.
3. El sistema reconstruirá todas las tablas y datos exactamente como estaban al momento de crear el backup.

---

## 12. Preguntas Frecuentes y Solución de Problemas

### ❓ ¿Qué ocurre si no tengo instalado PostgreSQL?
El CRM cuenta con un sistema de **resiliencia automática**. Si no detecta PostgreSQL, conmuta de inmediato a la base de datos local SQLite (`gys_crm.db`) sin interrumpir su trabajo ni perder datos.

### ❓ ¿Cómo abro WhatsApp si estoy usando una computadora sin la app instalada?
Al hacer clic en cualquier botón de WhatsApp, el sistema abrirá automáticamente **WhatsApp Web** en su navegador predeterminado.

### ❓ ¿Cómo cambio entre la sede de Los Olivos y Comas?
Utilice el selector desplegable ubicado en la esquina superior derecha. Podrá visualizar los datos de cada sede por separado o elegir `Todas` para ver los consolidados de la academia.

---

*GyS CRM — Desarrollado para el Taller de Marinera Garbo & Salero Semillero de Campeones.*
