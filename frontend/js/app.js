/**
 * ==============================================================================
 * GyS CRM — Frontend Application Logic (Arquitectura SPA)
 * Taller de Marinera Garbo & Salero Semillero de Campeones
 * ==============================================================================
 * 
 * Este módulo orquesta la lógica de interfaz de usuario, gestión de estado local,
 * sincronización con la API REST (FastAPI), renderizado dinámico de tablas,
 * generación de gráficos con Chart.js y emisión de comprobantes de pago.
 */

// ==============================================================================
// 1. ESTADO GLOBAL REACTIVO DE LA APLICACIÓN (Single Source of Truth)
// ==============================================================================
const state = {
  currentBranch: 'Los Olivos', // Sede seleccionada: 'Todas', 'Los Olivos' o 'Comas'
  currentUser: {
    username: 'admin_general',
    full_name: 'Directora General',
    role: 'admin_general', // Roles: 'admin_general' | 'admin_sede'
    branch: 'Todas',
  },
  clients: [],             // Lista en memoria de alumnos y prospectos
  interactions: [],        // Bitácora de seguimiento comercial y CRM
  classes: [],             // Sesiones de clase y horarios por sede
  memberships: [],         // Ciclos y suscripciones mensuales
  payments: [],            // Registro de ingresos y caja
  promotions: [],          // Catálogo de descuentos y promociones
  reminders: [],           // Recordatorios activos de seguimiento
  expiringMemberships: [], // Alertas de mensualidades por vencer (<= 5 días)
  dashboardData: null,     // Métricas consolidadas del dashboard gerencial
  charts: {
    quarterly: null,       // Instancia Chart.js: Evolución trimestral de ingresos
    modality: null,        // Instancia Chart.js: Distribución por modalidad de clase
  },
  selectedClientForProfile: null, // Alumno seleccionado para el modal de ficha integral
};

// ==============================================================================
// 2. CONFIGURACIÓN DE RED Y RESOLUCIÓN DE ENDPOINTS
// ==============================================================================
// Detecta automáticamente el origen del servidor (FastAPI :8000, LiveServer :5500 o producción)
const API_BASE = (window.location.origin && window.location.origin.startsWith('http') && !window.location.port.match(/^(5500|3000|5173)$/)) 
  ? window.location.origin 
  : 'http://127.0.0.1:8000';

/**
 * Genera el siguiente número correlativo de operación (ej: OP-001045).
 * Analiza las transacciones existentes para garantizar numeración secuencial ascendente.
 * @returns {string} Código correlativo formateado
 */
function generateNextOperationNumber() {
  let maxNum = 1000;
  if (state.payments && state.payments.length > 0) {
    state.payments.forEach(p => {
      if (p.transaction_reference) {
        const match = p.transaction_reference.match(/(\d+)/);
        if (match) {
          const val = parseInt(match[1], 10);
          if (val > maxNum && val < 99999999) {
            maxNum = val;
          }
        }
      }
    });
  } else {
    maxNum = 1000;
  }
  const nextNum = maxNum + 1;
  return `OP-${String(nextNum).padStart(6, '0')}`;
}

/**
 * Obtiene el turno u horario habitual sugerido para un alumno específico.
 * @param {string} clientId - Identificador UUID del cliente
 * @returns {string} Descripción del horario asignado
 */
function getClientSchedule(clientId) {
  if (!clientId) return '';
  const client = state.clients.find(c => c.id === clientId);
  if (!client) return '';

  // Busca si existe una clase programada para la sede preferida del alumno
  if (state.classes && state.classes.length > 0) {
    const branchClasses = state.classes.filter(cls => cls.branch === (client.preferred_branch || state.currentBranch));
    if (branchClasses.length > 0) {
      const cls = branchClasses[0];
      return `${cls.shift_time || 'Horario coordinado'} (${cls.name})`;
    }
  }

  if (client.preferred_branch === 'Comas') {
    return 'Lunes y Miércoles 5:00 - 6:30 PM (Sede Comas)';
  }
  return 'Lunes y Miércoles 4:00 - 5:30 PM (Sede Los Olivos)';
}

// DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  initApp();
});

function initApp() {
  initNavigation();
  initModals();
  initForms();
  initRoleSwitcher();
  initBranchSelector();
  initBackupAndImport();
  
  // Set default period inputs to current month (YYYY-MM)
  const now = new Date();
  const currentMonthStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  
  const monthInputs = ['dashboardPeriodMonth', 'membershipMonthFilter', 'paymentMonthFilter', 'paymentPeriodMonth', 'membershipPeriodMonth'];
  monthInputs.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = currentMonthStr;
  });

  // Set default dates for class modal
  const classStartsAt = document.getElementById('classStartsAt');
  if (classStartsAt) {
    const defaultStart = new Date(now.getTime() + 24 * 60 * 60 * 1000);
    defaultStart.setHours(18, 0, 0, 0);
    classStartsAt.value = defaultStart.toISOString().slice(0, 16);
  }

  // Load initial data
  loadAllData();
}

// ==============================================================================
// 3. ENRUTAMIENTO Y NAVEGACIÓN SPA (Vistas y Pantallas)
// ==============================================================================

/**
 * Inicializa los eventos de navegación del menú lateral y accesos rápidos de cabecera.
 */
function initNavigation() {
  const navLinks = document.querySelectorAll('.sidebar-nav .nav-link');
  navLinks.forEach(link => {
    link.addEventListener('click', e => {
      e.preventDefault();
      const targetView = link.getAttribute('data-view');
      switchView(targetView);
    });
  });

  // Alternador de menú lateral en dispositivos móviles/tablets
  const sidebarToggle = document.getElementById('sidebarToggle');
  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', () => {
      document.getElementById('appSidebar').classList.toggle('open');
    });
  }

  // Botones de acción rápida en la barra superior (Top Header)
  document.getElementById('btnQuickClient')?.addEventListener('click', () => openModal('clientFormModal'));
  document.getElementById('btnQuickPayment')?.addEventListener('click', () => openPaymentModal());
  document.getElementById('btnQuickLead')?.addEventListener('click', () => openModal('interactionModal'));
  document.getElementById('btnRefreshDashboard')?.addEventListener('click', () => loadDashboardData());
}

/**
 * Cambia la vista activa del CRM sin recargar la página.
 * Actualiza títulos, migas de pan y resalta la pestaña activa en el menú.
 * @param {string} viewName - Identificador de la vista ('dashboard', 'clients', 'payments', etc.)
 */
function switchView(viewName) {
  document.querySelectorAll('.sidebar-nav .nav-link').forEach(l => l.classList.remove('active'));
  document.querySelectorAll('.app-view').forEach(v => v.classList.remove('active'));

  const activeLink = document.querySelector(`.sidebar-nav .nav-link[data-view="${viewName}"]`);
  const targetView = document.getElementById(`view-${viewName}`);

  if (activeLink) activeLink.classList.add('active');
  if (targetView) targetView.classList.add('active');

  // Actualización dinámica de títulos y subtítulos en el encabezado
  const titles = {
    dashboard: { title: 'Dashboard Gerencial Mensual', sub: 'Resumen de ingresos, captación y vencimientos' },
    clients: { title: 'Directorio de Alumnos & Clientes', sub: 'Gestión de menores, apoderados y canales de captación' },
    interactions: { title: 'Seguimiento CRM & Contactos', sub: 'Historial de llamadas, WhatsApp y recordatorios' },
    classes: { title: 'Programación de Clases & Horarios', sub: 'Gestión por sedes (Los Olivos & Comas) y aforos' },
    memberships: { title: 'Membresías & Ciclos Mensuales', sub: 'Control de planes, asistencias y alertas de vencimiento a 5 días' },
    payments: { title: 'Caja & Registro de Cobros', sub: 'Yape, Plin, Transferencias, Efectivo y Emisión de Recibos' },
    promotions: { title: 'Catálogo de Promociones & Descuentos', sub: 'Descuentos por referidos (S/ 20), matrícula y manuales' },
    'web-simulator': { title: 'Portal Web & Captura de Leads', sub: 'Demostración de auto-ingreso de consultas web al CRM' },
    backup: { title: 'Base de Datos & Backup', sub: 'Respaldo, restauración y mantenimiento de información' },
  };

  if (titles[viewName]) {
    document.getElementById('pageTitle').textContent = titles[viewName].title;
    document.getElementById('pageSubtitle').textContent = titles[viewName].sub;
  }

  // Close sidebar on mobile
  document.getElementById('appSidebar').classList.remove('open');

  // Trigger data refresh if needed
  if (viewName === 'dashboard') loadDashboardData();
  else if (viewName === 'clients') loadClientsData();
  else if (viewName === 'interactions') loadInteractionsData();
  else if (viewName === 'classes') loadClassesData();
  else if (viewName === 'memberships') loadMembershipsData();
  else if (viewName === 'payments') loadPaymentsData();
  else if (viewName === 'promotions') loadPromotionsData();
}

