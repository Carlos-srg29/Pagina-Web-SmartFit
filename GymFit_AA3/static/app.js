let currentUser = null;
let clientRoutine = null;
let currentExerciseIndex = 0;
let trainerClients = [];
let adminUsers = [];
let adminTrainers = [];
let toastTimer = null;

const $ = (id) => document.getElementById(id);

function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, (char) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[char]));
}

function showToast(message, isError = false) {
    const toast = $('toast');
    toast.textContent = message;
    toast.classList.toggle('error', isError);
    toast.classList.remove('hidden');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.add('hidden'), 3400);
}

async function api(path, options = {}) {
    const config = { credentials: 'same-origin', ...options };
    if (config.body && typeof config.body !== 'string') {
        config.headers = { 'Content-Type': 'application/json', ...(config.headers || {}) };
        config.body = JSON.stringify(config.body);
    }
    const response = await fetch(path, config);
    let result;
    try {
        result = await response.json();
    } catch (_error) {
        throw new Error('El servidor respondió con un formato inesperado.');
    }
    if (!response.ok || result.success === false) {
        if (response.status === 401 && path !== '/api/login') {
            currentUser = null;
            showPublicView();
        }
        throw new Error(result.message || 'No se pudo completar la solicitud.');
    }
    return result;
}

function showPublicView() {
    $('public-view').classList.remove('hidden');
    $('app-view').classList.add('hidden');
    $('header-user').classList.add('hidden');
    ['client-view', 'trainer-view', 'admin-view'].forEach((id) => $(id).classList.add('hidden'));
    $('login-form').reset();
    $('register-form').reset();
    setAuthTab('login');
}

function showDashboard() {
    $('public-view').classList.add('hidden');
    $('app-view').classList.remove('hidden');
    $('header-user').classList.remove('hidden');
    $('header-user').textContent = `${currentUser.nombre} · ${roleName(currentUser.rol)}`;
    ['client-view', 'trainer-view', 'admin-view'].forEach((id) => $(id).classList.add('hidden'));

    if (currentUser.rol === 'cliente') {
        $('role-eyebrow').textContent = 'ESPACIO DEL CLIENTE';
        $('dashboard-title').textContent = `Hola, ${currentUser.nombre}`;
        $('dashboard-subtitle').textContent = 'Organiza tu entrenamiento y consulta cómo vas avanzando.';
        $('client-view').classList.remove('hidden');
        fillClientProfile();
        loadClientDashboard();
    } else if (currentUser.rol === 'entrenador') {
        $('role-eyebrow').textContent = 'ESPACIO DEL ENTRENADOR';
        $('dashboard-title').textContent = `Bienvenido, ${currentUser.nombre}`;
        $('dashboard-subtitle').textContent = 'Consulta la información y el avance de tus clientes asignados.';
        $('trainer-view').classList.remove('hidden');
        loadTrainerDashboard();
    } else {
        $('role-eyebrow').textContent = 'ADMINISTRACIÓN GENERAL';
        $('dashboard-title').textContent = `Hola, ${currentUser.nombre}`;
        $('dashboard-subtitle').textContent = 'Administra las cuentas y revisa la información general de GymFit.';
        $('admin-view').classList.remove('hidden');
        loadAdminDashboard();
    }
}

function roleName(role) {
    return ({ cliente: 'Cliente', entrenador: 'Entrenador', admin: 'Administrador' })[role] || 'Usuario';
}

function setAuthTab(tab) {
    document.querySelectorAll('[data-auth-tab]').forEach((button) => {
        const active = button.dataset.authTab === tab;
        button.classList.toggle('active', active);
        button.setAttribute('aria-selected', active ? 'true' : 'false');
    });
    $('login-form').classList.toggle('hidden', tab !== 'login');
    $('register-form').classList.toggle('hidden', tab !== 'register');
    $('auth-message').classList.add('hidden');
}

document.querySelectorAll('[data-auth-tab]').forEach((button) => {
    button.addEventListener('click', () => setAuthTab(button.dataset.authTab));
});

