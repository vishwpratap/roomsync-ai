
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
        <div class="dashboard-container fade-in">
            <div class="dash-header">
                <div class="dash-welcome">
                    <h2>Admin control room</h2>
                    <p class="subtitle">Tune matching, manage users, and evolve behavioral scenarios without rebuilding the stack.</p>
                </div>
                <div class="header-actions">
                    <button class="btn btn-secondary btn-sm" onclick="Admin.renderDashboard()">Refresh</button>
                    <button class="btn btn-secondary btn-sm" onclick="App.logout()">Logout</button>
                </div>
            </div>
            <div class="admin-grid">
                <section class="glass-card admin-panel" id="admin-metrics"><div class="loader">Loading dashboard...</div></section>
                <section class="glass-card admin-panel" id="admin-weights"><div class="loader">Loading weights...</div></section>
                <section class="glass-card admin-panel admin-wide" id="admin-users"><div class="loader">Loading users...</div></section>
                <section class="glass-card admin-panel admin-wide" id="admin-posts"><div class="loader">Loading room posts...</div></section>
                <section class="glass-card admin-panel admin-wide" id="admin-scenarios"><div class="loader">Loading scenarios...</div></section>
            </div>
        </div>`;
        await Promise.all([this.loadMetrics(), this.loadWeights(), this.loadUsers(), this.loadRoomPosts(), this.loadScenarios()]);
    },

    async loadMetrics() {
        const target = Utils.$("#admin-metrics");
        try {
            const data = await Api.getAdminDashboard();
            target.innerHTML = `
            <h3>Dashboard</h3>
            <div class="stats-grid">
                <div class="stat-card"><strong>${data.total_users}</strong><span>Total users</span></div>
                <div class="stat-card"><strong>${data.total_room_posts}</strong><span>Room posts</span></div>
                <div class="stat-card"><strong>${data.total_matches_generated}</strong><span>Matches generated</span></div>
                <div class="stat-card"><strong>${data.analytics.average_compatibility_score}%</strong><span>Average score</span></div>
            </div>
            <div class="stats-grid compact-grid">
                <div class="stat-card"><strong>${data.risk_distribution.LOW}</strong><span>Low risk</span></div>
                <div class="stat-card"><strong>${data.risk_distribution.MEDIUM}</strong><span>Medium risk</span></div>
                <div class="stat-card"><strong>${data.risk_distribution.HIGH}</strong><span>High risk</span></div>
                <div class="stat-card"><strong>${data.analytics.high_risk_matches_percent}%</strong><span>High-risk share</span></div>
            </div>
            <div class="muted">Top conflict types: ${(data.analytics.most_common_conflict_types || []).map(item => `${item.type} (${item.count})`).join(", ") || 'No data yet'}</div>
            <div style="margin-top:20px; padding-top:20px; border-top:1px solid rgba(255,255,255,0.1);">
                <button class="btn btn-danger btn-sm" onclick="Admin.cleanupDuplicatePosts()">🗑️ Cleanup Duplicate Room Posts</button>
                <small class="muted">Removes duplicate room posts from database (keeps oldest one per user/title/location/rent)</small>
                <br><br>
                <button class="btn btn-danger btn-sm" onclick="Admin.cleanupAllDuplicates()">🔥 Strong Cleanup (By Title)</button>
                <small class="muted">Removes ALL posts with same title, keeps only the oldest one</small>
                <br><br>
                <button class="btn btn-warning btn-sm" onclick="Admin.seedScenarios()">🌱 Re-seed Scenarios</button>
                <small class="muted">Re-seeds all scenarios with options (use if questionnaire shows no options)</small>
            </div>`;
        } catch (err) {
            target.innerHTML = `<p>${err.message}</p>`;
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
        try {
            const data = await fetch("https://roomsync-ai.onrender.com/admin/room-posts").then(r => r.json());
            const posts = data.posts || [];
            target.innerHTML = `
            <div class="section-head">
                <h3>Room Posts Management</h3>
                <small class="muted">${posts.length} total posts</small>
            </div>
            <div style="max-height:400px; overflow-y:auto;">
                ${posts.map(post => `
                    <div class="admin-item" style="padding:12px; border-bottom:1px solid rgba(255,255,255,0.1); display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <strong>${post.title}</strong>
                            <br><small class="muted">ID: ${post.id} | Owner: ${post.owner_name} | ₹${post.rent} | ${post.location}</small>
                        </div>
                        <button class="btn btn-danger btn-xs" onclick="Admin.deleteRoomPost(${post.id})">Delete</button>
                    </div>
                `).join("") || '<p class="muted">No room posts found.</p>'}
            </div>`;
        } catch (err) {
            target.innerHTML = `<p>${err.message}</p>`;
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
        const target = Utils.$("#admin-weights");
        try {
            const weights = await Api.getWeights();
            target.innerHTML = `
            <h3>Weight Control</h3>
            <p class="muted admin-copy">Recommended defaults give slightly more importance to cleanliness and behavioral traits, while keeping personality as a supporting signal.</p>
            <form class="fields-grid admin-weight-grid" onsubmit="Admin.saveWeights(event)">
                <div class="field"><label>Cleanliness Weight</label><input type="number" step="0.05" id="weight-cleanliness" value="${weights.cleanliness}" /><small>Most common source of day-to-day friction.</small></div>
                <div class="field"><label>Sleep Weight</label><input type="number" step="0.05" id="weight-sleep" value="${weights.sleep}" /><small>Important, but usually manageable with clear routines.</small></div>
                <div class="field"><label>Personality Weight</label><input type="number" step="0.05" id="weight-personality" value="${weights.personality}" /><small>Useful context, but should not overpower lifestyle fit.</small></div>
                <div class="field"><label>Trait Weight</label><input type="number" step="0.05" id="weight-trait" value="${weights.trait}" /><small>Behavior under real scenarios should strongly influence the score.</small></div>
                <div class="header-actions">
                    <button class="btn btn-secondary btn-sm" type="button" onclick="Admin.applyRecommendedWeights()">Use Recommended</button>
                    <button class="btn btn-primary btn-sm" type="submit">Update Weights</button>
                </div>
            </form>`;
        } catch (err) {
            target.innerHTML = `<p>${err.message}</p>`;
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
        try {
            const users = await Api.getAdminUsers(search);
            if (users.length && !users.some(user => user.id === this.selectedUserId)) {
                this.selectedUserId = users[0].id;
            }
            target.innerHTML = `
            <div class="section-head">
                <h3>User Management</h3>
                <input type="text" placeholder="Search users..." value="${search}" oninput="Admin.loadUsers(this.value)" />
            </div>
            <div class="admin-users-workspace">
                <div class="admin-user-list">
                    ${users.map(user => `
                <div class="search-item glass-card admin-user-row ${user.id === this.selectedUserId ? 'active' : ''}" data-user-id="${user.id}">
                    <div class="search-item-info admin-user-row-info" onclick="Admin.showUser(${user.id})">
                        <div class="admin-user-row-head">
                            <strong>${user.name}</strong>
                            <span class="badge badge-sm">${user.roommate_type || '-'}</span>
                        </div>
                        <div class="match-meta"><span>Cluster ${user.cluster_id ?? '-'}</span><span>${user.profession || '-'}</span><span>${user.gender || '-'}</span></div>
                    </div>
                    <div class="admin-user-row-actions">
                        <button class="btn btn-secondary btn-xs" type="button" onclick="Admin.showUser(${user.id})">View</button>
                        <button class="btn btn-secondary btn-xs" type="button" onclick="Admin.deleteUser(${user.id})">Delete</button>
                    </div>
                </div>`).join("") || '<p class="muted">No users found.</p>'}
                </div>
                <div id="admin-user-detail" class="admin-detail admin-detail-side">
                    <div class="detail-card glass-card admin-user-empty-state">
                        <h4>Select a user</h4>
                        <p class="muted">Pick someone from the list to view their profile details, traits, and scenario answers.</p>
                    </div>
                </div>
            </div>`;
            if (this.selectedUserId) {
                this.showUser(this.selectedUserId, false);
            }
        } catch (err) {
            target.innerHTML = `<p>${err.message}</p>`;
        }
    },

    async showUser(userId, smoothScroll = true) {
        try {
            this.selectedUserId = userId;
            Utils.$$(".admin-user-row").forEach(card => {
                card.classList.toggle("active", Number(card.dataset.userId) === userId);
            });
            const user = await Api.getAdminUser(userId);
            const preferences = user.preferences || {};
            const personality = user.personality || {};
            const traits = user.traits || {};
            const responses = user.responses || [];
            Utils.$("#admin-user-detail").innerHTML = `
            <div class="detail-card glass-card admin-user-detail-card slide-in-right">
                <div class="admin-user-summary">
                    <div>
                        <h4>${user.name}</h4>
                        <p class="muted">${user.profession || '-'} - ${user.gender || '-'} - cluster ${user.cluster_id ?? '-'}</p>
                    </div>
                    <span class="badge">${user.roommate_type || 'Balanced Roommate'}</span>
                </div>
                <div class="admin-pill-grid">
                    <div class="admin-pill-card"><span>Age</span><strong>${user.age || '-'}</strong></div>
                    <div class="admin-pill-card"><span>Profession</span><strong>${user.profession || '-'}</strong></div>
                    <div class="admin-pill-card"><span>Gender</span><strong>${user.gender || '-'}</strong></div>
                    <div class="admin-pill-card"><span>Cluster</span><strong>${user.cluster_id ?? '-'}</strong></div>
                </div>
                <div class="admin-user-sections">
                    <div class="admin-mini-panel">
                        <h5>Lifestyle Preferences</h5>
                        <div class="admin-kv-grid">
                            ${Object.entries(preferences).map(([key, value]) => `<div class="admin-kv-item"><span>${Admin.labelize(key)}</span><strong>${value}</strong></div>`).join("")}
                        </div>
                    </div>
                    <div class="admin-mini-panel">
                        <h5>Personality Profile</h5>
                        <div class="admin-kv-grid">
                            ${Object.entries(personality).map(([key, value]) => `<div class="admin-kv-item"><span>${Admin.labelize(key)}</span><strong>${value}</strong></div>`).join("")}
                        </div>
                    </div>
                    <div class="admin-mini-panel">
                        <h5>Behavior Traits</h5>
                        <div class="admin-kv-grid">
                            ${Object.entries(traits).map(([key, value]) => `<div class="admin-kv-item"><span>${Admin.labelize(key)}</span><strong>${value}</strong></div>`).join("")}
                        </div>
                    </div>
                    <div class="admin-mini-panel">
                        <h5>Scenario Answers</h5>
                        <div class="admin-response-list">
                            ${responses.length ? responses.map(item => `<div class="admin-response-item"><strong>${item.title}</strong><span>Option ${Number(item.selected_option) + 1}</span></div>`).join("") : '<p class="muted">No scenario responses recorded.</p>'}
                        </div>
                    </div>
                </div>
            </div>`;
            if (smoothScroll && window.innerWidth < 900) {
                Utils.$("#admin-user-detail")?.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        } catch (err) {
            Utils.toast(err.message, "error");
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
        try {
            const scenarios = await Api.getAdminScenarios();
            const active = scenarios.find(s => s.db_id === this.selectedScenarioId) || scenarios[0];
            this.selectedScenarioId = active?.db_id || null;
            target.innerHTML = `
            <div class="section-head">
                <h3>Scenario Manager</h3>
                <div class="header-actions">
                    <button class="btn btn-secondary btn-xs" onclick="Admin.applyPresetToCurrent()">Use Category Starter</button>
                    <button class="btn btn-primary btn-xs" onclick="Admin.newScenario()">New Scenario</button>
                </div>
            </div>
            <div class="scenario-admin-layout">
                <div class="scenario-list-mini">${scenarios.map(s => `<button class="scenario-mini ${s.db_id === this.selectedScenarioId ? 'active' : ''}" onclick="Admin.editScenario(${s.db_id})">${s.title}</button>`).join("")}</div>
                <div id="scenario-editor">${this.scenarioEditor(active)}</div>
            </div>`;
        } catch (err) {
            target.innerHTML = `<p>${err.message}</p>`;
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
