# InsureHub Architecture (MVP)

## 1. Overview

**InsureHub** is a Django + HTMX application for auto insurance underwriting. Applications flow through three pathways: auto-approval (risk < 20), manual review (risk 20–85), and auto-rejection (risk > 85).

```
Applicant Form
    ↓
Django Risk Scorer (Scikit-learn)
    ↓
Auto Categorize: Approved / Flagged / Rejected
    ↓
If Flagged: Underwriter Dashboard
   (Adjust deductible & risk override with HTMX sliders)
    ↓
Final Decision → Saved to SQLite/PostgreSQL
```

---

## 2. Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5.0+ |
| Database | SQLite (MVP) / PostgreSQL (prod) |
| Frontend | Django Templates + HTMX + Tailwind CSS |
| ML | Scikit-learn (Random Forest `.pkl`) |
| Containerization | Docker + Docker Compose |

---

## 3. Project Structure

```
insurehub/
├── config/                    # Django settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── underwriting/              # Main app
│   ├── models.py              # Application model
│   ├── views.py               # Intake + Dashboard views
│   ├── forms.py               # ApplicationForm
│   ├── urls.py
│   ├── services/
│   │   ├── risk_scorer.py     # ML model wrapper
│   │   ├── premium_calculator.py
│   │   └── stp_engine.py      # Auto-approval logic
│   └── templates/
│       ├── base.html
│       ├── intake/form.html
│       ├── dashboard/queue.html
│       ├── dashboard/policy_detail.html
│       └── partials/*.html    # HTMX fragments
├── models/
│   └── risk_model.pkl
├── static/
│   ├── css/tailwind.css
│   └── js/htmx.min.js
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── manage.py
```

---

## 4. Database Schema

```sql
CREATE TABLE underwriting_application (
    id VARCHAR(36) PRIMARY KEY,
    applicant_name VARCHAR(100),
    driver_age INTEGER,
    driving_experience_years INTEGER,
    vehicle_make_model VARCHAR(100),
    vehicle_year INTEGER,
    safety_rating INTEGER,           -- 1-5
    regional_risk_index INTEGER,     -- 1-100
    coverage_limit DECIMAL(10, 2),
    
    calculated_risk_score DECIMAL(5, 2),
    initial_premium DECIMAL(10, 2),
    final_premium DECIMAL(10, 2),
    
    deductible_override DECIMAL(10, 2),      -- £250-£2000
    risk_override_percentage DECIMAL(5, 2),  -- -25% to +25%
    underwriter_notes TEXT,
    underwriter_id INTEGER,
    
    status VARCHAR(20),    -- approved, rejected, flagged
    decision_timestamp TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 5. Core Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Home |
| `/applications/new/` | GET | Intake form |
| `/applications/create/` | POST | Save application |
| `/applications/preview/` | POST | HTMX: preview risk/premium |
| `/dashboard/` | GET | Underwriter queue |
| `/policies/<id>/` | GET | Policy detail + sliders |
| `/api/recalculate-premium/` | POST | HTMX: update premium |
| `/api/save-override/` | POST | Save underwriter changes |
| `/api/approve-policy/` | POST | Approve |
| `/api/reject-policy/` | POST | Reject |

---

## 6. Key Views (Code Sketch)

**Intake:**
```python
def application_form_view(request):
    return render(request, 'intake/form.html', {'form': ApplicationForm()})

def risk_preview_view(request):
    # HTMX endpoint: returns partial HTML with risk score
    form = ApplicationForm(request.POST)
    if form.is_valid():
        app = form.save(commit=False)
        scorer = RiskScoringService()
        app.calculated_risk_score = scorer.predict(app)
        app.initial_premium = calculate_premium(app.calculated_risk_score, app.coverage_limit)
        app.status = categorize_status(app.calculated_risk_score)
        return render(request, 'partials/risk_preview.html', {'app': app})
    return render(request, 'partials/risk_preview.html', {'form': form}, status=400)
```

**Underwriter Dashboard:**
```python
def dashboard_queue_view(request):
    apps = Application.objects.filter(status='flagged')
    return render(request, 'dashboard/queue.html', {'apps': apps})

def recalculate_premium_api(request):
    # HTMX endpoint: slider triggers this
    deductible = float(request.POST.get('deductible'))
    app_id = request.POST.get('app_id')
    app = Application.objects.get(id=app_id)
    
    new_premium = calculate_premium_with_overrides(
        app.initial_premium, deductible, request.POST.get('risk_override', 0)
    )
    return render(request, 'partials/premium_recalc.html', {'premium': new_premium})
