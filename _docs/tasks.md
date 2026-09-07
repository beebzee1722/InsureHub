# InsureHub MVP — Task Backlog

## 1. Project Setup & Passing Test
**Goal:** Bootstrap Django project with basic structure and one passing test.

**Description:** Create Django project (`config/`) and app (`underwriting/`), install dependencies from `requirements.txt`, run migrations on empty SQLite database, and write a simple test that passes. This task verifies the development environment is ready. By the end, you should be able to run `python manage.py test` and see ✓ pass.

---

## 2. Application Model & Migrations
**Goal:** Define the Application model with all required fields and create database migration.

**Description:** Create `underwriting/models.py` with the Application model matching the schema in architecture.md (applicant_name, driver_age, vehicle details, calculated_risk_score, initial_premium, final_premium, status, etc.). Add Django model Meta options (ordering, verbose_name). Run `makemigrations` and `migrate` to create the database table.

---

## 3. Django Admin Configuration
**Goal:** Set up Django Admin to browse and edit applications.

**Description:** Register the Application model in `underwriting/admin.py` with read-only fields for calculated_risk_score and timestamps. Add list_display, list_filter (by status, created_at), and search_fields. This gives underwriters a free admin interface to review applications without writing custom views yet.

---

## 4. ApplicationForm & Validation
**Goal:** Create a Django form that validates applicant intake data.

**Description:** Build `underwriting/forms.py` with ApplicationForm (ModelForm). Add validation for driver_age (18–100), safety_rating (1–5), regional_risk_index (1–100), and a custom clean() method to check driving_experience doesn't exceed years since age 18. Include widget overrides for better HTML rendering.

---

## 5. Risk Scoring Service
**Goal:** Wrap the Scikit-learn model in a reusable Python class.

**Description:** Create `underwriting/services/risk_scorer.py` with RiskScoringService class. Load the pre-trained `models/risk_model.pkl` in __init__(), implement a predict() method that takes an Application instance and returns a risk_score (0–100). Handle missing model file gracefully with a meaningful error.

---

## 6. Premium Calculator Service
**Goal:** Implement logic to convert risk scores into premiums.

**Description:** Create `underwriting/services/premium_calculator.py` with two functions: `calculate_premium(risk_score, coverage_limit)` for initial premium, and `calculate_premium_with_overrides(base_premium, deductible, risk_override_pct)` for underwriter-adjusted premium. Implement the formulas from the architecture doc.

---

## 7. STP Engine Service
**Goal:** Implement Straight-Through Processing categorization logic.

**Description:** Create `underwriting/services/stp_engine.py` with `categorize_status(risk_score)` function that returns 'approved' (< 20), 'rejected' (> 85), or 'flagged' (20–85). Add unit tests for all three bands.

---

## 8. Home & Intake Form View
**Goal:** Create landing page and application intake form page.

**Description:** Build `underwriting/views.py` with `home_view` (renders home.html with link to intake) and `application_form_view` (renders intake form). Use generic Django views or function-based views. No HTMX yet, just form rendering. Also create `underwriting/urls.py` to route these.

---

## 9. Application Creation & Risk Scoring View
**Goal:** Handle form submission, calculate risk, and save to database.

**Description:** Add `application_create_view` to views.py that receives POST from intake form, validates with ApplicationForm, calls RiskScoringService and premium_calculator, categorizes status with stp_engine, saves Application to DB, and redirects to a confirmation page. Render confirmation.html with risk score and decision.

---

## 10. HTMX Risk Preview Endpoint
**Goal:** Add endpoint for live risk preview as user fills form.

**Description:** Create `risk_preview_view` in views.py that accepts POST from HTMX, validates form data, runs risk/premium calculation (without saving), and returns `partials/risk_preview.html` fragment showing risk_score, initial_premium, and status. Add to urls.py with `/applications/preview/` route.

---

## 11. Base Template & Static Setup
**Goal:** Create base HTML template with Tailwind CSS and HTMX library.

**Description:** Create `underwriting/templates/base.html` with Django block structure (head, body, content), link to Tailwind CDN and HTMX JS library, add navigation (Home, Dashboard, Admin). Create placeholder blocks for child templates. Set up `underwriting/static/` directory structure.

---

## 12. Intake Templates
**Goal:** Build HTML forms for applicant intake and risk preview.

