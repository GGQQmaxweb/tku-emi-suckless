// Function to switch visible screen
function showPage(pageId) {
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    document.getElementById(pageId).classList.add('active');
}

// AUTO-RUN ON BOOT: Check session as soon as pywebview is loaded
window.addEventListener('pywebviewready', async () => {
    const session = await window.pywebview.api.check_saved_session();

    if (session.logged_in) {
        // User has a valid saved session -> Skip login!
        document.getElementById('user-display').innerText = session.username;
        showPage('page-dashboard');
    } else {
        // No saved session -> Show Login page
        showPage('page-login');
    }
});

// Login Handler
async function handleLogin() {
    const user = document.getElementById('username').value;
    const pass = document.getElementById('password').value;
    document.getElementById('loginbtn').innerText = "Login check took time please wait"
    
    const success = await window.pywebview.api.authenticate(user, pass);

    if (success) {
        document.getElementById('user-display').innerText = user;
        showPage('page-dashboard');
    } else {
        document.getElementById('login-error').innerText = "Invalid credentials!";
    }
}

// Logout Handler
async function handleLogout() {
    await window.pywebview.api.logout();
    document.getElementById('username').value = '';
    document.getElementById('password').value = '';
    showPage('page-login');
}