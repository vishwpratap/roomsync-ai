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

    // Hardcoded scenarios to bypass database issues
    HARDCODED_SCENARIOS: [
        {
            id: "dishes_overnight",
            title: "The Unwashed Dishes",
            question: "Your roommate leaves dishes unwashed in the sink overnight. What do you do?",
            description: "A small mess can reveal a lot about shared-space expectations.",
            icon: "🍽️",
            category: "cleanliness",
            options: [
                {text: "Do not even notice - no big deal", emoji: "😌", traits: {"cleanliness_tolerance": 5, "conflict_style": 5, "flexibility": 5}},
                {text: "Clean them yourself without saying anything", emoji: "🧹", traits: {"cleanliness_tolerance": 2, "conflict_style": 4, "flexibility": 4}},
                {text: "Politely ask them to wash up next time", emoji: "💬", traits: {"cleanliness_tolerance": 2, "conflict_style": 3, "flexibility": 3}},
                {text: "Get annoyed - this should not happen", emoji: "😤", traits: {"cleanliness_tolerance": 1, "conflict_style": 1, "flexibility": 1}},
            ],
        },
        {
            id: "loud_music_night",
            title: "Late Night Beats",
            question: "It is 11 PM on a weeknight and your roommate starts playing loud music. How do you react?",
            description: "Noise tolerance matters more than people think.",
            icon: "🎵",
            category: "noise",
            options: [
                {text: "Join in - the more the merrier", emoji: "🎉", traits: {"noise_tolerance": 5, "social_tolerance": 5, "flexibility": 5}},
                {text: "Put on headphones and ignore it", emoji: "🎧", traits: {"noise_tolerance": 4, "conflict_style": 5, "flexibility": 4}},
                {text: "Ask them to lower the volume a bit", emoji: "🤫", traits: {"noise_tolerance": 2, "conflict_style": 3, "flexibility": 3}},
                {text: "Tell them to stop immediately", emoji: "🛑", traits: {"noise_tolerance": 1, "conflict_style": 1, "flexibility": 1}},
            ],
        },
        {
            id: "surprise_guests",
            title: "Unexpected Visitors",
            question: "Your roommate invites 5 friends over without telling you. You planned a quiet evening. What do you do?",
            description: "Social energy can make or break a roommate fit.",
            icon: "🚪",
            category: "social",
            options: [
                {text: "Awesome - more people to hang out with", emoji: "🥳", traits: {"social_tolerance": 5, "flexibility": 5, "conflict_style": 5}},
                {text: "Join for a bit, then retreat to your room", emoji: "👋", traits: {"social_tolerance": 3, "flexibility": 4, "conflict_style": 4}},
                {text: "Say you would appreciate a heads up next time", emoji: "📱", traits: {"social_tolerance": 2, "conflict_style": 3, "flexibility": 2}},
                {text: "Confront them - this is your space too", emoji: "😠", traits: {"social_tolerance": 1, "conflict_style": 1, "flexibility": 1}},
            ],
        },
        {
            id: "fridge_food",
            title: "The Missing Leftovers",
            question: "You discover your roommate ate your leftover food without asking. How do you handle it?",
            description: "Shared boundaries often show up in everyday moments.",
            icon: "🍕",
            category: "sharing",
            options: [
                {text: "No worries - food is meant to be shared", emoji: "😊", traits: {"flexibility": 5, "conflict_style": 5, "social_tolerance": 5}},
                {text: "Mention it casually, but do not make a big deal", emoji: "🤷", traits: {"flexibility": 3, "conflict_style": 3, "social_tolerance": 3}},
                {text: "Set a clear rule: ask before taking", emoji: "📋", traits: {"flexibility": 2, "conflict_style": 2, "social_tolerance": 2}},
                {text: "Label everything - boundaries are important", emoji: "🏷️", traits: {"flexibility": 1, "conflict_style": 2, "social_tolerance": 1}},
            ],
        },
        {
            id: "early_alarm",
            title: "The Early Alarm",
            question: "Your roommate's alarm goes off at 5:30 AM every day and wakes you up. What is your approach?",
            description: "Sleep compatibility is a classic roommate issue.",
            icon: "⏰",
            category: "routine",
            options: [
                {text: "Might as well start the day early too", emoji: "🌅", traits: {"flexibility": 5, "noise_tolerance": 4, "conflict_style": 5}},
                {text: "Use earplugs and adapt", emoji: "😴", traits: {"flexibility": 4, "noise_tolerance": 3, "conflict_style": 4}},
                {text: "Ask for a vibrating alarm instead", emoji: "📳", traits: {"flexibility": 2, "noise_tolerance": 2, "conflict_style": 3}},
                {text: "This needs to change right away", emoji: "⚠️", traits: {"flexibility": 1, "noise_tolerance": 1, "conflict_style": 1}},
            ],
        },
        {
            id: "bathroom_schedule",
            title: "Bathroom Rush Hour",
            question: "You both need to get ready at 8 AM for work/school. How do you handle the bathroom situation?",
            description: "Morning routines can make or break the day.",
            icon: "🚿",
            category: "routine",
            options: [
                {text: "Wake up earlier to avoid conflict", emoji: "⏰", traits: {"flexibility": 5, "planning": 5, "conflict_style": 5}},
                {text: "Alternate days - fair is fair", emoji: "📅", traits: {"flexibility": 3, "planning": 4, "conflict_style": 3}},
                {text: "Discuss and create a schedule", emoji: "📝", traits: {"flexibility": 2, "planning": 3, "conflict_style": 2}},
                {text: "I need my time - they can adjust", emoji: "😤", traits: {"flexibility": 1, "planning": 2, "conflict_style": 1}},
            ],
        },
        {
            id: "shared_expenses",
            title: "Bill Splitting",
            question: "Your roommate forgets to pay their share of the electricity bill for the second month. What do you do?",
            description: "Money matters can strain even the best friendships.",
            icon: "💰",
            category: "financial",
            options: [
                {text: "Pay it for them - no big deal", emoji: "💸", traits: {"flexibility": 5, "conflict_style": 5, "trust": 5}},
                {text: "Remind them gently, but don't stress", emoji: "🤝", traits: {"flexibility": 3, "conflict_style": 3, "trust": 3}},
                {text: "Set up automatic payments together", emoji: "📱", traits: {"flexibility": 2, "conflict_style": 2, "trust": 2}},
                {text: "This is unacceptable - need a serious talk", emoji: "😠", traits: {"flexibility": 1, "conflict_style": 1, "trust": 1}},
            ],
        },
        {
            id: "study_focus",
            title: "Study Time",
            question: "You have an important exam tomorrow. Your roommate wants to watch a movie in the living room. What happens?",
            description: "Focus needs and social balance are key.",
            icon: "📚",
            category: "routine",
            options: [
                {text: "Study at the library - they can enjoy their time", emoji: "🏛️", traits: {"flexibility": 5, "conflict_style": 5, "social_tolerance": 4}},
                {text: "Ask them to use headphones, stay in the room", emoji: "🎧", traits: {"flexibility": 3, "conflict_style": 3, "social_tolerance": 3}},
                {text: "Suggest they watch it another day", emoji: "📅", traits: {"flexibility": 2, "conflict_style": 2, "social_tolerance": 2}},
                {text: "I need quiet - they need to leave", emoji: "🚫", traits: {"flexibility": 1, "conflict_style": 1, "social_tolerance": 1}},
            ],
        },
    ],

    async render() {
        this.step = 0;
        this.responses = {};
        this.basicData = {};
        const c = Utils.$("#app-content");
        c.innerHTML = '<div class="questionnaire-container fade-in"><div class="loader">Loading scenarios...</div></div>';

        try {
            // Use hardcoded scenarios instead of fetching from API
            this.scenarios = this.HARDCODED_SCENARIOS;
            console.log("[Questionnaire] Using hardcoded scenarios:", this.scenarios.length);

            // totalSteps = 1 (basic info) + scenarios.length + 1 (review)
            this.totalSteps = 1 + this.scenarios.length + 1;
            this.renderShell();
            this.renderStep();
        } catch (err) {
            console.error("[Questionnaire] Error loading scenarios:", err);
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
        console.log("[Questionnaire] Rendering scenario:", scenario);
        console.log("[Questionnaire] Scenario options:", scenario.options);

        const selected = this.responses[scenario.id];
        const icon = scenario.icon || "🎭";
        const title = scenario.title || "Scenario";
        const question = scenario.question || scenario.description || "";  // Use question field first, fallback to description

        body.innerHTML = `
        <div class="step-content scenario-step fade-in">
            <div class="scenario-header">
                <span class="scenario-icon">${icon}</span>
                <h3>${title}</h3>
                <p class="scenario-desc">${question}</p>
            </div>
            <div class="scenario-options">
                ${scenario.options && scenario.options.length > 0 ? scenario.options.map((opt, i) => `
                    <div class="scenario-option ${selected === i ? 'selected' : ''}"
                         onclick="Questionnaire.selectOption('${scenario.id}', ${i})" id="opt-${scenario.id}-${i}">
                        <span class="option-emoji">${opt.emoji || "📝"}</span>
                        <span class="option-text">${opt.text || "Option"}</span>
                        <span class="option-check">${selected === i ? '✓' : ''}</span>
                    </div>
                `).join("") : '<p class="muted">No options available for this scenario.</p>'}
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
