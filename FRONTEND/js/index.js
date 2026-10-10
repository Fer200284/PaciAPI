// ==========================================
// CONFIGURACIÓN GLOBAL Y ESTADO
// ==========================================
const API_BASE = 'https://paciapi-c8a0esfgbkcsf7b8.centralus-01.azurewebsites.net';
const API_LOCAL = `${API_BASE}/api`;
const LOGIN_URL =
    window.location.protocol === 'file:' || window.location.port === '8000'
        ? 'http://127.0.0.1:8000/login/'
        : `${window.location.origin}/login.html`;

let editandoId = {
    pacientes: null,
    examenesLaboratorio: null,
    medicos: null,
    citasmedicas: null,
    solicitudExamen: null,
    medicamentos: null,
    resultadosExamenes: null,
    usuarios: null,
    tratamientos: null,
    detalleTratamiento: null,
    categoriaMedicamento: null,
    sector: null,
    especialidad: null,
    patologiaCronica: null,
    pacientePatologia: null
};

let relacionesAtencionPorPaciente = {};
const INACTIVITY_TIMEOUT_MS = 2 * 60 * 1000;
const API_STATUS_TIMEOUT_MS = 5000;
let inactivityTimer = null;
let ultimoEstadoApi = null;

function setEstadoApi(online) {
    const estadoApi = document.getElementById('estadoApi');
    if (!estadoApi) return;

    const estadoDeseado = online ? '🟢 Conectado' : '🔴 Desconectado';
    if (ultimoEstadoApi === estadoDeseado) return;

    ultimoEstadoApi = estadoDeseado;
    estadoApi.innerHTML = estadoDeseado;
    estadoApi.style.color = online ? 'green' : 'red';
}

async function verificarEstadoApi() {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_STATUS_TIMEOUT_MS);

    try {
        const respuesta = await fetch(`${API_LOCAL}/pacientes/`, {
            method: 'GET',
            headers: getAuthHeaders(),
            cache: 'no-store',
            signal: controller.signal
        });

        if (!respuesta.ok) {
            throw new Error(`API respondió ${respuesta.status}`);
        }

        setEstadoApi(true);
    } catch (error) {
        console.error('API desconectada:', error);
        setEstadoApi(false);
    } finally {
        clearTimeout(timeoutId);
    }
}

// ==========================================
// INICIALIZACIÓN AL CARGAR LA PÁGINA
// ==========================================
document.addEventListener('DOMContentLoaded', async () => {
    const estadoApi = document.getElementById('estadoApi');
    if (estadoApi) {
        ultimoEstadoApi = '🟡 Verificando...';
        estadoApi.innerHTML = ultimoEstadoApi;
        estadoApi.style.color = '#d97706';
    }

    if (!await verificarSesion()) return;
    verificarEstadoApi();
    setInterval(verificarEstadoApi, 5000);
    bloquearNavegacionAtras();
    iniciarTemporizadorInactividad();
    configurarNavegacionSidebar();
    configurarBuscadores();
    marcarCamposObligatorios();
    configurarFormatoCedula();
    configurarBotonSalir();
    cargarDashboard();
    cargarDatosSeccionActiva();
});

function bloquearNavegacionAtras() {
    if (!window.history || !window.history.pushState) return;

    const restaurarEstado = () => {
        if (localStorage.getItem('accessToken')) {
            history.pushState(null, '', location.href);
        }
    };

    history.pushState(null, '', location.href);
    window.addEventListener('popstate', restaurarEstado);
}

function iniciarTemporizadorInactividad() {
    const resetTimer = () => {
        if (inactivityTimer) {
            clearTimeout(inactivityTimer);
        }

        inactivityTimer = setTimeout(() => {
            const tieneToken = !!localStorage.getItem('accessToken');
            if (!tieneToken) return;

            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            alert('La sesión se cerró por inactividad. Serás redirigido al login.');
            window.location.replace(LOGIN_URL);
        }, INACTIVITY_TIMEOUT_MS);
    };

    const eventosActividad = ['mousemove', 'keydown', 'click', 'scroll', 'touchstart', 'input'];
    eventosActividad.forEach(evento => {
        document.addEventListener(evento, resetTimer, { passive: true });
    });

    resetTimer();
}

function configurarBotonSalir() {
    const btnSalir = document.getElementById('btnSalir');
    if (!btnSalir) return;

    btnSalir.addEventListener('click', () => {
        const confirmarSalida = confirm('¿Seguro que deseas salir del dashboard?');
        if (!confirmarSalida) return;

        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        window.location.replace(LOGIN_URL);
    });
}

// ==========================================
// NAVEGACIÓN ENTRE SECCIONES (SIDEBAR)
// ==========================================
function configurarNavegacionSidebar() {
    const navLinks = document.querySelectorAll('.nav-link');
    const secciones = document.querySelectorAll('.seccion');
    const topbarTitulo = document.getElementById('topbarTitulo');
    const pacientesLink = document.querySelector('.nav-link-pacientes');
    const submenuPacientes = document.getElementById('submenuPacientes');

    if (pacientesLink && submenuPacientes) {
        pacientesLink.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopImmediatePropagation();
            const abierto = pacientesLink.getAttribute('aria-expanded') === 'true';
            pacientesLink.setAttribute('aria-expanded', String(!abierto));
            submenuPacientes.hidden = abierto;
            activarSeccion('pacientes', 'Pacientes', pacientesLink);
        });

        submenuPacientes.querySelectorAll('button').forEach(button => {
            button.addEventListener('click', () => {
                const destino = document.getElementById(button.dataset.seccion);
                navLinks.forEach(link => link.classList.remove('activo'));
                secciones.forEach(section => section.classList.remove('activa'));
                pacientesLink.classList.add('activo');
                if (destino) {
                    destino.classList.add('activa');
                    topbarTitulo.textContent = button.textContent;
                    cargarDatosSeccion(destino.id);
                }
            });
        });
    }

    document.querySelectorAll('.nav-link:not(.nav-link-pacientes)').forEach(link => {
        const submenu = link.nextElementSibling;
        if (!submenu || !submenu.classList.contains('submenu-pacientes')) return;

        link.setAttribute('aria-expanded', 'false');
        link.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopImmediatePropagation();
            const abierto = link.getAttribute('aria-expanded') === 'true';
            link.setAttribute('aria-expanded', String(!abierto));
            submenu.hidden = abierto;
            activarSeccion(link.dataset.seccion, 
                link.querySelector('span:nth-child(2)').textContent, link);
        });

        submenu.querySelectorAll('button').forEach(button => {
            button.addEventListener('click', () => {
                if (button.dataset.accion === 'nuevo') {
                    abrirModalPorSeccion(button.dataset.seccion);
                    return;
                }
                const destino = document.getElementById(button.dataset.seccion) ||
                 document.getElementById(link.dataset.seccion);
                navLinks.forEach(item => item.classList.remove('activo'));
                secciones.forEach(section => section.classList.remove('activa'));
                link.classList.add('activo');
                if (destino) {
                    destino.classList.add('activa');
                    topbarTitulo.textContent = button.textContent;
                    cargarDatosSeccion(destino.id);
                }
            });
        });
    });

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();

            navLinks.forEach(l => l.classList.remove('activo'));
            secciones.forEach(s => s.classList.remove('activa'));

            link.classList.add('activo');
            const seccionId = link.getAttribute('data-seccion');
            const seccionActual = document.getElementById(seccionId);

            if (seccionActual) {
                seccionActual.classList.add('activa');
                topbarTitulo.textContent = link.querySelector('span:nth-child(2)').textContent;
                cargarDatosSeccion(seccionId);
            }
        });
    });
}

function activarSeccion(seccionId, titulo, linkActivo) {
    const secciones = document.querySelectorAll('.seccion');
    const navLinks = document.querySelectorAll('.nav-link');
    const topbarTitulo = document.getElementById('topbarTitulo');
    const seccion = document.getElementById(seccionId);
    if (!seccion) return;

    navLinks.forEach(link => link.classList.remove('activo'));
    secciones.forEach(section => section.classList.remove('activa'));
    linkActivo.classList.add('activo');
    seccion.classList.add('activa');
    topbarTitulo.textContent = titulo;
    cargarDatosSeccion(seccionId);
}

function abrirModalPorSeccion(seccionId) {
    const acciones = {
        pacientes: () => abrirModalPacientes('crear'),
        sector: abrirModalSector,
        patologiasCronicas: abrirModalPatologiaCronica,
        pacientePatologia: abrirModalPacientePatologia,
        medicos: () => abrirModalMedicos('crear'),
        especialidades: abrirModalEspecialidad,
        citasmedicas: () => abrirModalCitasMedicas('crear'),
        tratamientos: abrirModalTratamiento,
        detalleTratamiento: abrirModalDetalleTratamiento,
        medicamentos: () => abrirModalMedicamentos('crear'),
        categoriasMedicamentos: abrirModalCategoriaMedicamento,
        resultadosExamenes: () => abrirModalResultadosExamenes('crear'),
        examenesLaboratorio: abrirModalExamenLaboratorio,
        solicitudesExamenes: abrirModalSolicitudExamen,
        usuarios: () => abrirModalUsuarios('crear')
    };
    if (acciones[seccionId]) acciones[seccionId]();
}

function cargarDatosSeccionActiva() {
    const seccionActiva = document.querySelector('.seccion.activa');
    if (seccionActiva) {
        cargarDatosSeccion(seccionActiva.id);
    }
}

function cargarDatosSeccion(seccionId) {
    switch (seccionId) {
        case 'dashboard':
            cargarDashboard();
            break;
        case 'pacientes':
            cargarPacientes();
            break;
        case 'sector':
            cargarSectores();
            break;
        case 'patologiasCronicas':
            cargarPatologiasCronicas();
            break;
        case 'pacientePatologia':
            cargarPacientesPatologias();
            break;
        case 'medicos':
            cargarMedicos();
            break;
        case 'especialidades':
            cargarEspecialidades();
            break;
        case 'citasmedicas':
            cargarCitasMedicas();
            break;
        case 'tratamientos':
            cargarTratamientos();
            break;
        case 'detalleTratamiento':
            cargarDetalleTratamiento();
            break;
        case 'medicamentos':
            cargarMedicamentos();
            break;
        case 'categoriasMedicamentos':
            cargarCategoriasMedicamentos();
            break;
        case 'resultadosExamenes':
            cargarResultadosExamenes();
            break;
        case 'examenesLaboratorio':
            cargarExamenesLaboratorio();
            break;
        case 'solicitudesExamenes':
            cargarSolicitudesExamenes();
            break;
        case 'usuarios':
            cargarUsuarios();
            break;
    }
}

function abrirModal(modalId) {
    limpiarErroresModales();
    document.querySelectorAll('.modal-overlay.activo').forEach(modal => {
        modal.classList.remove('activo');
    });
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('activo');
        document.body.classList.add('formulario-bloqueado');
    }
}

function cerrarModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove('activo');
    if (!document.querySelector('.modal-overlay.activo')) {
        document.body.classList.remove('formulario-bloqueado');
    }
    limpiarErroresModales();
}

function limpiarErroresModales() {
    const spansError = document.querySelectorAll('.modal-footer span');
    spansError.forEach(span => span.textContent = '');
}

function marcarCamposObligatorios() {
    document.querySelectorAll('.modal .form-input[required]').forEach(campo => {
        if (campo.closest('.form-field')) return;

        if (campo.tagName === 'SELECT') {
            const primeraOpcion = campo.options[0];
            if (primeraOpcion && !primeraOpcion.textContent.trim().startsWith('*')) {
                primeraOpcion.textContent = `* ${primeraOpcion.textContent.trim()}`;
            }
            return;
        }

        if (campo.placeholder && !campo.placeholder.startsWith('*')) {
            campo.placeholder = `* ${campo.placeholder}`;
        }
    });
}

function getAuthHeaders(extra = {}) {
    const token = localStorage.getItem('accessToken');
    return {
        ...extra,
        ...(token ? { Authorization: `Bearer ${token}` } : {})
    };
}

function safeArray(payload) {
    if (Array.isArray(payload)) return payload;
    if (payload && Array.isArray(payload.results)) return payload.results;
    return [];
}

async function fetchJsonOrThrow(url, options = {}) {
    const response = await fetch(url, options);
    if (!response.ok) {
        throw new Error(`API respondió ${response.status} en ${url}`);
    }
    return response.json();
}

function textValue(obj, ...keys) {
    for (const key of keys) {
        if (obj && obj[key] !== null && obj[key] !== undefined && obj[key] !== '') {
            return obj[key];
        }
    }
    return '';
}

function formatDate(value) {
    if (!value) return '';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toISOString().slice(0, 10);
}

function formatDateTime(value) {
    if (!value) return '';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    const partes = new Intl.DateTimeFormat('en-CA', {
        timeZone: 'America/Managua',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hourCycle: 'h23'
    }).formatToParts(date).reduce((resultado, parte) => {
        resultado[parte.type] = parte.value;
        return resultado;
    }, {});
    return `${partes.year}-${partes.month}-${partes.day} ${partes.hour}:${partes.minute}`;
}

function calcularEdad(fechaNacimiento) {
    if (!fechaNacimiento) return '-';
    const nacimiento = new Date(`${fechaNacimiento}T00:00:00`);
    if (Number.isNaN(nacimiento.getTime())) return '-';
    const hoy = new Date();
    let edad = hoy.getFullYear() - nacimiento.getFullYear();
    const aniversarioPendiente = hoy.getMonth() < nacimiento.getMonth()
        || (hoy.getMonth() === nacimiento.getMonth() && hoy.getDate() < nacimiento.getDate());
    if (aniversarioPendiente) edad -= 1;
    return edad >= 0 ? edad : '-';
}

function isTrue(value) {
    return value === true || value === 'true' || value === 1 || value === '1';
}

function formatEstado(value) {
    return isTrue(value) ? '🟢 Activo' : '🔴 Inactivo';
}

// ==========================================
// 1. DASHBOARD & CONEXIÓN API
// ==========================================
async function cargarDashboard() {
    try {
        const estadoApi = document.getElementById('estadoApi');

        const [pacientes, medicos, atenciones, examenes, medicamentos] = await Promise.all([
            fetchJsonOrThrow(`${API_LOCAL}/pacientes/`, { headers: getAuthHeaders() }),
            fetchJsonOrThrow(`${API_LOCAL}/medicos/`, { headers: getAuthHeaders() }),
            fetchJsonOrThrow(`${API_LOCAL}/atencion-cronico/`, { headers: getAuthHeaders() }),
            fetchJsonOrThrow(`${API_LOCAL}/resultados-examenes/`, { headers: getAuthHeaders() }),
            fetchJsonOrThrow(`${API_LOCAL}/medicamentos/`, { headers: getAuthHeaders() })
        ]);

        const pacientesCount = safeArray(pacientes).length;
        const medicosCount = safeArray(medicos).length;
        const atencionesCount = safeArray(atenciones).length;
        const examenesCount = safeArray(examenes).length;
        const medicamentosCount = safeArray(medicamentos).length;

        const totalPacientes = document.getElementById('totalPacientes');
        const totalMedicos = document.getElementById('totalMedicos');
        const totalCitasMedicas = document.getElementById('totalCitasMedicas');
        const totalResultadosExamenes = document.getElementById('totalResultadosExamenes');
        const totalMedicamentos = document.getElementById('totalMedicamentos');

        if (totalPacientes) totalPacientes.textContent = pacientesCount;
        if (totalMedicos) totalMedicos.textContent = medicosCount;
        if (totalCitasMedicas) totalCitasMedicas.textContent = atencionesCount;
        if (totalResultadosExamenes) totalResultadosExamenes.textContent = examenesCount;
        if (totalMedicamentos) totalMedicamentos.textContent = medicamentosCount;

        setEstadoApi(true);
    } catch (error) {
        console.error('Error al conectar con la API en el dashboard:', error);
        setEstadoApi(false);
    }
}

// ==========================================
// 2. GESTIÓN DE PACIENTES
// ==========================================
async function cargarEspecialidades() {
    await cargarCatalogoSimple('especialidades', 'Especialidades', 'bodyEspecialidades', 'cargandoEspecialidades', (item, index) => `
        <td>${index + 1}</td>
        <td>${item.nombre_especialidad || ''}</td>
        <td>${formatEstado(item.estado)}</td>
        <td>${formatDateTime(item.fecha_creacion)}</td>
        <td><button class="btn btn-sm btn-secundario" 
        onclick="editarEspecialidad(${item.id})">✏️ 
        Editar</button><button 
        class="btn btn-sm btn-peligro"
        onclick="eliminarEspecialidad(${item.id})">
        🗑️ Eliminar</button></td>
    `);
}

