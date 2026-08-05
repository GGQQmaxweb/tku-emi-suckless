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
        await getDashboardData();
        await updateProgressBar();
        await userInformation();
    } else {
        // No saved session -> Show Login page
        showPage('page-login');
    }
});

async function updateUserLocalData() {
    document.getElementById('UpdataUserdataBtn').innerText = "Updating data, please wait...";
    await window.pywebview.api.update_all_user_data();
    document.getElementById('UpdataUserdataBtn').innerText = "Update User Data";
}

async function getDashboardData() {
    const data = await window.pywebview.api.get_score();

    let table = `
        <table border="1" cellpadding="8" cellspacing="0">
            <thead>
                <tr>
                    <th>Category</th>
                    <th>Credits</th>
                </tr>
            </thead>
            <tbody>
    `;

    for (const [key, value] of Object.entries(data)) {
        table += `
            <tr>
                <td>${key.replace(/_/g, " ")}</td>
                <td>${value}</td>
            </tr>
        `;
    }

    table += `
            </tbody>
        </table>
    `;

    document.getElementById("dashboard-content").innerHTML = table;
}

async function updateRequiredCourses(withoutRefresh = false) {

    const data = await window.pywebview.api.missing_required_courses(withoutRefresh);

    let table = `
        <table border="1" cellpadding="8" cellspacing="0">
            <thead>
                <tr>
                    <th>Grade</th>
                    <th>Course Name</th>
                    <th>Course Code</th>
                    <th>Specialization</th>
                    <th>Group</th>
                    <th>Credits Up</th>
                    <th>Credits Down</th>
                    <th>Note</th>
                </tr>
            </thead>
            <tbody>
    `;

    for (const course of data) {
        table += `
            <tr>
                <td>${course.grade}</td>
                <td>${course.course_name}</td>
                <td>${course.course_code}</td>
                <td>${course.specialization}</td>
                <td>${course.group}</td>
                <td>${course.credits_up}</td>
                <td>${course.credits_down}</td>
                <td>${course.note}</td>
            </tr>
        `;
    }

    table += `
            </tbody>
        </table>
    `;

    document.getElementById("required-courses-content").innerHTML = table;
    document.getElementById('update-required-courses-btn').innerText = "Update Required Courses";
}

async function updateProgressBar() {
    const data = await window.pywebview.api.progress_on_graduation();
    const progressBar = document.getElementById('progress-bar');
    progressBar.style.width = `${data.total_percent}%`;
    progressBar.innerText = `${data.total_percent}%`;
}

async function userInformation() {
    const data = await window.pywebview.api.student_info();
    const infoDiv = document.getElementById('user-info');
    infoDiv.innerHTML = `
        <p><strong>Name:</strong> ${data.name} <strong>Student ID:</strong> ${data.id} <strong>Department:</strong> ${data.grade}</p>
    `;

}
async function updateAllGrades(withoutRefresh = false) {
    const data = await window.pywebview.api.all_years_course_grades(withoutRefresh);

    const gradesDiv = document.getElementById("all-grades-content");

    const rows = data.courses.map(course => `
        <tr>
            <td>${course.grade}</td>
            <td>${course.course_name}</td>
            <td>${course.course_code}</td>
            <td>${course.specialization}</td>
            <td>${course.group}</td>
            <td>${course.credits_up}</td>
            <td>${course.credits_down}</td>
            <td>${course.requirement_type}</td>
            <td>${course.status}</td>
        </tr>
    `).join("");

    gradesDiv.innerHTML = `
        <p><strong>Total Earned Credits:</strong> ${data.total_earned_credits}</p>

        <table border="1" cellpadding="8" cellspacing="0">
            <thead>
                <tr>
                    <th>Grade</th>
                    <th>Course Name</th>
                    <th>Course Code</th>
                    <th>Specialization</th>
                    <th>Group</th>
                    <th>Credits Up</th>
                    <th>Credits Down</th>
                    <th>Requirement Type</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                ${rows}
            </tbody>
        </table>
    `;

    document.getElementById("update-all-grades-btn").textContent = "Update All Grades";
}

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