const qs = (selector, root = document) => root.querySelector(selector);
const qsa = (selector, root = document) => [...root.querySelectorAll(selector)];

function showToast(message, type = "success") {
    const stack = qs("#toastStack");
    if (!stack) return;
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;
    stack.appendChild(toast);
    setTimeout(() => toast.remove(), 4200);
}

async function api(url, options = {}) {
    const response = await fetch(url, {
        headers: { "Content-Type": "application/json", ...(options.headers || {}) },
        credentials: "same-origin",
        ...options,
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.ok === false) throw new Error(data.message || "Request failed");
    return data;
}

window.addEventListener("load", () => {
    qs("#pageLoader")?.classList.add("done");
    setTimeout(() => qsa(".toast").forEach((toast) => toast.remove()), 4500);
});

document.addEventListener("DOMContentLoaded", () => {
    window.lucide?.createIcons();

    qsa(".reveal").forEach((item) => {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => entry.isIntersecting && entry.target.classList.add("visible"));
        }, { threshold: 0.18 });
        observer.observe(item);
    });

    qs("[data-nav-toggle]")?.addEventListener("click", () => qs("[data-nav-links]")?.classList.toggle("open"));
    qs("[data-sidebar-toggle]")?.addEventListener("click", () => qs(".sidebar")?.classList.toggle("open"));
    qs("[data-theme-toggle]")?.addEventListener("click", () => {
        document.body.classList.toggle("dark");
        localStorage.setItem("theme", document.body.classList.contains("dark") ? "dark" : "light");
    });
    if (localStorage.getItem("theme") === "dark") document.body.classList.add("dark");

    const roleSelect = qs("#roleSelect");
    roleSelect?.addEventListener("change", () => {
        qsa(".doctor-only").forEach((field) => field.classList.toggle("hidden", roleSelect.value !== "doctor"));
    });

    qsa("[data-validate]").forEach((form) => {
        form.addEventListener("submit", (event) => {
            if (!form.checkValidity()) {
                event.preventDefault();
                showToast("Please complete the highlighted fields.", "warning");
            }
        });
    });

    qs("#doctorSearch")?.addEventListener("input", debounce(searchDoctors, 250));
    qs("#appointmentForm")?.addEventListener("submit", bookAppointment);
    qs("#reportForm")?.addEventListener("submit", uploadReport);
    qs("#prescriptionForm")?.addEventListener("submit", uploadPrescription);
    qs("#reminderForm")?.addEventListener("submit", createReminder);
    qsa("[data-status-id]").forEach((button) => button.addEventListener("click", updateAppointmentStatus));
    qsa("[data-approve-doctor]").forEach((button) => button.addEventListener("click", approveDoctor));
    qs("[data-open-notifications]")?.addEventListener("click", openNotifications);
    qs("[data-close-modal]")?.addEventListener("click", () => qs("#notificationModal")?.classList.add("hidden"));

    if (qs("#appointmentTable")) loadAppointments();
    if (qs("#reminderList")) loadReminders();
    if (qs(".chat-panel")) initChat();
});

function debounce(callback, wait) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => callback(...args), wait);
    };
}

async function searchDoctors(event) {
    const results = qs("#doctorResults");
    const doctors = await api(`/patient/api/doctors?q=${encodeURIComponent(event.target.value)}`);
    results.innerHTML = doctors.map((doctor) => `
        <div class="list-card">
            <div class="avatar-sm">${doctor.name.slice(0, 2).toUpperCase()}</div>
            <div><strong>${doctor.name}</strong><span>${doctor.specialization} · ${doctor.experience_years} yrs · $${doctor.consultation_fee}</span></div>
            <a class="btn tiny primary" href="/patient/appointments">Book</a>
        </div>`).join("") || `<p class="muted">No matching doctors found.</p>`;
}

async function bookAppointment(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form));
    try {
        await api("/patient/api/appointments", { method: "POST", body: JSON.stringify(data) });
        showToast("Appointment request submitted.");
        form.reset();
        loadAppointments();
    } catch (error) {
        showToast(error.message, "danger");
    }
}

async function loadAppointments() {
    const table = qs("#appointmentTable tbody");
    if (!table) return;
    const appointments = await api("/patient/api/appointments");
    table.innerHTML = appointments.map((item) => `
        <tr>
            <td>${item.doctor}</td>
            <td>${new Date(item.scheduled_at).toLocaleString()}</td>
            <td><span class="status ${item.status.toLowerCase()}">${item.status}</span></td>
            <td><a href="/patient/consultation/${item.id}">Room</a> · <a href="/patient/chat/${item.id}">Chat</a></td>
        </tr>`).join("") || `<tr><td colspan="4">No appointments found.</td></tr>`;
}