$('login-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const submitButton = $('login-form').querySelector('button[type="submit"]');
    submitButton.disabled = true;
    try {
        const result = await api('/api/login', {
            method: 'POST',
            body: { correo: $('login-email').value.trim(), password: $('login-password').value }
        });
        currentUser = result.user;
        $('auth-message').classList.add('hidden');
        showDashboard();
        showToast('Sesión iniciada correctamente.');
    } catch (error) {
        showAuthMessage(error.message, true);
    } finally {
        submitButton.disabled = false;
    }
});

$('register-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const submitButton = $('register-form').querySelector('button[type="submit"]');
    submitButton.disabled = true;
    const body = {
        nombre: $('reg-nombre').value.trim(),
        apellido: $('reg-apellido').value.trim(),
        correo: $('reg-email').value.trim(),
        password: $('reg-password').value,
        edad: $('reg-edad').value,
        peso: $('reg-peso').value,
        estatura: $('reg-estatura').value,
        objetivo: $('reg-objetivo').value,
        nivel: $('reg-nivel').value
    };
    try {
        await api('/api/registro', { method: 'POST', body });
        $('login-email').value = body.correo;
        $('login-password').value = '';
        setAuthTab('login');
        showAuthMessage('Cuenta creada. Ahora ingresa con tu correo y contraseña.', false);
    } catch (error) {
        showAuthMessage(error.message, true);
    } finally {
        submitButton.disabled = false;
    }
});

function showAuthMessage(message, isError) {
    const notice = $('auth-message');
    notice.textContent = message;
    notice.classList.toggle('error', isError);
    notice.classList.remove('hidden');
}

$('logout-button').addEventListener('click', async () => {
    try { await api('/api/logout', { method: 'POST' }); } catch (_error) { /* La sesión local se cierra igualmente. */ }
    currentUser = null;
    clientRoutine = null;
    showPublicView();
    showToast('Sesión cerrada.');
});

function fillClientProfile() {
    $('profile-name').value = `${currentUser.nombre || ''} ${currentUser.apellido || ''}`.trim();
    $('profile-email').value = currentUser.correo || '';
    $('profile-age').value = currentUser.edad ?? '';
    $('profile-weight').value = currentUser.peso ?? '';
    $('profile-height').value = currentUser.estatura ?? '';
    $('profile-goal').value = currentUser.objetivo || '';
    $('profile-level').value = currentUser.nivel || '';
    updateClientMetrics();
    updateImc();
}

function updateClientMetrics() {
    $('client-metric-goal').textContent = currentUser?.objetivo || 'Sin definir';
    $('client-metric-level').textContent = currentUser?.nivel || 'Sin definir';
}

function updateImc() {
    const peso = Number($('profile-weight').value);
    const estatura = Number($('profile-height').value) / 100;
    const info = $('profile-imc');
    if (peso > 0 && estatura > 0) {
        info.textContent = `IMC referencial: ${(peso / (estatura * estatura)).toFixed(1)}. Es un dato orientativo y no reemplaza una evaluación profesional.`;
        info.classList.remove('hidden');
    } else {
        info.classList.add('hidden');
    }
}

$('profile-weight').addEventListener('input', updateImc);
$('profile-height').addEventListener('input', updateImc);

$('profile-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const body = {
        edad: $('profile-age').value,
        peso: $('profile-weight').value,
        estatura: $('profile-height').value,
        objetivo: $('profile-goal').value,
        nivel: $('profile-level').value
    };
    try {
        const result = await api('/api/cliente/perfil', { method: 'POST', body });
        currentUser = result.user;
        fillClientProfile();
        updateClientMetrics();
        await loadClientRoutine(false);
        showToast(result.message);
    } catch (error) {
        showToast(error.message, true);
    }
});

async function loadClientDashboard() {
    await Promise.all([loadClientHistory(), loadClientRoutine(true)]);
}

