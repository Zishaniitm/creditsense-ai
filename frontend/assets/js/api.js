/**
 * api.js — Axios wrapper with interceptors for CreditSense AI
 * Improvements: automatic 401 handling, centralized error logging,
 * environment-aware base URL from CONFIG
 */

// ── Axios instance with interceptors ─────────────────────────────
const axiosInstance = axios.create({
    baseURL: CONFIG.API_BASE,
    timeout: 10000,
    headers: { "Content-Type": "application/json" }
});

// Response interceptor — auto-logout on 401
axiosInstance.interceptors.response.use(
    response => response,
    error => {
        if (error.response?.status === 401) {
            console.warn("Session expired — redirecting to login");
            AUTH.clearSession();
            window.location.href = "../auth/index.html";
        }
        return Promise.reject(error);
    }
);

const API = {

    async post(path, body, authenticated = true) {
        const config = authenticated
            ? { headers: AUTH.headers() }
            : { headers: { "Content-Type": "application/json" } };
        const response = await axiosInstance.post(path, body, config);
        return response.data;
    },

    async get(path) {
        const response = await axiosInstance.get(path, {
            headers: AUTH.headers()
        });
        return response.data;
    },

    async patch(path, params) {
        const response = await axiosInstance.patch(path, null, {
            headers: AUTH.headers(),
            params:  params
        });
        return response.data;
    },

    auth: {
        async login(email, password) {
            return API.post("/auth/login", { email, password }, false);
        },
        async register(name, email, password) {
            return API.post("/auth/register", { name, email, password }, false);
        }
    },

    applications: {
        async submit(payload)        { return API.post("/applications", payload); },
        async getById(id)            { return API.get(`/applications/${id}`); },
        async decide(id, dec, notes) {
            return API.patch(`/applications/${id}/decision`, { decision: dec, notes });
        }
    },

    transactions: {
        async verify(payload) { return API.post("/transactions/verify", payload); }
    },

    analytics: {
        async portfolio() { return API.get("/analytics/portfolio"); }
    }
};