
/**
 * RoomSync AI - API Client
 */
const API_BASE = "https://roomsync-ai.onrender.com";

const Api = {
    async request(method, path, body = null, extraHeaders = {}) {
        const session = Utils.getSession();
        const headers = { "Content-Type": "application/json", ...extraHeaders };
        if (session?.role === "admin" && session.admin_id) {
            headers["X-Admin-Id"] = String(session.admin_id);
        }
        const options = { method, headers };
        if (body) options.body = JSON.stringify(body);
        const res = await fetch(`${API_BASE}${path}`, options);
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Request failed");
        return data;
    },

    signup(name, password) { return this.request("POST", "/signup", { name, password }); },
    login(name, password) { return this.request("POST", "/login", { name, password }); },
    adminLogin(email, password) { return this.request("POST", "/admin/login", { email, password }); },
    updateProfile(userId, age, profession, gender) { return this.request("PUT", `/user/${userId}`, { age, profession, gender }); },
    getScenarios() { return this.request("GET", "/scenarios"); },
    addUserScenarios(profileData) { return this.request("POST", "/add-user-scenarios", profileData); },
    addUser(profileData) { return this.request("POST", "/add-user", profileData); },
    getMatches(userId) { return this.request("GET", `/matches/${userId}`); },
    checkCompatibility(user1Id, user2Id) { return this.request("POST", "/compatibility", { user1_id: user1Id, user2_id: user2Id }); },
    searchUsers(query = "") { return this.request("GET", `/users?search=${encodeURIComponent(query)}`); },
    getAllUsers(query = "") { return this.request("GET", `/users?search=${encodeURIComponent(query)}`); },
    getUser(userId) { return this.request("GET", `/user/${userId}`); },
    recluster() { return this.request("POST", "/recluster"); },

    getAdminDashboard() { return this.request("GET", "/admin/dashboard"); },
    getAdminUsers(search = "") { return this.request("GET", `/admin/users?search=${encodeURIComponent(search)}`); },
    getAdminUser(userId) { return this.request("GET", `/admin/users/${userId}`); },
    deleteAdminUser(userId) { return this.request("DELETE", `/admin/users/${userId}`); },
    getWeights() { return this.request("GET", "/admin/weights"); },
    updateWeights(payload) { return this.request("PUT", "/admin/weights", payload); },
    getAdminScenarios() { return this.request("GET", "/admin/scenarios"); },
    createScenario(payload) { return this.request("POST", "/admin/scenarios", payload); },
    updateScenario(id, payload) { return this.request("PUT", `/admin/scenarios/${id}`, payload); },

    async createRoomPost(formData) {
        const res = await fetch(`${API_BASE}/room-post`, {
            method: "POST",
            body: formData,
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Request failed");
        return data;
    },
    async updateRoomPost(postId, formData) {
        const res = await fetch(`${API_BASE}/room-post/${postId}`, {
            method: "PUT",
            body: formData,
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Request failed");
        return data;
    },
    deleteRoomPost(postId, userId) { return this.request("DELETE", `/room-post/${postId}?user_id=${userId}`); },
    getRoomPosts(userId) { return this.request("GET", `/room-posts/${userId}`); },
    getRoomPost(postId, userId) { return this.request("GET", `/room-post/${postId}?user_id=${userId}`); },
    getMyRoomPosts(userId) { return this.request("GET", `/my-room-posts/${userId}`); },
    requestRoommate(postId, requester_user_id, message) { return this.request("POST", `/room-post/${postId}/request`, { requester_user_id, message }); },
    
    getConversations(userId) { return this.request("GET", `/conversations/${userId}`); },
    getMessages(conversationId, userId) { return this.request("GET", `/messages/${conversationId}?user_id=${userId}`); },
    getConversationById(conversationId) { return this.request("GET", `/conversation/${conversationId}`); },
    async sendMessage(conversationId, senderId, messageContent) {
        const formData = new FormData();
        formData.append("conversation_id", conversationId);
        formData.append("sender_id", senderId);
        formData.append("message_content", messageContent);
        const res = await fetch(`${API_BASE}/messages`, {
            method: "POST",
            body: formData,
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Request failed");
        return data;
    },
    getUnseenCount(userId) { return this.request("GET", `/unseen-count/${userId}`); },
};
