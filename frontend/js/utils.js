/**
 * RoomSync AI - Utility Helpers
 */
const Utils = {
    $(sel) { return document.querySelector(sel); },
    $$(sel) { return document.querySelectorAll(sel); },

    show(el) { if (typeof el === "string") el = this.$(el); if (el) el.classList.remove("hidden"); },
    hide(el) { if (typeof el === "string") el = this.$(el); if (el) el.classList.add("hidden"); },

    toast(msg, type = "info") {
        const t = document.createElement("div");
        t.className = `toast toast-${type}`;
        t.textContent = msg;
        document.body.appendChild(t);
        requestAnimationFrame(() => t.classList.add("show"));
        setTimeout(() => { t.classList.remove("show"); setTimeout(() => t.remove(), 400); }, 3000);
    },

    animateCount(el, target, duration = 1200) {
        let start = 0;
        const step = (ts) => {
            if (!start) start = ts;
            const p = Math.min((ts - start) / duration, 1);
            el.textContent = Math.round(p * target);
            if (p < 1) requestAnimationFrame(step);
        };
        requestAnimationFrame(step);
    },

    riskColor(level) {
        return level === "HIGH" ? "#ff4757" : level === "MEDIUM" ? "#ffa502" : "#2ed573";
    },

    riskIcon(level) {
        return level === "HIGH" ? "⚠️" : level === "MEDIUM" ? "⚡" : "✅";
    },

    scoreGradient(score) {
        if (score >= 75) return "linear-gradient(135deg, #2ed573, #7bed9f)";
        if (score >= 50) return "linear-gradient(135deg, #ffa502, #eccc68)";
        return "linear-gradient(135deg, #ff4757, #ff6b81)";
    },

    getSession() {
        const s = localStorage.getItem("roomsync_user");
        return s ? JSON.parse(s) : null;
    },

    setSession(data) {
        localStorage.setItem("roomsync_user", JSON.stringify(data));
    },

    clearSession() {
        localStorage.removeItem("roomsync_user");
    },

    getTheme() {
        return localStorage.getItem("roomsync_theme") || "default";
    },

    setTheme(theme) {
        localStorage.setItem("roomsync_theme", theme);
        if (theme === "pink-blue") {
            document.documentElement.setAttribute("data-theme", "pink-blue");
        } else {
            document.documentElement.removeAttribute("data-theme");
        }
    },

    initTheme() {
        const theme = this.getTheme();
        this.setTheme(theme);
    }
};
