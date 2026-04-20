# 🏠 RoomSync AI – Intelligent Roommate Compatibility System

AI-powered roommate matching system using personality analysis, weighted scoring, and K-Means clustering.

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
│   └── schema.sql       # Database schema
├── frontend/
│   ├── index.html       # SPA entry point
│   ├── css/style.css    # Design system
│   └── js/              # Modular JavaScript
└── README.md
```

## 🔌 API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/signup` | Create account |
| POST | `/login` | Authenticate |
| POST | `/add-user` | Save questionnaire |
| GET | `/matches/{user_id}` | Top 5 matches |
| POST | `/compatibility` | Compare two users |
| GET | `/users?search=` | Search users |
| GET | `/user/{user_id}` | User profile |
| POST | `/recluster` | Re-run ML clustering |

## 🧠 How It Works

1. **Weighted Scoring**: Cleanliness & smoking (20pts each), sleep & noise (15pts each), plus personality (10pts)
2. **K-Means Clustering**: Groups users into 3 lifestyle clusters; same cluster = +5 bonus
3. **Risk Detection**: Flags HIGH/MEDIUM/LOW conflicts (smoking mismatch, cleanliness gap, etc.)
4. **User Classification**: Labels like "Night Owl", "Social Explorer", "Disciplined Minimalist"