async function updateAppointmentStatus(event) {
    const button = event.currentTarget;
    try {
        await api(`/doctor/api/appointments/${button.dataset.statusId}/status`, {
            method: "POST",
            body: JSON.stringify({ status: button.dataset.status }),
        });
        showToast(`Appointment ${button.dataset.status.toLowerCase()}.`);
        location.reload();
    } catch (error) {
        showToast(error.message, "danger");
    }
}

async function approveDoctor(event) {
    const button = event.currentTarget;
    await api(`/admin/api/doctors/${button.dataset.approveDoctor}/approval`, {
        method: "POST",
        body: JSON.stringify({ approved: true }),
    });
    showToast("Doctor approved.");
    location.reload();
}

async function uploadReport(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const response = await fetch("/patient/api/reports", { method: "POST", body: new FormData(form), credentials: "same-origin" });
    const data = await response.json();
    showToast(data.ok ? "Medical report uploaded." : data.message, data.ok ? "success" : "danger");
    if (data.ok) form.reset();
}

async function uploadPrescription(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const response = await fetch("/doctor/api/prescriptions", { method: "POST", body: new FormData(form), credentials: "same-origin" });
    const data = await response.json();
    showToast(data.ok ? "Prescription uploaded." : "Could not upload prescription.", data.ok ? "success" : "danger");
    if (data.ok) form.reset();
}

async function loadReminders() {
    const list = qs("#reminderList");
    if (!list) return;
    const reminders = await api("/api/reminders");
    list.innerHTML = reminders.map((item) => `
        <div class="reminder-item">
            <div><strong>${item.medicine_name}</strong><span>${item.dosage} · ${item.reminder_time} · Taken ${item.taken_count} / Missed ${item.missed_count}</span></div>
            <div class="action-row">
                <button class="btn tiny primary" onclick="markReminder(${item.id}, 'taken')">Taken</button>
                <button class="btn tiny soft" onclick="markReminder(${item.id}, 'missed')">Missed</button>
            </div>
        </div>`).join("") || `<p class="muted">No reminders yet.</p>`;
}

async function createReminder(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form));
    try {
        await api("/api/reminders", { method: "POST", body: JSON.stringify(data) });
        showToast("Reminder added.");
        form.reset();
        loadReminders();
    } catch (error) {
        showToast(error.message, "danger");
    }
}

async function markReminder(id, action) {
    await api(`/api/reminders/${id}`, { method: "PATCH", body: JSON.stringify({ action }) });
    showToast(action === "taken" ? "Marked as taken." : "Marked as missed.", action === "taken" ? "success" : "warning");
    loadReminders();
}
window.markReminder = markReminder;

async function openNotifications() {
    const modal = qs("#notificationModal");
    const list = qs("#notificationList");
    modal?.classList.remove("hidden");
    const notifications = await api("/api/notifications");
    list.innerHTML = notifications.map((item) => `<div class="list-card"><i data-lucide="bell"></i><div><strong>${item.title}</strong><span>${item.body} · ${item.created_at}</span></div></div>`).join("") || `<p class="muted">No notifications.</p>`;
    window.lucide?.createIcons();
}

function initChat() {
    const panel = qs(".chat-panel");
    const appointmentId = panel.dataset.appointmentId;
    const stream = qs("#chatStream");
    const socket = io();
    const currentUserId = Number(window.MEDI_USER_ID || 0);

    fetch(`/patient/api/messages/${appointmentId}`, { credentials: "same-origin" })
        .then((res) => res.json())
        .then((messages) => {
            stream.innerHTML = messages.map(renderMessage).join("");
            stream.scrollTop = stream.scrollHeight;
        });

    socket.emit("join", { appointment_id: appointmentId });
    socket.on("chat_message", (message) => {
        stream.insertAdjacentHTML("beforeend", renderMessage(message, currentUserId));
        stream.scrollTop = stream.scrollHeight;
    });

    qs("#chatForm").addEventListener("submit", (event) => {
        event.preventDefault();
        const input = qs("#chatInput");
        socket.emit("chat_message", { appointment_id: appointmentId, body: input.value });
        input.value = "";
    });
}

function renderMessage(message, currentUserId = null) {
    const mine = currentUserId && Number(message.sender_id) === currentUserId;
    return `<div class="message ${mine ? "mine" : ""}"><strong>${message.sender}</strong><p>${escapeHtml(message.body)}</p><small>${message.created_at}</small></div>`;
}

function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#039;" }[char]));
}

setInterval(() => {
    qsa(".reminder-item").forEach((item) => {
        if (item.textContent.includes(new Date().toTimeString().slice(0, 5))) {
            showToast("Medicine reminder due now.", "warning");
        }
    });
}, 60000);