async function loadClientHistory() {
    try {
        const result = await api('/api/cliente/historial');
        $('client-metric-count').textContent = result.total_entrenamientos;
        $('client-metric-minutes').textContent = result.total_minutos;
        const container = $('client-history');
        if (!result.historial.length) {
            container.innerHTML = '<p class="muted-text">Todavía no has registrado entrenamientos. Cuando completes una sesión, podrás verla aquí.</p>';
            return;
        }
        container.innerHTML = result.historial.map((item) => `
            <div class="history-row">
                <div><strong>${escapeHtml(item.objetivo)} · ${escapeHtml(item.nivel)}</strong><small>${escapeHtml(item.fecha)}</small></div>
                <span class="history-minutes">${Number(item.minutos)} min</span>
            </div>`).join('');
    } catch (error) {
        $('client-history').innerHTML = `<p class="muted-text">${escapeHtml(error.message)}</p>`;
    }
}

async function loadClientRoutine(silent) {
    try {
        const result = await api('/api/cliente/rutina');
        clientRoutine = result.rutina;
        currentExerciseIndex = 0;
        $('routine-empty').classList.add('hidden');
        $('routine-content').classList.remove('hidden');
        $('routine-goal').textContent = `${clientRoutine.objetivo} · ${clientRoutine.nivel}`;
        $('routine-duration').textContent = clientRoutine.duracion;
        $('routine-list').innerHTML = clientRoutine.ejercicios.map((exercise) => `<li>${escapeHtml(exercise)}</li>`).join('');
        renderExerciseStep();
    } catch (error) {
        clientRoutine = null;
        $('routine-content').classList.add('hidden');
        $('routine-empty').classList.remove('hidden');
        $('routine-empty').querySelector('strong').textContent = 'Configura tu entrenamiento';
        $('routine-empty').querySelector('p').textContent = error.message || 'Guarda tu objetivo y tu nivel para consultar una rutina.';
        if (!silent && currentUser?.objetivo && currentUser?.nivel) showToast(error.message, true);
    }
}

function renderExerciseStep() {
    if (!clientRoutine || !clientRoutine.ejercicios.length) return;
    const total = clientRoutine.ejercicios.length;
    const exercise = clientRoutine.ejercicios[currentExerciseIndex];
    $('step-label').textContent = `Ejercicio ${currentExerciseIndex + 1}`;
    $('step-count').textContent = `${currentExerciseIndex + 1} de ${total}`;
    $('routine-progress').style.width = `${((currentExerciseIndex + 1) / total) * 100}%`;
    $('exercise-number').textContent = String(currentExerciseIndex + 1).padStart(2, '0');
    $('exercise-name').textContent = exercise;
    $('exercise-instruction').textContent = currentExerciseIndex === total - 1
        ? 'Este es el último ejercicio de la rutina. Termina a un ritmo cómodo y registra tu sesión cuando acabes.'
        : 'Completa el ejercicio con una técnica controlada. Cuando termines, continúa con el siguiente.';
    $('prev-exercise').disabled = currentExerciseIndex === 0;
    $('next-exercise').disabled = currentExerciseIndex === total - 1;
    $('next-exercise').textContent = currentExerciseIndex === total - 1 ? 'Rutina completada ✓' : 'Siguiente ejercicio →';
}

$('prev-exercise').addEventListener('click', () => {
    if (clientRoutine && currentExerciseIndex > 0) {
        currentExerciseIndex -= 1;
        renderExerciseStep();
    }
});
$('next-exercise').addEventListener('click', () => {
    if (clientRoutine && currentExerciseIndex < clientRoutine.ejercicios.length - 1) {
        currentExerciseIndex += 1;
        renderExerciseStep();
    }
});

$('workout-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
        const result = await api('/api/cliente/entrenamientos', {
            method: 'POST', body: { minutos: $('workout-minutes').value }
        });
        $('workout-minutes').value = '';
        await loadClientHistory();
        showToast(result.message);
    } catch (error) {
        showToast(error.message, true);
    }
});

async function loadTrainerDashboard() {
    try {
        const result = await api('/api/entrenador/clientes');
        trainerClients = result.clientes;
        $('trainer-client-count').textContent = trainerClients.length;
        $('trainer-workout-count').textContent = trainerClients.reduce((sum, c) => sum + Number(c.total_entrenamientos || 0), 0);
        $('trainer-minute-count').textContent = trainerClients.reduce((sum, c) => sum + Number(c.total_minutos || 0), 0);
        renderTrainerClients();
    } catch (error) {
        $('trainer-client-list').innerHTML = `<div class="empty-state"><strong>${escapeHtml(error.message)}</strong></div>`;
    }
}