// -------------------------------------------------------------
// Data Fetching & Sync
// -------------------------------------------------------------
async function loadAllData() {
  try {
    // 1. First ensure clients and classes are loaded
    await Promise.all([
      loadClientsData(),
      loadClassesData(),
    ]);

    // 2. Then load remaining data with full student context
    await Promise.all([
      loadDashboardData(),
      loadInteractionsData(),
      loadMembershipsData(),
      loadPaymentsData(),
      loadPromotionsData(),
      loadExpiringAlerts(),
    ]);
  } catch (err) {
    console.error('Error loading initial data:', err);
  }
}

async function loadDashboardData() {
  const period = document.getElementById('dashboardPeriodMonth')?.value || '';
  const branch = state.currentBranch;
  try {
    const res = await fetch(`${API_BASE}/dashboard/monthly?period_month=${period}&branch=${encodeURIComponent(branch)}`);
    if (!res.ok) throw new Error('Failed to load dashboard data');
    const data = await res.json();
    state.dashboardData = data;
    renderDashboard(data);
  } catch (err) {
    console.error(err);
  }
}

async function loadClientsData() {
  const search = document.getElementById('clientSearchInput')?.value || '';
  const status = document.getElementById('clientStatusFilter')?.value || '';
  const minor = document.getElementById('clientMinorFilter')?.value || '';
  const branch = state.currentBranch;

  let url = `${API_BASE}/clients?include_inactive=true&limit=100`;
  if (branch && branch !== 'Todas') url += `&branch=${encodeURIComponent(branch)}`;
  if (search) url += `&search=${encodeURIComponent(search)}`;
  if (status) url += `&status=${status}`;
  if (minor !== '') url += `&is_minor=${minor}`;

  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to load clients');
    const data = await res.json();
    state.clients = data;
    renderClientsTable(data);
    updateClientSelectDropdowns();
    const countBadge = document.getElementById('sidebarClientsCount');
    if (countBadge) countBadge.textContent = data.length;
  } catch (err) {
    console.error(err);
  }
}

async function loadInteractionsData() {
  const channel = document.getElementById('interactionChannelFilter')?.value || '';
  const result = document.getElementById('interactionResultFilter')?.value || '';

  let url = `${API_BASE}/interactions?`;
  if (channel) url += `&channel=${channel}`;
  if (result) url += `&result=${result}`;

  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to load interactions');
    const data = await res.json();
    state.interactions = data;
    renderInteractionsTable(data);

    // Also fetch pending reminders
    const remRes = await fetch(`${API_BASE}/interactions/reminders`);
    if (remRes.ok) {
      state.reminders = await remRes.json();
      const countEl = document.getElementById('sidebarRemindersCount');
      if (countEl) countEl.textContent = state.reminders.length;
      const badgeEl = document.getElementById('dashRemindersCountBadge');
      if (badgeEl) badgeEl.textContent = `${state.reminders.length} pendientes`;
      renderRemindersTable(state.reminders);
    }
  } catch (err) {
    console.error(err);
  }
}

async function loadClassesData() {
  const classType = document.getElementById('classTypeFilter')?.value || '';
  const branch = state.currentBranch;

  let url = `${API_BASE}/class-sessions?limit=100`;
  if (branch && branch !== 'Todas') url += `&branch=${encodeURIComponent(branch)}`;
  if (classType) url += `&class_type=${classType}`;

  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to load classes');
    const data = await res.json();
    state.classes = data;
    renderClassesGrid(data);
  } catch (err) {
    console.error(err);
  }
}

async function loadMembershipsData() {
  const period = document.getElementById('membershipMonthFilter')?.value || '';
  const status = document.getElementById('membershipStatusFilter')?.value || '';
  const paymentStatus = document.getElementById('membershipPaymentStatusFilter')?.value || '';
  const branch = state.currentBranch;

  let url = `${API_BASE}/memberships?limit=100`;
  if (branch && branch !== 'Todas') url += `&branch=${encodeURIComponent(branch)}`;
  if (period) url += `&period_month=${period}`;
  if (status) url += `&status=${status}`;
  if (paymentStatus) url += `&payment_status=${paymentStatus}`;

  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to load memberships');
    const data = await res.json();
    state.memberships = data;
    renderMembershipsTable(data);
  } catch (err) {
    console.error(err);
  }
}

async function loadPaymentsData() {
  const period = document.getElementById('paymentMonthFilter')?.value || '';
  const method = document.getElementById('paymentMethodFilter')?.value || '';
  const status = document.getElementById('paymentStatusFilter')?.value || '';
  const branch = state.currentBranch;

  let url = `${API_BASE}/payments?limit=100`;
  if (branch && branch !== 'Todas') url += `&branch=${encodeURIComponent(branch)}`;
  if (period) url += `&period_month=${period}`;
  if (method) url += `&payment_method=${method}`;
  if (status) url += `&status=${status}`;

  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to load payments');
    const data = await res.json();
    state.payments = data;
    renderPaymentsTable(data);
  } catch (err) {
    console.error(err);
  }
}

async function loadPromotionsData() {
  try {
    const res = await fetch(`${API_BASE}/promotions`);
    if (!res.ok) throw new Error('Failed to load promotions');
    const data = await res.json();
    state.promotions = data;
    renderPromotionsGrid(data);
    updatePromotionSelectDropdowns();
  } catch (err) {
    console.error(err);
  }
}

async function loadExpiringAlerts() {
  try {
    const res = await fetch(`${API_BASE}/memberships/expiring?days=5&branch=${state.currentBranch}`);
    if (res.ok) {
      const expiring = await res.json();
      state.expiringMemberships = expiring;
      document.getElementById('sidebarExpiringCount').textContent = expiring.length;
      document.getElementById('dashExpiringCountBadge').textContent = `${expiring.length} por vencer`;
      renderExpiringTable(expiring);
      renderUrgentBanner(expiring);
    }
  } catch (err) {
    console.error(err);
  }
}

// -------------------------------------------------------------
// Rendering Functions
// -------------------------------------------------------------
function renderDashboard(data) {
  // Update KPI Cards
  document.getElementById('kpiTotalRevenue').textContent = `S/ ${parseFloat(data.total_revenue).toFixed(2)}`;
  document.getElementById('kpiActiveClients').textContent = data.active_clients;
  document.getElementById('kpiNewClients').textContent = data.new_clients;
  document.getElementById('kpiRetiredClients').textContent = data.retired_clients;

  // 1. Render 3-Month Sales Trend Chart (Section 7.2)
  const ctxQuarterly = document.getElementById('quarterlySalesChart')?.getContext('2d');
  if (ctxQuarterly) {
    if (state.charts.quarterly) state.charts.quarterly.destroy();
    
    const labels = data.three_months_sales.map(s => s.month_name);
    const salesValues = data.three_months_sales.map(s => parseFloat(s.total_sales));
    const newClients = data.three_months_sales.map(s => s.clients_new);

    state.charts.quarterly = new Chart(ctxQuarterly, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Ingresos Totales (S/)',
            data: salesValues,
            backgroundColor: 'rgba(217, 119, 6, 0.85)',
            borderColor: '#d97706',
            borderWidth: 1,
            borderRadius: 6,
            yAxisID: 'y',
          },
          {
            label: 'Nuevos Alumnos',
            data: newClients,
            type: 'line',
            borderColor: '#3b82f6',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            borderWidth: 3,
            fill: false,
            tension: 0.3,
            yAxisID: 'y1',
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            type: 'linear',
            position: 'left',
            ticks: { callback: v => `S/ ${v}` },
            grid: { color: 'rgba(0,0,0,0.05)' }
          },
          y1: {
            type: 'linear',
            position: 'right',
            grid: { drawOnChartArea: false },
            ticks: { precision: 0 }
          }
        }
      }
    });
  }

  // 2. Render Revenue by Modality Pie Chart (Section 7.5)
  const ctxModality = document.getElementById('modalityRevenueChart')?.getContext('2d');
  if (ctxModality) {
    if (state.charts.modality) state.charts.modality.destroy();

    const modalityLabels = data.revenue_by_modality.map(m => m.label);
    const modalityAmounts = data.revenue_by_modality.map(m => parseFloat(m.total_amount));

    state.charts.modality = new Chart(ctxModality, {
      type: 'doughnut',
      data: {
        labels: modalityLabels,
        datasets: [{
          data: modalityAmounts,
          backgroundColor: [
            '#0a192f', // Navy
            '#d97706', // Gold Amber
            '#10b981', // Emerald
            '#6366f1', // Indigo
            '#94a3b8'  // Gray
          ],
          borderWidth: 2,
          borderColor: '#ffffff',
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } },
          tooltip: {
            callbacks: {
              label: item => ` ${item.label}: S/ ${item.raw.toFixed(2)}`
            }
          }
        }
      }
    });
  }

  // 3. Render Acquisition Channels (Section 7.6)
  const pillsContainer = document.getElementById('acquisitionPillsContainer');
  if (pillsContainer) {
    pillsContainer.innerHTML = data.acquisition_channels.map(c => `
      <div class="acq-pill">
        <div class="acq-pill-title">${c.label}</div>
        <div class="acq-pill-count">${c.clients_count}</div>
        <div class="acq-pill-pct">${c.percentage}% del total</div>
      </div>
    `).join('');
  }
}