```

---

## 7. HTMX Patterns

**Live preview on form change:**
```html
<form id="intake-form">
  <input type="number" name="driver_age" />
  <input type="text" name="vehicle_make_model" />
  <button type="button" 
    hx-post="/applications/preview/"
    hx-include="#intake-form"
    hx-target="#risk-preview">Preview</button>
</form>
<div id="risk-preview"></div>
```

**Slider with live recalculation:**
```html
<input type="range" name="deductible" min="250" max="2000"
  hx-post="/api/recalculate-premium/"
  hx-include="[name='app_id'],[name='risk_override']"
  hx-target="#premium-result"
  hx-trigger="change" />
<div id="premium-result">£1,200</div>
```

---

## 8. Service Layer

**risk_scorer.py:**
```python
class RiskScoringService:
    def __init__(self):
        self.model = joblib.load('models/risk_model.pkl')
    
    def predict(self, application) -> float:
        features = [app.driver_age, app.driving_experience_years, ...]
        return self.model.predict([features])[0]
```

**premium_calculator.py:**
```python
def calculate_premium(risk_score, coverage_limit):
    return risk_score * 12 * (coverage_limit / 1000)

def calculate_premium_with_overrides(base, deductible, risk_pct):
    deductible_factor = 1.0 - (deductible - 250) / 1750 * 0.15
    override_factor = 1.0 + (risk_pct / 100)
    return base * deductible_factor * override_factor
```

**stp_engine.py:**
```python
def categorize_status(risk_score):
    if risk_score < 20: return 'approved'
    elif risk_score > 85: return 'rejected'
    else: return 'flagged'
```

---

## 9. Docker & Docker Compose

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

**docker-compose.yml:**
```yaml
version: '3.9'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: insurehub
      POSTGRES_USER: insurehub
      POSTGRES_PASSWORD: ${DB_PASSWORD:-changeme}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      DEBUG: "False"
      DATABASE_URL: postgresql://insurehub:${DB_PASSWORD:-changeme}@db:5432/insurehub
      SECRET_KEY: ${SECRET_KEY:-dev-key-change-in-prod}
    depends_on:
      - db
    volumes:
      - .:/app
    command: >
      sh -c "python manage.py migrate &&
             python manage.py runserver 0.0.0.0:8000"

volumes:
  postgres_data:
```

**Start with Docker Compose:**
```bash
docker-compose up --build
# Access: http://localhost:8000
```

---

## 10. Local Development Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create .env file
echo "DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
SECRET_KEY=dev-insecure-key" > .env

# 3. Run migrations
python manage.py migrate

# 4. Create superuser
python manage.py createsuperuser

# 5. Start dev server
python manage.py runserver

# Access: http://localhost:8000/
# Admin: http://localhost:8000/admin/
# Dashboard: http://localhost:8000/dashboard/
```

---

## 11. Deployment (Production)

**With Docker Compose (single-machine):**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

**With Kubernetes or Cloud (future):**
- Push Docker image to registry
- Deploy Gunicorn + Nginx via orchestrator
- Use managed PostgreSQL (AWS RDS, Azure Database)
- Store static files in S3 / blob storage

---

## 12. Data Flow

**Intake (User Submits):**
1. User fills form → clicks "Preview"
2. HTMX POSTs `/applications/preview/`
3. Django validates, scores risk, calculates premium
4. Returns partial HTML (`risk_preview.html`) with results
5. HTMX swaps into `#risk-preview`
6. User clicks "Submit"
7. Form POSTs `/applications/create/`
8. Django saves to DB, redirects to confirmation

**Underwriter Review (Flagged App):**
1. Underwriter opens `/dashboard/` → sees flagged apps
2. Clicks app → HTMX loads `/policies/<id>/` with sliders
3. Adjusts deductible slider → HTMX POSTs `/api/recalculate-premium/`
4. Django recalculates premium, returns updated HTML
5. HTMX swaps into `#premium-result` (live feedback)
6. Underwriter clicks "Approve"
7. POSTs `/api/approve-policy/` → status = "approved", saved

---

## Summary

**MVP Stack:** Django (backend) + HTMX (frontend) + SQLite (local DB) + Scikit-learn (risk scoring) + Docker Compose (containerization).

**Key Wins:**
- Single Python codebase (no frontend/backend split)
- Live interactivity via HTMX (no React complexity)
- Zero-config SQLite for MVP, easy migration to PostgreSQL
- Docker Compose for consistent local/production environments
- Django Admin gives underwriter CRUD for free
