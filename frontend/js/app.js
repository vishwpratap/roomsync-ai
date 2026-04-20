
/**
 * RoomSync AI - Main App Controller
 */
const App = {
    init() {
        const session = Utils.getSession();
        if (!session) return this.navigate("auth");
        if (session.role === "admin") return this.navigate("admin-dashboard");
        
        // Try to restore previous page state
        if (session.has_profile) {
            if (Dashboard.restorePageState()) return;
            if (Rooms.restorePageState()) return;
            if (Chat.restorePageState()) return;
            return this.navigate("dashboard");
        }
        
        return this.navigate("questionnaire");
    },

    navigate(view, payload = null) {
        switch (view) {
            case "auth": Auth.render(); break;
            case "questionnaire": Questionnaire.render(); break;
            case "dashboard": Dashboard.render(); break;
            case "rooms": Rooms.renderBrowse(); break;
            case "room-create": Rooms.renderCreate(); break;
            case "room-detail": Rooms.renderDetail(payload); break;
            case "admin-dashboard": Admin.renderDashboard(); break;
            default: Auth.render();
        }
    },

    logout() {
        Utils.clearSession();
        Utils.toast("Logged out", "info");
        this.navigate("auth");
    }
};

document.addEventListener("DOMContentLoaded", () => App.init());