function abrirModalEspecialidad(id = null) {
    editandoId.especialidad = id;
    document.getElementById('nombreEspecialidad').value = '';
    document.getElementById('estadoEspecialidad').value = 'true';
    abrirModal('modalEspecialidad');
}

async function guardarEspecialidad() {
    const error = document.getElementById('especialidadError');
    const data = {
        nombre_especialidad: document.getElementById('nombreEspecialidad').value.trim(),
        estado: document.getElementById('estadoEspecialidad').value === 'true'
    };
    if (!data.nombre_especialidad) {
        error.textContent = 'Escriba el nombre de la especialidad.';
        return;
    }
    try {
        const id = editandoId.especialidad;
        const respuesta = await fetch(`${API_LOCAL}/especialidades/${id ? `${id}/` : ''}`, {
            method: id ? 'PUT' : 'POST',
            headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
            body: JSON.stringify(data)
        });
        if (!respuesta.ok) throw new Error(await respuesta.text());
        cerrarModal('modalEspecialidad');
        cargarEspecialidades();
    } catch (e) {
        error.textContent = 'No se pudo guardar la especialidad.';
        console.error(e);
    }
}

async function editarEspecialidad(id) {
    const respuesta = await fetch(`${API_LOCAL}/especialidades/${id}/`, { headers: getAuthHeaders() });
    const item = await respuesta.json();
    abrirModalEspecialidad(id);
    document.getElementById('nombreEspecialidad').value = item.nombre_especialidad || '';
    document.getElementById('estadoEspecialidad').value = String(item.estado);
}

async function eliminarEspecialidad(id) {
    if (!confirm('¿Desea eliminar esta especialidad?')) return;
    const respuesta = await fetch(`${API_LOCAL}/especialidades/${id}/`, { method: 'DELETE', headers: getAuthHeaders() });
    if (respuesta.ok) cargarEspecialidades();
}

function abrirModalSector(id = null) {
    editandoId.sector = id;
    document.getElementById('nombreSector').value = '';
    document.getElementById('numeroSector').value = '';
    document.getElementById('zonaSector').value = '';
    document.getElementById('estadoSector').value = 'true';
    abrirModal('modalSector');
}

async function guardarSector() {
    const error = document.getElementById('sectorError');
    const data = {
        nombre_sector: document.getElementById('nombreSector').value.trim(),
        numero_sector: Number(document.getElementById('numeroSector').value),
        zona_procedencia: document.getElementById('zonaSector').value,
        estado: document.getElementById('estadoSector').value === 'true'
    };
    if (!data.nombre_sector || !data.numero_sector || !data.zona_procedencia) {
        error.textContent = 'Complete todos los campos del sector.';
        return;
    }
    try {
        const id = editandoId.sector;
        const respuesta = await fetch(`${API_LOCAL}/sector/${id ? `${id}/` : ''}`, {
            method: id ? 'PUT' : 'POST',
            headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
            body: JSON.stringify(data)
        });
        if (!respuesta.ok) throw new Error(await respuesta.text());
        cerrarModal('modalSector');
        cargarSectores();
    } catch (e) {
        error.textContent = 'No se pudo guardar el sector.';
        console.error(e);
    }
}

async function editarSector(id) {
    const respuesta = await fetch(`${API_LOCAL}/sector/${id}/`, { headers: getAuthHeaders() });
    const item = await respuesta.json();
    abrirModalSector(id);
    document.getElementById('nombreSector').value = item.nombre_sector || '';
    document.getElementById('numeroSector').value = item.numero_sector || '';
    document.getElementById('zonaSector').value = item.zona_procedencia || '';
    document.getElementById('estadoSector').value = String(item.estado);
}

async function eliminarSector(id) {
    if (!confirm('¿Desea eliminar este sector?')) return;
    const respuesta = await fetch(`${API_LOCAL}/sector/${id}/`, 
    { method: 'DELETE', headers: getAuthHeaders() });
    if (respuesta.ok) cargarSectores();
}

function abrirModalPatologiaCronica(id = null) {
    editandoId.patologiaCronica = id;
    document.getElementById('nombrePatologiaCronica').value = '';
    document.getElementById('estadoPatologiaCronica').value = 'true';
    abrirModal('modalPatologiaCronica');
}

async function guardarPatologiaCronica() {
    const error = document.getElementById('patologiaCronicaError');
    const data = {
        nombre_patologia: document.getElementById('nombrePatologiaCronica').value.trim(),
        estado: document.getElementById('estadoPatologiaCronica').value === 'true'
    };
    if (!data.nombre_patologia) {
        error.textContent = 'Escriba el nombre de la patología.';
        return;
    }
    try {
        const id = editandoId.patologiaCronica;
        const respuesta = await fetch(`${API_LOCAL}/patologias-cronicas/${id ? `${id}/` : ''}`, {
            method: id ? 'PUT' : 'POST',
            headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
            body: JSON.stringify(data)
        });
        if (!respuesta.ok) throw new Error(await respuesta.text());
        cerrarModal('modalPatologiaCronica');
        cargarPatologiasCronicas();
    } catch (e) {
        error.textContent = 'No se pudo guardar la patología.';
        console.error(e);
    }
}

async function abrirModalPacientePatologia(id = null) {
    editandoId.pacientePatologia = id;
    document.getElementById('pacienteRelacion').value = '';
    document.getElementById('patologiaRelacion').value = '';
    document.getElementById('fechaDiagnosticoRelacion').value = '';
    document.getElementById('estadoRelacion').value = 'true';
    document.getElementById('observacionesRelacion').value = '';
    await llenarSelectRelacionesPacientePatologia();
    if (id) {
        const respuesta = await fetch(`${API_LOCAL}/paciente-patologia/${id}/`, 
        { headers: getAuthHeaders() });
        const item = await respuesta.json();
        document.getElementById('pacienteRelacion').value = item.id_paciente;
        document.getElementById('patologiaRelacion').value = item.id_patologia_cronica;
        document.getElementById('fechaDiagnosticoRelacion').value = item.fecha_de_diagnostico || '';
        document.getElementById('estadoRelacion').value = String(item.estado);
        document.getElementById('observacionesRelacion').value = item.observaciones || '';
    }
    abrirModal('modalPacientePatologia');
}

async function llenarSelectRelacionesPacientePatologia() {
    const [pacientesRespuesta, patologiasRespuesta] = await Promise.all([
        fetch(`${API_LOCAL}/pacientes/`, { headers: getAuthHeaders() }),
        fetch(`${API_LOCAL}/patologias-cronicas/`, { headers: getAuthHeaders() })
    ]);
    const pacientes = safeArray(await pacientesRespuesta.json());
    const patologias = safeArray(await patologiasRespuesta.json());
    const pacienteSelect = document.getElementById('pacienteRelacion');
    const patologiaSelect = document.getElementById('patologiaRelacion');
    pacienteSelect.innerHTML = '<option value="">-- Seleccione paciente --</option>';
    patologiaSelect.innerHTML = '<option value="">-- Seleccione patología --</option>';
    pacientes.forEach(paciente => {
        pacienteSelect.innerHTML += `<option value="${paciente.id}">${paciente.nombre} ${paciente.apellidos}</option>`;
    });
    patologias.forEach(patologia => {
        patologiaSelect.innerHTML += `<option value="${patologia.id}">${patologia.nombre_patologia}</option>`;
    });
}

async function guardarPacientePatologia() {
    const error = document.getElementById('pacientePatologiaError');
    const paciente = Number(document.getElementById('pacienteRelacion').value);
    const patologias = [Number(document.getElementById('patologiaRelacion').value)].filter(Boolean);
    const fechaDiagnostico = document.getElementById('fechaDiagnosticoRelacion').value;
    const estado = document.getElementById('estadoRelacion').value === 'true';
    const observaciones = document.getElementById('observacionesRelacion').value.trim();

    if (!paciente || !patologias.length || !fechaDiagnostico) {
        error.textContent = 'Seleccione paciente, una o más patologías y fecha de diagnóstico.';
        return;
    }
    try {
        const id = editandoId.pacientePatologia;
        const datosBase = {
            id_paciente: paciente,
            fecha_de_diagnostico: fechaDiagnostico,
            estado,
            observaciones
        };

        if (id) {
            const respuesta = await fetch(`${API_LOCAL}/paciente-patologia/${id}/`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
                body: JSON.stringify({ ...datosBase, id_patologia_cronica: patologias[0] })
            });
            if (!respuesta.ok) throw new Error(await respuesta.text());
        } else {
            for (const patologia of patologias) {
                const respuesta = await fetch(`${API_LOCAL}/paciente-patologia/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
                    body: JSON.stringify({ ...datosBase, id_patologia_cronica: patologia })
                });
                if (!respuesta.ok) throw new Error(await respuesta.text());
            }
        }
        cerrarModal('modalPacientePatologia');
        cargarPacientesPatologias();
    } catch (e) {
        error.textContent = 'No se pudo guardar la relación. Puede que ya exista.';
        console.error(e);
    }
}

async function cargarSectores() {
    await cargarCatalogoSimple('sector', 'Sectores', 'bodySectores', 'cargandoSectores', (item, index) => `
        <td>${index + 1}</td>
        <td>${item.nombre_sector || ''}</td>
        <td>${item.numero_sector || ''}</td>
        <td>${item.zona_procedencia || ''}</td>
        <td>${formatEstado(item.estado)}</td>
        <td>${formatDateTime(item.fecha_creacion)}</td>
        <td><button class="btn btn-sm btn-secundario" 
        onclick="editarSector(${item.id})">✏️ Editar</button><button 
        class="btn btn-sm btn-peligro"
        onclick="eliminarSector(${item.id})">
        🗑️ Eliminar</button></td>
    `);
}

async function cargarPatologiasCronicas() {
    await cargarCatalogoSimple('patologias-cronicas', 'Patologías crónicas', 'bodyPatologiasCronicas', 'cargandoPatologiasCronicas', (item, index) => `
        <td>${index + 1}</td>
        <td>${item.nombre_patologia || ''}</td>
        <td>${formatEstado(item.estado)}</td>
        <td>${formatDateTime(item.fecha_creacion)}</td>
        <td>
            <button class="btn btn-sm btn-detalles" onclick="mostrarDetallesFila(document.getElementById('tablaPatologiasCronicas'), this.closest('tr'))">👁 Ver detalles</button>
            <button class="btn btn-sm btn-secundario" onclick="editarPatologiaCronica(${item.id})">✏️ Editar</button>
            <button class="btn btn-sm btn-peligro" onclick="eliminarPatologiaCronica(${item.id})">🗑️ Eliminar</button>
        </td>
    `);
}

async function cargarPacientesPatologias() {
    const cargando = document.getElementById('cargandoPacientesPatologias');
    const tbody = document.getElementById('bodyPacientesPatologias');
    if (cargando) cargando.style.display = 'block';
    if (tbody) tbody.innerHTML = '';

    try {
        const [relacionesRespuesta, pacientesRespuesta, patologiasRespuesta] = await Promise.all([
            fetch(`${API_LOCAL}/paciente-patologia/`, { headers: getAuthHeaders() }),
            fetch(`${API_LOCAL}/pacientes/`, { headers: getAuthHeaders() }),
            fetch(`${API_LOCAL}/patologias-cronicas/`, { headers: getAuthHeaders() })
        ]);
        const relaciones = safeArray(await relacionesRespuesta.json());
        const pacientes = Object.fromEntries(safeArray(await pacientesRespuesta.json()).map(item => [item.id, item]));
        const patologias = Object.fromEntries(safeArray(await patologiasRespuesta.json()).map(item => [item.id, item]));

        if (cargando) cargando.style.display = 'none';
        relaciones.forEach((item, index) => {
            const paciente = pacientes[item.id_paciente] || {};
            const patologia = patologias[item.id_patologia_cronica] || {};
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${index + 1}</td>
                <td>${textValue(paciente, 'nombre')} ${textValue(paciente, 'apellidos')}</td>
                <td>${patologia.nombre_patologia || ''}</td>
                <td>${formatDate(item.fecha_de_diagnostico)}</td>
                <td>${formatEstado(item.estado)}</td>
                <td>${item.observaciones || ''}</td>
                <td>
                    <button class="btn btn-sm btn-detalles" onclick="mostrarDetallesFila(document.getElementById('tablaPacientesPatologias'), this.closest('tr'))">👁 Ver detalles</button>
                    <button class="btn btn-sm btn-secundario" onclick="editarPacientePatologia(${item.id})">✏️ Editar</button>
                    <button class="btn btn-sm btn-peligro" onclick="eliminarPacientePatologia(${item.id})">🗑️ Eliminar</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        if (cargando) cargando.textContent = '❌ Error al cargar pacientes con patologías.';
        console.error(error);
    }
}

async function cargarCatalogoSimple(endpoint, nombre, tbodyId, cargandoId, renderRow) {
    const cargando = document.getElementById(cargandoId);
    const tbody = document.getElementById(tbodyId);
    if (cargando) cargando.style.display = 'block';
    if (tbody) tbody.innerHTML = '';

    try {
        const respuesta = await fetch(`${API_LOCAL}/${endpoint}/`, { headers: getAuthHeaders() });
        const items = safeArray(await respuesta.json());
        if (cargando) cargando.style.display = 'none';
        items.forEach((item, index) => {
            const tr = document.createElement('tr');
            tr.innerHTML = renderRow(item, index);
            tbody.appendChild(tr);
        });
    } catch (error) {
        if (cargando) cargando.textContent = `❌ Error al cargar ${nombre.toLowerCase()}.`;
        console.error(error);
    }
}

async function cargarPacientes() {
    const cargando = document.getElementById('cargandoPacientes');
    const tbody = document.getElementById('bodyPacientes');
    if (cargando) cargando.style.display = 'block';
    if (tbody) tbody.innerHTML = '';

    try {
        const [respuesta, sectoresRespuesta, relacionesRespuesta, patologiasRespuesta] = await Promise.all([
            fetch(`${API_LOCAL}/pacientes/`, { headers: getAuthHeaders() }),
            fetch(`${API_LOCAL}/sector/`, { headers: getAuthHeaders() }),
            fetch(`${API_LOCAL}/paciente-patologia/`, { headers: getAuthHeaders() }),
            fetch(`${API_LOCAL}/patologias-cronicas/`, { headers: getAuthHeaders() })
        ]);
        const pacientes = safeArray(await respuesta.json());
        const sectores = safeArray(await sectoresRespuesta.json());
        const relaciones = safeArray(await relacionesRespuesta.json());
        const patologias = safeArray(await patologiasRespuesta.json());
        const sectoresPorId = Object.fromEntries(sectores.map(sector => [sector.id, sector]));
        const patologiasPorId = Object.fromEntries(patologias.map(patologia => [patologia.id, patologia]));
        const patologiasPorPaciente = relaciones.reduce((resultado, relacion) => {
            const pacienteId = relacion.id_paciente;
            const patologia = patologiasPorId[relacion.id_patologia_cronica];
            if (patologia) {
                resultado[pacienteId] = resultado[pacienteId] || [];
                resultado[pacienteId].push(patologia.nombre_patologia);
            }
            return resultado;
        }, {});

        if (cargando) cargando.style.display = 'none';

        pacientes.forEach((p, index) => {
            const tr = document.createElement('tr');
            tr.dataset.fechaCreacion = textValue(p, 'fecha_creacion', 'fecha_ingreso') || '';
            tr.innerHTML = `
                <td>${index + 1}</td>
                <td>${textValue(p, 'nombre', 'nombres') || ''}</td>
                <td>${textValue(p, 'apellidos') || ''}</td>
                <td>${textValue(p, 'cedula') || ''}</td>
                <td>${textValue(p, 'sexo') || ''}</td>
                <td>${formatDate(textValue(p, 'fecha_de_nacimiento', 'fecha_nacimiento'))}</td>
                <td>${calcularEdad(textValue(p, 'fecha_de_nacimiento', 'fecha_nacimiento'))}</td>
                <td>${sectoresPorId[p.id_sector]?.nombre_sector || 'Sin sector'}</td>
                <td>${patologiasPorPaciente[p.id]?.join(', ') || 'Ninguna'}</td>
                <td>${textValue(p, 'direccion') || ''}</td>
                <td>${textValue(p, 'celular', 'telefono') || ''}</td>
                <td>${textValue(p, 'barrio') || ''}</td>
                <td><strong>${formatEstado(textValue(p, 'estado', 'activo'))}</strong></td>
                <td>${formatDateTime(textValue(p, 'fecha_creacion', 'fecha_ingreso'))}</td>
                <td>
                    <button class="btn btn-sm btn-secundario" 
                    onclick="editarPaciente(${p.id})">✏️ Editar</button>
                    <button class="btn btn-sm btn-peligro" 
                    onclick="eliminarPaciente(${p.id}, '${textValue(p, 'nombre', 'nombres')}')">
                    🗑️ Eliminar</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        if (cargando) cargando.textContent = '❌ Error al cargar los pacientes.';
        console.error(error);
    }
}

function abrirModalPacientes(modo, id = null) {
    limpiarErroresModales();
    editandoId.pacientes = id;
    if (modo === 'crear' || modo === 'editar') {
        editandoId.pacientes = id;
        document.getElementById('modalPacTitulo').textContent = 'Nuevo Paciente';
        document.getElementById('nomPaciente').value = '';
        document.getElementById('apePaciente').value = '';
        document.getElementById('cedulaPaciente').value = '';
        document.getElementById('sexoPaciente').value = '';
        document.getElementById('fechaNacimiento').value = '';
        document.getElementById('direccionPaciente').value = '';
        document.getElementById('barrioPaciente').value = '';
        document.getElementById('telefonoPaciente').value = '';
        document.getElementById('sectorPaciente').value = '';
        document.querySelectorAll('#patologiaPaciente input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = false;
        });
        document.getElementById('buscarPatologiasPaciente').value = '';
        actualizarResumenPatologiasPaciente();
        document.getElementById('fechaDiagnostico').value = '';
        document.getElementById('observacionPatologia').value = '';
        document.getElementById('activoPaciente').value = 'true';
    }
    llenarSelectCatalogosPaciente();
    abrirModal('modalPacientes');
}

function formatearCedula(cedula) {
    const valor = String(cedula || '').replace(/[^0-9a-z]/gi, '').toUpperCase();
    const numeros = valor.replace(/[A-Z]/g, '').slice(0, 13);
    const letra = (valor.match(/[A-Z]/) || [''])[0];
    let formateada = numeros.slice(0, 3);
    if (numeros.length > 3) formateada += `-${numeros.slice(3, 9)}`;
    if (numeros.length > 9) formateada += `-${numeros.slice(9, 13)}`;
    return formateada + (numeros.length === 13 ? letra : '');
}

function configurarFormatoCedula() {
    const campo = document.getElementById('cedulaPaciente');
    if (!campo) return;
    campo.addEventListener('input', () => {
        campo.value = formatearCedula(campo.value);
    });
}

function alternarPatologiasPaciente() {
    const opciones = document.getElementById('patologiaPaciente');
    const boton = document.getElementById('patologiasPacienteBoton');
    const abierto = !opciones.hidden;
    opciones.hidden = abierto;
    boton.setAttribute('aria-expanded', String(!abierto));
}

function actualizarResumenPatologiasPaciente() {
    const resumen = document.getElementById('patologiasPacienteResumen');
    if (!resumen) return;
    const seleccionadas = document.querySelectorAll('#patologiaPaciente input[type="checkbox"]:checked').length;
    resumen.textContent = seleccionadas
        ? `${seleccionadas} patología${seleccionadas === 1 ? '' : 's'} seleccionada${seleccionadas === 1 ? '' : 's'}`
        : 'Seleccionar patologías';
}

function filtrarPatologiasPaciente() {
    const termino = document.getElementById('buscarPatologiasPaciente').value.trim().toLocaleLowerCase();
    document.querySelectorAll('#listaPatologiasPaciente .patologia-opcion').forEach(opcion => {
        const nombre = opcion.textContent.trim().toLocaleLowerCase();
        opcion.style.display = nombre.includes(termino) ? 'flex' : 'none';
    });
}

async function guardarPacientes() {
    const errorEl = document.getElementById('pacienteError');
    const data = {
        nombre: document.getElementById('nomPaciente').value.trim(),
        apellidos: document.getElementById('apePaciente').value.trim(),
        sexo: document.getElementById('sexoPaciente').value,
        fecha_de_nacimiento: document.getElementById('fechaNacimiento').value,
        celular: document.getElementById('telefonoPaciente').value.trim(),
        cedula: document.getElementById('cedulaPaciente').value.replace(/-/g, '').trim(),
        direccion: document.getElementById('direccionPaciente').value.trim(),
        barrio: document.getElementById('barrioPaciente').value.trim(),
        id_sector: document.getElementById('sectorPaciente').value ? Number(document.getElementById('sectorPaciente').value) : null,
        estado: document.getElementById('activoPaciente').value === 'true'
    };

    const patologias = Array.from(document.querySelectorAll('#patologiaPaciente input[type="checkbox"]:checked'))
        .map(checkbox => Number(checkbox.value))
        .filter(Boolean);
    const fechaDiagnostico = document.getElementById('fechaDiagnostico').value;
    const observacionPatologia = document.getElementById('observacionPatologia').value.trim();

    if (!data.nombre || 
        !data.apellidos || 
        !data.sexo || 
        !data.fecha_de_nacimiento || 
        !data.celular || 
        !data.cedula || 
        !data.direccion || 
        !data.barrio) {
        errorEl.textContent = 'Complete los campos obligatorios.';
        return;
    }

    if (patologias.length && !fechaDiagnostico) {
        errorEl.textContent = 'Seleccione la fecha de diagnóstico de la patología.';
        return;
    }

    try {
        const id = editandoId.pacientes;
        const res = await fetch(`${API_LOCAL}/pacientes/${id ? `${id}/` : ''}`, {
            method: id ? 'PUT' : 'POST',
            headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
            body: JSON.stringify(data)
        });

        if (res.ok) {
            const paciente = await res.json();
            if (patologias.length && !id) {
                for (const patologia of patologias) {
                    const relacion = await fetch(`${API_LOCAL}/paciente-patologia/`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
                        body: JSON.stringify({
                            id_paciente: paciente.id,
                            id_patologia_cronica: patologia,
                            fecha_de_diagnostico: fechaDiagnostico,
                            estado: true,
                            observaciones: observacionPatologia
                        })
                    });
                    if (!relacion.ok) throw new Error(await relacion.text());
                }
            }
            cerrarModal('modalPacientes');
            cargarPacientes();
            cargarDashboard();
        } else {
            const errText = await res.text();
            errorEl.textContent = 'Error al guardar.';
            console.error(errText);
        }
    } catch (error) {
        errorEl.textContent = 'Error de conexión.';
        console.error(error);
    }
}

