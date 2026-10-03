const loginForm = document.getElementById('loginForm');
const errorMsg = document.getElementById('error-msg');
const loginBtn = document.getElementById('loginBtn');

const APP_BASE = window.location.protocol === 'file:' ? 'http://127.0.0.1:8000' : window.location.origin;
const API_BASE = `${APP_BASE}/api`;

if (localStorage.getItem('accessToken')) {
    const volver = confirm('Ya tienes una sesión activa. ¿Deseas volver al dashboard?');
    if (volver) {
        window.location.replace(`${APP_BASE}/`);
    } else {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
    }
}

const resetLoginButton = () => {
    loginBtn.textContent = 'Iniciar Sesión';
    loginBtn.disabled = false;
};

loginForm.addEventListener('submit', async function (e) {
    e.preventDefault();

    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();

    if (!username || !password) {
        errorMsg.textContent = 'Debes completar usuario y contraseña.';
        errorMsg.style.display = 'block';
        return;
    }

    loginBtn.textContent = 'Verificando...';
    loginBtn.disabled = true;
    errorMsg.style.display = 'none';

    try {
        const response = await fetch(`${API_BASE}/token/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        let data = {};
        try {
            data = await response.json();
        } catch (jsonError) {
            data = {};
        }

        if (response.ok && data.access) {
            localStorage.setItem('accessToken', data.access);
            if (data.refresh) {
                localStorage.setItem('refreshToken', data.refresh);
            }
            window.location.href = `${APP_BASE}/`;
            return;
        }

        const message = data.detail || data.non_field_errors?.[0] || 'Usuario o contraseña incorrectos.';
        throw new Error(message);
    } catch (error) {
        console.error('Error de autenticación:', error);
        errorMsg.textContent = 'Usuario o contraseña incorrectos.';
        errorMsg.style.display = 'block';
        resetLoginButton();
    }
});