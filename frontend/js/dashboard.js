
/**
 * RoomSync AI - Dashboard Module
 */
const Dashboard = {
    matches: [],
    allUsers: [],
    compareUserId: null,

    async render() {
        const c = Utils.$("#app-content");
        const s = Utils.getSession();
        c.innerHTML = `
        <div class="dashboard-container fade-in">
            <div class="sidebar">
                <nav class="sidebar-nav">
                    <h4>Navigation</h4>
                    <div class="sidebar-menu">
                        <button class="sidebar-item active" onclick="Dashboard.render()">🏠 Dashboard</button>
                        <button class="sidebar-item" onclick="Dashboard.renderProfile()">👤 Profile</button>
                        <button class="sidebar-item" onclick="Dashboard.renderExploreUsers()">🔍 Explore Users</button>
                        <button class="sidebar-item" onclick="Rooms.renderBrowse()">🏠 Browse Rooms</button>
                        <button class="sidebar-item" onclick="Rooms.renderMyPosts()">📝 My Posts</button>
                        <button class="sidebar-item" onclick="Rooms.renderCreate()">➕ Create Post</button>
                        <button class="sidebar-item" onclick="Chat.render()">💬 Messages <span id="chat-badge" class="chat-badge" style="display:none">0</span></button>
                        <button class="sidebar-item logout" onclick="App.logout()">🚪 Logout</button>
                    </div>
                </nav>
            </div>
            <div class="main-content">
                <div class="dash-header">
                    <div class="dash-welcome">
                        <h2>Good to see you, <span class="accent">${s?.name || "User"}</span></h2>
                        <p class="dash-subtitle">Your behavior profile is ready. Explore smart matches or browse rooms with the same compatibility engine.</p>
                        <span class="badge">${s?.roommate_type || "Balanced Roommate"}</span>
                    </div>
                </div>
                <div class="dash-section">
                    <h3>⭐ Your Top Matches</h3>
                    <div class="matches-grid" id="matches-grid"><div class="loader">Loading matches...</div></div>
                </div>
                <div class="dash-section">
                    <h3>🔍 Search and Compare</h3>
                    <div class="search-bar-wrap">
                        <input type="text" id="search-input" placeholder="Search users by name..." oninput="Dashboard.search(this.value)"/>
                        <span class="search-icon">Find</span>
                    </div>
                    <div class="search-results" id="search-results"></div>
                </div>
                <div class="dash-section">
                    <h3>⚖️ Compare Any Two Users</h3>
                    <div class="compare-section glass-card">
                        <div class="compare-inputs">
                            <div class="compare-field">
                                <label>User 1 (You)</label>
                                <input type="text" value="${s?.name || ''}" disabled class="compare-input"/>
                            </div>
                            <div class="compare-vs">VS</div>
                            <div class="compare-field">
                                <label>User 2</label>
                                <input type="text" id="compare-user2" placeholder="Search for a user..." oninput="Dashboard.compareSearch(this.value)"/>
                                <div class="compare-dropdown" id="compare-dropdown"></div>
                            </div>
                        </div>
                        <div class="compare-actions">
                            <button class="btn btn-primary btn-sm" id="compare-btn" onclick="Dashboard.compareUsers()" disabled>Compare Compatibility</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>`;
        this.compareUserId = null;
        this.loadMatches(s.user_id);
        Chat.loadUnseenCount();
        this.savePageState('dashboard');
    },

    async loadMatches(userId) {
        const grid = Utils.$("#matches-grid");
        try {
            this.matches = await Api.getMatches(userId);
            if (!this.matches.length) {
                grid.innerHTML = '<div class="empty-state"><p>No matches yet. More users need to complete profiles.</p></div>';
                return;
            }
            grid.innerHTML = this.matches.map((m, i) => this.matchCard(m, i)).join("");
        } catch (err) {
            grid.innerHTML = `<div class="empty-state"><p>${err.message}</p></div>`;
        }
    },

    async loadExploreUsers() {
        const res = Utils.$("#explore-results");
        try {
            const users = await Api.getAllUsers();
            this.allUsers = users || [];
            const s = Utils.getSession();
            const filtered = this.allUsers.filter(u => u.id !== s.user_id);
            if (!filtered.length) {
                res.innerHTML = '<div class="empty-state"><p>No users found.</p></div>';
                return;
            }
            res.innerHTML = `<div class="search-list">${filtered.map(u => this.exploreUserCard(u, s)).join("")}</div>`;
        } catch (err) {
            res.innerHTML = `<div class="empty-state"><p>${err.message}</p></div>`;
        }
    },

    async exploreUsers(q) {
        const res = Utils.$("#explore-results");
        if (q.length < 1) {
            this.loadExploreUsers();
            return;
        }
        try {
            const users = await Api.getAllUsers(q);
            const s = Utils.getSession();
            const filtered = users.filter(u => u.id !== s.user_id);
            if (!filtered.length) {
                res.innerHTML = '<p class="muted">No users found.</p>';
                return;
            }
            res.innerHTML = `<div class="search-list">${filtered.map(u => this.exploreUserCard(u, s)).join("")}</div>`;
        } catch (err) {
            res.innerHTML = `<p class="muted">${err.message}</p>`;
        }
    },

    exploreUserCard(u, session) {
        return `
            <div class="search-item glass-card">
                <div class="search-item-info">
                    <strong>${u.name}</strong>
                    <span class="badge badge-sm">${u.roommate_type || "-"}</span>
                    <div class="match-meta"><span>${u.age || "-"} yrs</span><span>${u.profession || "-"}</span></div>
                </div>
                <button class="btn btn-primary btn-xs" onclick="Dashboard.checkCompatibility(${session.user_id}, ${u.id})">Check Compatibility</button>
            </div>`;
    },

    async checkCompatibility(userId1, userId2) {
        const btn = event.target;
        btn.disabled = true;
        btn.textContent = "Checking...";
        try {
            await Compatibility.show(userId1, userId2);
        } catch (err) {
            btn.disabled = false;
            btn.textContent = "Check Compatibility";
            alert("Failed to check compatibility: " + err.message);
        }
    },

    matchCard(m, i) {
        const scoreColor = m.total_score >= 75 ? "high" : m.total_score >= 50 ? "mid" : "low";
        const highlights = (m.highlights || []).slice(0, 2).map(h => `<span class="match-highlight">+ ${h}</span>`).join("");
        const warnings = (m.warnings || []).slice(0, 1).map(w => `<span class="match-warning">! ${w}</span>`).join("");
        return `
        <div class="match-card glass-card slide-up" style="animation-delay:${i * 0.08}s">
            <div class="match-rank">#${i + 1}</div>
            <div class="match-score-ring score-${scoreColor}">
                <svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="44" class="ring-bg"/><circle cx="50" cy="50" r="44" class="ring-fill" style="stroke-dashoffset:${276.5 - (276.5 * m.total_score / 100)}"/></svg>
                <span class="score-num">${Math.round(m.total_score)}%</span>
            </div>
            <div class="match-info">
                <h4>${m.name}</h4>
                <span class="badge badge-sm">${m.roommate_type || "-"}</span>
                <div class="match-meta">${m.age ? `<span>${m.age} yrs</span>` : ""}${m.profession ? `<span>${m.profession}</span>` : ""}${m.cluster_id !== null && m.cluster_id !== undefined ? `<span>Cluster ${m.cluster_id}</span>` : ""}</div>
            </div>
            <div class="match-insights">${highlights}${warnings}</div>
            <div class="match-risk risk-${m.risk_level.toLowerCase()}">${m.risk_level} Risk</div>
            <button class="btn btn-primary btn-sm btn-full" onclick="Compatibility.show(${Utils.getSession().user_id}, ${m.user_id})">View Analysis</button>
        </div>`;
    },

    async search(q) {
        const res = Utils.$("#search-results");
        if (q.length < 1) { res.innerHTML = ""; return; }
        try {
            this.allUsers = await Api.searchUsers(q);
            const s = Utils.getSession();
            const filtered = this.allUsers.filter(u => u.id !== s.user_id);
            if (!filtered.length) { res.innerHTML = '<p class="muted">No users found.</p>'; return; }
            res.innerHTML = `<div class="search-list">${filtered.map(u => `
                <div class="search-item glass-card">
                    <div class="search-item-info">
                        <strong>${u.name}</strong>
                        <span class="badge badge-sm">${u.roommate_type || "-"}</span>
                        <div class="match-meta"><span>${u.age || "-"} yrs</span><span>${u.profession || "-"}</span></div>
                    </div>
                    <button class="btn btn-primary btn-xs" onclick="Compatibility.show(${s.user_id}, ${u.id})">Compare</button>
                </div>`).join("")}</div>`;
        } catch (err) {
            res.innerHTML = `<p class="muted">${err.message}</p>`;
        }
    },

    async compareSearch(q) {
        const dd = Utils.$("#compare-dropdown");
        if (q.length < 1) { dd.innerHTML = ""; dd.classList.remove("show"); return; }
        try {
            const users = await Api.searchUsers(q);
            const s = Utils.getSession();
            const filtered = users.filter(u => u.id !== s.user_id);
            dd.innerHTML = filtered.slice(0, 5).map(u => `<div class="dd-item" onclick="Dashboard.selectCompareUser(${u.id}, decodeURIComponent('${encodeURIComponent(u.name)}'))">${u.name} <span class="badge badge-sm">${u.roommate_type || "-"}</span></div>`).join("") || '<div class="dd-item muted">No users found</div>';
            dd.classList.add("show");
        } catch (_err) {
            dd.innerHTML = "";
            dd.classList.remove("show");
        }
    },

    selectCompareUser(userId, name) {
        this.compareUserId = userId;
        Utils.$("#compare-user2").value = name;
        Utils.$("#compare-dropdown").classList.remove("show");
        Utils.$("#compare-btn").disabled = false;
    },

    compareUsers() {
        if (!this.compareUserId) return;
        Compatibility.show(Utils.getSession().user_id, this.compareUserId);
    },

    savePageState(page, data = null) {
        const state = { page, data, timestamp: Date.now() };
        localStorage.setItem('roomSync_pageState', JSON.stringify(state));
    },

    restorePageState() {
        const stateStr = localStorage.getItem('roomSync_pageState');
        if (!stateStr) return false;
        
        try {
            const state = JSON.parse(stateStr);
            // Only restore if less than 30 minutes old
            if (Date.now() - state.timestamp > 30 * 60 * 1000) {
                localStorage.removeItem('roomSync_pageState');
                return false;
            }
            
            switch (state.page) {
                case 'dashboard':
                    this.render();
                    return true;
                case 'explore-users':
                    this.renderExploreUsers();
                    return true;
                case 'profile':
                    this.renderProfile();
                    return true;
                default:
                    return false;
            }
        } catch (err) {
            console.error("Error restoring page state:", err);
            localStorage.removeItem('roomSync_pageState');
            return false;
        }
    },

    async renderExploreUsers() {
        const c = Utils.$("#app-content");
        const s = Utils.getSession();
        c.innerHTML = `
        <div class="dashboard-container fade-in">
            <div class="sidebar">
                <nav class="sidebar-nav">
                    <h4>Navigation</h4>
                    <div class="sidebar-menu">
                        <button class="sidebar-item" onclick="Dashboard.render()">🏠 Dashboard</button>
                        <button class="sidebar-item" onclick="Dashboard.renderProfile()">👤 Profile</button>
                        <button class="sidebar-item active" onclick="Dashboard.renderExploreUsers()">🔍 Explore Users</button>
                        <button class="sidebar-item" onclick="Rooms.renderBrowse()">🏠 Browse Rooms</button>
                        <button class="sidebar-item" onclick="Rooms.renderMyPosts()">📝 My Posts</button>
                        <button class="sidebar-item" onclick="Rooms.renderCreate()">➕ Create Post</button>
                        <button class="sidebar-item" onclick="Chat.render()">💬 Messages <span id="chat-badge" class="chat-badge" style="display:none">0</span></button>
                        <button class="sidebar-item logout" onclick="App.logout()">🚪 Logout</button>
                    </div>
                </nav>
            </div>
            <div class="main-content">
                <div class="dash-header">
                    <div class="dash-welcome">
                        <h2>Explore Users</h2>
                        <p class="dash-subtitle">Find and connect with other users in the platform.</p>
                    </div>
                </div>
                <div class="dash-section">
                    <h3>👥 All Users</h3>
                    <div class="search-bar-wrap">
                        <input type="text" id="explore-search-input" placeholder="Search users by name..." oninput="Dashboard.exploreUsers(this.value)"/>
                        <span class="search-icon">Find</span>
                    </div>
                    <div class="search-results" id="explore-results"><div class="loader">Loading users...</div></div>
                </div>
            </div>
        </div>`;
        this.loadExploreUsers();
        Chat.loadUnseenCount();
        this.savePageState('explore-users');
    },

    async renderProfile() {
        const c = Utils.$("#app-content");
        const s = Utils.getSession();
        try {
            const userData = await Api.getUser(s.user_id);
            c.innerHTML = `
            <button class="hamburger-menu" onclick="Dashboard.toggleSidebar()"><span></span></button>
            <div class="sidebar-overlay" onclick="Dashboard.closeSidebar()"></div>
            <div class="dashboard-container fade-in">
                <div class="sidebar">
                    <nav class="sidebar-nav">
                        <h4>Navigation</h4>
                        <div class="sidebar-menu">
                            <button class="sidebar-item" onclick="Dashboard.render()">🏠 Dashboard</button>
                            <button class="sidebar-item active" onclick="Dashboard.renderProfile()">👤 Profile</button>
                            <button class="sidebar-item" onclick="Dashboard.renderExploreUsers()">🔍 Explore Users</button>
                            <button class="sidebar-item" onclick="Rooms.renderBrowse()">🏠 Browse Rooms</button>
                            <button class="sidebar-item" onclick="Rooms.renderMyPosts()">📝 My Posts</button>
                            <button class="sidebar-item" onclick="Rooms.renderCreate()">➕ Create Post</button>
                            <button class="sidebar-item" onclick="Chat.render()">💬 Messages <span id="chat-badge" class="chat-badge" style="display:none">0</span></button>
                            <button class="sidebar-item logout" onclick="App.logout()">🚪 Logout</button>
                        </div>
                    </nav>
                </div>
                <div class="main-content">
                    <div class="dash-header">
                        <div class="dash-welcome">
                            <h2>My Profile</h2>
                            <p class="dash-subtitle">View and edit your profile information.</p>
                        </div>
                    </div>
                    <div class="dash-section">
                        <div class="detail-card glass-card">
                            <div class="q-body">
                                <h3>✏️ Edit Profile</h3>
                                <div class="fields-grid">
                                    <div class="field"><label>Name</label><input type="text" id="profile-name" value="${userData.name || ''}" disabled /></div>
                                    <div class="field"><label>Age</label><input type="number" id="profile-age" value="${userData.age || ''}" /></div>
                                    <div class="field"><label>Profession</label><input type="text" id="profile-profession" value="${userData.profession || ''}" /></div>
                                    <div class="field"><label>Gender</label><input type="text" id="profile-gender" value="${userData.gender || ''}" /></div>
                                </div>
                                <button class="btn btn-primary btn-sm" onclick="Dashboard.updateProfile()">Save Changes</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>`;
        } catch (err) {
            c.innerHTML = `<div class="empty-state"><p>Error loading profile: ${err.message}</p></div>`;
        }
        Chat.loadUnseenCount();
        this.savePageState('profile');
    },

    async updateProfile() {
        const s = Utils.getSession();
        const age = parseInt(Utils.$("#profile-age").value);
        const profession = Utils.$("#profile-profession").value.trim();
        const gender = Utils.$("#profile-gender").value.trim();
        
        try {
            await Api.updateProfile(s.user_id, age, profession, gender);
            alert("Profile updated successfully!");
            this.render();
        } catch (err) {
            alert("Failed to update profile: " + err.message);
        }
    }
};
