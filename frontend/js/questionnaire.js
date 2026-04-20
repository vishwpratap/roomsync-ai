/**
 * RoomSync AI - Scenario-Based Questionnaire
 * Step-by-step behavioral assessment with animated option cards.
 */
const Questionnaire = {
    step: 0,
    totalSteps: 0,
    scenarios: [],
    responses: {},
    basicData: {},

    async render() {
        this.step = 0;
        this.responses = {};
        this.basicData = {};
        const c = Utils.$("#app-content");
        c.innerHTML = '<div class="questionnaire-container fade-in"><div class="loader">Loading scenarios...</div></div>';

        try {
            this.scenarios = await Api.getScenarios();
            // totalSteps = 1 (basic info) + scenarios.length + 1 (review)
            this.totalSteps = 1 + this.scenarios.length + 1;
            this.renderShell();
            this.renderStep();
        } catch (err) {
            Utils.toast("Failed to load scenarios: " + err.message, "error");
        }
    },

    renderShell() {
        const c = Utils.$("#app-content");
        c.innerHTML = `
        <div class="questionnaire-container fade-in">
            <div class="q-header">
                <h2>Behavioral Assessment</h2>
                <p>Answer real-life scenarios to find your ideal roommate</p>
                <div class="progress-bar-wrap"><div class="progress-bar" id="q-progress"></div></div>
                <div class="step-counter" id="step-counter"></div>
            </div>
            <div class="q-body glass-card" id="q-body"></div>
            <div class="q-nav">
                <button class="btn btn-secondary" id="q-prev" onclick="Questionnaire.prev()" disabled>← Back</button>
                <span class="step-label" id="step-label"></span>
                <button class="btn btn-primary" id="q-next" onclick="Questionnaire.next()">Next →</button>
            </div>
        </div>`;
    },

    renderStep() {
        const body = Utils.$("#q-body");
        const pct = ((this.step + 1) / this.totalSteps) * 100;
        Utils.$("#q-progress").style.width = `${pct}%`;
        Utils.$("#q-prev").disabled = this.step === 0;
        const isLast = this.step === this.totalSteps - 1;
        Utils.$("#q-next").textContent = isLast ? "Submit ✓" : "Next →";
        Utils.$("#step-label").textContent = `Step ${this.step + 1} of ${this.totalSteps}`;
        Utils.$("#step-counter").textContent = this.step === 0 ? "👤 Basic Info" :
            (isLast ? "✅ Review & Submit" : `🎭 Scenario ${this.step} of ${this.scenarios.length}`);

        if (this.step === 0) {
            this.renderBasicInfo(body);
        } else if (this.step <= this.scenarios.length) {
            this.renderScenario(body, this.scenarios[this.step - 1]);
        } else {
            this.renderReview(body);
        }
    },

    renderBasicInfo(body) {
        const session = Utils.getSession();
        body.innerHTML = `
        <div class="step-content fade-in">
            <h3>👤 Tell us about yourself</h3>
            <div class="fields-grid">
                <div class="field">
                    <label>Name</label>
                    <div class="display-value">${session?.name || "User"}</div>
                </div>
                <div class="field">
                    <label for="q-age">Age</label>
                    <input type="number" id="q-age" min="16" max="100" value="${this.basicData.age || 22}" required/>
                </div>
                <div class="field">
                    <label for="q-profession">Profession</label>
                    <input type="text" id="q-profession" placeholder="e.g. Student, Engineer" value="${this.basicData.profession || ''}" required/>
                </div>
                <div class="field">
                    <label for="q-gender">Gender</label>
                    <select id="q-gender" required>
                        ${["Male","Female","Non-binary","Other"].map(o =>
                            `<option value="${o}" ${this.basicData.gender === o ? 'selected' : ''}>${o}</option>`
                        ).join("")}
                    </select>
                </div>
            </div>
        </div>`;
    },

    renderScenario(body, scenario) {
        const selected = this.responses[scenario.id];
        body.innerHTML = `
        <div class="step-content scenario-step fade-in">
            <div class="scenario-header">
                <span class="scenario-icon">${scenario.icon}</span>
                <h3>${scenario.title}</h3>
                <p class="scenario-desc">${scenario.description}</p>
            </div>
            <div class="scenario-options">
                ${scenario.options.map((opt, i) => `
                    <div class="scenario-option ${selected === i ? 'selected' : ''}"
                         onclick="Questionnaire.selectOption('${scenario.id}', ${i})" id="opt-${scenario.id}-${i}">
                        <span class="option-emoji">${opt.emoji}</span>
                        <span class="option-text">${opt.text}</span>
                        <span class="option-check">${selected === i ? '✓' : ''}</span>
                    </div>
                `).join("")}
            </div>
        </div>`;
    },

    selectOption(scenarioId, optionIdx) {
        this.responses[scenarioId] = optionIdx;
        // Update visual selection
        const scenario = this.scenarios.find(s => s.id === scenarioId);
        if (!scenario) return;
        scenario.options.forEach((_, i) => {
            const el = Utils.$(`#opt-${scenarioId}-${i}`);
            if (el) {
                el.classList.toggle("selected", i === optionIdx);
                el.querySelector(".option-check").textContent = i === optionIdx ? "✓" : "";
            }
        });
    },

    renderReview(body) {
        const session = Utils.getSession();
        const scenarioReviews = this.scenarios.map(s => {
            const sel = this.responses[s.id];
            const optText = sel !== undefined ? s.options[sel].text : "Not answered";
            const optEmoji = sel !== undefined ? s.options[sel].emoji : "❓";
            return `<div class="review-item">
                <span>${s.icon} ${s.title}</span>
                <strong>${optEmoji} ${optText}</strong>
            </div>`;
        }).join("");

        body.innerHTML = `
        <div class="step-content fade-in">
            <h3>✅ Review Your Assessment</h3>
            <div class="review-grid">
                <div class="review-section">
                    <h4>👤 Basic Info</h4>
                    <div class="review-item"><span>Name</span><strong>${session?.name || "—"}</strong></div>
                    <div class="review-item"><span>Age</span><strong>${this.basicData.age || "—"}</strong></div>
                    <div class="review-item"><span>Profession</span><strong>${this.basicData.profession || "—"}</strong></div>
                    <div class="review-item"><span>Gender</span><strong>${this.basicData.gender || "—"}</strong></div>
                </div>
                <div class="review-section">
                    <h4>🎭 Scenario Responses</h4>
                    ${scenarioReviews}
                </div>
            </div>
        </div>`;
    },

    saveBasicInfo() {
        const age = Utils.$("#q-age");
        const prof = Utils.$("#q-profession");
        const gen = Utils.$("#q-gender");
        if (age) this.basicData.age = parseInt(age.value);
        if (prof) this.basicData.profession = prof.value.trim();
        if (gen) this.basicData.gender = gen.value;
    },

    prev() {
        if (this.step > 0) {
            if (this.step === 0) this.saveBasicInfo();
            this.step--;
            this.renderStep();
        }
    },

    async next() {
        if (this.step === 0) {
            this.saveBasicInfo();
            if (!this.basicData.age || !this.basicData.profession || !this.basicData.gender) {
                Utils.toast("Please fill in all fields", "error");
                return;
            }
        }

        if (this.step > 0 && this.step <= this.scenarios.length) {
            const sid = this.scenarios[this.step - 1].id;
            if (this.responses[sid] === undefined) {
                Utils.toast("Please select an option", "error");
                return;
            }
        }

        if (this.step < this.totalSteps - 1) {
            this.step++;
            this.renderStep();
        } else {
            await this.submit();
        }
    },

    async submit() {
        const s = Utils.getSession();
        const btn = Utils.$("#q-next");
        btn.disabled = true;
        btn.textContent = "Analyzing...";

        try {
            const payload = {
                user_id: s.user_id,
                age: this.basicData.age,
                profession: this.basicData.profession,
                gender: this.basicData.gender,
                responses: this.scenarios.map(sc => ({
                    scenario_id: sc.id,
                    selected_option: this.responses[sc.id] ?? 0
                }))
            };

            const res = await Api.addUserScenarios(payload);
            Utils.setSession({ ...s, has_profile: true, roommate_type: res.roommate_type });
            Utils.toast("Profile analyzed! Finding your matches...", "success");
            setTimeout(() => App.navigate("dashboard"), 800);
        } catch (err) {
            Utils.toast(err.message, "error");
        } finally {
            btn.disabled = false;
            btn.textContent = "Submit ✓";
        }
    }
};
