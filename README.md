# 🏠 RoomSync AI – Intelligent Roommate Compatibility System

AI-powered roommate matching system using personality analysis, weighted scoring, and K-Means clustering to find the perfect roommate match.

## ✨ Features

- **Smart Compatibility Scoring**: Weighted algorithm considering cleanliness, smoking, sleep schedule, noise preferences, and personality traits
- **K-Means Clustering**: Groups users into lifestyle clusters for better matching
- **Risk Detection**: Identifies potential conflicts before they happen
- **User Classification**: Labels users as "Night Owl", "Social Explorer", "Disciplined Minimalist", etc.
- **Real-time Chat**: WebSocket-based messaging between matched users
- **Room Posting**: Browse and post available rooms with details
- **Theme Switching**: Beautiful UI with multiple themes (Default & Pink-Blue)
- **Admin Panel**: Comprehensive dashboard for managing users, rooms, and system settings
- **Responsive Design**: Works seamlessly on desktop and mobile devices

## 🎨 Themes

The application supports multiple themes for a personalized experience:

- **Default Theme**: Dark purple/blue gradient with glassmorphism effects
- **Pink-Blue Theme**: Light pink background with pink/blue accents (Default theme)

Theme selection is persisted via localStorage and applies across all pages including user dashboard, profile, explore users, browse rooms, chat, and admin panel.

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- MySQL (via XAMPP or standalone) running on `localhost:3306`
- pip (Python package manager)

### 1. Setup Database
```bash
# Start MySQL (XAMPP), then run:
mysql -u root < backend/schema.sql
```

### 2. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Run the Server
```bash
# From the project root directory:
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Open the App
Navigate to `http://localhost:8000` in your browser.

## 📁 Project Structure

```
├── backend/
│   ├── main.py          # FastAPI app + API routes
│   ├── db.py            # MySQL connection pool
│   ├── models.py        # Pydantic request/response models
│   ├── logic.py         # Compatibility scoring engine
│   ├── ml.py            # K-Means clustering
│   ├── classifier.py    # User type classification
│   ├── risk.py          # Risk detection engine
│   ├── schema.sql       # Database schema
│   └── requirements.txt # Python dependencies
├── frontend/
│   ├── index.html       # SPA entry point
│   ├── css/
│   │   └── style.css    # Design system + theme variables
│   └── js/
│       ├── app.js       # Main application entry point
│       ├── utils.js     # Utility functions + theme management
│       ├── dashboard.js # Dashboard logic
│       ├── rooms.js     # Room browsing logic
│       ├── chat.js      # Chat functionality
│       └── admin.js     # Admin panel logic
└── README.md
```

## 🔌 API Endpoints

### Authentication
| Method | Route | Description |
|--------|-------|-------------|
| POST | `/signup` | Create new user account |
| POST | `/login` | Authenticate user |

### User Management
| Method | Route | Description |
|--------|-------|-------------|
| POST | `/add-user` | Save questionnaire responses |
| GET | `/user/{user_id}` | Get user profile details |
| GET | `/users?search=` | Search users by name/email |
| GET | `/matches/{user_id}` | Get top 5 compatible matches |

### Compatibility
| Method | Route | Description |
|--------|-------|-------------|
| POST | `/compatibility` | Compare two users for compatibility |
| POST | `/recluster` | Re-run ML clustering on all users |

### Rooms
| Method | Route | Description |
|--------|-------|-------------|
| GET | `/rooms` | Get all room posts |
| POST | `/rooms` | Create new room post |
| POST | `/room-post/{post_id}/request` | Send roommate request |

### Chat
| Method | Route | Description |
|--------|-------|-------------|
| GET | `/conversations/{user_id}` | Get user conversations |
| GET | `/messages/{conversation_id}` | Get conversation messages |
| POST | `/messages` | Send new message |
| WS | `/ws/{user_id}` | WebSocket for real-time chat |

### Admin
| Method | Route | Description |
|--------|-------|-------------|
| GET | `/admin/users` | Get all users (admin only) |
| GET | `/admin/rooms` | Get all rooms (admin only) |
| DELETE | `/admin/users/{user_id}` | Delete user (admin only) |
| DELETE | `/admin/rooms/{room_id}` | Delete room (admin only) |

## 🧠 How It Works

### 1. Weighted Scoring System
The compatibility score is calculated using weighted preferences:
- **Cleanliness**: 20 points
- **Smoking**: 20 points
- **Sleep Schedule**: 15 points
- **Noise Level**: 15 points
- **Personality Traits**: 10 points

### 2. K-Means Clustering
Users are grouped into 3 lifestyle clusters based on their preferences:
- Users in the same cluster receive a +5 bonus to their compatibility score
- Clustering is re-run when the `/recluster` endpoint is called

### 3. Risk Detection
The system flags potential conflicts:
- **HIGH**: Smoking mismatch, large cleanliness gap
- **MEDIUM**: Moderate lifestyle differences
- **LOW**: Minor differences that are manageable

### 4. User Classification
Based on questionnaire responses, users are labeled:
- **Night Owl**: Late sleep schedule, active at night
- **Social Explorer**: High social interaction, enjoys meeting new people
- **Disciplined Minimalist**: Clean, organized, prefers quiet environment
- **Balanced Harmonizer**: Moderate preferences across all categories

## 🎯 User Flow

1. **Sign Up**: Create account with email and password
2. **Questionnaire**: Complete personality and lifestyle questionnaire
3. **Dashboard**: View compatibility matches and insights
4. **Explore**: Browse other users and compare compatibility
5. **Rooms**: Browse available rooms or post your own
6. **Chat**: Message matched users in real-time
7. **Theme**: Switch between themes using the dropdown in the sidebar

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **MySQL**: Relational database for user data
- **scikit-learn**: Machine learning library for K-Means clustering
- **Pydantic**: Data validation using Python type annotations

### Frontend
- **Vanilla JavaScript**: No framework dependencies
- **CSS Variables**: For theming and design system
- **WebSocket API**: Real-time chat functionality
- **LocalStorage**: Theme persistence

## 🎨 Theme System

The application uses CSS variables for theming. Themes are applied via the `data-theme` attribute on the `<html>` element.

### Available Themes
- `default`: Dark purple/blue gradient theme
- `pink-blue`: Light pink background with pink/blue accents (default)

### Theme Implementation
```javascript
// Get current theme
const theme = Utils.getTheme();

// Set theme
Utils.setTheme('pink-blue');

// Initialize theme on page load
Utils.initTheme();
```

### Theme Variables
Each theme defines CSS variables for:
- Background colors (primary, card, hover)
- Text colors (primary, secondary, muted)
- Accent colors (accent, accent-2, accent-3)
- Gradients (main, warm, success)
- Shadows and glow effects

## 🔧 Configuration

### Database Connection
Edit `backend/db.py` to configure MySQL connection:
```python
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "roomsync"
}
```

### Backend URL
Frontend API calls use the backend URL configured in each JavaScript file. Default: `https://roomsync-ai.onrender.com`

## 📝 Environment Variables

Create a `.env` file in the backend directory (optional):
```
DATABASE_URL=mysql://root:password@localhost:3306/roomsync
SECRET_KEY=your-secret-key
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Built with FastAPI and modern web technologies
- Inspired by the need for better roommate matching solutions
- Uses scikit-learn for machine learning clustering

## 📞 Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Made with ❤️ for finding the perfect roommate**