async function editarPaciente(id) {
    const respuesta = await fetch(`${API_LOCAL}/pacientes/${id}/`, { headers: getAuthHeaders() });
    const paciente = await respuesta.json();
    abrirModalPacientes('editar', id);
    document.getElementById('nomPaciente').value = paciente.nombre || '';
    document.getElementById('apePaciente').value = paciente.apellidos || '';
    document.getElementById('cedulaPaciente').value = formatearCedula(paciente.cedula);
    document.getElementById('sexoPaciente').value = paciente.sexo || '';
    document.getElementById('fechaNacimiento').value = paciente.fecha_de_nacimiento || '';
    document.getElementById('direccionPaciente').value = paciente.direccion || '';
    document.getElementById('barrioPaciente').value = paciente.barrio || '';
    document.getElementById('telefonoPaciente').value = paciente.celular || '';
    document.getElementById('sectorPaciente').value = paciente.id_sector || '';
    document.getElementById('activoPaciente').value = String(paciente.estado);
}

async function eliminarPaciente(id, nombre) {
    if (!confirm(`¿Desea eliminar a ${nombre}?`)) return;
    try {
        const res = await fetch(`${API_LOCAL}/pacientes/${id}/`,
             { method: 'DELETE', headers: getAuthHeaders() });
        if (res.ok) {
            cargarPacientes();
            cargarDashboard();
        } else {
            alert('No se pudo eliminar el registro.');
        }
    } catch (e) {
        console.error(e);
    }
}

