/**
 * RoomSync AI - Chat Module
 */
const Chat = {
    currentConversationId: null,
    refreshInterval: null,
    websocket: null,
    isConnected: false,

    async render() {
        const c = Utils.$("#app-content");
        const s = Utils.getSession();

        // Stop auto-refresh when going back to conversation list
        this.stopAutoRefresh();
        this.currentConversationId = null;

        // Connect to WebSocket
        this.connectWebSocket(s.user_id);
        
        try {
            const conversations = await Api.getConversations(s.user_id);
            
            c.innerHTML = `
            <div class="dashboard-container fade-in">
                <div class="sidebar">
                    <nav class="sidebar-nav">
                        <h4>Navigation</h4>
                        <div class="sidebar-menu">
                            <button class="sidebar-item" onclick="Dashboard.render()">🏠 Dashboard</button>
                            <button class="sidebar-item" onclick="Dashboard.renderProfile()">👤 Profile</button>
                            <button class="sidebar-item" onclick="Dashboard.renderExploreUsers()">🔍 Explore Users</button>
                            <button class="sidebar-item" onclick="Rooms.renderBrowse()">🏠 Browse Rooms</button>
                            <button class="sidebar-item" onclick="Rooms.renderMyPosts()">📝 My Posts</button>
                            <button class="sidebar-item" onclick="Rooms.renderCreate()">➕ Create Post</button>
                            <button class="sidebar-item active" onclick="Chat.render()">💬 Messages</button>
                            <button class="sidebar-item logout" onclick="App.logout()">🚪 Logout</button>
                        </div>
                    </nav>
                </div>
                <div class="main-content">
                    <div class="dash-header">
                        <div class="dash-welcome">
                            <h2>Messages</h2>
                            <p class="dash-subtitle">Chat with potential roommates about room details.</p>
                        </div>
                    </div>
                    <div class="dash-section">
                        ${conversations.length === 0 
                            ? '<div class="empty-state"><p>No conversations yet. Start chatting by requesting a roommate!</p></div>'
                            : `<div class="conversations-list">
                                ${conversations.map(conv => this.conversationCard(conv, s.user_id)).join("")}
                            </div>`
                        }
                    </div>
                </div>
            </div>`;
            
            // Load unseen count
            this.loadUnseenCount();
        } catch (err) {
            c.innerHTML = `<div class="empty-state"><p>Error loading conversations: ${err.message}</p></div>`;
        }
        
        // Save current page state
        this.savePageState('chat-list');
    },

    conversationCard(conv, userId) {
        const otherUserId = conv.user1_id === userId ? conv.user2_id : conv.user1_id;
        const otherUserName = conv.user1_id === userId ? conv.user2_name : conv.user1_name;
        const unseenClass = conv.unseen_count > 0 ? 'has-unseen' : '';
        const unseenBadge = conv.unseen_count > 0 ? `<span class="unseen-badge">${conv.unseen_count}</span>` : '';
        
        return `
        <div class="conversation-card glass-card ${unseenClass}" onclick="Chat.openConversation(${conv.id})">
            <div class="conversation-info">
                <h4>${otherUserName}</h4>
                <p class="muted">${conv.post_title ? conv.post_title : 'General chat'}</p>
                ${conv.post_location ? `<p class="muted small">${conv.post_location}</p>` : ''}
            </div>
            <div class="conversation-meta">
                ${unseenBadge}
                <p class="muted small">${new Date(conv.updated_at).toLocaleDateString()}</p>
            </div>
        </div>`;
    },

    async openConversation(conversationId) {
        const c = Utils.$("#app-content");
        const s = Utils.getSession();
        this.currentConversationId = conversationId;
        
        try {
            const messages = await Api.getMessages(conversationId, s.user_id);
            const conversation = await Api.getConversationById(conversationId);
            
            const otherUserId = conversation.user1_id === s.user_id ? conversation.user2_id : conversation.user1_id;
            const otherUserName = conversation.user1_id === s.user_id ? conversation.user2_name : conversation.user1_name;
            
            c.innerHTML = `
            <div class="dashboard-container fade-in">
                <div class="sidebar">
                    <nav class="sidebar-nav">
                        <h4>Navigation</h4>
                        <div class="sidebar-menu">
                            <button class="sidebar-item" onclick="Dashboard.render()">🏠 Dashboard</button>
                            <button class="sidebar-item" onclick="Dashboard.renderProfile()">👤 Profile</button>
                            <button class="sidebar-item" onclick="Dashboard.renderExploreUsers()">🔍 Explore Users</button>
                            <button class="sidebar-item" onclick="Rooms.renderBrowse()">🏠 Browse Rooms</button>
                            <button class="sidebar-item" onclick="Rooms.renderMyPosts()">📝 My Posts</button>
                            <button class="sidebar-item" onclick="Rooms.renderCreate()">➕ Create Post</button>
                            <button class="sidebar-item active" onclick="Chat.render()">💬 Messages</button>
                            <button class="sidebar-item logout" onclick="App.logout()">🚪 Logout</button>
                        </div>
                    </nav>
                </div>
                <div class="main-content">
                    <div class="dash-header">
                        <button class="btn btn-secondary btn-sm" onclick="Chat.render()">← Back to Messages</button>
                        <div class="dash-welcome">
                            <h2>Chat with ${otherUserName}</h2>
                            ${conversation.post_title ? `<p class="dash-subtitle">About: ${conversation.post_title}</p>` : ''}
                            <span id="connection-status" class="connection-status status-disconnected">○ Disconnected</span>
                        </div>
                    </div>
                    <div class="dash-section">
                        <div class="chat-container glass-card">
                            <div class="chat-messages" id="chat-messages">
                                ${messages.length === 0 
                                    ? '<p class="muted">No messages yet. Start the conversation!</p>'
                                    : messages.map(msg => this.messageCard(msg, s.user_id)).join("")
                                }
                            </div>
                            <div class="chat-input-area">
                                <form onsubmit="Chat.sendMessage(event)">
                                    <input type="text" id="chat-input" placeholder="Type a message..." required autocomplete="off" />
                                    <button type="submit" class="btn btn-primary">Send</button>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </div>`;
            
            // Scroll to bottom of messages
            const messagesContainer = Utils.$("#chat-messages");
            if (messagesContainer) {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
            
            // Focus on input
            const input = Utils.$("#chat-input");
            if (input) {
                input.focus();
            }
            
            // Don't start auto-refresh - WebSocket handles real-time updates
        } catch (err) {
            c.innerHTML = `<div class="empty-state"><p>Error loading conversation: ${err.message}</p></div>`;
        }
        
        // Save current page state
        this.savePageState('chat-conversation', conversationId);
    },

    startAutoRefresh(conversationId) {
        // Clear any existing interval
        this.stopAutoRefresh();
        
        // Refresh messages every 3 seconds
        this.refreshInterval = setInterval(async () => {
            if (this.currentConversationId === conversationId) {
                try {
                    const s = Utils.getSession();
                    const messages = await Api.getMessages(conversationId, s.user_id);
                    const messagesContainer = Utils.$("#chat-messages");
                    if (messagesContainer) {
                        const currentHTML = messagesContainer.innerHTML;
                        const newHTML = messages.map(msg => this.messageCard(msg, s.user_id)).join("");
                        if (currentHTML !== newHTML) {
                            messagesContainer.innerHTML = newHTML;
                            messagesContainer.scrollTop = messagesContainer.scrollHeight;
                        }
                    }
                } catch (err) {
                    console.error("Auto-refresh error:", err);
                }
            }
        }, 3000);
    },

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    },

    connectWebSocket(userId) {
        // Close existing connection if any
        if (this.websocket) {
            this.websocket.close();
        }

        const wsUrl = `wss://roomsync-ai.onrender.com/ws/${userId}`;
        this.websocket = new WebSocket(wsUrl);

        this.websocket.onopen = () => {
            console.log("[WebSocket] Connected");
            this.isConnected = true;
            this.updateConnectionStatus();
        };

        this.websocket.onmessage = (event) => {
            const message = JSON.parse(event.data);
            console.log("[WebSocket] Received message:", message);
            this.handleIncomingMessage(message);
        };

        this.websocket.onclose = () => {
            console.log("[WebSocket] Disconnected");
            this.isConnected = false;
            this.updateConnectionStatus();
            // Attempt to reconnect after 5 seconds
            setTimeout(() => {
                if (this.currentConversationId !== null) {
                    this.connectWebSocket(userId);
                }
            }, 5000);
        };

        this.websocket.onerror = (error) => {
            console.error("[WebSocket] Error:", error);
            this.isConnected = false;
            this.updateConnectionStatus();
        };
    },

    disconnectWebSocket() {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
            this.isConnected = false;
            this.updateConnectionStatus();
        }
    },

    updateConnectionStatus() {
        const statusEl = Utils.$("#connection-status");
        if (statusEl) {
            statusEl.className = this.isConnected ? 'status-connected' : 'status-disconnected';
            statusEl.textContent = this.isConnected ? '● Connected' : '○ Disconnected';
        }
    },

    handleIncomingMessage(message) {
        // Only handle if we're in the conversation
        if (this.currentConversationId === message.conversation_id) {
            const messagesContainer = Utils.$("#chat-messages");
            if (messagesContainer) {
                const s = Utils.getSession();
                const messageHTML = this.messageCard(message, s.user_id);
                messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
        }
    },

    messageCard(msg, userId) {
        const isOwn = msg.sender_id === userId;
        return `
        <div class="message ${isOwn ? 'own' : 'other'}">
            <div class="message-header">
                <span class="message-sender">${msg.sender_name}</span>
                <span class="message-time">${new Date(msg.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
            </div>
            <div class="message-content">${msg.message_content}</div>
        </div>`;
    },

    async sendMessage(event) {
        event.preventDefault();
        const input = Utils.$("#chat-input");
        const message = input.value.trim();
        
        if (!message || !this.currentConversationId) return;
        
        const s = Utils.getSession();
        
        try {
            await Api.sendMessage(this.currentConversationId, s.user_id, message);
            input.value = '';
            
            // Reload messages
            await this.openConversation(this.currentConversationId);
        } catch (err) {
            alert("Failed to send message: " + err.message);
        }
    },

    async loadUnseenCount() {
        const s = Utils.getSession();
        try {
            const result = await Api.getUnseenCount(s.user_id);
            const badge = Utils.$("#chat-badge");
            if (badge) {
                if (result.unseen_count > 0) {
                    badge.textContent = result.unseen_count;
                    badge.style.display = 'block';
                } else {
                    badge.style.display = 'none';
                }
            }
        } catch (err) {
            console.error("Error loading unseen count:", err);
        }
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
                case 'chat-conversation':
                    if (state.data) {
                        this.openConversation(state.data);
                        return true;
                    }
                    break;
                case 'chat-list':
                    this.render();
                    return true;
                default:
                    return false;
            }
        } catch (err) {
            console.error("Error restoring page state:", err);
            localStorage.removeItem('roomSync_pageState');
            return false;
        }
    }
};
