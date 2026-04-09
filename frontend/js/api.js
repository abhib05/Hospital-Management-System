/**
 * api.js – Centralised API client using fetch().
 * Automatically attaches Bearer token and handles errors.
 */

const API_BASE = window.location.origin;

// ── Token management ─────────────────────────────────────────────────────────
const Auth = {
    getToken:    () => sessionStorage.getItem("hms_token"),
    getUser:     () => JSON.parse(sessionStorage.getItem("hms_user") || "null"),
    setSession:  (data) => {
        sessionStorage.setItem("hms_token", data.access_token);
        sessionStorage.setItem("hms_user",  JSON.stringify({
            user_id: data.user_id,
            username: data.username,
            role: data.role,
        }));
    },
    clearSession: () => {
        sessionStorage.removeItem("hms_token");
        sessionStorage.removeItem("hms_user");
    },
    isLoggedIn: () => !!sessionStorage.getItem("hms_token"),
    redirectIfNotLoggedIn: (requiredRole = null) => {
        if (!Auth.isLoggedIn()) {
            window.location.href = "/index.html";
            return;
        }
        if (requiredRole) {
            const user = Auth.getUser();
            if (user?.role !== requiredRole && user?.role !== "Admin") {
                window.location.href = "/index.html";
            }
        }
    },
};

// ── HTTP helpers ─────────────────────────────────────────────────────────────
async function apiRequest(method, path, body = null, isFormData = false) {
    const headers = { Authorization: `Bearer ${Auth.getToken()}` };
    if (!isFormData) headers["Content-Type"] = "application/json";

    const opts = { method, headers };
    if (body) opts.body = isFormData ? body : JSON.stringify(body);

    const res = await fetch(`${API_BASE}${path}`, opts);

    if (res.status === 401) {
        Auth.clearSession();
        window.location.href = "/index.html";
        return;
    }

    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
    return data;
}

const api = {
    get:    (path) => apiRequest("GET",    path),
    post:   (path, body) => apiRequest("POST",   path, body),
    patch:  (path, body) => apiRequest("PATCH",  path, body),
    put:    (path, body) => apiRequest("PUT",    path, body),
    delete: (path) => apiRequest("DELETE",  path),
    postForm: (path, formData) => apiRequest("POST", path, formData, true),
};

// ── Toast notification system ─────────────────────────────────────────────────
function showToast(message, type = "success") {
    let container = document.getElementById("toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "toast-container";
        container.className = "fixed top-4 right-4 z-50 flex flex-col gap-2";
        document.body.appendChild(container);
    }

    const colors = {
        success: "bg-green-500",
        error:   "bg-red-500",
        warning: "bg-yellow-500",
        info:    "bg-blue-500",
    };
    const icons = {
        success: "✓",
        error:   "✕",
        warning: "⚠",
        info:    "ℹ",
    };

    const toast = document.createElement("div");
    toast.className = `${colors[type] || colors.info} text-white px-4 py-3 rounded-lg shadow-lg
                       flex items-center gap-2 min-w-64 max-w-sm text-sm font-medium
                       transform transition-all duration-300 translate-x-full opacity-0`;
    toast.innerHTML = `<span class="text-lg">${icons[type]}</span><span>${message}</span>`;
    container.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
        toast.classList.remove("translate-x-full", "opacity-0");
    });

    // Auto-remove after 3.5 s
    setTimeout(() => {
        toast.classList.add("translate-x-full", "opacity-0");
        toast.addEventListener("transitionend", () => toast.remove());
    }, 3500);
}

// ── Spinner helpers ───────────────────────────────────────────────────────────
function showSpinner(btnEl, text = "Processing…") {
    if (!btnEl) return;
    btnEl._originalHTML = btnEl.innerHTML;
    btnEl.disabled = true;
    btnEl.innerHTML = `<svg class="animate-spin h-4 w-4 inline mr-2" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
    </svg>${text}`;
}

function hideSpinner(btnEl) {
    if (!btnEl || !btnEl._originalHTML) return;
    btnEl.disabled = false;
    btnEl.innerHTML = btnEl._originalHTML;
}

// ── Date / time helpers ───────────────────────────────────────────────────────
function formatDateTime(isoStr) {
    if (!isoStr) return "—";
    return new Date(isoStr).toLocaleString("en-US", {
        dateStyle: "medium", timeStyle: "short",
    });
}

function formatDate(isoStr) {
    if (!isoStr) return "—";
    return new Date(isoStr).toLocaleDateString("en-US", { dateStyle: "medium" });
}

function formatCurrency(amount) {
    return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(amount || 0);
}

// ── Role-based redirect on page load ─────────────────────────────────────────
function redirectByRole() {
    const user = Auth.getUser();
    if (!user) return;
    const routes = {
        Doctor:     "/doctor_dashboard.html",
        Pharmacist: "/pharmacist_dashboard.html",
        Patient:    "/patient_portal.html",
        Admin:      "/admin_dashboard.html",
        LabTech:    "/labtech_dashboard.html",
    };
    const dest = routes[user.role];
    if (dest && !window.location.pathname.endsWith(dest.replace("/", ""))) {
        window.location.href = dest;
    }
}