// ==========================================
// 3. GESTIÓN DE MÉDICOS
// ==========================================
async function cargarMedicos() {
    const cargando = document.getElementById('cargandoMedicos');
    const tbody = document.getElementById('bodyMedicos');
    if (cargando) cargando.style.display = 'block';
    if (tbody) tbody.innerHTML = '';

    try {
        const respuesta = await fetch(`${API_LOCAL}/medicos/`, { headers: getAuthHeaders() });
        const data = await respuesta.json();
        const medicos = safeArray(data);
        if (cargando) cargando.style.display = 'none';

        medicos.forEach((m, index) => {
            const especialidad = m.id_especialidad && typeof m.id_especialidad === 'object'
                ? m.id_especialidad.nombre_especialidad || ''
                : '';

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${index + 1}</td>
                <td>${textValue(m, 'codigo_minsa') || ''}</td>
                <td>${textValue(m, 'nombre') || ''}</td>
                <td>${textValue(m, 'apellidos') || ''}</td>
                <td>${especialidad}</td>
                <td>${textValue(m, 'celular') || ''}</td>
                <td>${textValue(m, 'estado') !== '' ? formatEstado(m.estado) : ''}</td>
                <td>${formatDateTime(m.fecha_creacion)}</td>
                <td><button class="btn btn-sm btn-secundario"
                 onclick="editarMedico(${m.id})">✏️ 
                 Editar</button><button class="btn btn-sm 
                 btn-peligro" onclick="eliminarMedico(${m.id}, 
                 '${textValue(m, 'nombre')}')">🗑️ Eliminar</button></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        if (cargando) cargando.textContent = '❌ Error al cargar los médicos.';
        console.error(error);
    }
}

function abrirModalMedicos(modo, id = null) {
    limpiarErroresModales();
    editandoId.medicos = id;
    if (modo === 'crear' || modo === 'editar') {
        editandoId.medicos = id;
        document.getElementById('modalMedTitulo').textContent = 'Nuevo Médico';
        document.getElementById('codigo_minsa').value = '';
        document.getElementById('nomMedicos').value = '';
        document.getElementById('apeMedicos').value = '';
        document.getElementById('especialidad').value = '';
        document.getElementById('telefonoMedicos').value = '';
    }
    llenarSelectEspecialidades();
    abrirModal('modalMedicos');
}

async function guardarMedicos() {
    const errorEl = document.getElementById('MedicosError');
    const data = {
        id_especialidad: document.getElementById('especialidad').value ? 
        Number(document.getElementById('especialidad').value) : null,
        nombre: document.getElementById('nomMedicos').value.trim(),
        apellidos: document.getElementById('apeMedicos').value.trim(),
        celular: document.getElementById('telefonoMedicos').value.trim(),
        codigo_minsa: document.getElementById('codigo_minsa').value.trim(),
        estado: true
    };

    if (!data.nombre || 
        !data.apellidos || 
        !data.codigo_minsa || 
        !data.id_especialidad) {
        errorEl.textContent = 'Complete los campos obligatorios.';
        return;
    }

    try {
        const id = editandoId.medicos;
        const res = await fetch(`${API_LOCAL}/medicos/${id ? `${id}/` : ''}`, {
            method: id ? 'PUT' : 'POST',
            headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
            body: JSON.stringify(data)
        });

        if (res.ok) {
            cerrarModal('modalMedicos');
            cargarMedicos();
            cargarDashboard();
        } else {
            const errText = await res.text();
            errorEl.textContent = 'Error al registrar el médico.';
            console.error(errText);
        }
    } catch (error) {
        errorEl.textContent = 'Error de conexión.';
        console.error(error);
    }
}

async function editarMedico(id) {
    const respuesta = await fetch(`${API_LOCAL}/medicos/${id}/`, { headers: getAuthHeaders() });
    const medico = await respuesta.json();
    abrirModalMedicos('editar', id);
    document.getElementById('nomMedicos').value = medico.nombre || '';
    document.getElementById('apeMedicos').value = medico.apellidos || '';
    document.getElementById('codigo_minsa').value = medico.codigo_minsa || '';
    document.getElementById('telefonoMedicos').value = medico.celular || '';
    document.getElementById('especialidad').value = medico.id_especialidad || '';
}

async function eliminarMedico(id, nombre) {
    if (!confirm(`¿Desea eliminar al médico ${nombre}?`)) return;
    try {
        const res = await fetch(`${API_LOCAL}/medicos/${id}/`, 
            { method: 'DELETE', headers: getAuthHeaders() });
        if (res.ok) {
            cargarMedicos();
            cargarDashboard();
        } else {
            alert('No se puede eliminar porque tiene registros vinculados.');
        }
    } catch (e) {
        console.error(e);
    }
}

// ==========================================
// 4. GESTIÓN DE CITAS / ATENCIONES MÉDICAS
// ==========================================
async function cargarCitasMedicas() {
    const cargando = document.getElementById('cargandoCitasMedicas');
    const tbody = document.getElementById('bodyCitasMedicas');
    if (cargando) cargando.style.display = 'block';
    if (tbody) tbody.innerHTML = '';

    try {
        const [respuesta, relacionesRespuesta, pacientesRespuesta, patologiasRespuesta, medicosRespuesta] = await Promise.all([
            fetch(`${API_LOCAL}/atencion-cronico/`, { headers: getAuthHeaders() }),
            fetch(`${API_LOCAL}/paciente-patologia/`, { headers: getAuthHeaders() }),
            fetch(`${API_LOCAL}/pacientes/`, { headers: getAuthHeaders() }),
            fetch(`${API_LOCAL}/patologias-cronicas/`, { headers: getAuthHeaders() }),
            fetch(`${API_LOCAL}/medicos/`, { headers: getAuthHeaders() })
        ]);
        const citas = safeArray(await respuesta.json());
        const relacionesLista = safeArray(await relacionesRespuesta.json());
        const relaciones = Object.fromEntries(relacionesLista.map(item => [item.id, item]));
        const pacientes = Object.fromEntries(safeArray(await pacientesRespuesta.json()).map(item => [item.id, item]));
        const patologias = Object.fromEntries(safeArray(await patologiasRespuesta.json()).map(item => [item.id, item]));
        const medicos = Object.fromEntries(safeArray(await medicosRespuesta.json()).map(item => [item.id, item]));
        const patologiasPorPaciente = {};
        relacionesLista.forEach(relacionItem => {
            const pacienteRelacionId = typeof relacionItem.id_paciente === 'object'
                ? relacionItem.id_paciente.id
                : relacionItem.id_paciente;
            const patologiaRelacionId = typeof relacionItem.id_patologia_cronica === 'object'
                ? relacionItem.id_patologia_cronica.id
                : relacionItem.id_patologia_cronica;
            if (!patologiasPorPaciente[pacienteRelacionId]) patologiasPorPaciente[pacienteRelacionId] = [];
            const nombre = textValue(patologias[patologiaRelacionId], 'nombre_patologia');
            if (nombre && !patologiasPorPaciente[pacienteRelacionId].includes(nombre)) {
                patologiasPorPaciente[pacienteRelacionId].push(nombre);
            }
        });
        if (cargando) cargando.style.display = 'none';

        citas.forEach((c) => {
            const relacionId = typeof c.id_paciente_patologia === 'object'
                ? c.id_paciente_patologia.id
                : c.id_paciente_patologia;
            const relacion = relaciones[relacionId] || {};
            const pacienteId = typeof relacion.id_paciente === 'object'
                ? relacion.id_paciente.id
                : relacion.id_paciente;
            const patologiaId = typeof relacion.id_patologia_cronica === 'object'
                ? relacion.id_patologia_cronica.id
                : relacion.id_patologia_cronica;
            const paciente = pacientes[pacienteId] || {};
            const patologia = patologias[patologiaId] || {};
            const medicoId = typeof c.id_medico === 'object' ? c.id_medico.id : c.id_medico;
            const medico = medicos[medicoId] || {};
            const nombrePaciente = `${textValue(paciente, 'nombre')} ${textValue(paciente, 'apellidos')}`.trim();
            const nombrePatologia = patologiasPorPaciente[pacienteId]?.join(', ') || textValue(patologia, 'nombre_patologia');
            const pacientePatologia = nombrePaciente && nombrePatologia
                ? `Paciente: ${nombrePaciente} | Patología: ${nombrePatologia}`
                : nombrePaciente || nombrePatologia || 'Sin información';
            const nombreMedico = `${textValue(medico, 'nombre')} ${textValue(medico, 'apellidos')}`.trim();
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${c.id || ''}</td>
                <td>${pacientePatologia || 'Sin información'}</td>
                <td>${nombreMedico || 'Sin información'}</td>
                <td>${formatDate(textValue(c, 'fecha_atencion'))}</td>
                <td>${textValue(c, 'peso') ? `${textValue(c, 'peso')} kg` : '-'}</td>
                <td>${textValue(c, 'talla') ? `${textValue(c, 'talla')} cm` : '-'}</td>
                <td>${textValue(c, 'presion_arterial') || '-'}</td>
                <td>${formatDate(textValue(c, 'fecha_proxima_cita')) || '-'}</td>
                <td>${isTrue(textValue(c, 'asistio')) ? '✔ Sí' : '❌ No'}</td>
                <td>${isTrue(textValue(c, 'consulta_especializada')) ? '✔ Sí' : '❌ No'}</td>
                <td>${textValue(c, 'observaciones') || '-'}</td>
                <td>${formatDateTime(textValue(c, 'fecha_creacion'))}</td>
                <td><button class="btn btn-sm btn-secundario" onclick="editarCita(${c.id})">
                ✏️ Editar</button><button 
                class="btn btn-sm btn-peligro"
                 onclick="eliminarCita(${c.id})">
                 🗑️ Eliminar</button></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        if (cargando) cargando.textContent = '❌ Error al cargar atenciones.';
        console.error(error);
    }
}

async function cargarTratamientos() {
    const cargando = document.getElementById('cargandoTratamientos');
    const tbody = document.getElementById('bodyTratamientos');
    if (cargando) cargando.style.display = 'block';
    if (tbody) tbody.innerHTML = '';
    try {
        const [tratamientosRespuesta, contextoRespuesta] = await Promise.all([
            fetch(`${API_LOCAL}/tratamiento/`, { headers: getAuthHeaders() }),
            cargarContextoPacienteAtenciones()
        ]);
        const tratamientos = safeArray(await tratamientosRespuesta.json());
        const atenciones = Object.fromEntries(contextoRespuesta.atenciones.map(item => [item.id, item]));
        if (cargando) cargando.style.display = 'none';
        tratamientos.forEach((item, index) => {
            const atencion = atenciones[item.id_atencion_cronico];
            const referenciaAtencion = atencion
                ? crearEtiquetaAtencionPaciente(atencion, contextoRespuesta)
                : `Atención #${item.id_atencion_cronico || 'Sin asignar'}`;
            const fila = document.createElement('tr');
            fila.innerHTML = `
                <td>${index + 1}</td>
                <td>${referenciaAtencion}</td>
                <td>${formatDate(item.fecha_tratamiento)}</td>
                <td>${item.observaciones || ''}</td>
                <td>
                    <button class="btn btn-sm btn-secundario" onclick="editarTratamiento(${item.id})">✏️ Editar</button>
                    <button class="btn btn-sm btn-peligro" onclick="eliminarTratamiento(${item.id})">🗑️ Eliminar</button>
                </td>
            `;
            tbody.appendChild(fila);
        });
    } catch (error) {
        if (cargando) cargando.textContent = '❌ Error al cargar tratamientos.';
        console.error(error);
    }
}

async function cargarDetalleTratamiento() {
    const cargando = document.getElementById('cargandoDetalleTratamiento');
    const tbody = document.getElementById('bodyDetalleTratamiento');
    if (cargando) cargando.style.display = 'block';
    if (tbody) tbody.innerHTML = '';
    try {
        const [detallesRespuesta, tratamientosRespuesta, medicamentosRespuesta, contexto] = await Promise.all([
            fetch(`${API_LOCAL}/detalle-tratamiento/`, { headers: getAuthHeaders() }),
            fetch(`${API_LOCAL}/tratamiento/`, { headers: getAuthHeaders() }),
            fetch(`${API_LOCAL}/medicamentos/`, { headers: getAuthHeaders() }),
            cargarContextoPacienteAtenciones()
        ]);
        if (!detallesRespuesta.ok || !tratamientosRespuesta.ok || !medicamentosRespuesta.ok) {
            throw new Error('No se pudieron cargar los detalles relacionados del tratamiento.');
        }
        const detalles = safeArray(await detallesRespuesta.json());
        const tratamientos = new Map(safeArray(await tratamientosRespuesta.json()).map(item => [String(item.id), item]));
        const medicamentos = new Map(safeArray(await medicamentosRespuesta.json()).map(item => [String(item.id), item]));
        const atenciones = new Map(contexto.atenciones.map(item => [String(item.id), item]));

        if (cargando) cargando.style.display = 'none';
        detalles.forEach((item, index) => {
            const tratamiento = tratamientos.get(String(item.id_tratamiento));
            const atencion = tratamiento
                ? atenciones.get(String(tratamiento.id_atencion_cronico))
                : null;
            const medicamento = medicamentos.get(String(item.id_medicamento));
            const etiquetaTratamiento = tratamiento && atencion
                ? `${crearEtiquetaAtencionPaciente(atencion, contexto)} · Tratamiento #${tratamiento.id}`
                : tratamiento ? `Tratamiento #${tratamiento.id}` : 'Sin tratamiento';
            const fila = document.createElement('tr');
            fila.innerHTML = `
                <td>${index + 1}</td>
                <td>${etiquetaTratamiento}</td>
                <td>${medicamento?.nombre_medicamento || 'Sin medicamento'}</td>
                <td>${item.cantidad_entregada || ''}</td>
                <td>${item.indicacion || ''}</td>
                <td>
                    <button class="btn btn-sm btn-secundario"
                     onclick="editarDetalleTratamiento(${item.id})">✏️ Editar</button>
                    <button class="btn btn-sm btn-peligro"
                    onclick="eliminarDetalleTratamiento(${item.id})">🗑️ Eliminar</button>
                </td>
            `;
            tbody.appendChild(fila);
        });
    } catch (error) {
        if (cargando) cargando.textContent = '❌ Error al cargar detalles de tratamientos.';
        console.error(error);
    }
}

async function llenarSelectTratamientos(fecha = null) {
    if (!window.tratamientosDetalle) {
        const [tratamientosRespuesta, contexto] = await Promise.all([
            fetch(`${API_LOCAL}/tratamiento/`, { headers: getAuthHeaders() }),
            cargarContextoPacienteAtenciones()
        ]);
        if (!tratamientosRespuesta.ok) throw new Error('No se pudieron cargar los tratamientos.');
        window.tratamientosDetalle = safeArray(await tratamientosRespuesta.json());
        window.atencionesDetalleTratamiento = contexto.atenciones;
        window.contextoDetalleTratamiento = contexto;
    }
    const fechaInput = document.getElementById('fechaDetalleTratamiento');
    const select = document.getElementById('tratamientoDetalle');
    let fechaElegida = fecha || fechaInput.value || fechaLocalISO();
    if (!fecha) {
        const fechasDisponibles = window.atencionesDetalleTratamiento
            .map(item => fechaAtencionISO(item.fecha_atencion))
            .filter(Boolean)
            .sort();
        if (fechasDisponibles.length && !fechasDisponibles.includes(fechaElegida)) {
            fechaElegida = fechasDisponibles[fechasDisponibles.length - 1];
        }
    }
    fechaInput.value = fechaElegida;
    select.innerHTML = '<option value="">-- Seleccione tratamiento --</option>';
    const tratamientosDelDia = window.tratamientosDetalle.filter(item =>
        fechaAtencionISO(window.atencionesDetalleTratamiento.find(atencion =>
            String(atencion.id) === String(item.id_atencion_cronico))?.fecha_atencion) === fechaElegida);
    tratamientosDelDia.forEach(item => {
        const atencion = window.atencionesDetalleTratamiento.find(registro =>
            String(registro.id) === String(item.id_atencion_cronico));
        const etiqueta = atencion
            ? `${crearEtiquetaAtencionPaciente(atencion, window.contextoDetalleTratamiento)} · Tratamiento #${item.id}`
            : `Tratamiento #${item.id} - Atención ${item.id_atencion_cronico} - Paciente sin ficha`;
        const option = document.createElement('option');
        option.value = item.id;
        option.textContent = etiqueta;
        select.appendChild(option);
    });
    if (!tratamientosDelDia.length) {
        select.innerHTML = '<option value="">-- No hay tratamientos para este día --</option>';
    }
}

async function llenarSelectMedicamentosDetalle() {
    const respuesta = await fetch(`${API_LOCAL}/medicamentos/`, { headers: getAuthHeaders() });
    const medicamentos = safeArray(await respuesta.json());
    const select = document.getElementById('medicamentoDetalle');
    select.innerHTML = '<option value="">-- Seleccione medicamento --</option>';
    medicamentos.forEach(item => {
        select.innerHTML += `<option value="${item.id}">${item.nombre_medicamento} - ${item.presentacion} - ${item.concentracion}</option>`;
    });
}

function fechaLocalISO() {
    const hoy = new Date();
    const mes = String(hoy.getMonth() + 1).padStart(2, '0');
    const dia = String(hoy.getDate()).padStart(2, '0');
    return `${hoy.getFullYear()}-${mes}-${dia}`;
}

function fechaAtencionISO(valor) {
    return String(valor || '').slice(0, 10);
}

async function cargarContextoPacienteAtenciones() {
    const headers = { headers: getAuthHeaders() };
    const [atenciones, pacientes, pacientesPatologias] = await Promise.all([
        fetchJsonOrThrow(`${API_LOCAL}/atencion-cronico/`, headers),
        fetchJsonOrThrow(`${API_LOCAL}/pacientes/`, headers),
        fetchJsonOrThrow(`${API_LOCAL}/paciente-patologia/`, headers)
    ]);
    return {
        atenciones: safeArray(atenciones),
        pacientesPorId: new Map(safeArray(pacientes).map(item => [String(item.id), item])),
        pacientesPatologiasPorId: new Map(safeArray(pacientesPatologias).map(item => [String(item.id), item]))
    };
}

async function cargarContextoSolicitudesResultados() {
    const headers = { headers: getAuthHeaders() };
    const [solicitudes, examenes, contexto, tratamientos] = await Promise.all([
        fetchJsonOrThrow(`${API_LOCAL}/solicitud-de-examenes/`, headers),
        fetchJsonOrThrow(`${API_LOCAL}/examenes-de-laboratorio/`, headers),
        cargarContextoPacienteAtenciones(),
        fetchJsonOrThrow(`${API_LOCAL}/tratamiento/`, headers)
    ]);
    return {
        ...contexto,
        solicitudes: safeArray(solicitudes),
        examenesPorId: new Map(safeArray(examenes).map(item => [String(item.id), item])),
        tratamientos: safeArray(tratamientos),
        solicitudesPorId: new Map(safeArray(solicitudes).map(item => [String(item.id), item]))
    };
}

function crearEtiquetaAtencionPaciente(atencion, contexto) {
    const relacionId = obtenerIdRelacionado(atencion.id_paciente_patologia);
    const relacion = contexto.pacientesPatologiasPorId.get(String(relacionId));
    const pacienteId = obtenerIdRelacionado(relacion?.id_paciente);
    const paciente = contexto.pacientesPorId.get(String(pacienteId));
    const primerNombre = String(paciente?.nombre || '').trim().split(/\s+/)[0] || '';
    const primerApellido = String(paciente?.apellidos || '').trim().split(/\s+/)[0] || '';
    const nombrePaciente = `${primerNombre} ${primerApellido}`.trim();
    return nombrePaciente
        ? `Atención ${atencion.id} - ${nombrePaciente}`
        : `Atención ${atencion.id} - Paciente sin ficha`;
}

function crearEtiquetaSolicitudResultado(solicitud, contexto) {
    const examenId = obtenerIdRelacionado(solicitud.id_examen_de_laboratorio);
    const examen = contexto.examenesPorId.get(String(examenId));
    const atencionId = obtenerIdRelacionado(solicitud.id_atencion_cronico);
    const atencion = contexto.atenciones.find(item => String(item.id) === String(atencionId));
    const partes = [examen?.nombre_examen || 'Examen sin nombre'];
    if (atencion) {
        partes.push(crearEtiquetaAtencionPaciente(atencion, contexto));
        const tratamientos = contexto.tratamientos.filter(item =>
            String(obtenerIdRelacionado(item.id_atencion_cronico)) === String(atencion.id));
        tratamientos.forEach(tratamiento => partes.push(`Tratamiento #${tratamiento.id}`));
    } else {
        partes.push(`Atención ${atencionId || 'sin asignar'} - Paciente sin ficha`);
    }
    return partes.join(' · ');
}

async function llenarSelectAtencionesTratamiento(fecha = null) {
    if (!window.atencionesTratamiento) {
            const contexto = await cargarContextoPacienteAtenciones();
            window.atencionesTratamiento = contexto.atenciones;
            window.contextoAtencionesTratamiento = contexto;
    }
    const fechaInput = document.getElementById('fechaAtencionTratamiento');
    const select = document.getElementById('atencionTratamiento');
    let fechaElegida = fecha || fechaInput.value || fechaLocalISO();
    if (!fecha) {
        const fechasDisponibles = window.atencionesTratamiento
            .map(item => fechaAtencionISO(item.fecha_atencion))
            .filter(Boolean)
            .sort();
        if (fechasDisponibles.length && !fechasDisponibles.includes(fechaElegida)) {
            fechaElegida = fechasDisponibles[fechasDisponibles.length - 1];
        }
    }
    fechaInput.value = fechaElegida;
    select.innerHTML = '<option value="">-- Seleccione atención y paciente --</option>';
    const atencionesDelDia = window.atencionesTratamiento.filter(item =>
        fechaAtencionISO(item.fecha_atencion) === fechaElegida);
    atencionesDelDia.forEach(item => {
        const option = document.createElement('option');
        option.value = item.id;
        option.textContent = crearEtiquetaAtencionPaciente(item, window.contextoAtencionesTratamiento);
        select.appendChild(option);
    });
    if (!atencionesDelDia.length) {
        select.innerHTML = '<option value="">-- No hay atenciones para este día --</option>';
    }
}

async function abrirModalTratamiento(id = null) {
    editandoId.tratamientos = id;
    document.getElementById('modalTratamientoTitulo').textContent = id ? 'Editar tratamiento' : 'Nuevo tratamiento';
    document.getElementById('observacionesTratamiento').value = '';
    const fechaInput = document.getElementById('fechaAtencionTratamiento');
    if (!fechaInput.dataset.configurado) {
        fechaInput.dataset.configurado = 'true';
        fechaInput.addEventListener('change', () => llenarSelectAtencionesTratamiento(fechaInput.value));
    }
    let item = null;
    if (id) {
        await llenarSelectAtencionesTratamiento(fechaLocalISO());
        const respuesta = await fetch(`${API_LOCAL}/tratamiento/${id}/`, { headers: getAuthHeaders() });
        item = await respuesta.json();
        const atencion = window.atencionesTratamiento?.find(registro => registro.id === item.id_atencion_cronico);
        fechaInput.value = atencion ? fechaAtencionISO(atencion.fecha_atencion) : fechaLocalISO();
        document.getElementById('observacionesTratamiento').value = item.observaciones || '';
    }
    await llenarSelectAtencionesTratamiento(id ? fechaInput.value : null);
    if (item) document.getElementById('atencionTratamiento').value = item.id_atencion_cronico;
    abrirModal('modalTratamiento');
}

async function guardarTratamiento() {
    const data = {
        id_atencion_cronico: Number(document.getElementById('atencionTratamiento').value),
        observaciones: document.getElementById('observacionesTratamiento').value.trim()
    };
    const error = document.getElementById('tratamientoError');
    if (!data.id_atencion_cronico) {
        error.textContent = 'Seleccione una atención crónica.';
        return;
    }
    const id = editandoId.tratamientos;
    const respuesta = await fetch(`${API_LOCAL}/tratamiento/${id ? `${id}/` : ''}`, {
        method: id ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
        body: JSON.stringify(data)
    });
    if (!respuesta.ok) {
        error.textContent = 'No se pudo guardar el tratamiento.';
        return;
    }
    cerrarModal('modalTratamiento');
    cargarTratamientos();
}

async function editarTratamiento(id) {
    await abrirModalTratamiento(id);
}

async function eliminarTratamiento(id) {
    if (!confirm('¿Desea eliminar este tratamiento?')) return;
    const respuesta = await fetch(`${API_LOCAL}/tratamiento/${id}/`, { method: 'DELETE', headers: getAuthHeaders() });
    if (respuesta.ok) cargarTratamientos();
}

async function abrirModalDetalleTratamiento(id = null) {
    editandoId.detalleTratamiento = id;
    document.getElementById('modalDetalleTratamientoTitulo').textContent = id ? 
    'Editar medicamento en tratamiento' : 'Nuevo medicamento en tratamiento';
    const fechaInput = document.getElementById('fechaDetalleTratamiento');
    if (!fechaInput.dataset.configurado) {
        fechaInput.dataset.configurado = 'true';
        fechaInput.addEventListener('change', () => llenarSelectTratamientos(fechaInput.value));
    }
    await llenarSelectMedicamentosDetalle();
    document.getElementById('cantidadEntregada').value = '';
    document.getElementById('indicacionDetalle').value = '';
    let item = null;
    if (id) {
        const respuesta = await fetch(`${API_LOCAL}/detalle-tratamiento/${id}/`, { headers: getAuthHeaders() });
        item = await respuesta.json();
        await llenarSelectTratamientos(fechaLocalISO());
        const tratamiento = window.tratamientosDetalle.find(registro => registro.id === item.id_tratamiento);
        fechaInput.value = tratamiento
            ? window.atencionesDetalleTratamiento.find(atencion => atencion.id === tratamiento.id_atencion_cronico)?.fecha_atencion?.slice(0, 10)
            : fechaLocalISO();
        document.getElementById('medicamentoDetalle').value = item.id_medicamento;
        document.getElementById('cantidadEntregada').value = item.cantidad_entregada;
        document.getElementById('indicacionDetalle').value = item.indicacion || '';
    }
    await llenarSelectTratamientos(id ? fechaInput.value : null);
    if (item) document.getElementById('tratamientoDetalle').value = item.id_tratamiento;
    abrirModal('modalDetalleTratamiento');
}

async function guardarDetalleTratamiento() {
    const data = {
        id_tratamiento: Number(document.getElementById('tratamientoDetalle').value),
        id_medicamento: Number(document.getElementById('medicamentoDetalle').value),
        cantidad_entregada: Number(document.getElementById('cantidadEntregada').value),
        indicacion: document.getElementById('indicacionDetalle').value.trim()
    };
    const error = document.getElementById('detalleTratamientoError');
    if (!data.id_tratamiento || !data.id_medicamento || data.cantidad_entregada < 1 || !data.indicacion) {
        error.textContent = 'Complete tratamiento, medicamento, cantidad e indicación.';
        return;
    }
    const id = editandoId.detalleTratamiento;
    const respuesta = await fetch(`${API_LOCAL}/detalle-tratamiento/${id ? `${id}/` : ''}`, {
        method: id ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
        body: JSON.stringify(data)
    });
    if (!respuesta.ok) {
        error.textContent = 'No se pudo guardar el medicamento del tratamiento.';
        return;
    }
    cerrarModal('modalDetalleTratamiento');
    cargarDetalleTratamiento();
}

async function editarDetalleTratamiento(id) {
    await abrirModalDetalleTratamiento(id);
}

async function eliminarDetalleTratamiento(id) {
    if (!confirm('¿Desea eliminar este medicamento del tratamiento?')) return;
    const respuesta = await fetch(`${API_LOCAL}/detalle-tratamiento/${id}/`, 
        { method: 'DELETE', headers: getAuthHeaders() });
    if (respuesta.ok) cargarDetalleTratamiento();
}

async function abrirModalCitasMedicas(modo, id = null) {
    limpiarErroresModales();
    editandoId.citasmedicas = id;
    document.getElementById('fecha_hora').value = '';
    document.getElementById('motivo').value = '';
    document.getElementById('atendidaCita').value = 'false';
    document.getElementById('consultaEspecializada').value = 'false';
    document.getElementById('pesoAtencion').value = '';
    document.getElementById('tallaAtencion').value = '';
    document.getElementById('presionAtencion').value = '';
    document.getElementById('fechaProximaCita').value = '';
    delete document.getElementById('nomCitasMedicas').dataset.edicionRelacionId;
    await Promise.all([
        llenarSelectPacientesPatologias('nomCitasMedicas'),
        llenarSelectMedicos('cdCitasMedicas')
    ]);
    if (id) {
        const respuesta = await fetch(`${API_LOCAL}/atencion-cronico/${id}/`, { headers: getAuthHeaders() });
        const item = await respuesta.json();
        const relacion = Object.values(relacionesAtencionPorPaciente)
            .flat()
            .find(itemRelacion => itemRelacion.id === item.id_paciente_patologia);
        document.getElementById('nomCitasMedicas').value = relacion ? relacion.id_paciente : '';
        document.getElementById('nomCitasMedicas').dataset.edicionRelacionId = item.id_paciente_patologia;
        document.getElementById('cdCitasMedicas').value = item.id_medico;
        document.getElementById('fecha_hora').value = item.fecha_atencion || '';
        document.getElementById('motivo').value = item.observaciones || '';
        document.getElementById('atendidaCita').value = String(item.asistio);
        document.getElementById('consultaEspecializada').value = String(item.consulta_especializada);
        document.getElementById('pesoAtencion').value = item.peso || '';
        document.getElementById('tallaAtencion').value = item.talla || '';
        document.getElementById('presionAtencion').value = item.presion_arterial || '';
        document.getElementById('fechaProximaCita').value = item.fecha_proxima_cita || '';
    }
    abrirModal('modalCitasMedicas');
}

async function guardarCitasMedicas() {
    const pacienteSeleccionado = document.getElementById('nomCitasMedicas');
    const relacionesSeleccionadas = relacionesAtencionPorPaciente[pacienteSeleccionado.value] || [];
    const data = {
        id_medico: document.getElementById('cdCitasMedicas').value ? 
        Number(document.getElementById('cdCitasMedicas').value) : null,
        fecha_atencion: document.getElementById('fecha_hora').value,
        peso: document.getElementById('pesoAtencion').value || null,
        talla: document.getElementById('tallaAtencion').value || null,
        presion_arterial: document.getElementById('presionAtencion').value.trim() || null,
        fecha_proxima_cita: document.getElementById('fechaProximaCita').value || null,
        asistio: document.getElementById('atendidaCita').value === 'true',
        consulta_especializada: document.getElementById('consultaEspecializada').value === 'true',
        observaciones: document.getElementById('motivo').value || ''
    };

    try {
        const id = editandoId.citasmedicas;
        const idsRelacion = id
            ? [Number(pacienteSeleccionado.dataset.edicionRelacionId)]
            : relacionesSeleccionadas.length
                ? [relacionesSeleccionadas[0].id]
                : [];
        if (!idsRelacion.length || idsRelacion.some(Number.isNaN)) {
            document.getElementById('CitasMedicasError').textContent = 'Seleccione un paciente con patología.';
            return;
        }

        for (const relacionId of idsRelacion) {
            const res = await fetch(`${API_LOCAL}/atencion-cronico/${id ? `${id}/` : ''}`, {
                method: id ? 'PUT' : 'POST',
                headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
                body: JSON.stringify({ ...data, id_paciente_patologia: relacionId })
            });
            if (!res.ok) {
                document.getElementById('CitasMedicasError').textContent = 'No se pudo guardar la atención.';
                return;
            }
        }

        if (idsRelacion.length) {
            cerrarModal('modalCitasMedicas');
            cargarCitasMedicas();
            cargarDashboard();
        }
    } catch (error) {
        console.error(error);
    }
}

async function eliminarCita(id) {
    if (!confirm('¿Desea eliminar esta atención?')) return;
    try {
        const res = await fetch(`${API_LOCAL}/atencion-cronico/${id}/`, { method: 'DELETE', headers: getAuthHeaders() });
        if (res.ok) { cargarCitasMedicas(); cargarDashboard(); }
    } catch (e) { console.error(e); }
}

// ==========================================
// 5. GESTIÓN DE MEDICAMENTOS
// ==========================================
async function cargarCategoriasMedicamentos() {
    await cargarCatalogoSimple('categoria-medicamento', 
        'Categorías de medicamentos', 'bodyCategoriasMedicamentos', 
        'cargandoCategoriasMedicamentos', (item, index) => `
        <td>${index + 1}</td>
        <td>${item.nombre_categoria || ''}</td>
        <td>${formatEstado(item.estado)}</td>
        <td>${formatDateTime(item.fecha_creacion)}</td>
        <td>
            <button class="btn btn-sm btn-secundario"
             onclick="editarCategoriaMedicamento(${item.id})">✏️ Editar</button>
            <button class="btn btn-sm btn-peligro"
             onclick="eliminarCategoriaMedicamento(${item.id})">🗑️ Eliminar</button>
        </td>
    `);
}

function abrirModalCategoriaMedicamento(id = null) {
    editandoId.categoriaMedicamento = id;
    document.getElementById('nombreCategoriaMedicamento').value = '';
    document.getElementById('estadoCategoriaMedicamento').value = 'true';
    abrirModal('modalCategoriaMedicamento');
}

async function guardarCategoriaMedicamento() {
    const error = document.getElementById('categoriaMedicamentoError');
    const data = {
        nombre_categoria: document.getElementById('nombreCategoriaMedicamento').value.trim(),
        estado: document.getElementById('estadoCategoriaMedicamento').value === 'true'
    };
    if (!data.nombre_categoria) {
        error.textContent = 'Escriba el nombre de la categoría.';
        return;
    }
    const id = editandoId.categoriaMedicamento;
    const respuesta = await fetch(`${API_LOCAL}/categoria-medicamento/${id ? `${id}/` : ''}`, {
        method: id ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
        body: JSON.stringify(data)
    });
    if (!respuesta.ok) {
        error.textContent = 'No se pudo guardar la categoría.';
        return;
    }
    cerrarModal('modalCategoriaMedicamento');
    cargarCategoriasMedicamentos();
}

async function editarCategoriaMedicamento(id) {
    const respuesta = await fetch(`${API_LOCAL}/categoria-medicamento/${id}/`, 
        { headers: getAuthHeaders() });
    const item = await respuesta.json();
    abrirModalCategoriaMedicamento(id);
    document.getElementById('nombreCategoriaMedicamento').value = item.nombre_categoria || '';
    document.getElementById('estadoCategoriaMedicamento').value = String(item.estado);
}

async function eliminarCategoriaMedicamento(id) {
    if (!confirm('¿Desea eliminar esta categoría?')) return;
    const respuesta = await fetch(`${API_LOCAL}/categoria-medicamento/${id}/`,
         { method: 'DELETE', headers: getAuthHeaders() });
    if (respuesta.ok) cargarCategoriasMedicamentos();
}

async function cargarMedicamentos() {
    const cargando = document.getElementById('cargandoMedicamentos');
    const tbody = document.getElementById('bodyMedicamentos');
    if (cargando) cargando.style.display = 'block';
    if (tbody) tbody.innerHTML = '';

    try {
        const [respuesta, categoriasRespuesta] = await Promise.all([
            fetch(`${API_LOCAL}/medicamentos/`, { headers: getAuthHeaders() }),
            fetch(`${API_LOCAL}/categoria-medicamento/`, { headers: getAuthHeaders() })
        ]);
        const data = await respuesta.json();
        const categorias = Object.fromEntries(safeArray(await categoriasRespuesta.json()).map(item => 
            [item.id, item.nombre_categoria]));
        const medicamentos = safeArray(data);
        if (cargando) cargando.style.display = 'none';

        medicamentos.forEach((med) => {
            const categoriaId = typeof med.id_categoria_medicamento === 'object'
                ? med.id_categoria_medicamento.id
                : med.id_categoria_medicamento;
            const categoria = categorias[categoriaId] || '';

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${med.id || ''}</td>
                <td>${textValue(med, 'nombre_medicamento') || ''}</td>
                <td>${categoria}</td>
                <td>${textValue(med, 'presentacion') || ''}</td>
                <td>${textValue(med, 'concentracion') || ''}</td>
                <td>${formatEstado(textValue(med, 'estado'))}</td>
                <td>${formatDateTime(textValue(med, 'fecha_creacion'))}</td>
                <td><button class="btn btn-sm btn-secundario" onclick="editarMedicamento(${med.id})">✏️ Editar</button><button 
                class="btn btn-sm btn-peligro" 
                onclick="eliminarMedicamento(${med.id})">🗑️ Eliminar</button></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        if (cargando) cargando.textContent = '❌ Error al cargar medicamentos.';
        console.error(error);
    }
}

async function abrirModalMedicamentos(modo) {
    limpiarErroresModales();
    if (modo === 'crear') editandoId.medicamentos = null;
    await llenarSelectCategoriasMedicamentos('nomMedicamentos');
    document.getElementById('nombre').value = '';
    document.getElementById('presentacionMedicamento').value = '';
    document.getElementById('concentracionMedicamento').value = '';
    document.getElementById('estadoMedicamento').value = 'true';
    abrirModal('modalMedicamentos');
}

async function guardarMedicamentos() {
    const data = {
        id_categoria_medicamento: document.getElementById('nomMedicamentos').value ?
         Number(document.getElementById('nomMedicamentos').value) : null,
        nombre_medicamento: document.getElementById('nombre').value.trim(),
        presentacion: document.getElementById('presentacionMedicamento').value.trim(),
        concentracion: document.getElementById('concentracionMedicamento').value.trim(),
        estado: document.getElementById('estadoMedicamento').value === 'true'
    };

    try {
        const id = editandoId.medicamentos;
        const res = await fetch(`${API_LOCAL}/medicamentos/${id ? `${id}/` : ''}`, {
            method: id ? 'PUT' : 'POST',
            headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
            body: JSON.stringify(data)
        });

        if (res.ok) {
            cerrarModal('modalMedicamentos');
            cargarMedicamentos();
            cargarDashboard();
        } else {
            document.getElementById('MedicamentosError').textContent = 'Error al guardar.';
        }
    } catch (error) { console.error(error); }
}

async function eliminarMedicamento(id) {
    if (!confirm('¿Desea eliminar este medicamento?')) return;
    try {
        const res = await fetch(`${API_LOCAL}/medicamentos/${id}/`, 
            { method: 'DELETE', headers: getAuthHeaders() });
        if (res.ok) { cargarMedicamentos(); cargarDashboard(); }
    } catch (e) { console.error(e); }
}

// ==========================================
// 6. RESULTADOS DE EXÁMENES
// ==========================================
async function cargarResultadosExamenes() {
    const cargando = document.getElementById('cargandoResultadosExamenes');
    const tbody = document.getElementById('bodyResultadosExamenes');
    if (cargando) cargando.style.display = 'block';
    if (tbody) tbody.innerHTML = '';

    try {
        const [resultadosData, contexto] = await Promise.all([
            fetchJsonOrThrow(`${API_LOCAL}/resultados-examenes/`, { headers: getAuthHeaders() }),
            cargarContextoSolicitudesResultados()
        ]);
        const resultados = safeArray(resultadosData);
        if (cargando) cargando.style.display = 'none';

        resultados.forEach((resItem) => {
            const solicitud = contexto.solicitudesPorId.get(
                String(obtenerIdRelacionado(resItem.id_solicitud_examen))
            );
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${resItem.id || ''}</td>
                <td>${solicitud
                    ? crearEtiquetaSolicitudResultado(solicitud, contexto)
                    : 'Solicitud sin información relacionada'}</td>
                <td>${textValue(resItem, 'valor_resultado') ? `${textValue(resItem, 'valor_resultado')}%` : '-'}</td>
                <td>${textValue(resItem, 'interpretacion') || ''}</td>
                <td>${formatDateTime(textValue(resItem, 'fecha_resultado'))}</td>
                <td><button class="btn btn-sm btn-secundario" onclick="editarResultado(${resItem.id})">✏️
                 Editar</button><button class="btn btn-sm btn-peligro" onclick="eliminarResultado(${resItem.id})">🗑️ Eliminar</button></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        if (cargando) cargando.textContent = '❌ Error al cargar resultados.';
        console.error(error);
    }
}

async function abrirModalResultadosExamenes(modo, id = null) {
    limpiarErroresModales();
    editandoId.resultadosExamenes = id;
    const error = document.getElementById('ResultadosExamenesError');
    error.textContent = '';
    document.getElementById('resultado').value = '';
    document.getElementById('nombre_examen').value = '';
    try {
        await llenarSelectSolicitudesExamenes('nomResultadosExamenes');
        if (id) {
            const item = await fetchJsonOrThrow(
                `${API_LOCAL}/resultados-examenes/${id}/`,
                { headers: getAuthHeaders() }
            );
            document.getElementById('nomResultadosExamenes').value =
                obtenerIdRelacionado(item.id_solicitud_examen);
            document.getElementById('resultado').value = item.valor_resultado || '';
            document.getElementById('nombre_examen').value = item.interpretacion || '';
        }
        document.getElementById('modalRETitulo').textContent =
            id ? 'Editar resultado de examen' : 'Nuevo resultado de examen';
        document.getElementById('guardarResultadoExamenBtn').textContent =
            id ? 'Guardar cambios' : 'Guardar resultado';
        abrirModal('modalResultadosExamenes');
    } catch (loadError) {
        error.textContent = 'No se pudo cargar el resultado y sus solicitudes relacionadas.';
        console.error('No se pudo abrir el formulario del resultado:', loadError);
        abrirModal('modalResultadosExamenes');
    }
}

async function guardarResultadosExamenes() {
    const error = document.getElementById('ResultadosExamenesError');
    error.textContent = '';
    const solicitud = document.getElementById('nomResultadosExamenes').value;
    const valorResultado = document.getElementById('resultado').value.trim().replace('%', '').replace(',', '.');
    if (!solicitud) {
        error.textContent = 'Seleccione una solicitud de examen.';
        return;
    }

    if (valorResultado && !Number.isFinite(Number(valorResultado))) {
        error.textContent = 'Escriba un número válido, por ejemplo 36%.';
        return;
    }

    const data = {
        id_solicitud_examen: Number(solicitud),
        valor_resultado: valorResultado || null,
        interpretacion: document.getElementById('nombre_examen').value || ''
    };

    try {
        const id = editandoId.resultadosExamenes;
        const res = await fetch(`${API_LOCAL}/resultados-examenes/${id ? `${id}/` : ''}`, {
            method: id ? 'PUT' : 'POST',
            headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
            body: JSON.stringify(data)
        });

        if (res.ok) {
            cerrarModal('modalResultadosExamenes');
            cargarResultadosExamenes();
            cargarDashboard();
        } else {
            const detalle = await res.json().catch(() => null);
            const mensaje = detalle && typeof detalle === 'object'
                ? Object.values(detalle).flat().join(' ')
                : '';
            error.textContent = mensaje || `No se pudo guardar el resultado (${res.status}).`;
        }
    } catch (exception) {
        error.textContent = 'No se pudo conectar con la API.';
        console.error(exception);
    }
}

async function eliminarResultado(id) {
    if (!confirm('¿Desea eliminar este resultado?')) return;
    try {
        const res = await fetch(`${API_LOCAL}/resultados-examenes/${id}/`,
             { method: 'DELETE', headers: getAuthHeaders() });
        if (res.ok) { cargarResultadosExamenes(); cargarDashboard(); }
    } catch (e) { console.error(e); }
}

async function cargarExamenesLaboratorio() {
    await cargarCatalogoSimple('examenes-de-laboratorio', 
        'Exámenes de laboratorio', 'bodyExamenesLaboratorio', 
        'cargandoExamenesLaboratorio', (item, index) => `
        <td>${index + 1}</td>
        <td>${item.nombre_examen || ''}</td>
        <td>${item.unidad_medida || '-'}</td>
        <td>${item.valor_referencia || '-'}</td>
        <td>${formatDateTime(item.fecha_creacion)}</td>
        <td>${formatEstado(item.estado)}</td>
        <td><button class="btn btn-sm btn-secundario" 
        onclick="editarExamenLaboratorio(${item.id})">
        ✏️ Editar</button><button 
        class="btn btn-sm 
        btn-peligro" 
        onclick="eliminarExamenLaboratorio(${item.id})">
        🗑️ Eliminar</button></td>
    `);
}

async function abrirModalExamenLaboratorio(id = null) {
    editandoId.examenesLaboratorio = id;
    const error = document.getElementById('examenLaboratorioError');
    error.textContent = '';
    document.getElementById('nombreExamenLaboratorio').value = '';
    document.getElementById('unidadExamenLaboratorio').value = '';
    document.getElementById('referenciaExamenLaboratorio').value = '';
    document.getElementById('estadoExamenLaboratorio').value = 'true';
    try {
        if (id) {
            const item = await fetchJsonOrThrow(
                `${API_LOCAL}/examenes-de-laboratorio/${id}/`,
                { headers: getAuthHeaders() }
            );
            document.getElementById('nombreExamenLaboratorio').value = item.nombre_examen || '';
            document.getElementById('unidadExamenLaboratorio').value = item.unidad_medida || '';
            document.getElementById('referenciaExamenLaboratorio').value = item.valor_referencia || '';
            document.getElementById('estadoExamenLaboratorio').value = String(item.estado);
        }
        document.getElementById('modalExamenLaboratorioTitulo').textContent =
            id ? 'Editar examen de laboratorio' : 'Nuevo examen de laboratorio';
        document.getElementById('guardarExamenLaboratorioBtn').textContent =
            id ? 'Guardar cambios' : 'Guardar examen';
        abrirModal('modalExamenLaboratorio');
    } catch (loadError) {
        error.textContent = 'No se pudo cargar el examen de laboratorio.';
        console.error('No se pudo abrir el formulario del examen:', loadError);
        abrirModal('modalExamenLaboratorio');
    }
}

async function guardarExamenLaboratorio() {
    const error = document.getElementById('examenLaboratorioError');
    error.textContent = '';
    const data = {
        nombre_examen: document.getElementById('nombreExamenLaboratorio').value.trim(),
        unidad_medida: document.getElementById('unidadExamenLaboratorio').value.trim() || null,
        valor_referencia: document.getElementById('referenciaExamenLaboratorio').value.trim() || null,
        estado: document.getElementById('estadoExamenLaboratorio').value === 'true'
    };
    if (!data.nombre_examen) {
        error.textContent = 'Escriba el nombre del examen.';
        return;
    }
    const id = editandoId.examenesLaboratorio;
    const respuesta = await fetch(`${API_LOCAL}/examenes-de-laboratorio/${id ? `${id}/` : ''}`, {
        method: id ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
        body: JSON.stringify(data)
    });
    if (!respuesta.ok) {
        error.textContent = id ? 'No se pudieron guardar los cambios.' : 'No se pudo guardar el examen.';
        return;
    }
    cerrarModal('modalExamenLaboratorio');
    cargarExamenesLaboratorio();
}

async function cargarSolicitudesExamenes() {
    const cargando = document.getElementById('cargandoSolicitudesExamenes');
    const tbody = document.getElementById('bodySolicitudesExamenes');
    if (cargando) cargando.style.display = 'block';
    if (tbody) tbody.innerHTML = '';
    try {
        const [solicitudesRespuesta, examenesRespuesta, contexto] = await Promise.all([
            fetch(`${API_LOCAL}/solicitud-de-examenes/`, { headers: getAuthHeaders() }),
            fetch(`${API_LOCAL}/examenes-de-laboratorio/`, { headers: getAuthHeaders() }),
            cargarContextoPacienteAtenciones()
        ]);
        if (!solicitudesRespuesta.ok || !examenesRespuesta.ok) {
            throw new Error('No se pudieron cargar las solicitudes o los exámenes.');
        }
        const solicitudes = safeArray(await solicitudesRespuesta.json());
        const examenes = new Map(safeArray(await examenesRespuesta.json()).map(item => [String(item.id), item]));
        const atenciones = new Map(contexto.atenciones.map(item => [String(item.id), item]));
        if (cargando) cargando.style.display = 'none';

        solicitudes.forEach((item, index) => {
            const examen = examenes.get(String(item.id_examen_de_laboratorio));
            const atencion = atenciones.get(String(item.id_atencion_cronico));
            const referenciaAtencion = atencion
                ? crearEtiquetaAtencionPaciente(atencion, contexto)
                : `Atención ${item.id_atencion_cronico || 'sin asignar'} - Paciente sin ficha`;
            const fila = document.createElement('tr');
            fila.innerHTML = `
                <td>${index + 1}</td>
                <td>${examen?.nombre_examen || 'Sin examen'}</td>
                <td>${referenciaAtencion}</td>
                <td>${item.indicaciones || ''}</td>
                <td>${formatDateTime(item.fecha_de_envio)}</td>
                <td><button class="btn btn-sm btn-secundario"
                onclick="editarSolicitudExamen(${item.id})">✏️ Editar</button><button
                class="btn btn-sm btn-peligro"
                onclick="eliminarSolicitudExamen(${item.id})">🗑️ Eliminar</button></td>
            `;
            tbody.appendChild(fila);
        });
    } catch (error) {
        if (cargando) cargando.textContent = '❌ Error al cargar solicitudes de exámenes.';
        console.error(error);
    }
}

async function editarExamenLaboratorio(id) {
    await abrirModalExamenLaboratorio(id);
}

async function eliminarExamenLaboratorio(id) {
    if (!confirm('¿Desea eliminar este examen de laboratorio?')) return;
    const respuesta = await fetch(`${API_LOCAL}/examenes-de-laboratorio/${id}/`, 
        { method: 'DELETE', headers: getAuthHeaders() });
    if (respuesta.ok) cargarExamenesLaboratorio();
}

async function editarSolicitudExamen(id) {
    await abrirModalSolicitudExamen(id);
}

async function eliminarSolicitudExamen(id) {
    if (!confirm('¿Desea eliminar esta solicitud de examen?')) return;
    const respuesta = await fetch(`${API_LOCAL}/solicitud-de-examenes/${id}/`,
         { method: 'DELETE', headers: getAuthHeaders() });
    if (respuesta.ok) cargarSolicitudesExamenes();
}

// ==========================================
// 7. GESTIÓN DE USUARIOS
// ==========================================
async function cargarUsuarios() {
    const cargando = document.getElementById('cargandoUsuarios');
    const tbody = document.getElementById('bodyUsuarios');
    if (cargando) cargando.style.display = 'block';
    if (tbody) tbody.innerHTML = '';

    try {
        const respuesta = await fetch(`${API_LOCAL}/usuarios/`, { headers: getAuthHeaders() });
        const data = await respuesta.json();
        const usuarios = safeArray(data);
        if (cargando) cargando.style.display = 'none';

        usuarios.forEach((usr, index) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${index + 1}</td>
                <td>${usr.username || ''}</td>
                <td>${usr.first_name || ''}</td>
                <td>${usr.last_name || ''}</td>
                <td>${usr.email || ''}</td>
                <td>${usr.is_active ? '🟢 Activo' : '🔴 Inactivo'}</td>
                <td>
                    <button class="btn btn-sm btn-detalles" onclick="mostrarDetallesFila(document.getElementById('tablaUsuarios'), this.closest('tr'))">👁 Ver detalles</button>
                    <button class="btn btn-sm btn-secundario" onclick="editarUsuario(${usr.id})">✏️ Editar</button>
                    <button class="btn btn-sm btn-peligro" onclick="eliminarUsuario(${usr.id})">🗑️ Eliminar</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        if (cargando) cargando.textContent = '❌ Error al cargar usuarios.';
    }
}

function abrirModalUsuarios(modo) {
    limpiarErroresModales();
    editandoId.usuarios = modo === 'crear' ? null : editandoId.usuarios;
    document.getElementById('modalUsuTitulo').textContent = modo === 'editar' ? 
    'Editar usuario' : 'Nuevo usuario';
    document.getElementById('usernameUsuario').value = '';
    document.getElementById('firstNameUsuario').value = '';
    document.getElementById('lastNameUsuario').value = '';
    document.getElementById('emailUsuario').value = '';
    document.getElementById('passwordUsuario').value = '';
    abrirModal('modalUsuarios');
}

async function guardarUsuarios() {
    const data = {
        username: document.getElementById('usernameUsuario').value.trim(),
        first_name: document.getElementById('firstNameUsuario').value.trim(),
        last_name: document.getElementById('lastNameUsuario').value.trim(),
        email: document.getElementById('emailUsuario').value.trim(),
        password: document.getElementById('passwordUsuario').value
    };

    if (!data.username || (!editandoId.usuarios && !data.password)) {
        document.getElementById('UsuariosError').textContent = 'Complete usuario y contraseña.';
        return;
    }

    if (!editandoId.usuarios && data.password.length < 8) {
        document.getElementById('UsuariosError').textContent = 'La contraseña debe tener al menos 8 caracteres.';
        return;
    }

    if (!data.password) delete data.password;

    try {
        const id = editandoId.usuarios;
        const res = await fetch(`${API_LOCAL}/usuarios/${id ? `${id}/` : ''}`, {
            method: id ? 'PUT' : 'POST',
            headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
            body: JSON.stringify(data)
        });

        if (res.ok) {
            cerrarModal('modalUsuarios');
            cargarUsuarios();
        } else {
            document.getElementById('UsuariosError').textContent = 'Error al registrar el usuario.';
        }
    } catch (error) { console.error(error); }
}

async function eliminarUsuario(id) {
    if (!confirm('¿Desea eliminar este usuario?')) return;
    try {
        const res = await fetch(`${API_LOCAL}/usuarios/${id}/`, { method: 'DELETE', headers: getAuthHeaders() });
        if (res.ok) { cargarUsuarios(); }
    } catch (e) { console.error(e); }
}

// ==========================================
// FUNCIONES AUXILIARES (SELECTS Y FILTROS)
// ==========================================
async function llenarSelectEspecialidades() {
    try {
        const respuesta = await fetch(`${API_LOCAL}/especialidades/`, { headers: getAuthHeaders() });
        const especialidades = safeArray(await respuesta.json());
        const select = document.getElementById('especialidad');
        if (!select) return;

        select.innerHTML = '<option value="">-- Seleccione especialidad --</option>';
        especialidades.forEach(especialidad => {
            select.innerHTML += `<option value="${especialidad.id}">${especialidad.nombre_especialidad}</option>`;
        });
    } catch (error) {
        console.error('Error al cargar especialidades:', error);
    }
}

async function llenarSelectCatalogosPaciente() {
    try {
        const [sectoresRespuesta, patologiasRespuesta] = await Promise.all([
            fetch(`${API_LOCAL}/sector/`, { headers: getAuthHeaders() }),
            fetch(`${API_LOCAL}/patologias-cronicas/`, { headers: getAuthHeaders() })
        ]);
        const sectores = safeArray(await sectoresRespuesta.json());
        const patologias = safeArray(await patologiasRespuesta.json());
        const sectorSelect = document.getElementById('sectorPaciente');
        const patologiaSelect = document.getElementById('patologiaPaciente');
        const listaPatologias = document.getElementById('listaPatologiasPaciente');

        if (sectorSelect) {
            sectorSelect.innerHTML = '<option value="">-- Seleccione sector --</option>';
            sectores.forEach(sector => {
                sectorSelect.innerHTML += `<option value="${sector.id}">Sector ${sector.numero_sector}: ${sector.nombre_sector}
                (${sector.zona_procedencia})</option>`;
            });
        }

        if (patologiaSelect) {
            listaPatologias.innerHTML = patologias.length
                ? patologias.map(patologia => `
                    <label class="patologia-opcion"
                     data-nombre="${patologia.nombre_patologia.toLowerCase()}">
                        <input type="checkbox" 
                        value="${patologia.id}" onchange="actualizarResumenPatologiasPaciente()">
                        <span>${patologia.nombre_patologia}</span>
                    </label>
                `).join('')
                : '<span class="campo-ayuda">No hay patologías registradas.</span>';
            document.getElementById('buscarPatologiasPaciente').value = '';
            patologiaSelect.hidden = true;
            document.getElementById('patologiasPacienteBoton').setAttribute('aria-expanded', 'false');
            actualizarResumenPatologiasPaciente();
        }
    } catch (error) {
        console.error('Error al cargar sectores y patologías:', error);
    }
}

async function llenarSelectPacientesYMedicos(idSelectPaciente, idSelectMedico) {
    try {
        const resPac = await fetch(`${API_LOCAL}/pacientes/`, { headers: getAuthHeaders() });
        const pacData = await resPac.json();
        const pacientes = safeArray(pacData);
        const selPac = document.getElementById(idSelectPaciente);
        if (selPac) {
            selPac.innerHTML = '<option value="">-- Seleccione Paciente --</option>';
            pacientes.forEach(p => {
                selPac.innerHTML += `<option value="${p.id}">${textValue(p, 'nombre', 'nombres')} ${textValue(p, 'apellidos')}</option>`;
            });
        }

        const resMed = await fetch(`${API_LOCAL}/medicos/`, { headers: getAuthHeaders() });
        const medData = await resMed.json();
        const medicos = safeArray(medData);
        const selMed = document.getElementById(idSelectMedico);
        if (selMed) {
            selMed.innerHTML = '<option value="">-- Seleccione Médico --</option>';
            medicos.forEach(m => {
                selMed.innerHTML += `<option value="${m.id}">Dr(a). ${textValue(m, 'nombre')} ${textValue(m, 'apellidos')} (${m.codigo_minsa || ''})</option>`;
            });
        }
    } catch (e) {
        console.error('Error al llenar selects de pacientes y médicos:', e);
    }
}

async function llenarSelectCategoriasMedicamentos(idSelect) {
    try {
        const res = await fetch(`${API_LOCAL}/categoria-medicamento/`, { headers: getAuthHeaders() });
        const data = await res.json();
        const categorias = safeArray(data);
        const select = document.getElementById(idSelect);
        if (!select) return;

        select.innerHTML = '<option value="">-- Seleccione Categoría --</option>';
            categorias.forEach(item => {
            select.innerHTML += `<option value="${item.id}">${textValue(item, 'nombre_categoria')}</option>`;
        });
    } catch (e) {
        console.error('Error al cargar categorías:', e);
    }
}

async function llenarSelectSolicitudesExamenes(idSelect) {
    const contexto = await cargarContextoSolicitudesResultados();
    const select = document.getElementById(idSelect);
    if (!select) return;

    select.innerHTML = '<option value="">-- Seleccione examen, atención y paciente --</option>';
    contexto.solicitudes.forEach(item => {
        const option = document.createElement('option');
        option.value = item.id;
        option.textContent = crearEtiquetaSolicitudResultado(item, contexto);
        select.appendChild(option);
    });
}

function configurarBuscadores() {
    configurarFiltroInput('buscarPacientes', 'tablaPacientes');
    configurarFiltroInput('buscarSectores', 'tablaSectores');
    configurarFiltroInput('buscarPatologiasCronicas', 'tablaPatologiasCronicas');
    configurarFiltroInput('buscarPacientesPatologias', 'tablaPacientesPatologias');
    configurarFiltroInput('buscarEspecialidades', 'tablaEspecialidades');
    configurarFiltroInput('buscarMedicos', 'tablaMedicos');
    configurarFiltroInput('buscarCitasMedicas', 'tablaCitasMedicas');
    configurarFiltroInput('buscarTratamientos', 'tablaTratamientos');
    configurarFiltroInput('buscarDetalleTratamiento', 'tablaDetalleTratamiento');
    configurarFiltroInput('buscarMedicamentos', 'tablaMedicamentos');
    configurarFiltroInput('buscarCategoriasMedicamentos', 'tablaCategoriasMedicamentos');
    configurarFiltroInput('buscarResultadosExamenes', 'tablaResultadosExamenes');
    configurarFiltroInput('buscarExamenesLaboratorio', 'tablaExamenesLaboratorio');
    configurarFiltroInput('buscarSolicitudesExamenes', 'tablaSolicitudesExamenes');
    configurarFiltroInput('buscarUsuarios', 'tablaUsuarios');
    configurarOrdenYSeleccion();
}

function configurarFiltroInput(idInput, idTabla) {
    const input = document.getElementById(idInput);
    if (!input) return;

    input.addEventListener('keyup', () => {
        const filtro = input.value.toLowerCase();
        const filas = document.querySelectorAll(`#${idTabla} tbody tr`);

        filas.forEach(fila => {
            const textoFila = fila.textContent.toLowerCase();
            fila.style.display = textoFila.includes(filtro) ? '' : 'none';
        });
        actualizarNumeracion(document.querySelector(`#${idTabla} tbody`));
    });
}

function actualizarNumeracion(cuerpo) {
    if (!cuerpo) return;
    let numero = 1;
    cuerpo.querySelectorAll('tr').forEach(fila => {
        if (fila.style.display === 'none') return;
        if (fila.cells[0]) fila.cells[0].textContent = numero++;
    });
}

function configurarOrdenYSeleccion() {
    document.querySelectorAll('.tabla').forEach(tabla => {
        const contenedor = tabla.closest('.tabla-contenedor');
        const cabecera = contenedor?.querySelector('.tabla-cabecera');
        const cuerpo = tabla.querySelector('tbody');
        if (!cabecera || !cuerpo || cabecera.querySelector('.orden-tabla')) return;
        const indiceFecha = Array.from(tabla.tHead?.rows[0]?.cells || [])
            .findIndex(celda => /cread|fecha.*ingres|fecha.*registro/i.test(celda.textContent));

        const orden = document.createElement('select');
        orden.className = 'orden-tabla';
        orden.setAttribute('aria-label', 'Ordenar listado');
        orden.innerHTML = `
            <option value="original">Orden original</option>
            <option value="az">Nombre A-Z</option>
            <option value="za">Nombre Z-A</option>
            <option value="recientes">Más recientes</option>
            <option value="antiguos">Más antiguos</option>
        `;
        const buscador = cabecera.querySelector('.buscador');
        if (buscador) {
            const filtros = document.createElement('div');
            filtros.className = 'filtros-tabla';
            cabecera.insertBefore(filtros, buscador);
            filtros.appendChild(buscador);
        }

        const botonNuevo = cabecera.querySelector('.btn-primario');
        if (botonNuevo) {
            const acciones = document.createElement('div');
            acciones.className = 'acciones-tabla';
            cabecera.insertBefore(acciones, botonNuevo);
            acciones.appendChild(orden);
            acciones.appendChild(botonNuevo);
        } else {
            cabecera.appendChild(orden);
        }

        orden.addEventListener('change', () => {
            const filas = Array.from(cuerpo.querySelectorAll('tr'));
            if (orden.value === 'original') {
                filas.sort((filaA, filaB) =>
                    Number(filaA.dataset.ordenOriginal) - Number(filaB.dataset.ordenOriginal));
            } else {
                filas.sort((filaA, filaB) => compararFilas(filaA, filaB, orden.value, indiceFecha));
            }
            filas.forEach(fila => cuerpo.appendChild(fila));
            actualizarNumeracion(cuerpo);
        });

        const observarFilas = () => {
            cuerpo.querySelectorAll('tr').forEach((fila, indice) => {
                if (!fila.dataset.ordenOriginal) fila.dataset.ordenOriginal = indice;
                if (fila.dataset.seleccionConfigurada) return;
                fila.dataset.seleccionConfigurada = 'true';
                fila.addEventListener('click', evento => {
                    if (evento.target.closest('button, a, input, select')) return;
                    cuerpo.querySelectorAll('tr.fila-seleccionada').forEach(filaActiva =>
                        filaActiva.classList.remove('fila-seleccionada'));
                    fila.classList.add('fila-seleccionada');
                });

                const celdaAcciones = fila.lastElementChild;
                if (celdaAcciones?.tagName === 'TD' && !fila.dataset.detalleConfigurado) {
                    const botonesActuales = Array.from(celdaAcciones.querySelectorAll('button'));
                    const yaTieneDetalles = botonesActuales.some(boton => boton.classList.contains('btn-detalles'));

                    if (!yaTieneDetalles && botonesActuales.length > 0) {
                        const botonDetalles = document.createElement('button');
                        botonDetalles.type = 'button';
                        botonDetalles.className = 'btn btn-sm btn-detalles';
                        botonDetalles.textContent = '👁 Ver detalles';
                        botonDetalles.addEventListener('click', evento => {
                            evento.stopPropagation();
                            mostrarDetallesFila(tabla, fila);
                        });
                        botonesActuales.unshift(botonDetalles);
                    }

                    if (botonesActuales.length > 0) {
                        const barraAcciones = document.createElement('div');
                        barraAcciones.className = 'barra-acciones';
                        botonesActuales.forEach(boton => {
                            boton.title = boton.classList.contains('btn-detalles')
                                ? 'Ver detalles'
                                : boton.classList.contains('btn-peligro')
                                    ? 'Eliminar'
                                    : 'Editar';
                            boton.setAttribute('aria-label', boton.title);
                            barraAcciones.appendChild(boton);
                        });
                        celdaAcciones.replaceChildren(barraAcciones);
                    }

                    fila.dataset.detalleConfigurado = 'true';
                }
            });
            actualizarNumeracion(cuerpo);
        };

        observarFilas();
        new MutationObserver(observarFilas).observe(cuerpo, { childList: true });
    });
}

function mostrarDetallesFila(tabla, fila) {
    let modal = document.getElementById('modalDetalles');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'modalDetalles';
        modal.className = 'modal-overlay modal-detalles-overlay';
        modal.innerHTML = `
            <div class="modal modal-detalles">
                <div class="modal-header">
                    <div>
                        <span class="detalles-marca">Pacien<span>Care</span></span>
                        <h3 id="modalDetallesTitulo">Detalles del registro</h3>
                    </div>
                    <button type="button" aria-label="Cerrar detalles">✕</button>
                </div>
                <div class="modal-body modal-detalles-body" id="modalDetallesCuerpo"></div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secundario btn-imprimir-detalles">⬇ Descargar PDF</button>
                    <button type="button" class="btn btn-primario btn-cerrar-detalles">Cerrar</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        modal.querySelector('.modal-header button').addEventListener('click', () => cerrarModal('modalDetalles'));
        modal.querySelector('.btn-imprimir-detalles').addEventListener('click', descargarDetallesPdf);
        modal.querySelector('.btn-cerrar-detalles').addEventListener('click', () => cerrarModal('modalDetalles'));
    }

    const nombresSecciones = {
        pacientes: 'Paciente', sector: 'Sector', patologiasCronicas: 'Patología crónica',
        pacientePatologia: 'Paciente y patología', medicos: 'Médico', especialidades: 'Especialidad',
        citasmedicas: 'Atención médica', tratamientos: 'Tratamiento', detalleTratamiento: 'Detalle de tratamiento',
        medicamentos: 'Medicamento', categoriasMedicamentos: 'Categoría de medicamento',
        resultadosExamenes: 'Resultado de examen', examenesLaboratorio: 'Examen de laboratorio',
        solicitudesExamenes: 'Solicitud de examen', usuarios: 'Usuario'
    };
    const seccion = tabla.closest('.seccion')?.id;
    const titulo = document.getElementById('modalDetallesTitulo');
    const cuerpo = document.getElementById('modalDetallesCuerpo');
    titulo.textContent = `Detalles de ${nombresSecciones[seccion] || 'registro'}`;
    cuerpo.innerHTML = `
        <div class="detalle-documento">
            <div class="detalle-documento-cabecera">
                <div class="detalle-documento-marca">Pacien<span>Care</span></div>
                <div class="detalle-documento-tipo">
                    <span>Registro clínico</span>
                    <strong>Información detallada</strong>
                </div>
            </div>
            <div class="detalle-documento-linea"></div>
            <div class="detalle-documento-tabla-wrap">
                <table class="detalle-documento-tabla">
                    <thead><tr><th>Campo</th><th>Información</th></tr></thead>
                    <tbody id="detalleDocumentoFilas"></tbody>
                </table>
            </div>
        </div>
    `;

    const encabezados = Array.from(tabla.tHead?.rows[0]?.cells || []);
    const valores = Array.from(fila.cells);
    const filasDetalle = document.getElementById('detalleDocumentoFilas');
    encabezados.slice(0, -1).forEach((encabezado, indice) => {
        const detalle = document.createElement('tr');
        if (indice === 0) detalle.className = 'detalle-documento-principal';
        const etiqueta = document.createElement('th');
        etiqueta.scope = 'row';
        etiqueta.textContent = encabezado.textContent.trim();
        const valor = document.createElement('td');
        valor.textContent = valores[indice]?.textContent.trim() || 'Sin información';
        detalle.append(etiqueta, valor);
        filasDetalle.appendChild(detalle);
    });

    abrirModal('modalDetalles');
}

async function descargarDetallesPdf() {
    const titulo = document.getElementById('modalDetallesTitulo')?.textContent || 'Detalles del registro';
    const modalDocumento = document.querySelector('#modalDetalles .modal-detalles');
    if (window.html2pdf && modalDocumento) {
        const pie = modalDocumento.querySelector('.modal-footer');
        const cerrar = modalDocumento.querySelector('.modal-header button');
        const displayPie = pie?.style.display || '';
        const visibilityCerrar = cerrar?.style.visibility || '';
        if (pie) pie.style.display = 'none';
        if (cerrar) cerrar.style.visibility = 'hidden';
        try {
            await window.html2pdf()
                .set({
                    margin: 10,
                    filename: `${titulo.replace(/\s+/g, '_')}.pdf`,
                    image: { type: 'jpeg', quality: 0.98 },
                    html2canvas: { scale: 2, useCORS: true, backgroundColor: '#ffffff' },
                    jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
                })
                .from(modalDocumento)
                .save();
        } finally {
            if (pie) pie.style.display = displayPie;
            if (cerrar) cerrar.style.visibility = visibilityCerrar;
        }
        return;
    }
    const filas = Array.from(document.querySelectorAll('#detalleDocumentoFilas tr')).map(fila => {
        const celdas = Array.from(fila.cells);
        return [celdas[0]?.textContent.trim() || '', celdas[1]?.textContent.trim() || ''];
    });
    const limpiarTexto = texto => texto.normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/[^\x20-\x7E]/g, '?')
        .replace(/[\\()]/g, caracter => `\\${caracter}`)
        .replace(/[\r\n]+/g, ' ');
    const limitarTexto = texto => {
        const limpio = limpiarTexto(texto);
        return limpio.length > 58 ? `${limpio.slice(0, 55)}...` : limpio;
    };
    const textoPdf = (texto, x, y, tamano, fuente = 'F1', color = '0.12 0.18 0.25') => [
        `${color} rg`,
        'BT',
        `/${fuente} ${tamano} Tf`,
        `${x} ${y} Td`,
        `(${limitarTexto(texto)}) Tj`,
        'ET'
    ];
    const comandos = [
        '0.98 0.99 1 rg',
        '45 45 505 752 re f',
        '0.12 0.30 0.51 rg',
        '45 760 505 3 re f',
        ...textoPdf('PacienCare', 60, 725, 20, 'F2', '0.12 0.30 0.51'),
        ...textoPdf(titulo, 60, 695, 15, 'F2'),
        ...textoPdf('Registro clinico', 390, 725, 9, 'F1', '0.39 0.47 0.56'),
        ...textoPdf('Informacion detallada', 390, 707, 10, 'F2'),
        '0.79 0.84 0.89 RG',
        '60 682 m 535 682 l S',
        '0.94 0.96 0.98 rg',
        '60 638 475 30 re f',
        '0.79 0.84 0.89 RG',
        '60 638 475 30 re S',
        ...textoPdf('Campo', 72, 649, 9, 'F2', '0.39 0.47 0.56'),
        ...textoPdf('Informacion', 250, 649, 9, 'F2', '0.39 0.47 0.56')
    ];
    filas.forEach(([campo, valor], indice) => {
        const y = 606 - (indice * 32);
        if (indice % 2 === 0) {
            comandos.push('0.97 0.98 0.99 rg', `60 ${y - 9} 475 32 re f`);
        }
        comandos.push('0.84 0.88 0.92 RG', `60 ${y - 9} m 535 ${y - 9} l S`);
        comandos.push(...textoPdf(campo, 72, y, 9, 'F2', '0.39 0.47 0.56'));
        comandos.push(...textoPdf(valor, 250, y, 9, 'F1'));
    });
    comandos.push(
        '0.84 0.88 0.92 RG',
        `60 ${574 - (filas.length * 32)} m 535 ${574 - (filas.length * 32)} l S`,
        ...textoPdf('PacienCare - Documento generado desde el sistema clinico', 60, 70, 8, 'F1', '0.39 0.47 0.56')
    );
    const logo = await prepararLogoPdf();
    if (logo) comandos.splice(5, 0, 'q', '65 0 0 65 465 690 cm', '/Im1 Do', 'Q');
    const contenido = comandos.join('\n');
    const ascii = texto => new TextEncoder().encode(texto);
    const contenidoBytes = ascii(contenido).length;
    const objetos = [
        [1, '<< /Type /Catalog /Pages 2 0 R >>'],
        [2, '<< /Type /Pages /Kids [3 0 R] /Count 1 >>'],
        [3, '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R /F2 5 0 R >> /XObject << /Im1 6 0 R >> >> /Contents 7 0 R >>'],
        [4, '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>'],
        [5, '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>'],
        [6, logo
            ? [`<< /Type /XObject /Subtype /Image /Width ${logo.width} /Height ${logo.height} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${logo.bytes.length} >>\nstream\n`, logo.bytes, '\nendstream']
            : '<< /Length 0 >>\nstream\n\nendstream'],
        [7, `<< /Length ${contenidoBytes} >>\nstream\n${contenido}\nendstream`]
    ];
    const partes = [ascii('%PDF-1.4\n')];
    const offsets = [0];
    let posicion = partes[0].length;
    objetos.forEach(([numero, objeto]) => {
        offsets[numero] = posicion;
        const cabecera = ascii(`${numero} 0 obj\n`);
        partes.push(cabecera);
        posicion += cabecera.length;
        if (Array.isArray(objeto)) {
            objeto.forEach(parte => {
                const bytes = typeof parte === 'string' ? ascii(parte) : parte;
                partes.push(bytes);
                posicion += bytes.length;
            });
        } else {
            const bytes = ascii(objeto);
            partes.push(bytes);
            posicion += bytes.length;
        }
        const cierre = ascii('\nendobj\n');
        partes.push(cierre);
        posicion += cierre.length;
    });
    const posicionXref = posicion;
    let xref = `xref\n0 ${objetos.length + 1}\n0000000000 65535 f \n`;
    for (let indice = 1; indice <= objetos.length; indice++) {
        xref += `${String(offsets[indice]).padStart(10, '0')} 00000 n \n`;
    }
    xref += `trailer\n<< /Size ${objetos.length + 1} /Root 1 0 R >>\nstartxref\n${posicionXref}\n%%EOF`;
    partes.push(ascii(xref));
    const archivo = new Blob(partes, { type: 'application/pdf' });
    const enlace = document.createElement('a');
    enlace.href = URL.createObjectURL(archivo);
    enlace.download = `${limpiarTexto(titulo).replace(/\s+/g, '_')}.pdf`;
    enlace.click();
    URL.revokeObjectURL(enlace.href);
}

async function prepararLogoPdf() {
    try {
        const respuesta = await fetch('/static/paci.png');
        const blob = await respuesta.blob();
        const url = URL.createObjectURL(blob);
        const imagen = await new Promise((resolver, rechazar) => {
            const elemento = new Image();
            elemento.onload = () => resolver(elemento);
            elemento.onerror = rechazar;
            elemento.src = url;
        });
        URL.revokeObjectURL(url);
        const lienzo = document.createElement('canvas');
        lienzo.width = 180;
        lienzo.height = 180;
        const contexto = lienzo.getContext('2d');
        contexto.fillStyle = '#ffffff';
        contexto.fillRect(0, 0, lienzo.width, lienzo.height);
        contexto.drawImage(imagen, 0, 0, lienzo.width, lienzo.height);
        const base64 = lienzo.toDataURL('image/jpeg', 0.82).split(',')[1];
        const bytes = Uint8Array.from(atob(base64), caracter => caracter.charCodeAt(0));
        return { bytes, width: lienzo.width, height: lienzo.height };
    } catch (error) {
        console.error('No se pudo cargar el logo del PDF:', error);
        return null;
    }
}

function compararFilas(filaA, filaB, criterio, indiceFecha = -1) {
    const celdasA = Array.from(filaA.cells);
    const celdasB = Array.from(filaB.cells);
    const textoA = filaA.textContent.trim().toLowerCase();
    const textoB = filaB.textContent.trim().toLowerCase();

    if (criterio === 'recientes' || criterio === 'antiguos') {
        const valorFechaA = filaA.dataset.fechaCreacion ||
            (indiceFecha >= 0 ? celdasA[indiceFecha]?.textContent || '' : textoA);
        const valorFechaB = filaB.dataset.fechaCreacion ||
            (indiceFecha >= 0 ? celdasB[indiceFecha]?.textContent || '' : textoB);
        const fechaA = extraerFechaFila(valorFechaA);
        const fechaB = extraerFechaFila(valorFechaB);
        const diferencia = fechaA - fechaB;
        if (diferencia === 0) {
            return Number(filaA.dataset.ordenOriginal) - Number(filaB.dataset.ordenOriginal);
        }
        return criterio === 'recientes' ? -diferencia : diferencia;
    }

    const nombreA = (celdasA[1]?.textContent || celdasA[0]?.textContent || '').trim();
    const nombreB = (celdasB[1]?.textContent || celdasB[0]?.textContent || '').trim();
    const diferencia = nombreA.localeCompare(nombreB, 'es', { sensitivity: 'base' });
    return criterio === 'za' ? -diferencia : diferencia;
}

function extraerFechaFila(textoFila) {
    const fechas = [];
    const fechasIso = textoFila.match(/\d{4}-\d{1,2}-\d{1,2}/g) || [];
    fechasIso.forEach(fecha => {
        const [anio, mes, dia] = fecha.split('-');
        fechas.push(new Date(`${anio}-${mes.padStart(2, '0')}-${dia.padStart(2, '0')}`).getTime());
    });

    const fechasLatinas = textoFila.match(/\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4}/g) || [];
    fechasLatinas.forEach(fecha => {
        const partes = fecha.split(/[\/-]/);
        const dia = partes[0].padStart(2, '0');
        const mes = partes[1].padStart(2, '0');
        const anio = partes[2].length === 2 ? `20${partes[2]}` : partes[2];
        fechas.push(new Date(`${anio}-${mes}-${dia}`).getTime());
    });

    return fechas.filter(Number.isFinite).sort((fechaA, fechaB) => fechaB - fechaA)[0] || 0;
}

function obtenerTokenCSRF() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, 10) === ('csrftoken=')) {
                cookieValue = decodeURIComponent(cookie.substring(10));
                break;
            }
        }
    }
    return cookieValue;
}

async function llenarSelectMedicos(idSelect) {
    const respuesta = await fetch(`${API_LOCAL}/medicos/`, { headers: getAuthHeaders() });
    const medicos = safeArray(await respuesta.json());
    const select = document.getElementById(idSelect);
    if (!select) return;

    select.innerHTML = '<option value="">-- Seleccione Médico --</option>';
    medicos.forEach(medico => {
        select.innerHTML += `<option value="${medico.id}">Dr(a). ${textValue(medico, 'nombre')} ${textValue(medico, 'apellidos')}</option>`;
    });
}

async function llenarSelectPacientesPatologias(idSelect) {
    const [pacientesRespuesta, relacionesRespuesta, patologiasRespuesta] = await Promise.all([
        fetch(`${API_LOCAL}/pacientes/`, { headers: getAuthHeaders() }),
        fetch(`${API_LOCAL}/paciente-patologia/`, { headers: getAuthHeaders() }),
        fetch(`${API_LOCAL}/patologias-cronicas/`, { headers: getAuthHeaders() })
    ]);
    const pacientes = safeArray(await pacientesRespuesta.json());
    const relaciones = safeArray(await relacionesRespuesta.json());
    const patologias = Object.fromEntries(safeArray(await patologiasRespuesta.json()).map(item => [item.id, item.nombre_patologia]));
    const nombres = Object.fromEntries(pacientes.map(item => [item.id, `${item.nombre} ${item.apellidos}`]));
    const select = document.getElementById(idSelect);
    if (!select) return;

    select.innerHTML = '<option value="">-- Seleccione paciente y patología --</option>';
    const relacionesPorPaciente = {};
    relaciones.forEach(relacion => {
        if (!relacionesPorPaciente[relacion.id_paciente]) relacionesPorPaciente[relacion.id_paciente] = [];
        relacionesPorPaciente[relacion.id_paciente].push(relacion);
    });
    relacionesAtencionPorPaciente = relacionesPorPaciente;

    Object.entries(relacionesPorPaciente).forEach(([pacienteId, relacionesPaciente]) => {
        const opcion = document.createElement('option');
        opcion.value = pacienteId;
        opcion.textContent = `${nombres[pacienteId] || 'Paciente'} — ${relacionesPaciente.map(relacion => patologias[relacion.id_patologia_cronica] || 'Patología').join(', ')}`;
        select.appendChild(opcion);
    });
}

async function editarMedicamento(id) {
    const respuesta = await fetch(`${API_LOCAL}/medicamentos/${id}/`, { headers: getAuthHeaders() });
    const item = await respuesta.json();
    await abrirModalMedicamentos('editar');
    document.getElementById('nombre').value = item.nombre_medicamento || '';
    document.getElementById('presentacionMedicamento').value = item.presentacion || '';
    document.getElementById('concentracionMedicamento').value = item.concentracion || '';
    document.getElementById('estadoMedicamento').value = String(item.estado);
    document.getElementById('nomMedicamentos').value = item.id_categoria_medicamento;
    editandoId.medicamentos = id;
}

async function editarUsuario(id) {
    const respuesta = await fetch(`${API_LOCAL}/usuarios/${id}/`, { headers: getAuthHeaders() });
    if (!respuesta.ok) return;
    const usuario = await respuesta.json();
    editandoId.usuarios = id;
    abrirModalUsuarios('editar');
    document.getElementById('usernameUsuario').value = usuario.username || '';
    document.getElementById('firstNameUsuario').value = usuario.first_name || '';
    document.getElementById('lastNameUsuario').value = usuario.last_name || '';
    document.getElementById('emailUsuario').value = usuario.email || '';
}

async function editarPatologiaCronica(id) {
    const respuesta = await fetch(`${API_LOCAL}/patologias-cronicas/${id}/`, { headers: getAuthHeaders() });
    const item = await respuesta.json();

    abrirModalPatologiaCronica(id);
    document.getElementById('nombrePatologiaCronica').value = item.nombre_patologia || '';
    document.getElementById('estadoPatologiaCronica').value = String(item.estado);
}

async function eliminarPatologiaCronica(id) {
    if (!confirm('¿Desea eliminar esta patología?')) return;
    const respuesta = await fetch(`${API_LOCAL}/patologias-cronicas/${id}/`, { method: 'DELETE', headers: getAuthHeaders() });
    if (respuesta.ok) cargarPatologiasCronicas();
}

async function editarPacientePatologia(id) {
    await abrirModalPacientePatologia(id);
}

async function eliminarPacientePatologia(id) {
    if (!confirm('¿Desea eliminar esta relación?')) return;
    const respuesta = await fetch(`${API_LOCAL}/paciente-patologia/${id}/`, { method: 'DELETE', headers: getAuthHeaders() });
    if (respuesta.ok) cargarPacientesPatologias();
}

async function editarCita(id) {
    await abrirModalCitasMedicas('editar', id);
}

async function editarResultado(id) {
    await abrirModalResultadosExamenes('editar', id);
}

async function abrirModalSolicitudExamen(id = null) {
    editandoId.solicitudExamen = id;
    const error = document.getElementById('solicitudExamenError');
    error.textContent = '';
    try {
        const headers = { headers: getAuthHeaders() };
        const requests = [
            fetchJsonOrThrow(`${API_LOCAL}/examenes-de-laboratorio/`, headers),
            cargarContextoPacienteAtenciones()
        ];
        if (id) requests.push(fetchJsonOrThrow(`${API_LOCAL}/solicitud-de-examenes/${id}/`, headers));
        const [examenes, contexto, solicitud] = await Promise.all(requests);
        window.atencionesSolicitudExamen = contexto.atenciones;
        window.contextoSolicitudExamen = contexto;

        const examenSelect = document.getElementById('examenSolicitud');
        examenSelect.innerHTML = '<option value="">-- Seleccione examen de laboratorio --</option>';
        safeArray(examenes).forEach(item => {
            examenSelect.innerHTML += `<option value="${item.id}">${item.nombre_examen} (${item.unidad_medida || 'sin unidad'})</option>`;
        });
        const fechaInput = document.getElementById('fechaSolicitudExamen');
        if (!fechaInput.dataset.configurado) {
            fechaInput.dataset.configurado = 'true';
            fechaInput.addEventListener('change', () => cargarAtencionesSolicitudPorFecha(fechaInput.value));
        }
        if (solicitud) {
            const atencion = contexto.atenciones.find(item =>
                String(item.id) === String(solicitud.id_atencion_cronico));
            fechaInput.value = atencion ? fechaAtencionISO(atencion.fecha_atencion) : fechaLocalISO();
        }
        await cargarAtencionesSolicitudPorFecha(solicitud ? fechaInput.value : null);
        document.getElementById('examenSolicitud').value = solicitud?.id_examen_de_laboratorio || '';
        document.getElementById('atencionSolicitud').value = solicitud?.id_atencion_cronico || '';
        document.getElementById('indicacionesSolicitud').value = solicitud?.indicaciones || '';
        document.getElementById('modalSolicitudExamenTitulo').textContent =
            id ? 'Editar solicitud de examen' : 'Nueva solicitud de examen';
        document.getElementById('guardarSolicitudExamenBtn').textContent =
            id ? 'Guardar cambios' : 'Guardar solicitud';
        abrirModal('modalSolicitudExamen');
    } catch (loadError) {
        console.error('No se pudo cargar la solicitud de examen:', loadError);
        error.textContent = 'No se pudo cargar la información necesaria. Intente de nuevo.';
        document.getElementById('examenSolicitud').value = '';
        document.getElementById('atencionSolicitud').innerHTML =
            '<option value="">No se pudieron cargar las atenciones</option>';
        abrirModal('modalSolicitudExamen');
    }
}

function obtenerIdRelacionado(valor) {
    return valor && typeof valor === 'object' ? valor.id : valor;
}

function crearEtiquetaAtencionSolicitud(item) {
    return crearEtiquetaAtencionPaciente(item, window.contextoSolicitudExamen);
}

function cargarAtencionesSolicitudPorFecha(fecha = null) {
    const fechaInput = document.getElementById('fechaSolicitudExamen');
    const atencionSelect = document.getElementById('atencionSolicitud');
    let fechaElegida = fecha || fechaInput.value || fechaLocalISO();
    const fechasDisponibles = window.atencionesSolicitudExamen
        .map(item => fechaAtencionISO(item.fecha_atencion))
        .filter(Boolean)
        .sort();
    if (!fecha && fechasDisponibles.length && !fechasDisponibles.includes(fechaElegida)) {
        fechaElegida = fechasDisponibles[fechasDisponibles.length - 1];
    }
    fechaInput.value = fechaElegida;
    atencionSelect.innerHTML = '<option value="">-- Seleccione atención y paciente --</option>';
    const atencionesDelDia = window.atencionesSolicitudExamen.filter(item =>
        fechaAtencionISO(item.fecha_atencion) === fechaElegida);
    atencionesDelDia.forEach(item => {
        const option = document.createElement('option');
        option.value = item.id;
        option.textContent = crearEtiquetaAtencionSolicitud(item);
        atencionSelect.appendChild(option);
    });
    if (!atencionesDelDia.length) {
        atencionSelect.innerHTML = '<option value="">-- No hay atenciones para este día --</option>';
    }
}

async function guardarSolicitudExamen() {
    const error = document.getElementById('solicitudExamenError');
    error.textContent = '';
    const data = {
        id_examen_de_laboratorio: Number(document.getElementById('examenSolicitud').value),
        id_atencion_cronico: Number(document.getElementById('atencionSolicitud').value),
        indicaciones: document.getElementById('indicacionesSolicitud').value.trim()
    };
    if (!data.id_examen_de_laboratorio || !data.id_atencion_cronico || !data.indicaciones) {
        error.textContent = 'Seleccione examen, atención y escriba las indicaciones.';
        return;
    }
    const id = editandoId.solicitudExamen;
    const respuesta = await fetch(`${API_LOCAL}/solicitud-de-examenes/${id ? `${id}/` : ''}`, {
        method: id ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
        body: JSON.stringify(data)
    });
    if (!respuesta.ok) {
        error.textContent = id ? 'No se pudieron guardar los cambios.' : 'No se pudo guardar la solicitud.';
        return;
    }
    cerrarModal('modalSolicitudExamen');
    cargarSolicitudesExamenes();
}

async function verificarSesion() {
    const token = localStorage.getItem('accessToken');
    if (!token) {
        window.location.replace(LOGIN_URL);
        return false;
    }

    try {
        const respuesta = await fetch(`${API_LOCAL}/pacientes/`, {
            headers: getAuthHeaders()
        });
        if (respuesta.status === 401 || respuesta.status === 403) {
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            window.location.replace(LOGIN_URL);
            return false;
        }
        return respuesta.ok;
    } catch (error) {
        console.error('No se pudo verificar la sesión:', error);
        return true;
    }
}