/**
 * RoomSync AI - Room Listing Module
 */
const Rooms = {
    galleryIndex: 0,

    async renderBrowse() {
        const c = Utils.$("#app-content");
        const session = Utils.getSession();
        c.innerHTML = `
        <div class="dashboard-container fade-in">
            <div class="sidebar">
                <nav class="sidebar-nav">
                    <h4>Navigation</h4>
                    <div class="sidebar-menu">
                        <button class="sidebar-item" onclick="Dashboard.render()">🏠 Dashboard</button>
                        <button class="sidebar-item" onclick="Dashboard.renderProfile()">👤 Profile</button>
                        <button class="sidebar-item" onclick="Dashboard.renderExploreUsers()">🔍 Explore Users</button>
                        <button class="sidebar-item active" onclick="Rooms.renderBrowse()">🏠 Browse Rooms</button>
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
                        <h2>Browse room posts</h2>
                        <p class="subtitle">Open any post to see room details and your compatibility with the person who posted it.</p>
                    </div>
                </div>
                <div class="matches-grid" id="room-grid"><div class="loader">Loading room posts...</div></div>
            </div>
        </div>`;

        try {
            const posts = await Api.getRoomPosts(session.user_id);
            console.log("[Browse Rooms] API returned posts:", posts);
            console.log("[Browse Rooms] Number of posts from API:", posts.length);
            console.log("[Browse Rooms] Post IDs:", posts.map(p => p.id));
            
            // Deduplicate by post ID
            const uniquePosts = [];
            const seenIds = new Set();
            for (const post of posts) {
                if (!seenIds.has(post.id)) {
                    seenIds.add(post.id);
                    uniquePosts.push(post);
                } else {
                    console.log("[Browse Rooms] Skipping duplicate post ID:", post.id);
                }
            }
            console.log("[Browse Rooms] Unique posts after dedup:", uniquePosts);
            console.log("[Browse Rooms] Number of unique posts:", uniquePosts.length);
            
            const grid = Utils.$("#room-grid");
            if (!uniquePosts.length) {
                grid.innerHTML = '<div class="empty-state"><p>No room posts yet. You could absolutely be the first one here.</p></div>';
                return;
            }
            const html = uniquePosts.map(post => this.roomCard(post)).join("");
            console.log("[Browse Rooms] Generated HTML length:", html.length);
            grid.innerHTML = html;
            console.log("[Browse Rooms] Grid children count after render:", grid.children.length);
        } catch (err) {
            console.error("[Browse Rooms] Error:", err);
            Utils.$("#room-grid").innerHTML = `<div class="empty-state"><p>${err.message}</p></div>`;
        }
        Chat.loadUnseenCount();
        this.savePageState('rooms-browse');
    },

    roomCard(post) {
        const image = (post.images && post.images[0]) || post.image_url || "";
        const imageCount = post.images?.length || (post.image_url ? 1 : 0);
        const session = Utils.getSession();
        const isOwnPost = post.user_id === session.user_id;
        return `
        <div class="room-card glass-card">
            ${image ? `<div class="room-thumb" style="background-image:url('${image}')"></div>` : '<div class="room-thumb room-thumb-empty">Room Post</div>'}
            <div class="room-card-body">
                <div class="room-card-top">
                    <h4>${post.title}</h4>
                    <span class="badge badge-sm">${imageCount} image${imageCount === 1 ? "" : "s"}</span>
                </div>
                <p class="muted">Hosted by ${post.owner_name || "User"}</p>
                <p class="muted">${post.location} - ₹${post.rent}</p>
                <p>${post.description.slice(0, 130)}${post.description.length > 130 ? "..." : ""}</p>
                <div class="room-compat-meta">
                    <span>${post.gender_preference || "Any"} preference</span>
                    <span>${post.created_at ? "Recently posted" : "Available now"}</span>
                </div>
                ${isOwnPost ? `
                <div class="room-actions" style="display:flex; gap:8px; margin-top:12px;">
                    <button class="btn btn-secondary btn-xs" onclick="Rooms.renderEdit(${post.id})">Edit</button>
                    <button class="btn btn-danger btn-xs" onclick="Rooms.deletePost(${post.id})">Delete</button>
                </div>
                <button class="btn btn-primary btn-sm btn-full" onclick="Rooms.renderDetail(${post.id})">View Post</button>
                ` : `
                <button class="btn btn-primary btn-sm btn-full" onclick="Rooms.renderDetail(${post.id})">View Post</button>
                `}
            </div>
        </div>`;
    },

    async renderDetail(postId) {
        const c = Utils.$("#app-content");
        const session = Utils.getSession();
        c.innerHTML = '<div class="compat-loading fade-in"><div class="loader">Loading room detail...</div></div>';

        try {
            const post = await Api.getRoomPost(postId, session.user_id);
            const compat = post.compatibility || {};
            const images = (post.images && post.images.length ? post.images : (post.image_url ? [post.image_url] : []));
            this.galleryIndex = 0;

            c.innerHTML = `
            <button class="hamburger-menu" onclick="Dashboard.toggleSidebar()"><span></span></button>
            <div class="sidebar-overlay" onclick="Dashboard.closeSidebar()"></div>
            <div class="dashboard-container fade-in">
                <div class="sidebar">
                    <nav class="sidebar-nav">
                        <h4>Navigation</h4>
                        <div class="sidebar-menu">
                            <button class="sidebar-item" onclick="Dashboard.render()">🏠 Dashboard</button>
                            <button class="sidebar-item" onclick="Dashboard.renderProfile()">👤 Profile</button>
                            <button class="sidebar-item" onclick="Dashboard.renderExploreUsers()">🔍 Explore Users</button>
                            <button class="sidebar-item active" onclick="Rooms.renderBrowse()">🏠 Browse Rooms</button>
                            <button class="sidebar-item" onclick="Rooms.renderMyPosts()">📝 My Posts</button>
                            <button class="sidebar-item" onclick="Rooms.renderCreate()">➕ Create Post</button>
                            <button class="sidebar-item logout" onclick="App.logout()">🚪 Logout</button>
                        </div>
                    </nav>
                </div>
                <div class="main-content">
                    <div class="back-btn">
                        <button class="btn btn-secondary btn-sm" onclick="Rooms.renderBrowse()">← Back to Rooms</button>
                    </div>
                    <div class="room-detail-card glass-card">
                        <div class="room-detail-head">
                            <div>
                                <h3>${post.title}</h3>
                                <p class="muted">Hosted by ${post.owner_name || "User"} - ${post.location}</p>
                            </div>
                            <div class="room-price">₹${post.rent}</div>
                        </div>

                        ${this.renderGallery(images)}

                        <div class="room-detail-copy">
                            <p>${post.description}</p>
                        </div>

                        <div class="detail-card glass-card owner-compat-card">
                        <div class="owner-compat-head">
                            <div>
                                <h4>Your compatibility with ${compat.owner?.name || post.owner_name || "the host"}</h4>
                                <p class="muted">This score compares your behavior profile with the profile of the person who posted this room.</p>
                            </div>
                            <div class="owner-compat-score">${compat.match || 0}%</div>
                        </div>
                        <div class="room-compat-badges">
                            <span class="match-risk risk-${(compat.risk_level || "LOW").toLowerCase()}">${compat.risk_level || "LOW"} risk</span>
                            <span class="badge badge-sm">${compat.owner?.roommate_type || post.owner_roommate_type || "Balanced Roommate"}</span>
                        </div>
                        <div class="score-breakdown">
                            ${Compatibility.breakdownBar("Lifestyle", compat.breakdown?.lifestyle || 0, 100, "Home")}
                            ${Compatibility.breakdownBar("Personality", compat.breakdown?.personality || 0, 100, "Mind")}
                            ${Compatibility.breakdownBar("Behavior", compat.breakdown?.traits || 0, 100, "Traits")}
                        </div>
                    </div>

                    <div class="compat-details room-detail-grid">
                        <div class="detail-card glass-card">
                            <h4>Compatibility Highlights</h4>
                            <ul class="insights-list highlights-list">${(compat.highlights || []).length ? (compat.highlights || []).map(item => `<li><span class="insight-icon">+</span>${item}</li>`).join("") : '<li><span class="insight-icon">+</span>No major strengths surfaced yet.</li>'}</ul>
                        </div>
                        <div class="detail-card glass-card">
                            <h4>Things to watch</h4>
                            <ul class="insights-list warnings-list">${(compat.warnings || []).length ? (compat.warnings || []).map(item => `<li><span class="insight-icon">!</span>${item}</li>`).join("") : '<li><span class="insight-icon">+</span>No major warnings detected.</li>'}</ul>
                        </div>
                    </div>

                    <button class="btn btn-primary" onclick="Rooms.requestRoommate(${post.id})">Request Roommate</button>
                </div>
                </div>
            </div>`;
        } catch (err) {
            Utils.toast(err.message, "error");
            this.renderBrowse();
        }
        Chat.loadUnseenCount();
        this.savePageState('rooms-detail', postId);
    },

    renderGallery(images) {
        if (!images.length) {
            return '<div class="room-gallery-empty room-thumb-empty">No room images uploaded</div>';
        }

        return `
        <div class="room-gallery-shell">
            <div class="room-gallery-track" id="room-gallery-track" onscroll="Rooms.syncGalleryDots()">
                ${images.map((url, index) => `
                    <div class="room-gallery-slide" data-index="${index}">
                        <img src="${url}" alt="Room image ${index + 1}" class="room-gallery-image" />
                    </div>
                `).join("")}
            </div>
            ${images.length > 1 ? `
                <button class="gallery-nav gallery-prev" type="button" onclick="Rooms.moveGallery(-1)">‹</button>
                <button class="gallery-nav gallery-next" type="button" onclick="Rooms.moveGallery(1)">›</button>
                <div class="gallery-dots">
                    ${images.map((_, index) => `<button class="gallery-dot ${index === 0 ? "active" : ""}" type="button" data-index="${index}" onclick="Rooms.goToGallery(${index})"></button>`).join("")}
                </div>
            ` : ""}
        </div>`;
    },

    syncGalleryDots() {
        const track = Utils.$("#room-gallery-track");
        if (!track) return;
        const slideWidth = track.clientWidth || 1;
        const index = Math.round(track.scrollLeft / slideWidth);
        this.galleryIndex = index;
        Utils.$$(".gallery-dot").forEach(dot => {
            dot.classList.toggle("active", Number(dot.dataset.index) === index);
        });
    },

    moveGallery(direction) {
        const track = Utils.$("#room-gallery-track");
        if (!track) return;
        const slides = Utils.$$(".room-gallery-slide");
        const nextIndex = Math.max(0, Math.min(slides.length - 1, this.galleryIndex + direction));
        this.goToGallery(nextIndex);
    },

    goToGallery(index) {
        const track = Utils.$("#room-gallery-track");
        if (!track) return;
        const slideWidth = track.clientWidth || 1;
        track.scrollTo({ left: slideWidth * index, behavior: "smooth" });
        this.galleryIndex = index;
        Utils.$$(".gallery-dot").forEach(dot => {
            dot.classList.toggle("active", Number(dot.dataset.index) === index);
        });
    },

    async deletePost(postId) {
        if (!confirm("Are you sure you want to delete this room post? This action cannot be undone.")) return;
        
        const session = Utils.getSession();
        try {
            await Api.deleteRoomPost(postId, session.user_id);
            alert("Room post deleted successfully!");
            this.renderBrowse();
        } catch (err) {
            alert("Failed to delete post: " + err.message);
        }
    },

    async renderEdit(postId) {
        const c = Utils.$("#app-content");
        c.innerHTML = '<div class="compat-loading fade-in"><div class="loader">Loading room post...</div></div>';
        
        try {
            const post = await Api.getRoomPost(postId, null);
            const session = Utils.getSession();
            
            if (post.user_id !== session.user_id) {
                c.innerHTML = '<div class="empty-state"><p>You can only edit your own posts.</p></div>';
                return;
            }
            
            c.innerHTML = `
            <button class="hamburger-menu" onclick="Dashboard.toggleSidebar()"><span></span></button>
            <div class="sidebar-overlay" onclick="Dashboard.closeSidebar()"></div>
            <div class="dashboard-container fade-in">
                <div class="sidebar">
                    <nav class="sidebar-nav">
                        <h4>Navigation</h4>
                        <div class="sidebar-menu">
                            <button class="sidebar-item" onclick="Dashboard.render()">🏠 Dashboard</button>
                            <button class="sidebar-item" onclick="Dashboard.renderProfile()">👤 Profile</button>
                            <button class="sidebar-item" onclick="Dashboard.renderExploreUsers()">🔍 Explore Users</button>
                            <button class="sidebar-item" onclick="Rooms.renderBrowse()">🏠 Browse Rooms</button>
                            <button class="sidebar-item active" onclick="Rooms.renderMyPosts()">📝 My Posts</button>
                            <button class="sidebar-item" onclick="Rooms.renderCreate()">➕ Create Post</button>
                            <button class="sidebar-item logout" onclick="App.logout()">🚪 Logout</button>
                        </div>
                    </nav>
                </div>
                <div class="main-content">
                    <div class="dash-header">
                        <div class="dash-welcome">
                            <h2>Edit room post</h2>
                            <p class="subtitle">Update your room post details and photos.</p>
                        </div>
                    </div>
                    <form class="glass-card room-form" onsubmit="Rooms.submitEdit(event, ${postId})">
                    <div class="fields-grid two-col">
                        <div class="field"><label>Title</label><input type="text" id="room-title" value="${post.title}" required /></div>
                        <div class="field"><label>Location</label><input type="text" id="room-location" value="${post.location}" required /></div>
                        <div class="field"><label>Rent</label><input type="number" id="room-rent" value="${post.rent}" min="1" required /></div>
                        <div class="field"><label>Gender Preference</label><input type="text" id="room-gender" value="${post.gender_preference || 'Any'}" /></div>
                    </div>
                    <div class="field full"><label>Description</label><textarea id="room-description" rows="5" required>${post.description}</textarea></div>
                    <div class="field full"><label>Upload Images (optional)</label><input type="file" id="room-images" multiple accept="image/*" /></div>
                    <div class="field full"><label>Current Images</label><div id="current-images" style="display:flex; gap:8px; flex-wrap:wrap;"></div></div>
                    <button type="submit" class="btn btn-primary btn-sm btn-full">Save Changes</button>
                </form>
                </div>
            </div>`;
            
            // Display current images
            const imagesDiv = Utils.$("#current-images");
            if (post.images && post.images.length) {
                post.images.forEach(img => {
                    imagesDiv.innerHTML += `<img src="${img}" style="width:80px; height:80px; object-fit:cover; border-radius:4px;" />`;
                });
            } else if (post.image_url) {
                imagesDiv.innerHTML = `<img src="${post.image_url}" style="width:80px; height:80px; object-fit:cover; border-radius:4px;" />`;
            }
        } catch (err) {
            c.innerHTML = `<div class="empty-state"><p>Error loading post: ${err.message}</p></div>`;
        }
        Chat.loadUnseenCount();
        this.savePageState('rooms-edit', postId);
    },

    async submitEdit(event, postId) {
        event.preventDefault();
        const session = Utils.getSession();
        const formData = new FormData();
        formData.append("user_id", session.user_id);
        formData.append("title", Utils.$("#room-title").value.trim());
        formData.append("description", Utils.$("#room-description").value.trim());
        formData.append("rent", Utils.$("#room-rent").value);
        formData.append("location", Utils.$("#room-location").value.trim());
        formData.append("gender_preference", Utils.$("#room-gender").value.trim() || "Any");
        
        const imageInput = Utils.$("#room-images");
        if (imageInput && imageInput.files) {
            for (const file of imageInput.files) {
                formData.append("images", file);
            }
        }
        
        try {
            await Api.updateRoomPost(postId, formData);
            alert("Room post updated successfully!");
            this.renderBrowse();
        } catch (err) {
            alert("Failed to update post: " + err.message);
        }
    },

    renderMyPosts() {
        const c = Utils.$("#app-content");
        const session = Utils.getSession();
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
                        <button class="sidebar-item active" onclick="Rooms.renderMyPosts()">📝 My Posts</button>
                        <button class="sidebar-item" onclick="Rooms.renderCreate()">➕ Create Post</button>
                        <button class="sidebar-item logout" onclick="App.logout()">🚪 Logout</button>
                    </div>
                </nav>
            </div>
            <div class="main-content">
                <div class="dash-header">
                    <div class="dash-welcome">
                        <h2>My Room Posts</h2>
                        <p class="subtitle">Manage your room posts - edit details or delete them.</p>
                    </div>
                </div>
                <div class="matches-grid" id="my-posts-grid"><div class="loader">Loading your posts...</div></div>
            </div>
        </div>`;
        this.loadMyPosts();
        Chat.loadUnseenCount();
        this.savePageState('rooms-myposts');
    },

    async loadMyPosts() {
        const grid = Utils.$("#my-posts-grid");
        const session = Utils.getSession();
        try {
            const posts = await Api.getMyRoomPosts(session.user_id);
            console.log("[My Posts] API returned posts:", posts);
            console.log("[My Posts] Number of posts from API:", posts.length);
            console.log("[My Posts] Post IDs:", posts.map(p => p.id));
            
            // Deduplicate by post ID
            const uniquePosts = [];
            const seenIds = new Set();
            for (const post of posts) {
                if (!seenIds.has(post.id)) {
                    seenIds.add(post.id);
                    uniquePosts.push(post);
                } else {
                    console.log("[My Posts] Skipping duplicate post ID:", post.id);
                }
            }
            console.log("[My Posts] Unique posts after dedup:", uniquePosts);
            console.log("[My Posts] Number of unique posts:", uniquePosts.length);
            
            if (!uniquePosts.length) {
                grid.innerHTML = '<div class="empty-state"><p>You haven\'t created any room posts yet.</p><button class="btn btn-primary btn-sm" onclick="Rooms.renderCreate()">Create Your First Post</button></div>';
                return;
            }
            const html = uniquePosts.map(post => this.myPostCard(post)).join("");
            console.log("[My Posts] Generated HTML length:", html.length);
            grid.innerHTML = html;
            console.log("[My Posts] Grid children count after render:", grid.children.length);
        } catch (err) {
            console.error("[My Posts] Error:", err);
            grid.innerHTML = `<div class="empty-state"><p>${err.message}</p></div>`;
        }
    },

    myPostCard(post) {
        const image = (post.images && post.images[0]) || post.image_url || "";
        const imageCount = post.images?.length || (post.image_url ? 1 : 0);
        return `
        <div class="room-card glass-card">
            ${image ? `<div class="room-thumb" style="background-image:url('${image}')"></div>` : '<div class="room-thumb room-thumb-empty">Room Post</div>'}
            <div class="room-card-body">
                <div class="room-card-top">
                    <h4>${post.title}</h4>
                    <span class="badge badge-sm">${imageCount} image${imageCount === 1 ? "" : "s"}</span>
                </div>
                <p class="muted">${post.location} - ₹${post.rent}</p>
                <p>${post.description.slice(0, 130)}${post.description.length > 130 ? "..." : ""}</p>
                <div class="room-compat-meta">
                    <span>${post.gender_preference || "Any"} preference</span>
                    <span>${post.created_at ? "Recently posted" : "Available now"}</span>
                </div>
                <div class="room-actions" style="display:flex; gap:8px; margin-top:12px;">
                    <button class="btn btn-secondary btn-xs" onclick="Rooms.renderEdit(${post.id})">Edit</button>
                    <button class="btn btn-danger btn-xs" onclick="Rooms.deletePost(${post.id})">Delete</button>
                    <button class="btn btn-primary btn-xs" onclick="Rooms.renderDetail(${post.id})">View</button>
                </div>
            </div>
        </div>`;
    },

    renderCreate() {
        const c = Utils.$("#app-content");
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
                        <button class="sidebar-item active" onclick="Rooms.renderCreate()">➕ Create Post</button>
                        <button class="sidebar-item logout" onclick="App.logout()">🚪 Logout</button>
                    </div>
                </nav>
            </div>
            <div class="main-content">
                <div class="dash-header">
                    <div class="dash-welcome">
                        <h2>Create a room post</h2>
                        <p class="subtitle">Share the room details and upload real photos from your device. Compatibility will be shown against you as the host.</p>
                    </div>
                </div>
            <form class="glass-card room-form" onsubmit="Rooms.submitPost(event)">
                <div class="fields-grid two-col">
                    <div class="field"><label>Title</label><input type="text" id="room-title" required /></div>
                    <div class="field"><label>Location</label><input type="text" id="room-location" required /></div>
                    <div class="field"><label>Rent</label><input type="number" id="room-rent" min="1" required /></div>
                    <div class="field"><label>Gender Preference</label><input type="text" id="room-gender" value="Any" /></div>
                    <div class="field full"><label>Description</label><textarea id="room-description" rows="5" required></textarea></div>
                    <div class="field full">
                        <label>Upload Room Images</label>
                        <div class="upload-dropzone">
                            <input type="file" id="room-images" accept="image/*" multiple onchange="Rooms.previewUploads(event)" />
                            <p>Select one or more photos from your device.</p>
                            <span class="muted">PNG, JPG, WEBP, or GIF</span>
                        </div>
                    </div>
                    <div class="field full">
                        <div class="upload-preview-grid" id="upload-preview-grid"></div>
                    </div>
                </div>
                <button class="btn btn-primary" type="submit">Publish Room Post</button>
            </form>
            </div>
        </div>`;
        Chat.loadUnseenCount();
        this.savePageState('rooms-create');
    },

    previewUploads(e) {
        const files = Array.from(e.target.files || []);
        const preview = Utils.$("#upload-preview-grid");
        if (!preview) return;
        if (!files.length) {
            preview.innerHTML = "";
            return;
        }
        preview.innerHTML = files.map(file => `
            <div class="upload-preview-card">
                <img src="${URL.createObjectURL(file)}" alt="${file.name}" />
                <span>${file.name}</span>
            </div>
        `).join("");
    },

    async submitPost(e) {
        e.preventDefault();
        const s = Utils.getSession();
        const formData = new FormData();
        formData.append("user_id", String(s.user_id));
        formData.append("title", Utils.$("#room-title").value.trim());
        formData.append("description", Utils.$("#room-description").value.trim());
        formData.append("rent", String(Number(Utils.$("#room-rent").value)));
        formData.append("location", Utils.$("#room-location").value.trim());
        formData.append("gender_preference", Utils.$("#room-gender").value.trim() || "Any");

        Array.from(Utils.$("#room-images").files || []).forEach(file => {
            formData.append("images", file);
        });

        try {
            await Api.createRoomPost(formData);
            Utils.toast("Room post published", "success");
            this.renderBrowse();
        } catch (err) {
            Utils.toast(err.message, "error");
        }
    },

    async requestRoommate(postId) {
        const session = Utils.getSession();
        const message = prompt("Send a message to the room owner:");
        if (!message) return;
        Api.requestRoommate(postId, session.user_id, message)
            .then(() => {
                Utils.toast("Roommate request sent!", "success");
            })
            .catch(err => Utils.toast(err.message, "error"));
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
                case 'rooms-browse':
                    this.renderBrowse();
                    return true;
                case 'rooms-myposts':
                    this.renderMyPosts();
                    return true;
                case 'rooms-create':
                    this.renderCreate();
                    return true;
                case 'rooms-edit':
                    if (state.data) {
                        this.renderEdit(state.data);
                        return true;
                    }
                    break;
                case 'rooms-detail':
                    if (state.data) {
                        this.renderDetail(state.data);
                        return true;
                    }
                    break;
                default:
                    return false;
            }
        } catch (err) {
            console.error("Error restoring page state:", err);
            localStorage.removeItem('roomSync_pageState');
            return false;
        }
    },
};