**Description:** Create `underwriting/templates/intake/form.html` (extends base.html, renders ApplicationForm with HTMX attributes for preview button), `intake/confirmation.html` (shows risk decision and next steps), and `partials/risk_preview.html` (displays risk_score, initial_premium, status as a fragment).

---

## 13. Underwriter Dashboard Queue View
**Goal:** Show list of flagged applications awaiting review.

**Description:** Add `dashboard_queue_view` to views.py that queries Application.objects.filter(status='flagged'), orders by created_at. Render `dashboard/queue.html` with table of applications (applicant_name, risk_score, created_at), each row clickable to view full policy detail.

---

## 14. Policy Detail View & Sliders Template
**Goal:** Display single policy with interactive sliders for underwriter adjustments.

**Description:** Add `policy_detail_view` to views.py that retrieves one Application by ID and renders `dashboard/policy_detail.html`. Template shows applicant info, risk score, initial premium, and two range sliders (deductible £250–£2000, risk override -25% to +25%). Include HTMX hx-trigger="change" to POST slider changes.

---

## 15. Recalculate Premium HTMX Endpoint
**Goal:** Return updated premium HTML when underwriter adjusts sliders.

**Description:** Add `recalculate_premium_api` to views.py (POST endpoint) that receives app_id, deductible, and risk_override from HTMX, calls premium_calculator.calculate_premium_with_overrides(), returns `partials/premium_recalc.html` fragment with new final_premium. No database save yet.

---

## 16. Save Underwriter Override Endpoint
**Goal:** Persist underwriter adjustments (deductible, notes) to database.

**Description:** Add `save_override_view` to views.py that POSTs from dashboard notes/save button, updates Application model (deductible_override, risk_override_percentage, underwriter_notes, underwriter_id), recalculates final_premium, saves to DB, and returns success. Consider adding AuditTrail logging.

---

## 17. Approve/Reject Policy Endpoints
**Goal:** Allow underwriter to make final approval/rejection decisions.

**Description:** Add `approve_policy_view` and `reject_policy_view` to views.py. Both receive app_id via POST, update status to 'approved' or 'rejected', set decision_timestamp, save to DB, and return success message. Routes: `/api/approve-policy/`, `/api/reject-policy/`.

---

## 18. Dashboard Templates
**Goal:** Build HTML for underwriter queue and policy detail pages.

**Description:** Create `dashboard/queue.html` (table of flagged applications with click-to-view), `dashboard/policy_detail.html` (full policy with sliders, notes textarea, approve/reject buttons), and `partials/premium_recalc.html` (just the premium amount to swap).

---

## 19. Docker Setup
**Goal:** Containerize the app for local and production environments.

**Description:** Create Dockerfile (based on python:3.11-slim, installs requirements, runs migrations, starts Gunicorn) and docker-compose.yml with web and PostgreSQL services. Ensure docker-compose.yml works locally with SQLite for MVP, PostgreSQL ready for prod. Write a quick start guide.

---

## 20. Sample Data & Fixtures
**Goal:** Load test applications for manual underwriter testing.

**Description:** Create `underwriting/fixtures/initial_policies.json` with 10–15 sample applications across all three status buckets (approved, rejected, flagged). Run `python manage.py loaddata` to populate. Or write a management command to generate randomized test data.

---

## 21. Integration Tests
**Goal:** Test full user workflows (intake → approval, intake → flagged → underwriter override).

**Description:** Write `underwriting/tests/test_workflows.py` with integration tests: test intake form submission → risk score saved, test flagged app → underwriter slider adjustment → premium recalculated, test approve/reject endpoints. Use Django TestClient to simulate HTTP requests.

---

## 22. Audit Trail Model & Logging (Optional for MVP)
**Goal:** Record all application state changes for compliance review.

**Description:** Create AuditTrail model in models.py (application FK, action, changed_fields JSON, underwriter_id, timestamp). Add logging calls in create/update views (e.g., when status changes, log who changed it and what changed). Display audit trail in admin or a read-only page.

---

## Notes

- **Task order:** Start with 1–7 (foundation), then 8–18 (features), then 19–22 (deployment & polish).
- **Independence:** Each task includes all context needed; you don't need to read others unless you want to understand the full picture.
- **Handing off:** Any task can be assigned to a teammate with just the task description and architecture.md.
- **Testing:** Each task should include a test or manual verification step.
