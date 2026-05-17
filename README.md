# Smart Load Forecasting and Demand Response — Backend

**Project:** AI-Based Smart Load Forecasting and Demand Response  
**Team:** Seashiftsync (079BEL082, 079BEL083, 079BEL087)  
**Tech Stack:** Python, Django, Django REST Framework, SQLite, React (frontend — separate repo)

---

## What Is This Project?

This is the **backend** of a web application that uses Artificial Intelligence to predict electricity consumption and help users reduce their energy bills.

In simple terms:
- Users log in and see **how much electricity they will use** in the next 24 hours
- The system tells them **when electricity demand will be highest** (peak hours)
- It suggests **when to shift heavy appliances** (like washing machines) to cheaper, off-peak hours
- Admins can see data for all users; normal users only see their own data

---

## Who Built What

| Team Member | Roll No | Responsibility |
|---|---|---|
| Member 1 | 079BEL082 | Data collection, preprocessing, Django backend, APIs, authentication |
| Member 2 | 079BEL083 | AI forecasting model (machine learning) |
| Member 3 | 079BEL087 | Demand response logic, dashboard (React frontend) |

---

## How the System Works (Big Picture)

```
User opens React app
        ↓
Logs in → Django gives back a secure JWT token
        ↓
React uses token to call Django APIs
        ↓
Django reads the AI model → returns 24-hour electricity forecast
        ↓
System flags peak hours → suggests demand response actions
        ↓
User sees their personalised energy dashboard
```

---

## Project Folder Structure

```
backend/
│
├── smart_load_api/          ← Django project settings and config
│   ├── settings.py          ← database, installed apps, JWT config
│   ├── urls.py              ← root URL dispatcher
│   └── celery.py            ← background task config (optional)
│
├── accounts/                ← User system (login, register, roles)
│   ├── models.py            ← CustomUser model
│   ├── serializers.py       ← data formatting for API responses
│   ├── views.py             ← register, login, logout, profile APIs
│   ├── admin.py             ← user management in Django admin panel
│   ├── signals.py           ← auto-assigns roles (superuser → admin)
│   └── urls.py              ← /api/auth/...
│
├── data_ingestion/          ← Handles raw electricity data
│   ├── models.py            ← LoadReading, HouseholdMeter models
│   ├── serializers.py
│   ├── views.py             ← APIs to upload and view readings
│   ├── management/
│   │   └── commands/
│   │       └── seed_forecast_data.py  ← imports CSV into database
│   └── urls.py              ← /api/data/...
│
├── forecasting/             ← AI prediction engine
│   ├── models.py            ← ForecastResult, LoadReading models
│   ├── serializers.py
│   ├── views.py             ← APIs to get 24-hour predictions
│   ├── ml/
│   │   ├── load_forecast_model_best.pkl  ← trained AI model file
│   │   ├── load_forecast_model_lr.pkl    ← linear regression model
│   │   ├── load_forecast_model_rf.pkl    ← random forest model
│   │   ├── predict.py                    ← loads model, runs prediction
│   │   └── data/
│   │       └── simulated_load_data.csv   ← 90 days of training data
│   └── urls.py              ← /api/forecast/...
│
├── demand_response/         ← Peak detection and load-shift suggestions
│   ├── models.py            ← DRAction, PeakEvent models
│   ├── views.py             ← APIs for alerts and actions
│   └── urls.py              ← /api/dr/...
│
├── analytics/               ← Historical stats and performance metrics
│   ├── views.py             ← APIs for charts and model accuracy
│   └── urls.py              ← /api/analytics/...
│
├── notifications/           ← Email alerts for peak demand events
│   ├── tasks.py             ← background Celery tasks
│   └── utils.py
│
├── manage.py                ← Django command-line tool
├── requirements.txt         ← all Python packages needed
├── .env.example             ← template for environment variables
└── .gitignore               ← files Git should never track
```

---

## Setting Up the Project (Step by Step)

If you are seeing this repository for the first time, follow these steps exactly.

### Step 1 — Clone the repository

