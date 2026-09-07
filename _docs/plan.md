# Software Requirements Document (SRD)
## InsureHub – Auto Insurance Underwriting Platform (MVP)

---

### 1. Executive Summary & Vision
**InsureHub** is an AI-powered insurance underwriting workflow application designed to streamline risk assessment, automate low-risk auto insurance policy approvals, and empower human underwriters with interactive risk-sensitivity controls.

By focusing specifically on vehicle specifications, safety ratings, and regional risk metrics, InsureHub reduces manual review bottlenecks through **Straight-Through Processing (STP)** while providing human underwriters with granular pricing adjustments for complex cases.

---

### 2. Architecture & Architectural Decisions Log

#### 2.1 AI / Machine Learning Engine
* **Selected Architecture:** `Scikit-learn` Random Forest Model (Exported via `.pkl`)
* **Rationale:** Delivers high precision and near-zero evaluation latency, natively supports feature importance metrics, and operates locally in Python without API latency or subscription overhead.
* **Alternatives Evaluated:**
  * *LLM-based API Prompting:* Higher latency, recurring costs, non-deterministic scoring.
  * *Static Rule Matrices:* Lacks multi-variable predictive flexibility for slider simulations.

#### 2.2 User Interface & Application State
* **Selected Framework:** **Streamlit** (Python) using `st.session_state`
* **Rationale:** Streamlit enables rapid full-stack Python execution, seamless multi-tab layouts, real-time widget reactivity (interactive sliders), and zero frontend-backend decoupled complexity.
* **Alternatives Evaluated:**
  * *Gradio:* Optimized for simple input/output models, but less suited for multi-view tabular admin dashboards.
  * *React + Flask:* Over-engineered for MVP delivery, introducing multi-repo overhead.

#### 2.3 Data Storage & ORM Layer
* **Selected Database:** **SQLite** managed via **SQLAlchemy ORM**
* **Rationale:** Zero-configuration local database persistence. Using SQLAlchemy abstracts SQL logic, preventing injection bugs while maintaining seamless portability to PostgreSQL for production scaling.
* **Alternatives Evaluated:**
  * *Raw `sqlite3` queries:* Manual tuple mapping and prone to syntax bugs.
  * *In-Memory Dictionaries:* Application restart results in permanent data loss.

---

### 3. Core Functional Requirements

#### 3.1 Application Intake & Risk Scoring
* **Data Inputs:** Applicant Age, Driver Experience, Vehicle Make/Model, Vehicle Age, Safety Rating (1–5), Regional Theft/Accident Index (1–100), Base Coverage Limit.
* **Risk Calculation:** Predicts risk score ($0–100$) and baseline annual premium ($£$).

#### 3.2 Straight-Through Processing (STP) Engine
* **Auto-Approval Threshold:** Risk Score $< 20$ (Instantly issued policy).
* **Auto-Rejection Threshold:** Risk Score $> 85$ (Automatic decline).
* **Flagged / Manual Review:** Risk Score between $20$ and $85$ (Assigned to Underwriter Queue).

#### 3.3 Interactive Underwriter Dashboard
* **Sensitivity Sliders:** Allows underwriters to adjust key variables live:
  * Adjust Deductible Amount ($£250 - £2,000$)
  * Apply Manual Risk Override / Discount Factors ($-25\%$ to $+25\%$)
* **Live Calculation:** Re-computes risk exposure and revised premium in real-time before approval.

#### 3.4 Audit Trail & Policy Logging
* Full persistence of all decisions in SQLite: `Application ID`, `Risk Score`, `Initial Premium`, `Adjusted Premium`, `Status` (`Approved`, `Rejected`, `Underwriter Modified`), and `Underwriter Notes`.

---

### 4. Database Schema Specification

```sql
-- Applications Table
CREATE TABLE applications (
    id VARCHAR PRIMARY KEY,
    applicant_name VARCHAR(100),
    driver_age INTEGER,
    driving_experience_years INTEGER,
    vehicle_make_model VARCHAR(100),
    vehicle_year INTEGER,
    safety_rating INTEGER,
    regional_risk_index INTEGER,
    coverage_limit REAL,
    calculated_risk_score REAL,
    initial_premium REAL,
    final_premium REAL,
    status VARCHAR(50),
    underwriter_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 5. Implementation Stack & Dependencies

```txt
python >= 3.10
streamlit >= 1.28.0
pandas >= 2.0.0
numpy >= 1.24.0
scikit-learn >= 1.3.0
sqlalchemy >= 2.0.0
```

---

### 6. Next Steps & Development Roadmap

1. **Phase 1 (MVP Code):** Execute single-file Streamlit script (`app.py`) embedding database models and risk logic.
2. **Phase 2 (Model Training):** Train model on historical auto claims data to replace initial heuristic weights.
3. **Phase 3 (Enterprise Readiness):** Migrate SQLite storage to Azure/AWS PostgreSQL and implement OAuth2 authentication.
