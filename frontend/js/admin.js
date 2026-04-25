
/**
 * RoomSync AI - Admin Module
 */
const AdminScenarioPresets = {
    cleanliness: {
        title: "Shared Kitchen Cleanup",
        question: "Your roommate keeps leaving the shared kitchen a little messy after cooking. What feels most natural to you?",
        description: "Use this when you want to measure cleanliness expectations in shared spaces.",
        options: [
            { text: "It does not bother me much.", style: "easygoing" },
            { text: "I will usually tidy up and move on.", style: "adaptive" },
            { text: "I would ask for a cleaner routine.", style: "communicative" },
            { text: "I expect the kitchen to stay clean every time.", style: "strict" },
        ],
    },
    noise: {
        title: "Late-Night Noise",
        question: "It is getting late and your roommate starts making more noise than usual. What do you usually do?",
        description: "Use this to capture sound sensitivity and quiet-hour expectations.",
        options: [
            { text: "I can usually ignore it.", style: "easygoing" },
            { text: "I adjust first and see if it settles down.", style: "adaptive" },
            { text: "I ask them to lower the noise a little.", style: "communicative" },
            { text: "I want strict quiet hours at night.", style: "strict" },
        ],
    },
    social: {
        title: "Unexpected Guests",
        question: "Your roommate invites friends over without much notice. What feels closest to your reaction?",
        description: "Use this to evaluate guest comfort and social energy.",
        options: [
            { text: "I am usually happy to roll with it.", style: "easygoing" },
            { text: "I can adapt, even if I need a little space.", style: "adaptive" },
            { text: "I would like a heads-up next time.", style: "communicative" },
            { text: "I need firm guest boundaries.", style: "strict" },
        ],
    },
    sharing: {
        title: "Shared Items",
        question: "Your roommate uses something of yours without asking. How do you handle it?",
        description: "Use this to measure boundaries and shared-property expectations.",
        options: [
            { text: "I am pretty relaxed about sharing.", style: "easygoing" },
            { text: "I usually let it go once or twice.", style: "adaptive" },
            { text: "I remind them to ask first next time.", style: "communicative" },
            { text: "I want very clear personal boundaries.", style: "strict" },
        ],
    },
    routine: {
        title: "Daily Routine Clash",
        question: "You and your roommate have very different daily routines. What sounds most like you?",
        description: "Use this to understand routine, flexibility, and habit overlap.",
        options: [
            { text: "I can adapt pretty easily.", style: "easygoing" },
            { text: "I adjust if the household still feels calm.", style: "adaptive" },
            { text: "I talk through a routine that works for both of us.", style: "communicative" },
            { text: "I prefer a predictable routine every day.", style: "strict" },
        ],
    },
    balance: {
        title: "Work vs Social Time",
        question: "You need a focused evening, but your roommate wants a lively shared space. What feels right?",
        description: "Use this to test how people balance focus and fun in shared living.",
        options: [
            { text: "I can usually go with the flow.", style: "easygoing" },
            { text: "I adapt if I can still make my plan work.", style: "adaptive" },
            { text: "I ask for a compromise that night.", style: "communicative" },
            { text: "My quiet plan should take priority.", style: "strict" },
        ],
    },
    compromise: {
        title: "Shared Decision",
        question: "You and your roommate want different things for the apartment. How do you usually approach it?",
        description: "Use this to measure flexibility and conflict handling in shared decisions.",
        options: [
            { text: "I am fine letting the other person choose.", style: "easygoing" },
            { text: "I adjust if it keeps things smooth.", style: "adaptive" },
            { text: "I talk it out and aim for middle ground.", style: "communicative" },
            { text: "I prefer a clear rule or fixed agreement.", style: "strict" },
        ],
    },
    flexibility: {
        title: "Unexpected Change",
        question: "A sudden change affects the apartment routine. What feels most like you?",
        description: "Use this when you want to understand how adaptable someone is under change.",
        options: [
            { text: "I take it in stride.", style: "easygoing" },
            { text: "I adapt once I understand the situation.", style: "adaptive" },
            { text: "I talk through what needs to change.", style: "communicative" },
            { text: "I prefer sticking to the original plan.", style: "strict" },
        ],
    },
    fairness: {
        title: "Bills and Fairness",
        question: "A shared expense feels uneven this month. What is your usual response?",
        description: "Use this to measure fairness expectations and conflict style.",
        options: [
            { text: "I do not mind keeping it simple.", style: "easygoing" },
            { text: "I let it slide if it is not a pattern.", style: "adaptive" },
            { text: "I bring it up and suggest a fair split.", style: "communicative" },
            { text: "I want a clear, exact system every time.", style: "strict" },
        ],
    },
};