function renderUrgentBanner(expiringList) {
  const container = document.getElementById('urgentAlertsBanner');
  if (!container) return;

  if (expiringList.length === 0) {
    container.innerHTML = '';
    return;
  }

  container.innerHTML = `
    <div class="urgent-alert alert-warning">
      <div>
        <i class="fa-solid fa-bell"></i> <strong>Aviso de Cobranza:</strong> Hay <strong>${expiringList.length} membresía(s)</strong> que vencen en los próximos 5 días. Realice el seguimiento por WhatsApp.
      </div>
      <button class="btn btn-sm btn-primary" onclick="switchView('memberships')">Ver Lista & Cobrar</button>
    </div>
  `;
}

function renderExpiringTable(expiringList) {
  const tbody = document.querySelector('#dashExpiringTable tbody');
  if (!tbody) return;

  if (expiringList.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-3">No hay membresías por vencer en los próximos 5 días.</td></tr>`;
    return;
  }

  tbody.innerHTML = expiringList.map(m => {
    const client = state.clients.find(c => c.id === m.client_id);
    const clientDisplayName = m.client_name || (client ? `${client.first_name} ${client.last_name}` : 'Alumno');
    return `
      <tr>
        <td>
          <a href="#" class="client-name-link font-weight-bold" onclick="openClientProfile('${m.client_id}'); return false;">
            <strong>${clientDisplayName}</strong>
          </a>
        </td>
        <td><span class="badge badge-secondary">${m.branch}</span></td>
        <td>${m.plan_name}</td>
        <td><span class="badge badge-danger">${m.end_date}</span></td>
        <td>
          <button class="btn btn-sm btn-primary" onclick="openPaymentForMembership('${m.id}', '${m.client_id}')" title="Registrar Cobro Inmediato">
            <i class="fa-solid fa-cash-register"></i> Cobrar
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

function renderRemindersTable(reminders) {
  const tbody = document.querySelector('#dashRemindersTable tbody');
  if (!tbody) return;

  if (reminders.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-3">No hay recordatorios pendientes.</td></tr>`;
    return;
  }

  tbody.innerHTML = reminders.slice(0, 5).map(r => {
    const client = state.clients.find(c => c.id === r.client_id) || { first_name: 'Prospecto', last_name: '', whatsapp: '' };
    return `
      <tr>
        <td><strong>${client.first_name} ${client.last_name}</strong></td>
        <td><span class="badge badge-primary">${r.channel}</span></td>
        <td>${r.motive.replace(/_/g, ' ')}</td>
        <td><span class="badge badge-warning">${r.result.replace(/_/g, ' ')}</span></td>
        <td>${r.attended_by}</td>
      </tr>
    `;
  }).join('');
}

function renderClientsTable(clients) {
  const tbody = document.getElementById('clientsTableBody');
  if (!tbody) return;

  if (clients.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted">No se encontraron alumnos registrados con los filtros seleccionados.</td></tr>`;
    return;
  }

  tbody.innerHTML = clients.map(c => {
    const isMinorBadge = c.is_minor 
      ? `<span class="badge badge-warning"><i class="fa-solid fa-child"></i> Menor</span>`
      : `<span class="badge badge-secondary">Adulto</span>`;

    const statusBadges = {
      active: `<span class="badge badge-success">Activo</span>`,
      interested: `<span class="badge badge-primary">Interesado</span>`,
      retired: `<span class="badge badge-danger">Retirado</span>`,
    };

    const guardianInfo = c.is_minor && c.guardian_name 
      ? `<div><strong>${c.guardian_name}</strong> (${c.guardian_relationship || 'Tutor'})<br><small class="text-muted"><i class="fa-brands fa-whatsapp text-success"></i> ${c.guardian_phone || '-'}</small></div>`
      : `<span class="text-muted">Directo</span>`;

    const directPhone = c.whatsapp || c.phone || '-';

    const retirementDisplay = c.status === 'retired' && c.uninterested_reason
      ? `<br><small class="text-danger"><i class="fa-solid fa-user-xmark"></i> ${c.uninterested_reason.replace(/_/g, ' ')}</small>`
      : '';

    return `
      <tr>
        <td>
          <a href="#" class="client-name-link font-weight-bold" onclick="openClientProfile('${c.id}'); return false;">
            <strong>${c.first_name} ${c.last_name}</strong>
          </a>
          <br><small class="text-muted">${c.email || ''}</small>
        </td>
        <td>
          ${c.dni ? `<strong>${c.dni}</strong>` : '<span class="text-muted">Sin DNI</span>'}
          <br>${isMinorBadge}
        </td>
        <td><span class="badge badge-secondary">${c.preferred_branch || 'Los Olivos'}</span></td>
        <td>
          <a href="https://wa.me/${directPhone.replace(/[^0-9]/g, '')}" target="_blank" class="text-success font-weight-bold">
            <i class="fa-brands fa-whatsapp"></i> ${directPhone}
          </a>
        </td>
        <td>${guardianInfo}</td>
        <td><span class="badge badge-secondary">${c.acquisition_source}</span></td>
        <td>
          ${statusBadges[c.status] || c.status}
          ${retirementDisplay}
        </td>
        <td>
          <div class="d-flex gap-1">
            <button class="btn btn-sm btn-light" onclick="openClientProfile('${c.id}')" title="Ver Ficha 360°">
              <i class="fa-solid fa-eye"></i>
            </button>
            <button class="btn btn-sm btn-light" onclick="editClient('${c.id}')" title="Editar">
              <i class="fa-solid fa-pen"></i>
            </button>
            ${c.status === 'active' ? `
              <button class="btn btn-sm btn-light text-danger" onclick="openRetireClientModal('${c.id}')" title="Dar de baja / Retirar alumno">
                <i class="fa-solid fa-user-minus"></i>
              </button>
            ` : (c.status === 'retired' ? `
              <button class="btn btn-sm btn-light text-success" onclick="handleReactivateClient('${c.id}')" title="Reactivar e inscribir alumno">
                <i class="fa-solid fa-user-plus"></i>
              </button>
            ` : '')}
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function renderInteractionsTable(interactions) {
  const tbody = document.getElementById('interactionsTableBody');
  if (!tbody) return;

  if (interactions.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" class="text-center py-4 text-muted">No se registran interacciones con los filtros actuales.</td></tr>`;
    return;
  }

  tbody.innerHTML = interactions.map(it => {
    const client = state.clients.find(c => c.id === it.client_id) || { first_name: 'Cliente', last_name: '', phone: '' };
    const dateFormatted = new Date(it.interaction_date).toLocaleString('es-PE', { dateStyle: 'short', timeStyle: 'short' });

    const resultBadges = {
      pidio_informacion: '<span class="badge badge-primary">Pidió información</span>',
      vino_a_probarse: '<span class="badge badge-info">Vino a probar</span>',
      se_inscribio: '<span class="badge badge-success">Se inscribió</span>',
      se_matriculo: '<span class="badge badge-success">Se matriculó</span>',
      lo_pensara: '<span class="badge badge-warning">Lo pensará</span>',
      no_respondio: '<span class="badge badge-danger">No respondió</span>',
    };

    return `
      <tr>
        <td>${dateFormatted}</td>
        <td>
          <a href="#" onclick="openClientProfile('${it.client_id}'); return false;">
            <strong>${client.first_name} ${client.last_name}</strong>
          </a>
        </td>
        <td><span class="badge badge-secondary">${it.channel}</span></td>
        <td>${it.motive.replace(/_/g, ' ')}</td>
        <td style="max-width: 250px;">${it.summary}</td>
        <td>${resultBadges[it.result] || it.result}</td>
        <td>${it.uninterested_reason ? it.uninterested_reason.replace(/_/g, ' ') : '<span class="text-muted">-</span>'}</td>
        <td>${it.attended_by}</td>
        <td>
          ${it.reminder_active ? '<span class="badge badge-warning"><i class="fa-solid fa-clock"></i> Pendiente</span>' : '<span class="badge badge-secondary">Cerrado</span>'}
        </td>
      </tr>
    `;
  }).join('');
}

function renderClassesGrid(classes) {
  const grid = document.getElementById('classesCardsGrid');
  if (!grid) return;

  if (classes.length === 0) {
    grid.innerHTML = `<div class="col-12 text-center py-5 text-muted">No hay clases programadas para esta sede.</div>`;
    return;
  }

  grid.innerHTML = classes.map(cls => {
    const startsAt = new Date(cls.starts_at).toLocaleString('es-PE', { dateStyle: 'short', timeStyle: 'short' });
    const fillPercentage = Math.min(100, Math.round((0 / cls.capacity) * 100));

    return `
      <div class="class-card">
        <div class="class-card-header">
          <div>
            <div class="class-card-title">${cls.name}</div>
            <span class="class-card-branch"><i class="fa-solid fa-location-dot"></i> ${cls.branch}</span>
          </div>
          <span class="badge badge-secondary">${cls.class_type}</span>
        </div>
        <div class="class-card-body">
          <div class="class-info-row">
            <i class="fa-solid fa-clock text-warning"></i>
            <span>${cls.shift_time || startsAt}</span>
          </div>
          <div class="class-info-row">
            <i class="fa-solid fa-graduation-cap"></i>
            <span>Nivel: <strong>${cls.level}</strong> (${cls.age_group})</span>
          </div>
          <div class="class-info-row">
            <i class="fa-solid fa-chalkboard-user"></i>
            <span>Profesor: ${cls.instructor_name || 'Por asignar'}</span>
          </div>

          <div class="class-capacity-bar">
            <div class="class-capacity-fill" style="width: ${fillPercentage}%"></div>
          </div>
          <div class="d-flex justify-content-between text-muted text-sm mb-3">
            <span>Aforo: ${cls.capacity} alumnos máx.</span>
          </div>

          <button class="btn btn-sm btn-primary full-width" onclick="openEnrollmentModal('${cls.id}')">
            <i class="fa-solid fa-user-plus"></i> Inscribir Alumno
          </button>
        </div>
      </div>
    `;
  }).join('');
}

function renderMembershipsTable(memberships) {
  const tbody = document.getElementById('membershipsTableBody');
  if (!tbody) return;

  if (memberships.length === 0) {
    tbody.innerHTML = `<tr><td colspan="10" class="text-center py-4 text-muted">No se encontraron membresías con los filtros actuales.</td></tr>`;
    return;
  }

  tbody.innerHTML = memberships.map(m => {
    const client = state.clients.find(c => c.id === m.client_id);
    const clientDisplayName = m.client_name || (client ? `${client.first_name} ${client.last_name}` : 'Alumno');
    const clientDni = m.client_dni || (client ? client.dni : null);
    
    const paymentBadges = {
      paid: '<span class="badge badge-success"><i class="fa-solid fa-check"></i> Pagado</span>',
      pending: '<span class="badge badge-danger"><i class="fa-solid fa-clock"></i> Pendiente</span>',
      partial: '<span class="badge badge-warning"><i class="fa-solid fa-circle-half-stroke"></i> Parcial</span>',
    };

    const statusBadges = {
      active: '<span class="badge badge-success">Activa</span>',
      expiring_soon: '<span class="badge badge-warning">Por Vencer</span>',
      expired: '<span class="badge badge-secondary">Vencida</span>',
      cancelled: '<span class="badge badge-danger">Cancelada</span>',
    };

    return `
      <tr>
        <td>
          <a href="#" class="client-name-link font-weight-bold" onclick="openClientProfile('${m.client_id}'); return false;">
            <strong>${clientDisplayName}</strong>
          </a>
          ${clientDni ? `<br><small class="text-muted">DNI: ${clientDni}</small>` : ''}
        </td>
        <td><span class="badge badge-secondary">${m.branch}</span></td>
        <td><strong>${m.plan_name}</strong></td>
        <td><span class="badge badge-primary">${m.period_month}</span></td>
        <td><small>${m.start_date} al <strong>${m.end_date}</strong></small></td>
        <td><span class="badge badge-secondary">${m.classes_attended} / ${m.classes_total} asist.</span></td>
        <td><strong>S/ ${parseFloat(m.final_price).toFixed(2)}</strong></td>
        <td>${paymentBadges[m.payment_status] || m.payment_status}</td>
        <td>${statusBadges[m.status] || m.status}</td>
        <td>
          ${m.payment_status !== 'paid' ? `
            <button class="btn btn-sm btn-primary" onclick="openPaymentForMembership('${m.id}', '${m.client_id}')" title="Registrar Cobro">
              <i class="fa-solid fa-cash-register"></i> Cobrar
            </button>
          ` : `
            <span class="text-success small"><i class="fa-solid fa-circle-check"></i> Al día</span>
          `}
        </td>
      </tr>
    `;
  }).join('');
}

function renderPaymentsTable(payments) {
  const tbody = document.getElementById('paymentsTableBody');
  if (!tbody) return;

  if (payments.length === 0) {
    tbody.innerHTML = `<tr><td colspan="10" class="text-center py-4 text-muted">No se registran pagos en el periodo.</td></tr>`;
    return;
  }

  tbody.innerHTML = payments.map(p => {
    const client = state.clients.find(c => c.id === p.client_id);
    const clientDisplayName = p.client_name || (client ? `${client.first_name} ${client.last_name}` : 'Alumno');
    const dateFormatted = new Date(p.payment_date).toLocaleString('es-PE', { dateStyle: 'short', timeStyle: 'short' });

    const statusBadge = p.status === 'completed'
      ? `<span class="badge badge-success">Completado</span>`
      : `<span class="badge badge-danger">Anulado</span>`;

    return `
      <tr>
        <td>${dateFormatted}</td>
        <td>
          <a href="#" class="client-name-link" onclick="openClientProfile('${p.client_id}'); return false;">
            <strong>${clientDisplayName}</strong>
          </a>
        </td>
        <td><strong>${p.concept.toUpperCase()}</strong> ${p.shift_detail ? `<br><small class="text-muted"><i class="fa-solid fa-clock"></i> ${p.shift_detail}</small>` : ''}</td>
        <td><span class="badge badge-primary">${p.period_month}</span></td>
        <td><span class="badge badge-secondary">${p.payment_method.toUpperCase()}</span></td>
        <td><strong class="text-success">S/ ${parseFloat(p.amount).toFixed(2)}</strong></td>
        <td><span class="badge badge-secondary">${p.branch}</span></td>
        <td>${p.registered_by}</td>
        <td>${statusBadge}</td>
        <td>
          <button class="btn btn-sm btn-light" onclick="viewReceipt('${p.id}')" title="Ver Recibo">
            <i class="fa-solid fa-receipt"></i>
          </button>
          ${p.status === 'completed' ? `
            <button class="btn btn-sm btn-danger" onclick="openCancelPaymentModal('${p.id}')" title="Anular Pago">
              <i class="fa-solid fa-ban"></i>
            </button>
          ` : ''}
        </td>
      </tr>
    `;
  }).join('');
}

function renderPromotionsGrid(promos) {
  const grid = document.getElementById('promotionsCardsGrid');
  if (!grid) return;

  if (promos.length === 0) {
    grid.innerHTML = `<div class="col-12 text-center py-5 text-muted">No hay promociones configuradas.</div>`;
    return;
  }

  grid.innerHTML = promos.map(pr => {
    let displayVal = `S/ ${pr.discount_value}`;
    if (pr.discount_type === 'percentage') displayVal = `${pr.discount_value}%`;
    if (pr.discount_type === 'enrollment_fee_waiver') displayVal = `Gratis (100%)`;

    return `
      <div class="promo-card">
        <div class="promo-val-badge">${displayVal}</div>
        <h4>${pr.name}</h4>
        <p class="text-muted text-sm mb-3">${pr.description || 'Válido para 8 clases en el mes correspondiente.'}</p>
        <span class="badge badge-success">Activa</span>
      </div>
    `;
  }).join('');
}

// -------------------------------------------------------------
// 360° Profile & Timeline View (Section 3.7)
// -------------------------------------------------------------
async function openClientProfile(clientId) {
  const client = state.clients.find(c => c.id === clientId);
  if (!client) return;

  state.selectedClientForProfile = client;

  document.getElementById('profileClientName').textContent = `${client.first_name} ${client.last_name}`;
  document.getElementById('profileClientMeta').textContent = `DNI: ${client.dni || 'Sin DNI'} | Sede: ${client.preferred_branch || 'Los Olivos'} | Estado: ${client.status.toUpperCase()}`;

  // Populate info list
  const infoList = document.getElementById('profileInfoList');
  infoList.innerHTML = `
    <li><strong>DNI:</strong> <span>${client.dni || 'No registrado'}</span></li>
    <li><strong>WhatsApp Directo:</strong> <span>${client.whatsapp || '-'}</span></li>
    <li><strong>Teléfono:</strong> <span>${client.phone || '-'}</span></li>
    <li><strong>Año de Nacimiento:</strong> <span>${client.birth_year || '-'} (${client.is_minor ? 'Menor de edad' : 'Mayor de edad'})</span></li>
    ${client.is_minor ? `
      <li><strong>Apoderado (Tutor):</strong> <span>${client.guardian_name || '-'} (${client.guardian_relationship || 'Tutor'})</span></li>
      <li><strong>WhatsApp Apoderado:</strong> <span>${client.guardian_phone || '-'}</span></li>
    ` : ''}
    <li><strong>Sede:</strong> <span>${client.preferred_branch}</span></li>
    <li><strong>Canal de Captación:</strong> <span>${client.acquisition_source}</span></li>
    ${client.referrer_name ? `<li><strong>Recomendado por:</strong> <span>${client.referrer_name} (${client.referrer_phone})</span></li>` : ''}
    ${client.status === 'retired' && client.uninterested_reason ? `<li><strong>Motivo de Retiro:</strong> <span class="text-danger fw-bold">${client.uninterested_reason}</span></li>` : ''}
    <li><strong>Notas:</strong> <span>${client.notes || 'Ninguna'}</span></li>
  `;

  // Toggle Retire / Reactivate profile action buttons
  const btnRetire = document.getElementById('btnProfileRetireClient');
  const btnReactivate = document.getElementById('btnProfileReactivateClient');
  if (btnRetire && btnReactivate) {
    if (client.status === 'retired') {
      btnRetire.classList.add('hidden');
      btnReactivate.classList.remove('hidden');
    } else {
      btnRetire.classList.remove('hidden');
      btnReactivate.classList.add('hidden');
    }
  }

  // WhatsApp Button setup
  updateWhatsAppTrigger();

  // Load and render timeline
  const timelineContainer = document.getElementById('profileTimelineContainer');
  timelineContainer.innerHTML = '<div class="text-center text-muted">Cargando línea de tiempo 360°...</div>';

  try {
    const res = await fetch(`${API_BASE}/clients/${clientId}/timeline`);
    if (res.ok) {
      const timeline = await res.json();
      if (timeline.length === 0) {
        timelineContainer.innerHTML = '<div class="text-muted text-center py-4">No hay eventos registrados en el historial de este alumno.</div>';
      } else {
        timelineContainer.innerHTML = timeline.map(item => {
          const dateStr = new Date(item.timestamp).toLocaleString('es-PE', { dateStyle: 'medium', timeStyle: 'short' });
          return `
            <div class="timeline-item item-${item.event_type}">
              <div class="timeline-dot"></div>
              <div class="timeline-time">${dateStr} &bull; ${item.author_or_channel}</div>
              <div class="timeline-title">${item.title}</div>
              <div class="timeline-desc">${item.description}</div>
            </div>
          `;
        }).join('');
      }
    }
  } catch (err) {
    timelineContainer.innerHTML = '<div class="text-danger">Error al cargar la línea de tiempo.</div>';
  }

  openModal('clientProfileModal');
}

function updateWhatsAppTrigger() {
  const client = state.selectedClientForProfile;
  if (!client) return;

  const phone = (client.is_minor && client.guardian_phone) ? client.guardian_phone : (client.whatsapp || client.phone || '');
  const template = document.getElementById('profileWspTemplateSelect')?.value || 'bienvenida';
  
  const cleanPhone = phone.replace(/[^0-9]/g, '');
  const greetingName = client.is_minor ? (client.guardian_name || client.first_name) : client.first_name;

  let message = '';
  if (template === 'recordatorio_pago') {
    message = `Hola estimado(a) ${greetingName}, le saludamos del Taller de Marinera Garbo & Salero. Le recordamos cordialmente que la mensualidad de marinera para el alumno(a) ${client.first_name} está próxima a vencer. Puede regularizar su pago mediante Yape, Plin o Transferencia. ¡Muchas gracias!`;
  } else if (template === 'bienvenida') {
    message = `¡Hola ${greetingName}! Te damos la más cálida bienvenida a la familia de Garbo & Salero Semillero de Campeones. Te compartimos los horarios y el enlace a nuestro grupo oficial de WhatsApp para avisos importantes.`;
  } else if (template === 'clase_prueba') {
    message = `Hola ${greetingName}, confirmamos tu clase de prueba demostrativa de Marinera Norteña en nuestra Sede ${client.preferred_branch}. Recuerda asistir con ropa cómoda y pañuelo. ¡Te esperamos!`;
  } else {
    message = `Hola ${greetingName}, le escribimos del Taller de Marinera Garbo & Salero para consultar si tiene alguna duda sobre nuestros turnos y clases. Con gusto le asesoramos.`;
  }

  const wspBtn = document.getElementById('btnSendWspMessage');
  if (wspBtn) {
    wspBtn.href = `https://wa.me/${cleanPhone.startsWith('51') ? cleanPhone : '51' + cleanPhone}?text=${encodeURIComponent(message)}`;
  }
}

// -------------------------------------------------------------
// Modals & Forms Handlers
// -------------------------------------------------------------
function initModals() {
  document.querySelectorAll('[data-close-modal]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active'));
    });
  });

  // Modal open triggers
  document.getElementById('btnOpenNewClientModal')?.addEventListener('click', () => openModal('clientFormModal'));
  document.getElementById('btnOpenNewInteractionModal')?.addEventListener('click', () => openModal('interactionModal'));
  document.getElementById('btnOpenNewClassModal')?.addEventListener('click', () => openModal('classModal'));
  document.getElementById('btnOpenNewMembershipModal')?.addEventListener('click', () => openModal('membershipModal'));
  document.getElementById('btnOpenNewPaymentModal')?.addEventListener('click', () => openPaymentModal());
  
  // Real-time auto-fill when changing student in Payment Modal
  document.getElementById('paymentClientId')?.addEventListener('change', (e) => {
    const selectedClientId = e.target.value;
    const client = state.clients.find(c => c.id === selectedClientId);
    if (client) {
      if (client.preferred_branch) {
        const branchSelect = document.getElementById('paymentBranch');
        if (branchSelect) branchSelect.value = client.preferred_branch;
      }
      const shiftInput = document.getElementById('paymentShiftDetail');
      if (shiftInput) {
        shiftInput.value = getClientSchedule(selectedClientId);
      }
    }
  });

  // Profile sub-buttons
  document.getElementById('btnProfileAddInteraction')?.addEventListener('click', () => {
    if (state.selectedClientForProfile) {
      document.getElementById('interactionClientId').value = state.selectedClientForProfile.id;
      openModal('interactionModal');
    }
  });

  document.getElementById('btnProfileAddPayment')?.addEventListener('click', () => {
    if (state.selectedClientForProfile) {
      openPaymentModal(state.selectedClientForProfile.id);
    }
  });

  document.getElementById('btnProfileApplyDiscount')?.addEventListener('click', () => {
    if (state.selectedClientForProfile) {
      document.getElementById('discountClientId').value = state.selectedClientForProfile.id;
      openModal('discountModal');
    }
  });

  document.getElementById('btnProfileRetireClient')?.addEventListener('click', () => {
    if (state.selectedClientForProfile) {
      openRetireClientModal(state.selectedClientForProfile.id);
    }
  });

  document.getElementById('btnProfileReactivateClient')?.addEventListener('click', () => {
    if (state.selectedClientForProfile) {
      handleReactivateClient(state.selectedClientForProfile.id);
    }
  });

  document.getElementById('profileWspTemplateSelect')?.addEventListener('change', updateWhatsAppTrigger);
}

