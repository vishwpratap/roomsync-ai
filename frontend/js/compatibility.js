/**
 * RoomSync AI - Compatibility Result Module
 * Detailed breakdown with recommendation, trait comparison, and risk analysis.
 */
const Compatibility = {
    async show(user1Id, user2Id) {
        const c = Utils.$("#app-content");
        c.innerHTML = '<div class="compat-loading fade-in"><div class="loader">Analyzing compatibility...</div></div>';
        try {
            const res = await Api.checkCompatibility(user1Id, user2Id);
            this.renderResult(res);
        } catch (err) {
            Utils.toast(err.message, "error");
            Dashboard.render();
        }
    },

    renderResult(r) {
        const c = Utils.$("#app-content");
        const scoreColor = r.total_score >= 75 ? "high" : r.total_score >= 50 ? "mid" : "low";
        const recClass = r.total_score >= 80 ? "rec-great" : r.total_score >= 65 ? "rec-good" : r.total_score >= 45 ? "rec-caution" : "rec-bad";
        const recIcon = r.total_score >= 80 ? "🌟" : r.total_score >= 65 ? "👍" : r.total_score >= 45 ? "⚡" : "🚫";

        c.innerHTML = `
        <div class="compat-container fade-in">
            <button class="btn btn-secondary btn-sm back-btn" onclick="Dashboard.render()">← Back to Dashboard</button>

            <div class="compat-header">
                <div class="compat-vs">
                    <div class="compat-user">
                        <div class="user-avatar">${(r.user1_name||"?")[0]}</div>
                        <h4>${r.user1_name}</h4>
                        <span class="badge badge-sm">${r.user1_type||"—"}</span>
                    </div>
                    <div class="vs-divider"><span>VS</span></div>
                    <div class="compat-user">
                        <div class="user-avatar avatar-alt">${(r.user2_name||"?")[0]}</div>
                        <h4>${r.user2_name}</h4>
                        <span class="badge badge-sm">${r.user2_type||"—"}</span>
                    </div>
                </div>
            </div>

            <!-- Recommendation Banner -->
            <div class="recommendation-banner ${recClass}">
                <span class="rec-icon">${recIcon}</span>
                <span class="rec-text">${r.recommendation || "Proceed with Caution"}</span>
            </div>

            <!-- Score Section -->
            <div class="compat-score-section glass-card">
                <div class="big-score score-${scoreColor}" id="big-score-num">0</div>
                <div class="big-score-label">Overall Compatibility</div>
                <div class="score-breakdown">
                    ${this.breakdownBar("Lifestyle", r.lifestyle_score, 100, "🏠")}
                    ${this.breakdownBar("Personality", r.personality_score, 100, "🧠")}
                    ${this.breakdownBar("Behavioral Traits", r.trait_score, 100, "🎭")}
                    <div class="breakdown-item bonus-item">
                        <span>🔗 Cluster Bonus</span>
                        <span class="bonus-val">+${r.cluster_bonus || 0}</span>
                    </div>
                    <div class="breakdown-item penalty-item">
                        <span>⚡ Penalties</span>
                        <span class="penalty-val">${r.penalties || 0}</span>
                    </div>
                </div>
            </div>

            <!-- Details Grid -->
            <div class="compat-details">
                <!-- Risk Card -->
                <div class="detail-card glass-card risk-card risk-${r.risk_level.toLowerCase()}">
                    <h4>${Utils.riskIcon(r.risk_level)} Risk Level: ${r.risk_level}</h4>
                    ${r.conflicts && r.conflicts.length ? r.conflicts.map(cf => `
                        <div class="conflict-item">
                            <span class="conflict-severity severity-${cf.severity.toLowerCase()}">${cf.severity}</span>
                            <span class="conflict-field">${cf.field.replace(/_/g, ' ')}</span>
                            <p>${cf.description}</p>
                        </div>`).join("") : '<p class="muted">No significant conflicts detected! 🎉</p>'}
                </div>

                <!-- Highlights -->
                <div class="detail-card glass-card highlights-card">
                    <h4>✨ Positive Insights</h4>
                    ${r.highlights && r.highlights.length ? `<ul class="insights-list highlights-list">${r.highlights.map(h=>`<li><span class="insight-icon">✅</span> ${h}</li>`).join("")}</ul>` : '<p class="muted">No specific highlights.</p>'}
                </div>

                <!-- Warnings -->
                <div class="detail-card glass-card warnings-card">
                    <h4>⚠️ Risk Warnings</h4>
                    ${r.warnings && r.warnings.length ? `<ul class="insights-list warnings-list">${r.warnings.map(w=>`<li><span class="insight-icon">⚠️</span> ${w}</li>`).join("")}</ul>` : '<p class="muted">No warnings – looking good! 🎉</p>'}
                </div>
            </div>
        </div>`;

        // Animate score count-up
        setTimeout(() => Utils.animateCount(Utils.$("#big-score-num"), Math.round(r.total_score), 1500), 200);
    },

    breakdownBar(label, value, max, icon) {
        const pct = Math.min(Math.round(value), 100);
        const color = pct >= 75 ? "bar-high" : pct >= 50 ? "bar-mid" : "bar-low";
        return `<div class="breakdown-item">
            <span>${icon} ${label}</span>
            <div class="bar-track"><div class="bar-fill ${color}" style="width:${pct}%"></div></div>
            <span class="bar-value">${pct}%</span>
        </div>`;
    }
};
