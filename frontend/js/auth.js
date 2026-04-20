
/**
 * RoomSync AI - Auth Module
 */
const Auth = {
    mode: "login",

    render() {
        const c = Utils.$("#app-content");
        c.innerHTML = `
        <div class="auth-container fade-in">
            <div class="auth-card glass-card">
                <div class="auth-logo">
                    <div class="logo-icon">RS</div>
                    <h1>RoomSync <span class="accent">AI</span></h1>
                    <p class="subtitle">Behavior-based roommate matching, now with listings and admin tools.</p>
                </div>
                <div class="auth-tabs auth-tabs-3">
                    <button id="tab-login" class="auth-tab active" onclick="Auth.toggle('login')">User Login</button>
                    <button id="tab-signup" class="auth-tab" onclick="Auth.toggle('signup')">Sign Up</button>
                    <button id="tab-admin" class="auth-tab" onclick="Auth.toggle('admin')">Admin</button>
                </div>
                <form id="auth-form" class="auth-form" onsubmit="Auth.submit(event)">
                    <div class="input-group">
                        <label for="auth-name">${this.mode === "admin" ? "Admin Email" : "Username"}</label>
                        <input type="text" id="auth-name" placeholder="${this.mode === "admin" ? "admin@roomsync.ai" : "Enter your username"}" required minlength="2" />
                    </div>
                    <div class="input-group">
                        <label for="auth-pass">Password</label>
                        <input type="password" id="auth-pass" placeholder="Enter your password" required minlength="4" />
                    </div>
                    <button type="submit" class="btn btn-primary btn-full" id="auth-submit">
                        <span id="auth-btn-text">${this.mode === "signup" ? "Create Account" : this.mode === "admin" ? "Admin Login" : "Login"}</span>
                    </button>
                </form>
                <p class="auth-footer" id="auth-footer">${this.footerText()}</p>
            </div>
        </div>`;
    },

    footerText() {
        if (this.mode === "signup") return "Already have an account? <a href=\"#\" onclick=\"Auth.toggle('login');return false;\">Login</a>";
        if (this.mode === "admin") return 'Default seed admin: <strong>admin@roomsync.ai / admin123</strong>. Change it after login.';
        return "Need an account? <a href=\"#\" onclick=\"Auth.toggle('signup');return false;\">Sign up</a>";
    },

    toggle(mode) {
        this.mode = mode;
        this.render();
        Utils.$("#tab-login").classList.toggle("active", mode === "login");
        Utils.$("#tab-signup").classList.toggle("active", mode === "signup");
        Utils.$("#tab-admin").classList.toggle("active", mode === "admin");
    },

    async submit(e) {
        e.preventDefault();
        const nameOrEmail = Utils.$("#auth-name").value.trim();
        const pass = Utils.$("#auth-pass").value;
        const btn = Utils.$("#auth-submit");
        btn.disabled = true;
        btn.querySelector("span").textContent = "Please wait...";

        try {
            let res;
            if (this.mode === "signup") {
                res = await Api.signup(nameOrEmail, pass);
                Utils.setSession({ user_id: res.user_id, name: res.name, has_profile: false, role: "user" });
                Utils.toast(`Welcome, ${res.name}!`, "success");
                return App.navigate("questionnaire");
            }
            if (this.mode === "admin") {
                res = await Api.adminLogin(nameOrEmail, pass);
                Utils.setSession({ admin_id: res.admin_id, email: res.email, role: "admin" });
                Utils.toast("Admin session ready", "success");
                return App.navigate("admin-dashboard");
            }
            res = await Api.login(nameOrEmail, pass);
            Utils.setSession({ user_id: res.user_id, name: res.name, has_profile: res.has_profile, roommate_type: res.roommate_type, role: "user" });
            Utils.toast(`Welcome back, ${res.name}!`, "success");
            App.navigate(res.has_profile ? "dashboard" : "questionnaire");
        } catch (err) {
            Utils.toast(err.message, "error");
        } finally {
            btn.disabled = false;
            btn.querySelector("span").textContent = this.mode === "signup" ? "Create Account" : this.mode === "admin" ? "Admin Login" : "Login";
        }
    }
};