$('trainer-search').addEventListener('input', renderTrainerClients);

function renderTrainerClients() {
    const query = $('trainer-search').value.trim().toLowerCase();
    const filtered = trainerClients.filter((client) => `${client.nombre} ${client.apellido} ${client.correo}`.toLowerCase().includes(query));
    const list = $('trainer-client-list');
    if (!filtered.length) {
        list.innerHTML = '<div class="empty-state"><strong>No hay clientes para mostrar</strong><p>Los clientes nuevos deben estar asignados a tu cuenta por el administrador.</p></div>';
        return;
    }
    list.innerHTML = filtered.map((client) => {
        const imc = client.peso && client.estatura ? (client.peso / ((client.estatura / 100) ** 2)).toFixed(1) : 'Sin dato';
        return `<article class="person-card">
            <div class="person-heading"><span class="avatar">${escapeHtml(initials(client.nombre, client.apellido))}</span><div><strong>${escapeHtml(client.nombre)} ${escapeHtml(client.apellido)}</strong><small>${escapeHtml(client.correo)}</small></div></div>
            <dl class="person-data">
                <div><dt>Edad</dt><dd>${escapeHtml(client.edad ?? '—')} años</dd></div>
                <div><dt>Objetivo</dt><dd>${escapeHtml(client.objetivo || 'Sin definir')}</dd></div>
                <div><dt>Nivel</dt><dd>${escapeHtml(client.nivel || 'Sin definir')}</dd></div>
                <div><dt>Peso / estatura</dt><dd>${client.peso ? `${escapeHtml(client.peso)} kg` : '—'} / ${client.estatura ? `${escapeHtml(client.estatura)} cm` : '—'}</dd></div>
                <div><dt>IMC referencial</dt><dd>${escapeHtml(imc)}</dd></div>
                <div><dt>Progreso</dt><dd>${Number(client.total_entrenamientos || 0)} sesiones · ${Number(client.total_minutos || 0)} min</dd></div>
            </dl>
            <div class="person-actions"><span class="tag tag-role">Cliente asignado</span><button class="button button-outline button-small" type="button" data-trainer-history="${Number(client.id)}">Ver historial</button></div>
        </article>`;
    }).join('');
}

function initials(first, last) {
    return `${String(first || '').charAt(0)}${String(last || '').charAt(0)}`.toUpperCase() || 'U';
}

