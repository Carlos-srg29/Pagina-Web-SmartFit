let currentUser = null;

function toggleView(view) {
    if (view === 'register') {
        document.getElementById('login-section').classList.add('hidden');
        document.getElementById('register-section').classList.remove('hidden');
    } else {
        document.getElementById('register-section').classList.add('hidden');
        document.getElementById('login-section').classList.remove('hidden');
    }
}

async function registrar() {
    const nombre = document.getElementById('reg-nombre').value.trim();
    const apellido = document.getElementById('reg-apellido').value.trim();
    const correo = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-password').value;
    const edad = document.getElementById('reg-edad').value;

    if (!nombre || !correo || !password || !edad) {
        alert("Por favor completa los campos requeridos.");
        return;
    }

    try {
        const response = await fetch('/api/registro', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre, apellido, correo, password, edad })
        });

        const data = await response.json();
        alert(data.message);
        if (data.success) toggleView('login');
    } catch (error) {
        alert("No se pudo conectar con el servidor.");
    }
}

async function login() {
    const correo = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;

    if (!correo || !password) {
        alert("Ingresa tu correo y contraseña.");
        return;
    }

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ correo, password })
        });

        const data = await response.json();

        if (data.success) {
            currentUser = data.user;
            document.getElementById('login-section').classList.add('hidden');

            if (currentUser.rol === 'entrenador') {
                document.getElementById('trainer-section').classList.remove('hidden');
                cargarClientesEntrenador();
            } else {
                document.getElementById('user-section').classList.remove('hidden');
                document.getElementById('welcome-msg').innerText = `¡Bienvenido, ${currentUser.nombre}!`;
                document.getElementById('select-objetivo').value = currentUser.objetivo || '';
                document.getElementById('select-nivel').value = currentUser.nivel || '';
                cargarHistorial();
            }
        } else {
            alert(data.message);
        }
    } catch (error) {
        alert("No se pudo conectar con el servidor.");
    }
}

async function guardarPreferencias() {
    const objetivo = document.getElementById('select-objetivo').value;
    const nivel = document.getElementById('select-nivel').value;

    if (!objetivo || !nivel) {
        alert("Selecciona un objetivo y un nivel.");
        return;
    }

    try {
        const response = await fetch('/api/actualizar-perfil', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUser.id, objetivo, nivel })
        });

        const data = await response.json();
        alert(data.message);

        if (data.success) {
            currentUser.objetivo = objetivo;
            currentUser.nivel = nivel;
        }
    } catch (error) {
        alert("No se pudo guardar la configuración.");
    }
}

async function mostrarRutina() {
    const objetivo = document.getElementById('select-objetivo').value;
    const nivel = document.getElementById('select-nivel').value;
    const box = document.getElementById('routine-container');

    if (!objetivo || !nivel) {
        alert("Primero debes seleccionar un objetivo y nivel.");
        return;
    }

    try {
        const response = await fetch('/api/rutina', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ objetivo, nivel })
        });

        const data = await response.json();

        if (!data.success) {
            alert(data.message);
            return;
        }

        const rutina = data.rutina;
        const ejercicios = rutina.ejercicios
            .map((ejercicio, index) => `${index + 1}. ${ejercicio}`)
            .join('\n');

        // Usa como valor inicial de registro la primera duración indicada por la rutina.
        // Ej.: "45-60 min" -> 45 y "50 min" -> 50.
        const duracionCoincide = String(rutina.duracion).match(/\d+/);
        const minutosSugeridos = duracionCoincide ? Number(duracionCoincide[0]) : 45;

        box.innerHTML = `
            <h4>Rutina: ${rutina.objetivo} (${rutina.nivel})</h4>
            <p><strong>Duración:</strong> ${rutina.duracion}</p>
            <pre style="white-space: pre-wrap;">${ejercicios}</pre>
            <button onclick="registrarEntrenamiento()" style="background:#10b981;">Registrar entrenamiento realizado</button>
        `;
        box.classList.remove('hidden');
    } catch (error) {
        alert("No se pudo obtener la rutina.");
    }
}

async function registrarEntrenamiento() {
    const objetivo = document.getElementById('select-objetivo').value;
    const nivel = document.getElementById('select-nivel').value;
    // El valor inicial coincide con la duración mostrada en la rutina.
    const rutinaVisible = document.querySelector('#routine-container strong')?.parentElement?.textContent || '';
    const duracionCoincide = rutinaVisible.match(/\d+/);
    const minutosSugeridos = duracionCoincide ? Number(duracionCoincide[0]) : 45;
    const minutosTexto = prompt("¿Cuántos minutos entrenaste?", String(minutosSugeridos));

    if (minutosTexto === null) return;

    const minutos = Number(minutosTexto);
    if (!Number.isInteger(minutos) || minutos <= 0) {
        alert("Ingresa una cantidad de minutos válida.");
        return;
    }

    try {
        const response = await fetch('/api/registrar-entrenamiento', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUser.id,
                objetivo,
                nivel,
                minutos
            })
        });

        const data = await response.json();
        alert(data.message);

        if (data.success) cargarHistorial();
    } catch (error) {
        alert("No se pudo registrar el entrenamiento.");
    }
}

async function cargarHistorial() {
    if (!currentUser) return;

    try {
        const response = await fetch(`/api/historial/${currentUser.id}`);
        const data = await response.json();
        const historialBox = document.getElementById('history-container');

        historialBox.innerHTML = `
            <h4>Mi progreso</h4>
            <p><strong>Entrenamientos:</strong> ${data.total_entrenamientos}</p>
            <p><strong>Minutos acumulados:</strong> ${data.total_minutos}</p>
        `;

        if (data.historial.length > 0) {
            historialBox.innerHTML += '<hr><strong>Historial:</strong>';
            data.historial.forEach(item => {
                historialBox.innerHTML += `
                    <p>${item.fecha} — ${item.objetivo} / ${item.nivel} — ${item.minutos} min</p>
                `;
            });
        }

        historialBox.classList.remove('hidden');
    } catch (error) {
        console.log("No se pudo cargar el historial.", error);
    }
}

async function cargarClientesEntrenador() {
    try {
        const response = await fetch('/api/entrenador/clientes');
        const data = await response.json();
        const listDiv = document.getElementById('trainer-clients-list');
        listDiv.innerHTML = '';

        if (data.clientes.length === 0) {
            listDiv.innerHTML = '<p>No hay clientes registrados.</p>';
            return;
        }

        data.clientes.forEach(c => {
            listDiv.innerHTML += `
                <div class="client-card">
                    <p><strong>Cliente:</strong> ${c.nombre} ${c.apellido}</p>
                    <p><strong>Correo:</strong> ${c.correo} | <strong>Edad:</strong> ${c.edad}</p>
                    <p><strong>Objetivo:</strong> ${c.objetivo || 'No definido'}</p>
                    <p><strong>Nivel:</strong> ${c.nivel || 'No definido'}</p>
                </div>
            `;
        });
    } catch (error) {
        alert("No se pudo cargar la lista de clientes.");
    }
}

function logout() {
    currentUser = null;
    document.getElementById('user-section').classList.add('hidden');
    document.getElementById('trainer-section').classList.add('hidden');
    document.getElementById('routine-container').classList.add('hidden');
    document.getElementById('history-container').classList.add('hidden');
    document.getElementById('login-section').classList.remove('hidden');
}

if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/sw.js').catch(err => console.log(err));
}