function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.add('active');
}

function openPaymentModal(clientId = null, membershipId = null) {
  const form = document.getElementById('paymentForm');
  if (form) form.reset();

  // 1. Auto-generate sequential / correlative operation reference
  const opRefInput = document.getElementById('paymentRef');
  if (opRefInput) {
    opRefInput.value = generateNextOperationNumber();
  }

  // 2. Set default period month (current YYYY-MM)
  const now = new Date();
  const currentMonthStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  const periodInput = document.getElementById('paymentPeriodMonth');
  if (periodInput) {
    periodInput.value = currentMonthStr;
  }

  // 3. Ensure student dropdowns are up to date
  updateClientSelectDropdowns();

  const clientSelect = document.getElementById('paymentClientId');
  const targetClientId = clientId || (state.clients.length > 0 ? state.clients[0].id : null);

  if (targetClientId && clientSelect) {
    clientSelect.value = targetClientId;
  }

  // 4. If opened for a specific membership (e.g. from alert or table)
  if (membershipId) {
    const mem = state.memberships.find(m => m.id === membershipId);
    if (mem) {
      if (mem.client_id && clientSelect) clientSelect.value = mem.client_id;
      const amtInput = document.getElementById('paymentAmount');
      if (amtInput) amtInput.value = parseFloat(mem.final_price).toFixed(2);
      if (periodInput) periodInput.value = mem.period_month;
      const branchSelect = document.getElementById('paymentBranch');
      if (branchSelect) branchSelect.value = mem.branch;
      const conceptSelect = document.getElementById('paymentConcept');
      if (conceptSelect) conceptSelect.value = 'mensualidad';
    }
  } else {
    const amtInput = document.getElementById('paymentAmount');
    if (amtInput && !amtInput.value) amtInput.value = '150.00';
  }

  // 5. Auto-populate schedule and branch for selected client
  const finalClientId = clientSelect ? clientSelect.value : targetClientId;
  if (finalClientId) {
    const client = state.clients.find(c => c.id === finalClientId);
    if (client && client.preferred_branch && !membershipId) {
      const branchSelect = document.getElementById('paymentBranch');
      if (branchSelect) branchSelect.value = client.preferred_branch;
    }
    const shiftInput = document.getElementById('paymentShiftDetail');
    if (shiftInput) {
      shiftInput.value = getClientSchedule(finalClientId);
    }
  }

  openModal('paymentModal');
}

