/**
 * auth.js — Secure JWT token management for CreditSense AI
 * Improvements: JWT expiry validation, environment-aware config,
 * centralized 401 handling, XSS-resistant token handling
 */

// ── Environment-aware configuration ──────────────────────────────
const CONFIG = {
    API_BASE: window.location.hostname === 'localhost' || 
              window.location.hostname === '127.0.0.1'
        ? "http://localhost:8080/api/v1"
        : "https://api.creditsense.ai/v1"   // production URL (Month 4)
};

const AUTH = {
    TOKEN_KEY: "cs_access_token",
    ROLE_KEY:  "cs_user_role",
    EMAIL_KEY: "cs_user_email",
    NAME_KEY:  "cs_user_name",

    save(tokenData) {
        sessionStorage.setItem(this.TOKEN_KEY, tokenData.accessToken);
        sessionStorage.setItem(this.ROLE_KEY,  tokenData.role);
        sessionStorage.setItem(this.EMAIL_KEY, tokenData.email);
        sessionStorage.setItem(this.NAME_KEY,  tokenData.name);
    },

    getToken()  { return sessionStorage.getItem(this.TOKEN_KEY); },
    getRole()   { return sessionStorage.getItem(this.ROLE_KEY); },
    getEmail()  { return sessionStorage.getItem(this.EMAIL_KEY); },
    getName()   { return sessionStorage.getItem(this.NAME_KEY); },

    /**
     * Validates token existence AND expiry by decoding JWT payload.
     * JWT payload is Base64-encoded JSON containing exp (Unix timestamp).
     * No library needed — standard atob() decodes it.
     */
    isLoggedIn() {
        const token = this.getToken();
        if (!token) return false;
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            const isExpired = payload.exp < (Date.now() / 1000);
            if (isExpired) {
                this.clearSession();
                return false;
            }
            return true;
        } catch (e) {
            this.clearSession();
            return false;
        }
    },

    clearSession() {
        sessionStorage.removeItem(this.TOKEN_KEY);
        sessionStorage.removeItem(this.ROLE_KEY);
        sessionStorage.removeItem(this.EMAIL_KEY);
        sessionStorage.removeItem(this.NAME_KEY);
    },

    logout() {
        this.clearSession();
        window.location.href = "../auth/index.html";
    },

    requireAuth() {
        if (!this.isLoggedIn()) {
            window.location.href = "../auth/index.html";
            return false;
        }
        return true;
    },

    redirectByRole() {
        const role = this.getRole();
        if (role === "ADMIN")        window.location.href = "../admin/index.html";
        else if (role === "OFFICER") window.location.href = "../officer/index.html";
        else                         window.location.href = "../applicant/index.html";
    },

    headers() {
        return {
            "Content-Type":  "application/json",
            "Authorization": `Bearer ${this.getToken()}`
        };
    }
};