```bash
git clone <repository-url>
cd backend
```

### Step 2 — Create a virtual environment

A virtual environment keeps this project's packages separate from everything else on your computer.

```bash
python -m venv .venv
```

Activate it:

```bash
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Mac / Linux
source .venv/bin/activate
```

You should see `(.venv)` appear at the start of your terminal line. Keep it active for all steps below.

### Step 3 — Install required packages

```bash
pip install -r requirements.txt
```

### Step 4 — Create your environment file

The `.env` file holds secret values like your database password and Django secret key. It is never committed to Git.

```bash
# Windows
copy .env.example .env

# Mac / Linux
cp .env.example .env
```

Open `.env` and fill in the values:

```
SECRET_KEY=any-long-random-string-here
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
```

For development, the values above are fine as-is.

### Step 5 — Set up the database

```bash
python manage.py makemigrations accounts
python manage.py makemigrations
python manage.py migrate
```

### Step 6 — Create an admin account

```bash
python manage.py createsuperuser
```

It will ask for your email, first name, last name, and password. The system automatically gives superusers the Admin role.

### Step 7 — Seed the electricity data into the database

This imports 90 days of simulated electricity readings from the CSV file into your database:

```bash
python manage.py seed_forecast_data
```

You should see: `✓ Seeded 2160 records from CSV.`

### Step 8 — Start the server

```bash
python manage.py runserver
```

Open your browser and go to `http://localhost:8000/admin` — you should see the Django admin panel.

---

## API Endpoints Reference

All endpoints are prefixed with `/api/`. Every endpoint except register and login requires a JWT token in the `Authorization` header.

### Authentication — `/api/auth/`

| Method | URL | What it does | Login required? |
|---|---|---|---|
| POST | `/api/auth/register/` | Create a new user account | No |
| POST | `/api/auth/login/` | Log in, get access + refresh tokens | No |
| POST | `/api/auth/logout/` | Log out, invalidate refresh token | Yes |
| POST | `/api/auth/token/refresh/` | Get a new access token silently | No |
| GET | `/api/auth/profile/` | View your own profile | Yes |
| PUT | `/api/auth/profile/` | Update your own profile | Yes |

### Forecasting — `/api/forecast/`

| Method | URL | What it does | Login required? |
|---|---|---|---|
| GET | `/api/forecast/predict/` | Get next 24-hour load forecast | Yes |
| GET | `/api/forecast/history/` | View your past forecast results | Yes |
| GET | `/api/forecast/readings/` | View historical load readings | Yes |

### Demand Response — `/api/dr/`

| Method | URL | What it does |
|---|---|---|
| GET | `/api/dr/alerts/` | Get peak hour alerts |
| GET | `/api/dr/actions/` | Get load-shift recommendations |

### Analytics — `/api/analytics/`

| Method | URL | What it does |
|---|---|---|
| GET | `/api/analytics/metrics/` | Model accuracy (MAE, RMSE, R²) |
| GET | `/api/analytics/chart/` | Historical consumption data for charts |

---

## How to Call the APIs (Testing Without React)

**On Windows PowerShell:**

```powershell
# Step 1 — Log in and save the token
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login/" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"email":"your@email.com","password":"yourpassword"}'

$token = $response.access

# Step 2 — Call a protected endpoint
Invoke-RestMethod -Uri "http://localhost:8000/api/forecast/predict/" `
  -Method GET `
  -Headers @{ Authorization = "Bearer $token" }
```

**On Mac / Linux terminal:**

```bash
# Step 1 — Log in
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","password":"yourpassword"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access'])")

# Step 2 — Call a protected endpoint
curl http://localhost:8000/api/forecast/predict/ \
  -H "Authorization: Bearer $TOKEN"
```

Or use **Postman** (recommended for beginners) — download at postman.com.

---

## User Roles and Permissions

The system has three types of users:

| Role | Who | What they can access |
|---|---|---|
| Admin | Superuser — created via `createsuperuser` | Everything — all users' data, Django admin panel |
| Staff | `is_staff=True` users | All users' data, but not the admin panel |
| User | Normal registered users | Only their own data |