function initForms() {
  // Minor checkbox toggle
  const isMinorCheckbox = document.getElementById('clientIsMinor');
  const guardianContainer = document.getElementById('guardianFieldsContainer');
  if (isMinorCheckbox && guardianContainer) {
    isMinorCheckbox.addEventListener('change', () => {
      guardianContainer.classList.toggle('hidden', !isMinorCheckbox.checked);
    });
  }

  // Referral source toggle
  const sourceSelect = document.getElementById('clientAcquisitionSource');
  const referralContainer = document.getElementById('referralFieldsContainer');
  if (sourceSelect && referralContainer) {
    sourceSelect.addEventListener('change', () => {
      referralContainer.classList.toggle('hidden', sourceSelect.value !== 'referral');
    });
  }

  // Web simulator minor toggle
  const webMinor = document.getElementById('webIsMinor');
  const webGuardian = document.getElementById('webGuardianFields');
  if (webMinor && webGuardian) {
    webMinor.addEventListener('change', () => {
      webGuardian.classList.toggle('hidden', !webMinor.checked);
    });
  }

  // 1. Client Form Submit
  document.getElementById('clientForm')?.addEventListener('submit', async e => {
    e.preventDefault();
    const clientId = document.getElementById('formClientId').value;

    const payload = {
      first_name: document.getElementById('clientFirstName').value,
      last_name: document.getElementById('clientLastName').value,
      dni: document.getElementById('clientDni').value || null,
      whatsapp: document.getElementById('clientWhatsapp').value || null,
      phone: document.getElementById('clientPhone').value || null,
      birth_year: document.getElementById('clientBirthYear').value ? parseInt(document.getElementById('clientBirthYear').value) : null,
      is_minor: document.getElementById('clientIsMinor').checked,
      guardian_name: document.getElementById('clientGuardianName').value || null,
      guardian_phone: document.getElementById('clientGuardianPhone').value || null,
      guardian_relationship: document.getElementById('clientGuardianRelationship').value || null,
      guardian_dni: document.getElementById('clientGuardianDni').value || null,
      preferred_branch: document.getElementById('clientPreferredBranch').value,
      status: document.getElementById('clientStatus').value,
      acquisition_source: document.getElementById('clientAcquisitionSource').value,
      referrer_name: document.getElementById('clientReferrerName').value || null,
      referrer_phone: document.getElementById('clientReferrerPhone').value || null,
      uninterested_reason: document.getElementById('clientUninterestedReason').value || null,
      notes: document.getElementById('clientNotes').value || null,
    };

    try {
      const url = clientId ? `${API_BASE}/clients/${clientId}` : `${API_BASE}/clients`;
      const method = clientId ? 'PATCH' : 'POST';

      const res = await fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Error al guardar cliente');
      }

      showToast('Alumno guardado exitosamente', 'success');
      document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active'));
      document.getElementById('clientForm').reset();
      loadClientsData();
      loadDashboardData();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // 2. Interaction Form Submit
  document.getElementById('interactionForm')?.addEventListener('submit', async e => {
    e.preventDefault();
    const payload = {
      client_id: document.getElementById('interactionClientId').value,
      channel: document.getElementById('interactionChannel').value,
      motive: document.getElementById('interactionMotive').value,
      summary: document.getElementById('interactionSummary').value,
      result: document.getElementById('interactionResult').value,
      uninterested_reason: document.getElementById('interactionUninterestedReason').value || null,
      attended_by: document.getElementById('interactionAttendedBy').value,
      next_followup_date: document.getElementById('interactionFollowupDate').value || null,
    };

    try {
      const res = await fetch(`${API_BASE}/interactions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error('Error al registrar interacción');

      showToast('Interacción registrada con éxito', 'success');
      document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active'));
      document.getElementById('interactionForm').reset();
      loadInteractionsData();
      loadDashboardData();
      if (state.selectedClientForProfile) openClientProfile(state.selectedClientForProfile.id);
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // 3. Payment Form Submit
  document.getElementById('paymentForm')?.addEventListener('submit', async e => {
    e.preventDefault();
    const payload = {
      client_id: document.getElementById('paymentClientId').value,
      amount: parseFloat(document.getElementById('paymentAmount').value),
      period_month: document.getElementById('paymentPeriodMonth').value,
      concept: document.getElementById('paymentConcept').value,
      shift_detail: document.getElementById('paymentShiftDetail').value || null,
      payment_method: document.getElementById('paymentMethod').value,
      transaction_reference: document.getElementById('paymentRef').value || null,
      branch: document.getElementById('paymentBranch').value,
      registered_by: state.currentUser.full_name,
    };

    try {
      const res = await fetch(`${API_BASE}/payments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error('Error al registrar el cobro');
      const createdPayment = await res.json();

      showToast('Pago registrado correctamente', 'success');
      document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active'));
      document.getElementById('paymentForm').reset();

      loadPaymentsData();
      loadMembershipsData();
      loadDashboardData();
      viewReceipt(createdPayment.id);
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // 4. Cancel Payment Form Submit (Section 6.5)
  document.getElementById('cancelPaymentForm')?.addEventListener('submit', async e => {
    e.preventDefault();
    const paymentId = document.getElementById('cancelPaymentId').value;
    const payload = {
      cancellation_reason: document.getElementById('cancelReason').value,
      cancelled_by: document.getElementById('cancelAuthorizedBy').value,
    };

    try {
      const res = await fetch(`${API_BASE}/payments/${paymentId}/cancel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error('Error al anular el pago');

      showToast('Pago anulado y registrado en auditoría', 'success');
      document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active'));
      loadPaymentsData();
      loadMembershipsData();
      loadDashboardData();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // 5. Membership Form Submit
  document.getElementById('membershipForm')?.addEventListener('submit', async e => {
    e.preventDefault();
    const payload = {
      client_id: document.getElementById('membershipClientId').value,
      branch: document.getElementById('membershipBranch').value,
      class_type: document.getElementById('membershipClassType').value,
      plan_name: document.getElementById('membershipPlanName').value,
      period_month: document.getElementById('membershipPeriodMonth').value,
      start_date: document.getElementById('membershipStartDate').value,
      end_date: document.getElementById('membershipEndDate').value,
      price: parseFloat(document.getElementById('membershipPrice').value),
      discount_applied: parseFloat(document.getElementById('membershipDiscount').value || 0),
      payment_status: document.getElementById('membershipPaymentStatus').value,
    };

    try {
      const res = await fetch(`${API_BASE}/memberships`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error('Error al asignar membresía');

      showToast('Membresía creada exitosamente', 'success');
      document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active'));
      loadMembershipsData();
      loadDashboardData();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // 6. Discount Apply Submit
  document.getElementById('discountForm')?.addEventListener('submit', async e => {
    e.preventDefault();
    const clientId = document.getElementById('discountClientId').value;
    const promoId = document.getElementById('discountPromotionSelect').value;

    const payload = {
      promotion_id: promoId || null,
      promotion_name: promoId ? null : document.getElementById('discountName').value,
      discount_type: promoId ? null : document.getElementById('discountType').value,
      discount_value: promoId ? null : parseFloat(document.getElementById('discountValue').value),
      reason: document.getElementById('discountReason').value,
      applied_by: document.getElementById('discountAppliedBy').value,
    };

    try {
      const res = await fetch(`${API_BASE}/clients/${clientId}/discounts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error('Error al aplicar el descuento');

      showToast('Descuento aplicado correctamente', 'success');
      document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active'));
      loadDashboardData();
      if (state.selectedClientForProfile) openClientProfile(clientId);
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // 7. Class Form Submit
  document.getElementById('classForm')?.addEventListener('submit', async e => {
    e.preventDefault();
    const payload = {
      name: document.getElementById('className').value,
      class_type: document.getElementById('classType').value,
      branch: document.getElementById('classBranch').value,
      level: document.getElementById('classLevel').value,
      age_group: document.getElementById('classAgeGroup').value,
      shift_time: document.getElementById('classShiftTime').value || null,
      starts_at: document.getElementById('classStartsAt').value,
      ends_at: document.getElementById('classEndsAt').value || null,
      capacity: parseInt(document.getElementById('classCapacity').value),
      instructor_name: document.getElementById('classInstructor').value || null,
    };

    try {
      const res = await fetch(`${API_BASE}/class-sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error('Error al programar clase');

      showToast('Clase programada exitosamente', 'success');
      document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active'));
      loadClassesData();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // 8. Web Simulator Form Submit (Section 9.2 Auto-Ingestion)
  document.getElementById('publicWebLeadForm')?.addEventListener('submit', async e => {
    e.preventDefault();
    const payload = {
      first_name: document.getElementById('webFirstName').value,
      last_name: document.getElementById('webLastName').value,
      whatsapp: document.getElementById('webWhatsapp').value,
      phone: document.getElementById('webWhatsapp').value,
      email: document.getElementById('webEmail').value || null,
      preferred_branch: document.getElementById('webPreferredBranch').value,
      class_interest: document.getElementById('webClassInterest').value,
      is_minor: document.getElementById('webIsMinor').checked,
      guardian_name: document.getElementById('webGuardianName')?.value || null,
      guardian_phone: document.getElementById('webGuardianPhone')?.value || null,
      message: document.getElementById('webMessage').value || null,
    };

    const resultBox = document.getElementById('webLeadResultBox');
    resultBox.classList.remove('hidden');
    resultBox.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Procesando consulta...';

    try {
      const res = await fetch(`${API_BASE}/public/leads`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error('Error al enviar consulta');
      const leadRes = await res.json();

      resultBox.innerHTML = `
        <strong><i class="fa-solid fa-circle-check text-success"></i> ¡Consulta Enviada con Éxito!</strong><br>
        ${leadRes.message}<br>
        <small class="text-muted">ID de Cliente generado: ${leadRes.client_id} &bull; Sede: ${leadRes.preferred_branch}</small>
      `;

      // Append live log
      const liveFeed = document.getElementById('webLiveLogFeed');
      const placeholder = liveFeed.querySelector('.log-placeholder');
      if (placeholder) placeholder.remove();

      const logItem = document.createElement('div');
      logItem.className = 'log-item';
      logItem.innerHTML = `
        <strong><i class="fa-solid fa-bolt text-warning"></i> Nuevo Lead Ingresado:</strong> ${payload.first_name} ${payload.last_name} (${payload.preferred_branch})<br>
        <span class="text-muted">Canal: Web &bull; Interés: ${payload.class_interest} &bull; WhatsApp: ${payload.whatsapp}</span>
      `;
      liveFeed.prepend(logItem);

      // Refresh CRM data
      loadClientsData();
      loadInteractionsData();
      loadDashboardData();
    } catch (err) {
      resultBox.innerHTML = `<span class="text-danger">${err.message}</span>`;
    }
  });

  // 9. Retire Client Form Submit
  document.getElementById('retireClientForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const clientId = document.getElementById('retireClientId').value;
    const reason = document.getElementById('retireReasonSelect').value;
    const notes = document.getElementById('retireNotes').value;

    if (!reason) {
      showToast('Por favor selecciona el motivo principal de retiro.', 'error');
      return;
    }

    const submitBtn = document.getElementById('btnSubmitRetireClient');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Procesando baja...';

    try {
      const res = await fetch(`${API_BASE}/clients/${clientId}/retire`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reason: reason,
          notes: notes,
          retired_by: state.currentUser.full_name,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Error al procesar el retiro del alumno');
      }

      showToast('Retiro y baja del alumno registrada exitosamente. Membresías canceladas.', 'success');
      document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active'));
      document.getElementById('retireClientForm').reset();
      await loadAllData();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalText;
    }
  });

  // 10. Sync Monthly Cycles Button
  document.getElementById('btnSyncMonthlyCycles')?.addEventListener('click', async () => {
    const period = document.getElementById('membershipMonthFilter')?.value || `${new Date().getFullYear()}-${String(new Date().getMonth() + 1).padStart(2, '0')}`;
    const branch = state.currentBranch;

    showToast('Sincronizando cuotas mensuales del periodo...', 'info');
    try {
      const res = await fetch(`${API_BASE}/memberships/generate-monthly-cycles?period_month=${period}&branch=${branch}`, {
        method: 'POST',
      });
      if (res.ok) {
        const created = await res.json();
        showToast(`Sincronización completa: ${created.length} cuotas generadas para ${period}.`, 'success');
        loadMembershipsData();
        loadDashboardData();
      } else {
        showToast('Error al sincronizar cuotas mensuales.', 'error');
      }
    } catch (err) {
      showToast('Error de conexión al sincronizar cuotas.', 'error');
    }
  });

  // Filters change triggers
  document.getElementById('clientSearchInput')?.addEventListener('input', debounce(loadClientsData, 300));
  document.getElementById('clientStatusFilter')?.addEventListener('change', loadClientsData);
  document.getElementById('clientMinorFilter')?.addEventListener('change', loadClientsData);
  document.getElementById('interactionChannelFilter')?.addEventListener('change', loadInteractionsData);
  document.getElementById('interactionResultFilter')?.addEventListener('change', loadInteractionsData);
  document.getElementById('classTypeFilter')?.addEventListener('change', loadClassesData);
  document.getElementById('membershipMonthFilter')?.addEventListener('change', loadMembershipsData);
  document.getElementById('membershipStatusFilter')?.addEventListener('change', loadMembershipsData);
  document.getElementById('membershipPaymentStatusFilter')?.addEventListener('change', loadMembershipsData);
  document.getElementById('paymentMonthFilter')?.addEventListener('change', loadPaymentsData);
  document.getElementById('paymentMethodFilter')?.addEventListener('change', loadPaymentsData);
  document.getElementById('paymentStatusFilter')?.addEventListener('change', loadPaymentsData);
  document.getElementById('dashboardPeriodMonth')?.addEventListener('change', loadDashboardData);
}

// -------------------------------------------------------------
// Receipts & Actions
// -------------------------------------------------------------
function viewReceipt(paymentId) {
  const payment = state.payments.find(p => p.id === paymentId);
  if (!payment) return;

  const client = state.clients.find(c => c.id === payment.client_id) || { first_name: 'Alumno', last_name: '', dni: '-' };
  const dateFormatted = new Date(payment.payment_date).toLocaleString('es-PE', { dateStyle: 'full', timeStyle: 'short' });

  const receiptBody = document.getElementById('receiptBody');
  receiptBody.innerHTML = `
    <div class="receipt-row"><strong>N° Recibo:</strong> <span>REC-${payment.id.slice(0, 8).toUpperCase()}</span></div>
    <div class="receipt-row"><strong>Fecha:</strong> <span>${dateFormatted}</span></div>
    <div class="receipt-row"><strong>Alumno:</strong> <span>${client.first_name} ${client.last_name}</span></div>
    <div class="receipt-row"><strong>DNI:</strong> <span>${client.dni || '-'}</span></div>
    <div class="receipt-row"><strong>Sede:</strong> <span>${payment.branch}</span></div>
    <div class="receipt-row"><strong>Concepto:</strong> <span>${payment.concept.toUpperCase()} (${payment.period_month})</span></div>
    ${payment.shift_detail ? `<div class="receipt-row"><strong>Turno:</strong> <span>${payment.shift_detail}</span></div>` : ''}
    <div class="receipt-row"><strong>Método de Pago:</strong> <span>${payment.payment_method.toUpperCase()}</span></div>
    ${payment.transaction_reference ? `<div class="receipt-row"><strong>N° Operación:</strong> <span>${payment.transaction_reference}</span></div>` : ''}
    <div class="receipt-row"><strong>Atendido por:</strong> <span>${payment.registered_by}</span></div>
    <div class="receipt-total">
      <span>TOTAL PAGADO</span>
      <span>S/ ${parseFloat(payment.amount).toFixed(2)}</span>
    </div>
  `;

  const wspBtn = document.getElementById('btnShareWspReceipt');
  if (wspBtn) {
    const directPhone = client.whatsapp || client.phone || '';
    const cleanPhone = directPhone.replace(/[^0-9]/g, '');
    const message = `*TALLER DE MARINERA GARBO & SALERO*\n*Comprobante de Pago*\nRecibo: REC-${payment.id.slice(0, 8).toUpperCase()}\nAlumno: ${client.first_name} ${client.last_name}\nConcepto: ${payment.concept.toUpperCase()} (${payment.period_month})\nMonto: S/ ${parseFloat(payment.amount).toFixed(2)}\nMétodo: ${payment.payment_method.toUpperCase()}\nSede: ${payment.branch}\n¡Muchas gracias por su preferencia!`;
    wspBtn.href = `https://wa.me/${cleanPhone.startsWith('51') ? cleanPhone : '51' + cleanPhone}?text=${encodeURIComponent(message)}`;
  }

  openModal('receiptModal');
}

function openCancelPaymentModal(paymentId) {
  if (state.currentUser.role !== 'admin_general') {
    showToast('Solo la Administración General tiene permisos para anular pagos.', 'error');
    return;
  }
  document.getElementById('cancelPaymentId').value = paymentId;
  document.getElementById('cancelAuthorizedBy').value = state.currentUser.full_name;
  openModal('cancelPaymentModal');
}

function openPaymentForMembership(membershipId, clientId) {
  openPaymentModal(clientId, membershipId);
}

function openRetireClientModal(clientId) {
  const client = state.clients.find(c => c.id === clientId);
  if (!client) return;

  document.getElementById('retireClientId').value = client.id;
  document.getElementById('retireClientNameDisplay').textContent = `${client.first_name} ${client.last_name}`;
  document.getElementById('retireReasonSelect').value = '';
  document.getElementById('retireNotes').value = '';
  openModal('modalRetireClient');
}

async function handleReactivateClient(clientId) {
  const client = state.clients.find(c => c.id === clientId);
  const clientName = client ? `${client.first_name} ${client.last_name}` : 'el alumno';

  if (!confirm(`¿Deseas reactivar a ${clientName} como alumno activo e incluirlo en el ciclo mensual actual?`)) {
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/clients/${clientId}/reactivate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        reactivated_by: state.currentUser.full_name,
      }),
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || 'Error al reactivar alumno');
    }

    showToast(`¡${clientName} ha sido reactivado como alumno activo!`, 'success');
    document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active'));
    await loadAllData();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Expose globally for HTML onclick handlers
window.openRetireClientModal = openRetireClientModal;
window.handleReactivateClient = handleReactivateClient;
window.openPaymentForMembership = openPaymentForMembership;
window.openPaymentModal = openPaymentModal;

function updateClientSelectDropdowns() {
  const selects = ['interactionClientId', 'paymentClientId', 'membershipClientId', 'discountClientId'];
  const sortedClients = [...state.clients].sort((a, b) => (a.last_name || '').localeCompare(b.last_name || ''));

  selects.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      const currentVal = el.value;
      el.innerHTML = sortedClients.map(c => `
        <option value="${c.id}" data-branch="${c.preferred_branch || 'Los Olivos'}">${c.last_name}, ${c.first_name} (${c.preferred_branch || 'Sede'}) [${c.status.toUpperCase()}]</option>
      `).join('');
      if (currentVal && sortedClients.some(c => c.id === currentVal)) {
        el.value = currentVal;
      }
    }
  });
}

function updatePromotionSelectDropdowns() {
  const el = document.getElementById('discountPromotionSelect');
  if (el) {
    el.innerHTML = `
      <option value="">-- Descuento Manual / Personalizado --</option>
      ${state.promotions.map(pr => `<option value="${pr.id}">${pr.name} (S/ ${pr.discount_value})</option>`).join('')}
    `;
    el.addEventListener('change', () => {
      document.getElementById('manualDiscountFields').classList.toggle('hidden', !!el.value);
    });
  }
}

function initBranchSelector() {
  const branchSelect = document.getElementById('currentBranchSelect');
  if (branchSelect) {
    branchSelect.addEventListener('change', () => {
      state.currentBranch = branchSelect.value;
      loadAllData();
      showToast(`Sede cambiada a: ${branchSelect.value}`, 'info');
    });
  }
}

function initRoleSwitcher() {
  const roleBtn = document.getElementById('btnRoleSwitch');
  if (roleBtn) {
    roleBtn.addEventListener('click', () => {
      if (state.currentUser.role === 'admin_general') {
        state.currentUser = {
          username: 'admin_sede',
          full_name: 'Administrador de Sede',
          role: 'admin_sede',
          branch: state.currentBranch,
        };
      } else {
        state.currentUser = {
          username: 'admin_general',
          full_name: 'Directora General',
          role: 'admin_general',
          branch: 'Todas',
        };
      }
      document.getElementById('currentUserName').textContent = state.currentUser.full_name;
      document.getElementById('currentUserRole').textContent = state.currentUser.role === 'admin_general' ? 'Admin General' : 'Admin Sede';
      showToast(`Rol cambiado a: ${state.currentUser.full_name}`, 'info');
    });
  }
}

// -------------------------------------------------------------
// Toast Notifications
// -------------------------------------------------------------
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<i class="fa-solid fa-circle-info"></i> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// -------------------------------------------------------------
// Backup & Bulk Import Logic
// -------------------------------------------------------------
function initBackupAndImport() {
  // Top Buttons in Clients view
  const btnExportCsv = document.getElementById('btnExportClientsCsvTop');
  if (btnExportCsv) {
    btnExportCsv.addEventListener('click', () => {
      window.location.href = `${API_BASE}/backup/export-clients-csv`;
      showToast('Descargando lista de clientes en formato Excel (CSV)...', 'info');
    });
  }

  const btnImportCsvTop = document.getElementById('btnImportClientsCsvTop');
  if (btnImportCsvTop) {
    btnImportCsvTop.addEventListener('click', () => {
      // Navigate to backup view and highlight dropzone
      const backupLink = document.querySelector('.nav-link[data-view="backup"]');
      if (backupLink) backupLink.click();
      const dropzone = document.getElementById('csvDropzone');
      if (dropzone) {
        dropzone.scrollIntoView({ behavior: 'smooth' });
        dropzone.classList.add('dragover');
        setTimeout(() => dropzone.classList.remove('dragover'), 1500);
      }
    });
  }

  // CSV Dropzone file change
  const csvFileInput = document.getElementById('csvFileInput');
  const csvDropzoneText = document.getElementById('csvDropzoneText');
  if (csvFileInput && csvDropzoneText) {
    csvFileInput.addEventListener('change', () => {
      if (csvFileInput.files && csvFileInput.files[0]) {
        csvDropzoneText.innerHTML = `<strong>Archivo seleccionado:</strong> ${csvFileInput.files[0].name} (${(csvFileInput.files[0].size / 1024).toFixed(1)} KB)`;
      }
    });
  }

  // JSON Dropzone file change
  const jsonFileInput = document.getElementById('jsonFileInput');
  const jsonDropzoneText = document.getElementById('jsonDropzoneText');
  if (jsonFileInput && jsonDropzoneText) {
    jsonFileInput.addEventListener('change', () => {
      if (jsonFileInput.files && jsonFileInput.files[0]) {
        jsonDropzoneText.innerHTML = `<strong>Archivo seleccionado:</strong> ${jsonFileInput.files[0].name} (${(jsonFileInput.files[0].size / 1024).toFixed(1)} KB)`;
      }
    });
  }

  // Handle CSV Import Form Submit
  const importCsvForm = document.getElementById('importClientsCsvForm');
  const csvResultBox = document.getElementById('importCsvResultBox');
  if (importCsvForm) {
    importCsvForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!csvFileInput.files || !csvFileInput.files[0]) {
        showToast('Por favor selecciona un archivo CSV primero.', 'error');
        return;
      }

      const submitBtn = document.getElementById('btnSubmitImportCsv');
      const originalText = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Importando alumnos...';

      try {
        const formData = new FormData();
        formData.append('file', csvFileInput.files[0]);

        const res = await fetch(`${API_BASE}/backup/import-clients-csv`, {
          method: 'POST',
          body: formData,
        });

        const data = await res.json();
        if (res.ok) {
          showToast(`¡Carga exitosa! ${data.imported_count} alumnos importados.`, 'success');
          if (csvResultBox) {
            csvResultBox.className = 'result-alert-box alert-success';
            csvResultBox.innerHTML = `
              <strong><i class="fa-solid fa-circle-check"></i> Importación Exitosa</strong><br>
              ${data.message}<br>
              <span class="text-xs">Los nuevos clientes ya están visibles en la sección de Alumnos y en el Dashboard.</span>
            `;
            csvResultBox.classList.remove('hidden');
          }
          // Reload all tables and dashboard
          await loadAllData();
          importCsvForm.reset();
          if (csvDropzoneText) csvDropzoneText.textContent = 'Haz clic o arrastra tu archivo .csv aquí';
        } else {
          showToast(data.detail || 'Error al importar archivo CSV.', 'error');
          if (csvResultBox) {
            csvResultBox.className = 'result-alert-box alert-danger';
            csvResultBox.innerHTML = `<strong><i class="fa-solid fa-triangle-exclamation"></i> Error al importar:</strong> ${data.detail || 'Verifique el formato del archivo.'}`;
            csvResultBox.classList.remove('hidden');
          }
        }
      } catch (err) {
        showToast('Error de conexión al importar clientes.', 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
      }
    });
  }

  // Handle Full JSON Backup Import Form Submit
  const importJsonForm = document.getElementById('importFullJsonForm');
  const jsonResultBox = document.getElementById('importJsonResultBox');
  if (importJsonForm) {
    importJsonForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!jsonFileInput.files || !jsonFileInput.files[0]) {
        showToast('Por favor selecciona un archivo JSON de respaldo.', 'error');
        return;
      }

      if (!confirm('¿Deseas restaurar y sincronizar la base de datos con este archivo de respaldo?')) {
        return;
      }

      const submitBtn = document.getElementById('btnSubmitImportJson');
      const originalText = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Restaurando base de datos...';

      try {
        const formData = new FormData();
        formData.append('file', jsonFileInput.files[0]);

        const res = await fetch(`${API_BASE}/backup/import-full`, {
          method: 'POST',
          body: formData,
        });

        const data = await res.json();
        if (res.ok) {
          showToast('¡Base de datos restaurada y sincronizada exitosamente!', 'success');
          if (jsonResultBox) {
            jsonResultBox.className = 'result-alert-box alert-success';
            const counts = data.imported_counts || {};
            const countSummary = Object.entries(counts).map(([k, v]) => `<strong>${k}:</strong> ${v}`).join(' | ');
            jsonResultBox.innerHTML = `
              <strong><i class="fa-solid fa-circle-check"></i> Base de datos sincronizada:</strong><br>
              ${countSummary || 'Registros actualizados.'}
            `;
            jsonResultBox.classList.remove('hidden');
          }
          await loadAllData();
          importJsonForm.reset();
          if (jsonDropzoneText) jsonDropzoneText.textContent = 'Selecciona o arrastra el archivo .json de respaldo';
        } else {
          showToast(data.detail || 'Error al restaurar base de datos.', 'error');
          if (jsonResultBox) {
            jsonResultBox.className = 'result-alert-box alert-danger';
            jsonResultBox.innerHTML = `<strong><i class="fa-solid fa-triangle-exclamation"></i> Error:</strong> ${data.detail || 'Formato JSON inválido.'}`;
            jsonResultBox.classList.remove('hidden');
          }
        }
      } catch (err) {
        showToast('Error de conexión al restaurar base de datos.', 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
      }
    });
  }
}