const AdminOptionStyles = {
    easygoing: {
        label: "Easygoing",
        traits: { cleanliness_tolerance: 5, noise_tolerance: 5, social_tolerance: 5, conflict_style: 5, flexibility: 5 },
    },
    adaptive: {
        label: "Adaptive",
        traits: { cleanliness_tolerance: 4, noise_tolerance: 4, social_tolerance: 3, conflict_style: 4, flexibility: 4 },
    },
    communicative: {
        label: "Communicative",
        traits: { cleanliness_tolerance: 2, noise_tolerance: 2, social_tolerance: 2, conflict_style: 3, flexibility: 3 },
    },
    strict: {
        label: "Strict Boundary",
        traits: { cleanliness_tolerance: 1, noise_tolerance: 1, social_tolerance: 1, conflict_style: 1, flexibility: 1 },
    },
};

const AdminScenarioCategories = Object.keys(AdminScenarioPresets);

const Admin = {
    selectedScenarioId: null,
    selectedUserId: null,

    async renderDashboard() {
        const c = Utils.$("#app-content");
        c.innerHTML = `
        <div class="admin-container fade-in">
            <div class="admin-sidebar">
                <div class="admin-brand">
                    <h1>Admin</h1>
                    <span class="admin-badge">Control Panel</span>
                </div>
                <nav class="admin-nav">
                    <button class="admin-nav-item active" data-section="overview" onclick="Admin.switchSection('overview')">
                        <span class="nav-icon">📊</span>
                        <span>Overview</span>
                    </button>
                    <button class="admin-nav-item" data-section="users" onclick="Admin.switchSection('users')">
                        <span class="nav-icon">👥</span>
                        <span>Users</span>
                    </button>
                    <button class="admin-nav-item" data-section="posts" onclick="Admin.switchSection('posts')">
                        <span class="nav-icon">🏠</span>
                        <span>Room Posts</span>
                    </button>
                    <button class="admin-nav-item" data-section="scenarios" onclick="Admin.switchSection('scenarios')">
                        <span class="nav-icon">📝</span>
                        <span>Scenarios</span>
                    </button>
                    <button class="admin-nav-item" data-section="settings" onclick="Admin.switchSection('settings')">
                        <span class="nav-icon">⚙️</span>
                        <span>Settings</span>
                    </button>
                </nav>
                <div class="admin-footer">
                    <button class="admin-logout-btn" onclick="App.logout()">
                        <span>🚪</span>
                        <span>Logout</span>
                    </button>
                </div>
            </div>
            <div class="admin-main">
                <div class="admin-header">
                    <h2 id="admin-section-title">Overview</h2>
                    <button class="admin-refresh-btn" onclick="Admin.renderDashboard()">🔄 Refresh</button>
                </div>
                <div class="admin-content" id="admin-content">
                    <div class="admin-section active" id="section-overview">
                        <div class="admin-card admin-card-full" id="admin-metrics"><div class="loader">Loading...</div></div>
                    </div>
                    <div class="admin-section" id="section-users">
                        <div class="admin-card admin-card-full" id="admin-users"><div class="loader">Loading...</div></div>
                    </div>
                    <div class="admin-section" id="section-posts">
                        <div class="admin-card admin-card-full" id="admin-posts"><div class="loader">Loading...</div></div>
                    </div>
                    <div class="admin-section" id="section-scenarios">
                        <div class="admin-card admin-card-full" id="admin-scenarios"><div class="loader">Loading...</div></div>
                    </div>
                    <div class="admin-section" id="section-settings">
                        <div class="admin-card admin-card-full" id="admin-settings"><div class="loader">Loading...</div></div>
                    </div>
                </div>
            </div>
        </div>`;
        await Promise.all([this.loadMetrics(), this.loadUsers(), this.loadRoomPosts(), this.loadScenarios()]);
    },

    switchSection(section) {
        document.querySelectorAll('.admin-nav-item').forEach(item => item.classList.remove('active'));
        document.querySelector(`[data-section="${section}"]`).classList.add('active');
        
        document.querySelectorAll('.admin-section').forEach(sec => sec.classList.remove('active'));
        document.getElementById(`section-${section}`).classList.add('active');
        
        const titles = {
            overview: 'Overview',
            users: 'User Management',
            posts: 'Room Posts',
            scenarios: 'Scenario Management',
            settings: 'Settings'
        };
        document.getElementById('admin-section-title').textContent = titles[section];
        
        // Load weights only when switching to settings section
        if (section === 'settings') {
            this.loadWeights();
        }
    },

    async loadMetrics() {
        const target = Utils.$("#admin-metrics");
        if (!target) {
            console.error("Admin metrics target not found");
            return;
        }
        try {
            target.innerHTML = '<div class="loader">Loading...</div>';
            const data = await Api.getAdminDashboard();
            target.innerHTML = `
            <h3>📊 Overview</h3>
            <div class="admin-stats-grid">
                <div class="admin-stat-item">
                    <span class="stat-value">${data.total_users || 0}</span>
                    <span class="stat-label">Total Users</span>
                </div>
                <div class="admin-stat-item">
                    <span class="stat-value">${data.total_room_posts || 0}</span>
                    <span class="stat-label">Room Posts</span>
                </div>
                <div class="admin-stat-item">
                    <span class="stat-value">${data.total_matches_generated || 0}</span>
                    <span class="stat-label">Matches</span>
                </div>
                <div class="admin-stat-item">
                    <span class="stat-value">${data.analytics?.average_compatibility_score || 0}%</span>
                    <span class="stat-label">Avg Score</span>
                </div>
            </div>`;
        } catch (err) {
            console.error("Failed to load metrics:", err);
            target.innerHTML = `<p class="error-text">Failed to load overview: ${err.message}</p>`;
        }
    },

    async cleanupDuplicatePosts() {
        if (!confirm("This will delete duplicate room posts from the database. Are you sure?")) return;
        try {
            const result = await fetch("https://roomsync-ai.onrender.com/cleanup-duplicate-posts", { method: "POST" });
            const data = await result.json();
            alert(data.message);
            this.loadMetrics();
        } catch (err) {
            alert("Failed to cleanup: " + err.message);
        }
    },

    async cleanupAllDuplicates() {
        if (!confirm("This will delete ALL posts with the same title, keeping only the oldest one. Are you sure?")) return;
        try {
            const result = await fetch("https://roomsync-ai.onrender.com/cleanup-all-duplicates", { method: "POST" });
            const data = await result.json();
            alert(data.message);
            this.loadMetrics();
        } catch (err) {
            alert("Failed to cleanup: " + err.message);
        }
    },

    async loadRoomPosts() {
        const target = Utils.$("#admin-posts");
        if (!target) {
            console.error("Admin posts target not found");
            return;
        }
        try {
            target.innerHTML = '<div class="loader">Loading...</div>';
            const data = await fetch("https://roomsync-ai.onrender.com/admin/room-posts").then(r => r.json());
            const posts = data.posts || [];
            target.innerHTML = `
            <div class="admin-section-header">
                <h3>🏠 Room Posts Management</h3>
                <small class="muted">${posts.length} total posts</small>
            </div>
            <div class="admin-table-container">
                <table class="admin-table">
                    <thead>
                        <tr>
                            <th>Title</th>
                            <th>Owner</th>
                            <th>Location</th>
                            <th>Rent</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${posts.map(post => `
                        <tr>
                            <td><strong>${post.title}</strong></td>
                            <td>${post.owner_name || "User"}</td>
                            <td>${post.location}</td>
                            <td>₹${post.rent}</td>
                            <td>
                                <button class="admin-table-btn danger" onclick="Admin.deleteRoomPost(${post.id})">Delete</button>
                            </td>
                        </tr>
                        `).join("") || '<tr><td colspan="5" class="no-data">No room posts found</td></tr>'}
                    </tbody>
                </table>
            </div>`;
        } catch (err) {
            console.error("Failed to load room posts:", err);
            target.innerHTML = `<p class="error-text">Failed to load room posts: ${err.message}</p>`;
        }
    },

    async deleteRoomPost(postId) {
        if (!confirm("Delete this room post? This action cannot be undone.")) return;
        try {
            const result = await fetch(`https://roomsync-ai.onrender.com/admin/room-posts/${postId}`, { method: "DELETE" });
            const data = await result.json();
            alert(data.message);
            this.loadRoomPosts();
            this.loadMetrics();
        } catch (err) {
            alert("Failed to delete post: " + err.message);
        }
    },

    async seedScenarios() {
        if (!confirm("This will delete all existing scenarios and re-seed them with options. Are you sure?")) return;
        try {
            const result = await fetch("https://roomsync-ai.onrender.com/admin/seed-scenarios", { method: "POST" });
            const data = await result.json();
            alert(data.message);
            this.loadMetrics();
        } catch (err) {
            alert("Failed to seed scenarios: " + err.message);
        }
    },

    async loadWeights() {
        const target = Utils.$("#admin-settings");
        if (!target) {
            console.error("Admin settings target not found");
            return;
        }
        try {
            target.innerHTML = '<div class="loader">Loading...</div>';
            const weights = await Api.getWeights();
            target.innerHTML = `
            <div class="admin-section-header">
                <h3>⚙️ Settings</h3>
            </div>
            <div class="admin-card">
                <h4>Weight Control</h4>
                <p class="muted" style="margin-bottom: 20px;">Recommended defaults give slightly more importance to cleanliness and behavioral traits, while keeping personality as a supporting signal.</p>
                <form class="admin-weight-form" onsubmit="Admin.saveWeights(event)">
                    <div class="admin-weight-grid">
                        <div class="admin-weight-item">
                            <label>Cleanliness Weight</label>
                            <input type="number" step="0.05" id="weight-cleanliness" value="${weights.cleanliness}" />
                            <small>Most common source of day-to-day friction.</small>
                        </div>
                        <div class="admin-weight-item">
                            <label>Sleep Weight</label>
                            <input type="number" step="0.05" id="weight-sleep" value="${weights.sleep}" />
                            <small>Important, but usually manageable with clear routines.</small>
                        </div>
                        <div class="admin-weight-item">
                            <label>Personality Weight</label>
                            <input type="number" step="0.05" id="weight-personality" value="${weights.personality}" />
                            <small>Useful context, but should not overpower lifestyle fit.</small>
                        </div>
                        <div class="admin-weight-item">
                            <label>Trait Weight</label>
                            <input type="number" step="0.05" id="weight-trait" value="${weights.trait}" />
                            <small>Behavior under real scenarios should strongly influence the score.</small>
                        </div>
                    </div>
                    <div class="admin-weight-actions">
                        <button type="button" class="admin-action-btn" onclick="Admin.applyRecommendedWeights()">Use Recommended</button>
                        <button type="submit" class="admin-action-btn" style="background: var(--gradient-main); color: #fff;">Update Weights</button>
                    </div>
                </form>
            </div>`;
        } catch (err) {
            console.error("Failed to load weights:", err);
            target.innerHTML = `<p class="error-text">Failed to load settings: ${err.message}</p>`;
        }
    },

    applyRecommendedWeights() {
        Utils.$("#weight-cleanliness").value = 1.25;
        Utils.$("#weight-sleep").value = 1.10;
        Utils.$("#weight-personality").value = 0.95;
        Utils.$("#weight-trait").value = 1.15;
    },

    async saveWeights(e) {
        e.preventDefault();
        try {
            await Api.updateWeights({
                cleanliness: Number(Utils.$("#weight-cleanliness").value),
                sleep: Number(Utils.$("#weight-sleep").value),
                personality: Number(Utils.$("#weight-personality").value),
                trait: Number(Utils.$("#weight-trait").value),
            });
            Utils.toast("Weights updated", "success");
            this.loadMetrics();
        } catch (err) {
            Utils.toast(err.message, "error");
        }
    },

    async loadUsers(search = "") {
        const target = Utils.$("#admin-users");
        if (!target) {
            console.error("Admin users target not found");
            return;
        }
        try {
            target.innerHTML = '<div class="loader">Loading...</div>';
            const users = await Api.getAdminUsers(search);
            if (users.length && !users.some(user => user.id === this.selectedUserId)) {
                this.selectedUserId = users[0].id;
            }
            target.innerHTML = `
            <div class="admin-section-header">
                <h3>👥 User Management</h3>
                <input type="text" class="admin-search-input" placeholder="Search users..." value="${search}" oninput="Admin.loadUsers(this.value)" />
            </div>
            <div class="admin-table-container">
                <table class="admin-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Type</th>
                            <th>Profession</th>
                            <th>Cluster</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${users.map(user => `
                        <tr class="${user.id === this.selectedUserId ? 'active' : ''}">
                            <td><strong>${user.name}</strong></td>
                            <td><span class="admin-badge-small">${user.roommate_type || '-'}</span></td>
                            <td>${user.profession || '-'}</td>
                            <td>${user.cluster_id ?? '-'}</td>
                            <td>
                                <button class="admin-table-btn" onclick="Admin.showUser(${user.id})">View</button>
                                <button class="admin-table-btn danger" onclick="Admin.deleteUser(${user.id})">Delete</button>
                            </td>
                        </tr>
                        `).join("") || '<tr><td colspan="5" class="no-data">No users found</td></tr>'}
                    </tbody>
                </table>
            </div>`;
        } catch (err) {
            console.error("Failed to load users:", err);
            target.innerHTML = `<p class="error-text">Failed to load users: ${err.message}</p>`;
        }
    },

    async showUser(userId) {
        try {
            this.selectedUserId = userId;
            const user = await Api.getAdminUser(userId);
            alert(`User: ${user.name}\nProfession: ${user.profession || '-'}\nType: ${user.roommate_type || '-'}\nCluster: ${user.cluster_id ?? '-'}`);
        } catch (err) {
            alert("Failed to load user: " + err.message);
        }
    },

    labelize(key) {
        return key.replace(/_/g, " ").replace(/\b\w/g, match => match.toUpperCase());
    },

    async deleteUser(userId) {
        if (!window.confirm("Delete this user and related profile data?")) return;
        try {
            await Api.deleteAdminUser(userId);
            Utils.toast("User deleted", "success");
            this.loadUsers();
            this.loadMetrics();
        } catch (err) {
            Utils.toast(err.message, "error");
        }
    },

    async loadScenarios() {
        const target = Utils.$("#admin-scenarios");
        if (!target) {
            console.error("Admin scenarios target not found");
            return;
        }
        try {
            target.innerHTML = '<div class="loader">Loading...</div>';
            const scenarios = await Api.getAdminScenarios();
            target.innerHTML = `
            <div class="admin-section-header">
                <h3>📝 Scenario Management</h3>
                <div style="display: flex; gap: 8px;">
                    <button class="admin-action-btn" onclick="Admin.newScenario()">+ New Scenario</button>
                    <button class="admin-action-btn" onclick="Admin.clearAndSeedScenarios()">🔄 Clear & Seed Demo</button>
                </div>
            </div>
            <div class="admin-table-container">
                <table class="admin-table">
                    <thead>
                        <tr>
                            <th>Title</th>
                            <th>Category</th>
                            <th>Options</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${scenarios.map(s => `
                        <tr>
                            <td><strong>${s.title}</strong></td>
                            <td><span class="admin-badge-small">${s.category || '-'}</span></td>
                            <td>${s.options?.length || 0} options</td>
                            <td>
                                <button class="admin-table-btn" onclick="Admin.editScenario(${s.db_id})">Edit</button>
                            </td>
                        </tr>
                        `).join("") || '<tr><td colspan="4" class="no-data">No scenarios found</td></tr>'}
                    </tbody>
                </table>
            </div>`;
        } catch (err) {
            console.error("Failed to load scenarios:", err);
            target.innerHTML = `<p class="error-text">Failed to load scenarios: ${err.message}</p>`;
        }
    },

    async clearAndSeedScenarios() {
        if (!confirm("This will delete all existing scenarios and add 4 demo scenarios. Continue?")) return;
        try {
            console.log("Clearing scenarios...");
            await fetch(`${API_BASE}/admin/clear-scenarios`, {
                method: "POST",
                headers: { "Content-Type": "application/json" }
            });
            console.log("Seeding demo scenarios...");
            await fetch(`${API_BASE}/admin/seed-demo-scenarios`, {
                method: "POST",
                headers: { "Content-Type": "application/json" }
            });
            Utils.toast("Scenarios cleared and demo data seeded", "success");
            this.loadScenarios();
        } catch (err) {
            console.error("Failed to clear and seed scenarios:", err);
            Utils.toast("Failed to clear and seed: " + err.message, "error");
        }
    },

    async newScenario() {
        console.log("Opening new scenario form");
        const target = Utils.$("#admin-scenarios");
        const options = [
            { text: "", emoji: "", index: 0 },
            { text: "", emoji: "", index: 1 },
            { text: "", emoji: "", index: 2 },
            { text: "", emoji: "", index: 3 }
        ];
        
        target.innerHTML = `
        <div class="admin-section-header">
            <h3>📝 New Scenario</h3>
            <button class="admin-action-btn" onclick="Admin.loadScenarios()">← Back</button>
        </div>
        <div class="admin-card">
            <form class="admin-weight-form" onsubmit="Admin.createScenario(event)">
                <div class="admin-weight-item">
                    <label>Title</label>
                    <input type="text" id="scenario-title" required />
                </div>
                <div class="admin-weight-item">
                    <label>Category</label>
                    <select id="scenario-category">
                        ${AdminScenarioCategories.map(category => `<option value="${category}">${Admin.labelize(category)}</option>`).join("")}
                    </select>
                </div>
                <div class="admin-weight-item">
                    <label>Slug</label>
                    <input type="text" id="scenario-slug" required />
                </div>
                <div class="admin-weight-item" style="grid-column: 1 / -1;">
                    <label>Question</label>
                    <textarea id="scenario-question" rows="3" required></textarea>
                </div>
                <div class="admin-weight-item" style="grid-column: 1 / -1;">
                    <label>Admin Note</label>
                    <textarea id="scenario-description" rows="2"></textarea>
                </div>
                <div class="admin-weight-item" style="grid-column: 1 / -1;">
                    <label>Icon Label</label>
                    <input type="text" id="scenario-icon" />
                </div>
                <div style="grid-column: 1 / -1; margin-top: 20px;">
                    <h4 style="margin-bottom: 16px;">Response Options</h4>
                    <div class="admin-weight-grid">
                        ${options.map((option, index) => `
                            <div class="admin-weight-item">
                                <label>Option ${index + 1} Text</label>
                                <textarea id="option-text-${index}" rows="2"></textarea>
                            </div>
                            <div class="admin-weight-item">
                                <label>Option ${index + 1} Emoji</label>
                                <input type="text" id="option-emoji-${index}" />
                            </div>
                        `).join("")}
                    </div>
                </div>
                <div class="admin-weight-actions">
                    <button type="submit" class="admin-action-btn" style="background: var(--gradient-main); color: #fff;">Create Scenario</button>
                </div>
            </form>
        </div>`;
    },

    async createScenario(e) {
        e.preventDefault();
        console.log("Creating new scenario");
        try {
            const options = [];
            for (let i = 0; i < 4; i++) {
                const text = Utils.$(`#option-text-${i}`).value;
                const emoji = Utils.$(`#option-emoji-${i}`).value;
                if (text.trim()) {
                    options.push({ text, emoji, traits: {} });
                }
            }
            
            const scenarioData = {
                title: Utils.$("#scenario-title").value,
                category: Utils.$("#scenario-category").value,
                slug: Utils.$("#scenario-slug").value,
                question: Utils.$("#scenario-question").value,
                description: Utils.$("#scenario-description").value,
                icon: Utils.$("#scenario-icon").value,
                options: options
            };
            
            console.log("Scenario data to create:", scenarioData);
            await Api.createScenario(scenarioData);
            console.log("Scenario created successfully");
            Utils.toast("Scenario created successfully", "success");
            this.loadScenarios();
        } catch (err) {
            console.error("Failed to create scenario:", err);
            Utils.toast("Failed to create scenario: " + err.message, "error");
        }
    },

    async editScenario(scenarioId) {
        console.log("Editing scenario:", scenarioId);
        try {
            const scenarios = await Api.getAdminScenarios();
            console.log("Loaded scenarios:", scenarios);
            const scenario = scenarios.find(s => s.db_id === scenarioId);
            if (!scenario) {
                console.error("Scenario not found for ID:", scenarioId);
                alert("Scenario not found");
                return;
            }
            
            const options = (scenario.options || []).slice(0, 4).map((option, index) => ({
                text: option.text || "",
                emoji: option.emoji || "",
                index,
            }));
            
            while (options.length < 4) {
                options.push({ text: "", emoji: "", index: options.length });
            }
            
            const target = Utils.$("#admin-scenarios");
            target.innerHTML = `
            <div class="admin-section-header">
                <h3>📝 Edit Scenario</h3>
                <button class="admin-action-btn" onclick="Admin.loadScenarios()">← Back</button>
            </div>
            <div class="admin-card">
                <form class="admin-weight-form" onsubmit="Admin.saveScenario(event, ${scenario.db_id})">
                    <div class="admin-weight-item">
                        <label>Title</label>
                        <input type="text" id="scenario-title" value="${scenario.title || ''}" required />
                    </div>
                    <div class="admin-weight-item">
                        <label>Category</label>
                        <select id="scenario-category">
                            ${AdminScenarioCategories.map(category => `<option value="${category}" ${scenario.category === category ? "selected" : ""}>${Admin.labelize(category)}</option>`).join("")}
                        </select>
                    </div>
                    <div class="admin-weight-item">
                        <label>Slug</label>
                        <input type="text" id="scenario-slug" value="${scenario.slug || ''}" required />
                    </div>
                    <div class="admin-weight-item" style="grid-column: 1 / -1;">
                        <label>Question</label>
                        <textarea id="scenario-question" rows="3" required>${scenario.question || ''}</textarea>
                    </div>
                    <div class="admin-weight-item" style="grid-column: 1 / -1;">
                        <label>Admin Note</label>
                        <textarea id="scenario-description" rows="2">${scenario.description || ''}</textarea>
                    </div>
                    <div class="admin-weight-item" style="grid-column: 1 / -1;">
                        <label>Icon Label</label>
                        <input type="text" id="scenario-icon" value="${scenario.icon || ''}" />
                    </div>
                    <div style="grid-column: 1 / -1; margin-top: 20px;">
                        <h4 style="margin-bottom: 16px;">Response Options</h4>
                        <div class="admin-weight-grid">
                            ${options.map((option, index) => `
                                <div class="admin-weight-item">
                                    <label>Option ${index + 1} Text</label>
                                    <textarea id="option-text-${index}" rows="2" required>${option.text}</textarea>
                                </div>
                                <div class="admin-weight-item">
                                    <label>Option ${index + 1} Emoji</label>
                                    <input type="text" id="option-emoji-${index}" value="${option.emoji}" />
                                </div>
                            `).join("")}
                        </div>
                    </div>
                    <div class="admin-weight-actions">
                        <button type="submit" class="admin-action-btn" style="background: var(--gradient-main); color: #fff;">Save Scenario</button>
                    </div>
                </form>
            </div>`;
        } catch (err) {
            console.error("Failed to load scenario for editing:", err);
            alert("Failed to load scenario: " + err.message);
        }
    },

    async saveScenario(e, scenarioId) {
        e.preventDefault();
        console.log("Saving scenario:", scenarioId);
        try {
            const options = [];
            for (let i = 0; i < 4; i++) {
                const text = Utils.$(`#option-text-${i}`).value;
                const emoji = Utils.$(`#option-emoji-${i}`).value;
                if (text.trim()) {
                    options.push({ text, emoji, traits: {} });
                }
            }
            
            const scenarioData = {
                title: Utils.$("#scenario-title").value,
                category: Utils.$("#scenario-category").value,
                slug: Utils.$("#scenario-slug").value,
                question: Utils.$("#scenario-question").value,
                description: Utils.$("#scenario-description").value,
                icon: Utils.$("#scenario-icon").value,
                options: options
            };
            
            console.log("Scenario data to save:", scenarioData);
            await Api.updateScenario(scenarioId, scenarioData);
            console.log("Scenario saved successfully");
            Utils.toast("Scenario updated successfully", "success");
            this.loadScenarios();
        } catch (err) {
            console.error("Failed to save scenario:", err);
            Utils.toast("Failed to save scenario: " + err.message, "error");
        }
    },

    scenarioEditor(scenario) {
        if (!scenario) return '<p class="muted">No scenarios yet.</p>';
        const options = (scenario.options || []).slice(0, 4).map((option, index) => ({
            text: option.text || "",
            emoji: option.emoji || "",
            style: this.detectOptionStyle(option.traits),
            index,
        }));
        while (options.length < 4) {
            options.push({ text: "", emoji: "", style: "adaptive", index: options.length });
        }
        return `
        <form class="fields-grid" onsubmit="Admin.saveScenario(event, ${scenario.db_id || 0})">
            <div class="field"><label>Title</label><input type="text" id="scenario-title" value="${scenario.title || ''}" required /></div>
            <div class="field"><label>Category</label><select id="scenario-category" onchange="Admin.onCategoryChange(this.value)">${AdminScenarioCategories.map(category => `<option value="${category}" ${scenario.category === category ? "selected" : ""}>${Admin.labelize(category)}</option>`).join("")}</select></div>
            <div class="field"><label>Slug</label><input type="text" id="scenario-slug" value="${scenario.slug || ''}" required /></div>
            <div class="field full"><label>Question</label><textarea id="scenario-question" rows="3" required>${scenario.question || ''}</textarea></div>
            <div class="field full"><label>Admin Note</label><textarea id="scenario-description" rows="2">${scenario.description || ''}</textarea></div>
            <div class="field"><label>Icon Label</label><input type="text" id="scenario-icon" value="${scenario.icon || ''}" /></div>
            <div class="field full">
                <div class="scenario-help-row">
                    <label>Response Options</label>
                    <button class="btn btn-secondary btn-xs" type="button" onclick="Admin.applyPresetToCurrent()">Fill Starter Options</button>
                </div>
                <div class="scenario-option-editor-grid">
                    ${options.map((option, index) => `
                        <div class="scenario-option-editor">
                            <h5>Option ${index + 1}</h5>
                            <label>Option Text</label>
                            <textarea id="option-text-${index}" rows="2" required>${option.text}</textarea>
                            <label>Behavior Style</label>
                            <select id="option-style-${index}">
                                ${Object.entries(AdminOptionStyles).map(([styleKey, style]) => `<option value="${styleKey}" ${option.style === styleKey ? "selected" : ""}>${style.label}</option>`).join("")}
                            </select>
                            <p class="muted">${this.styleHelpText(option.style)}</p>
                        </div>
                    `).join("")}
                </div>
            </div>
            <button class="btn btn-primary btn-sm" type="submit">Save Scenario</button>
        </form>`;
    },

    detectOptionStyle(traits = {}) {
        const styles = Object.entries(AdminOptionStyles);
        for (const [styleKey, style] of styles) {
            if (JSON.stringify(style.traits) === JSON.stringify(traits || {})) {
                return styleKey;
            }
        }
        return "adaptive";
    },

    styleHelpText(styleKey) {
        const messages = {
            easygoing: "Very tolerant and flexible in shared living situations.",
            adaptive: "Usually adjusts first and keeps the peace.",
            communicative: "Prefers talking things through and setting expectations.",
            strict: "Needs firm boundaries and clear standards.",
        };
        return messages[styleKey] || messages.adaptive;
    },

    editScenario(id) {
        this.selectedScenarioId = id;
        this.loadScenarios();
    },

    newScenario() {
        const editor = Utils.$("#scenario-editor");
        const preset = AdminScenarioPresets.cleanliness;
        editor.innerHTML = this.scenarioEditor({
            db_id: 0,
            slug: "new_scenario",
            title: preset.title,
            question: preset.question,
            description: preset.description,
            icon: "SCENARIO",
            category: "cleanliness",
            options: preset.options.map(option => ({ text: option.text, emoji: "", traits: AdminOptionStyles[option.style].traits })),
        });
    },

    onCategoryChange(category) {
        const slugField = Utils.$("#scenario-slug");
        if (slugField && (!slugField.value || slugField.value === "new_scenario")) {
            slugField.value = `${category}_scenario`;
        }
    },

    applyPresetToCurrent() {
        const category = Utils.$("#scenario-category")?.value || "cleanliness";
        const preset = AdminScenarioPresets[category];
        if (!preset) return;
        Utils.$("#scenario-title").value = preset.title;
        Utils.$("#scenario-question").value = preset.question;
        Utils.$("#scenario-description").value = preset.description;
        Utils.$("#scenario-slug").value = `${category}_${preset.title.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "")}`;
        for (let index = 0; index < 4; index += 1) {
            const option = preset.options[index];
            if (!option) continue;
            Utils.$(`#option-text-${index}`).value = option.text;
            Utils.$(`#option-style-${index}`).value = option.style;
        }
    },

    async saveScenario(e, scenarioId) {
        e.preventDefault();
        try {
            const options = [0, 1, 2, 3].map(index => {
                const style = Utils.$(`#option-style-${index}`).value;
                return {
                    text: Utils.$(`#option-text-${index}`).value.trim(),
                    emoji: "",
                    traits: AdminOptionStyles[style].traits,
                };
            });
            const payload = {
                slug: Utils.$("#scenario-slug").value.trim(),
                title: Utils.$("#scenario-title").value.trim(),
                question: Utils.$("#scenario-question").value.trim(),
                description: Utils.$("#scenario-description").value.trim(),
                icon: Utils.$("#scenario-icon").value.trim(),
                category: Utils.$("#scenario-category").value.trim(),
                options,
            };
            if (scenarioId) await Api.updateScenario(scenarioId, payload);
            else await Api.createScenario(payload);
            Utils.toast("Scenario saved", "success");
            this.loadScenarios();
        } catch (err) {
            Utils.toast(`Scenario save failed: ${err.message}`, "error");
        }
    }
};