Roles are assigned automatically via signals:
- Create a superuser → automatically gets `admin` role
- Set `is_staff=True` → automatically gets `staff` role
- Normal registration → gets `user` role

---

## The AI Model (How the Forecasting Works)

The machine learning model was built by Member 2 (079BEL083) and lives inside `forecasting/ml/`.

**What it does:**
1. Takes features as input: hour of day, day of week, is it a weekend, month, temperature
2. Runs them through a trained Random Forest model (94.5% accurate, R² = 0.9449)
3. Returns predicted electricity consumption in kW for each of the next 24 hours
4. Flags hours above the 85th percentile as peak demand hours

**Training data:** 90 days of simulated hourly electricity readings (2,160 rows) stored in `forecasting/ml/data/simulated_load_data.csv`

**Model files:**
- `load_forecast_model_best.pkl` — the best model (Random Forest), used by the API
- `load_forecast_model_lr.pkl` — Linear Regression (backup/comparison)
- `load_forecast_model_rf.pkl` — Random Forest (same as best)

These `.pkl` files are not tracked by Git (too large). Get them from the shared Google Drive folder and place them in `forecasting/ml/`.

---

## Environment Variables (.env)

Never share your `.env` file. Copy `.env.example` to create yours.

| Variable | Description | Example |
|---|---|---|
| `SECRET_KEY` | Django secret key — any long random string | `abc123xyz...` |
| `DEBUG` | True in development, False in production | `True` |
| `DATABASE_URL` | Database connection string | `sqlite:///db.sqlite3` |
| `ALLOWED_HOSTS` | Allowed server hostnames | `localhost,127.0.0.1` |

---

## Common Problems and Fixes

**`Apps aren't loaded yet` error on startup**
- Check `accounts/__init__.py` — it must be completely empty. Remove any import lines inside it.

**`no such table` error**
- You haven't run migrations yet. Run `python manage.py migrate`.

**`InconsistentMigrationHistory` error**
- Delete `db.sqlite3` and all numbered migration files (keep `__init__.py`), then re-run migrations.

**`AlreadyRegistered` error in admin**
- Your `accounts/admin.py` has a duplicate registration. The `try/except admin.site.unregister()` block at the top of that file fixes it.

**`ModuleNotFoundError` for pandas, sklearn, etc.**
- Run `pip install -r requirements.txt` with your virtual environment activated.

**Model `.pkl` file not found**
- Download the model files from the shared Google Drive and place them in `forecasting/ml/`.

---

## Git Workflow for the Team

```bash
# Before starting work each day
git pull origin main

# After making changes
git add .
git commit -m "accounts: add logout view"
git push origin your-branch-name

# Never commit directly to main — open a pull request
```

**Files that are intentionally not in Git** (see `.gitignore`):
- `.env` — contains secrets
- `db.sqlite3` — your local database
- `.venv/` — virtual environment
- `*.pkl` — large model files (share via Google Drive)
- `*.csv` — large data files (share via Google Drive)

---

## Requirements

```
django
djangorestframework
djangorestframework-simplejwt
django-cors-headers
pandas
numpy
scikit-learn
```

Full list with versions: see `requirements.txt`

---

## Academic Context

This project fulfils the following phases of the curriculum:

| Phase | Description | Status |
|---|---|---|
| Phase 1 | Data collection and preprocessing | ✅ Complete |
| Phase 2 | AI model training (Linear Regression + Random Forest) | ✅ Complete |
| Phase 3 | 24-hour load forecasting via API | ✅ Complete |
| Phase 4 | Peak demand identification and demand response | ✅ Complete |
| Phase 5 | Dashboard and deployment | ⏳ In progress |

**Model performance:**
- Best model: Random Forest
- R² score: 0.9449 (94.5% accuracy)
- MAE: 5.77 kW
- Peak hours detected: 17:00–20:00 (evening)
- Baseline load factor: 69.09%

---

*Seashiftsync — 079BEL082, 079BEL083, 079BEL087*