$('trainer-client-list').addEventListener('click', async (event) => {
    const button = event.target.closest('[data-trainer-history]');
    if (!button) return;
    const id = Number(button.dataset.trainerHistory);
    const detail = $('trainer-history-detail');
    try {
        const result = await api(`/api/entrenador/clientes/${id}/historial`);
        renderHistoryDetail(detail, `${result.cliente.nombre} ${result.cliente.apellido}`, result.cliente.correo, result);
        detail.classList.remove('hidden');
        detail.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (error) {
        showToast(error.message, true);
    }
});

function renderHistoryDetail(container, name, email, data) {
    const history = data.historial.length ? data.historial.map((item) => `
        <div class="history-row"><div><strong>${escapeHtml(item.objetivo)} · ${escapeHtml(item.nivel)}</strong><small>${escapeHtml(item.fecha)}</small></div><span class="history-minutes">${Number(item.minutos)} min</span></div>`).join('') : '<p class="muted-text">Todavía no hay entrenamientos registrados.</p>';
    container.innerHTML = `<div class="history-detail-header"><div><span class="eyebrow">HISTORIAL DE ENTRENAMIENTO</span><h2>${escapeHtml(name)}</h2><p>${escapeHtml(email)}</p></div><button class="button button-outline button-small" type="button" data-close-detail>Cerrar</button></div>
        <div class="detail-stats"><span class="detail-stat">Sesiones: <strong>${Number(data.total_entrenamientos)}</strong></span><span class="detail-stat">Minutos: <strong>${Number(data.total_minutos)}</strong></span></div>
        <div class="history-list">${history}</div>`;
}

$('trainer-history-detail').addEventListener('click', (event) => {
    if (event.target.closest('[data-close-detail]')) $('trainer-history-detail').classList.add('hidden');
});

async function loadAdminDashboard() {
    try {
        const [summary, usersResult, trainersResult] = await Promise.all([
            api('/api/admin/resumen'), api('/api/admin/usuarios'), api('/api/admin/entrenadores')
        ]);
        $('admin-total-users').textContent = summary.resumen.usuarios;
        $('admin-total-clients').textContent = summary.resumen.clientes;
        $('admin-total-trainers').textContent = summary.resumen.entrenadores;
        $('admin-total-inactive').textContent = summary.resumen.inactivos;
        adminUsers = usersResult.usuarios;
        adminTrainers = trainersResult.entrenadores;
        populateTrainerSelect();
        renderAdminUsers();
    } catch (error) {
        showToast(error.message, true);
    }
}

function populateTrainerSelect() {
    const select = $('admin-new-trainer');
    const previous = select.value;
    select.innerHTML = '<option value="">Asignar automáticamente</option>' + adminTrainers.map((trainer) =>
        `<option value="${Number(trainer.id)}">${escapeHtml(trainer.nombre)} ${escapeHtml(trainer.apellido)}</option>`
    ).join('');
    if ([...select.options].some((option) => option.value === previous)) select.value = previous;
}

$('admin-new-role').addEventListener('change', () => {
    $('admin-assignment-field').classList.toggle('hidden', $('admin-new-role').value !== 'cliente');
});
$('admin-search').addEventListener('input', renderAdminUsers);
$('admin-role-filter').addEventListener('change', renderAdminUsers);
$('admin-status-filter').addEventListener('change', renderAdminUsers);

$('admin-create-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const submitButton = $('admin-create-form').querySelector('button[type="submit"]');
    submitButton.disabled = true;
    const body = {
        nombre: $('admin-new-name').value.trim(),
        apellido: $('admin-new-lastname').value.trim(),
        correo: $('admin-new-email').value.trim(),
        edad: $('admin-new-age').value,
        rol: $('admin-new-role').value,
        password: $('admin-new-password').value,
        entrenador_id: $('admin-new-trainer').value
    };
    try {
        const result = await api('/api/admin/usuarios', { method: 'POST', body });
        $('admin-create-form').reset();
        $('admin-assignment-field').classList.remove('hidden');
        await loadAdminDashboard();
        showToast(result.message);
    } catch (error) {
        showToast(error.message, true);
    } finally {
        submitButton.disabled = false;
    }
});

function renderAdminUsers() {
    const query = $('admin-search').value.trim().toLowerCase();
    const role = $('admin-role-filter').value;
    const status = $('admin-status-filter').value;
    const filtered = adminUsers.filter((user) => {
        const matchesQuery = `${user.nombre} ${user.apellido} ${user.correo}`.toLowerCase().includes(query);
        const matchesRole = role === 'todos' || user.rol === role;
        const matchesStatus = status === 'todos' || (status === 'activos' ? user.activo : !user.activo);
        return matchesQuery && matchesRole && matchesStatus;
    });
    const body = $('admin-users-body');
    if (!filtered.length) {
        body.innerHTML = '<tr><td colspan="6">No hay cuentas que coincidan con la búsqueda.</td></tr>';
        return;
    }
    body.innerHTML = filtered.map((user) => {
        const details = [];
        if (user.edad) details.push(`${escapeHtml(user.edad)} años`);
        if (user.peso) details.push(`${escapeHtml(user.peso)} kg`);
        if (user.estatura) details.push(`${escapeHtml(user.estatura)} cm`);
        if (user.objetivo) details.push(escapeHtml(user.objetivo));
        if (user.nivel) details.push(`Nivel ${escapeHtml(user.nivel)}`);
        details.push(`${Number(user.total_entrenamientos || 0)} sesiones · ${Number(user.total_minutos || 0)} min`);
        const trainerName = user.entrenador_nombre ? `${user.entrenador_nombre} ${user.entrenador_apellido || ''}` : 'Sin asignar';
        const trainerSelect = user.rol === 'cliente' ? `<select data-assign-client="${Number(user.id)}" aria-label="Asignar entrenador a ${escapeHtml(user.nombre)}"><option value="">Sin asignar</option>${adminTrainers.map((trainer) => `<option value="${Number(trainer.id)}" ${Number(user.entrenador_id) === Number(trainer.id) ? 'selected' : ''}>${escapeHtml(trainer.nombre)} ${escapeHtml(trainer.apellido)}</option>`).join('')}</select><small class="user-meta">${escapeHtml(trainerName)}</small>` : '—';
        const stateAction = user.id === currentUser.id ? '<span class="user-meta">Cuenta propia</span>' : `<button type="button" class="button ${user.activo ? 'button-danger' : 'button-primary'}" data-toggle-user="${Number(user.id)}" data-next-state="${user.activo ? '0' : '1'}">${user.activo ? 'Desactivar' : 'Activar'}</button>`;
        return `<tr>
            <td><span class="user-name">${escapeHtml(user.nombre)} ${escapeHtml(user.apellido)}</span><span class="user-email">${escapeHtml(user.correo)}</span></td>
            <td><span class="tag tag-role">${escapeHtml(roleName(user.rol))}</span></td>
            <td>${details.map((d) => `<span class="user-meta">${d}</span>`).join('')}</td>
            <td>${trainerSelect}</td>
            <td><span class="tag ${user.activo ? 'tag-active' : 'tag-inactive'}">${user.activo ? 'Activo' : 'Desactivado'}</span></td>
            <td><div class="table-actions"><button type="button" class="button button-outline" data-admin-history="${Number(user.id)}">Ver historial</button>${stateAction}</div></td>
        </tr>`;
    }).join('');
}

$('admin-users-body').addEventListener('click', async (event) => {
    const historyButton = event.target.closest('[data-admin-history]');
    if (historyButton) {
        try {
            const result = await api(`/api/admin/usuarios/${Number(historyButton.dataset.adminHistory)}/historial`);
            const detail = $('admin-history-detail');
            renderHistoryDetail(detail, `${result.usuario.nombre} ${result.usuario.apellido}`, `${result.usuario.correo} · ${roleName(result.usuario.rol)}`, result);
            detail.classList.remove('hidden');
            detail.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } catch (error) { showToast(error.message, true); }
        return;
    }
    const toggleButton = event.target.closest('[data-toggle-user]');
    if (toggleButton) {
        const id = Number(toggleButton.dataset.toggleUser);
        const active = toggleButton.dataset.nextState === '1';
        const label = active ? 'activar' : 'desactivar';
        if (!window.confirm(`¿Confirmas que deseas ${label} esta cuenta?`)) return;
        try {
            const result = await api(`/api/admin/usuarios/${id}/estado`, { method: 'POST', body: { activo: active } });
            await loadAdminDashboard();
            showToast(result.message);
        } catch (error) { showToast(error.message, true); }
    }
});

$('admin-users-body').addEventListener('change', async (event) => {
    const select = event.target.closest('[data-assign-client]');
    if (!select) return;
    try {
        const result = await api(`/api/admin/usuarios/${Number(select.dataset.assignClient)}/entrenador`, {
            method: 'POST', body: { entrenador_id: select.value }
        });
        await loadAdminDashboard();
        showToast(result.message);
    } catch (error) {
        showToast(error.message, true);
        await loadAdminDashboard();
    }
});

$('admin-history-detail').addEventListener('click', (event) => {
    if (event.target.closest('[data-close-detail]')) $('admin-history-detail').classList.add('hidden');
});

$('whatsapp-button').addEventListener('click', (event) => {
    event.preventDefault();
    const message = encodeURIComponent('Hola, estoy usando GymFit y quisiera realizar una consulta o dejar una sugerencia/queja.');
    const number = String(window.GYMFIT_WHATSAPP || '').replace(/\D/g, '');
    const url = number ? `https://wa.me/${number}?text=${message}` : `https://api.whatsapp.com/send?text=${message}`;
    window.open(url, '_blank', 'noopener,noreferrer');
});

async function startApp() {
    try {
        const result = await api('/api/me');
        currentUser = result.user;
        showDashboard();
    } catch (_error) {
        showPublicView();
    }
}

startApp();
