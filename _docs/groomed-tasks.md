# InsureHub MVP — Groomed Backlog

## Task 1: Project Setup & Passing Test

**Goal:** Bootstrap a Django project with basic structure and a passing test to verify the development environment is ready.

**Acceptance criteria**
- [ ] Django project created at `config/` directory
- [ ] Django app `underwriting/` created and added to INSTALLED_APPS
- [ ] `requirements.txt` (or `pyproject.toml`) contains Django and pytest/pytest-django
- [ ] Database migrations run without errors (`python manage.py migrate`)
- [ ] At least one test exists in `underwriting/tests/test_*.py` and passes
- [ ] Running `python manage.py test` shows ✓ pass (or `pytest` shows passed)
- [ ] Dev server starts without errors (`python manage.py runserver`)

**Out of scope**
- Docker configuration (see Task 19)
- Static file serving setup beyond development defaults
- Database seeding or fixtures

**Constraints**
- Use Django 5.0+ (as locked in `pyproject.toml`)
- Use pytest with pytest-django for testing
- Database: SQLite for development
- Must include `.gitignore` for Python/Django artifacts

---

## Task 2: Application Model & Migrations

**Goal:** Define the Application model with all required fields matching the architecture schema, and create the initial database migration.

**Acceptance criteria**
- [ ] `underwriting/models.py` contains Application model with all fields:
  - applicant_name (CharField, required)
  - driver_age (PositiveIntegerField, range 16–120)
  - vehicle_type (CharField, choices from architecture.md)
  - safety_rating (PositiveIntegerField, 1–5)
  - regional_risk_index (PositiveIntegerField, 1–100)
  - driving_experience_years (PositiveIntegerField)
  - calculated_risk_score (PositiveIntegerField, 0–100, nullable until saved)
  - initial_premium (DecimalField, nullable until calculated)
  - final_premium (DecimalField, nullable until calculated)
  - status (CharField, choices: 'flagged', 'approved', 'rejected', default 'flagged')
  - deductible_override (DecimalField, optional)
  - risk_override_percentage (DecimalField, -25 to +25, optional)
  - underwriter_notes (TextField, blank=True)
  - underwriter_id (ForeignKey to User, optional)
  - created_at (DateTimeField, auto_now_add=True)
  - updated_at (DateTimeField, auto_now=True)
  - decision_timestamp (DateTimeField, optional)
- [ ] Model has Meta options: ordering by created_at descending, verbose_name set
- [ ] Migration file created via `python manage.py makemigrations`
- [ ] Migration runs successfully: `python manage.py migrate`
- [ ] Test verifies Application can be created and saved with required fields

**Out of scope**
- Admin interface customization (see Task 3)
- Audit trail model (see Task 22)
- Automatic premium calculation on save (see Task 9)

**Constraints**
- Stay in `underwriting/models.py`
- Use Django ORM only (no raw SQL)
- Model must be migrationable with no circular dependencies
- Field names and types must match architecture.md exactly

---

## Task 3: Django Admin Configuration

**Goal:** Register Application model in Django Admin with appropriate filters, search, and read-only fields so underwriters can browse and edit applications.

**Acceptance criteria**
- [ ] Application model registered in `underwriting/admin.py`
- [ ] list_display shows: applicant_name, driver_age, calculated_risk_score, status, created_at (7 columns max)
- [ ] list_filter includes: status, created_at
- [ ] search_fields allows searching by: applicant_name
- [ ] calculated_risk_score and created_at/updated_at/decision_timestamp are read-only
- [ ] underwriter_notes textarea is editable in admin
- [ ] Admin page loads without errors at `/admin/underwriting/application/`
- [ ] Admin list page shows at least one test application (manual add or via fixture)
- [ ] Editing and saving an application works without errors

**Out of scope**
- Custom admin actions (e.g., bulk approve/reject)
- Inline editing of related models
- Admin permissions/groups beyond default Django admin access

**Constraints**
- Use Django's built-in ModelAdmin class
- No custom templates or JavaScript
- Stay in `underwriting/admin.py`

---

## Task 4: ApplicationForm & Validation

**Goal:** Create a Django form that validates applicant intake data with edge case handling.

**Acceptance criteria**
- [ ] `underwriting/forms.py` contains ApplicationForm as ModelForm for Application
- [ ] driver_age validation: rejects < 18, rejects > 100
- [ ] safety_rating validation: rejects < 1, rejects > 5
- [ ] regional_risk_index validation: rejects < 1, rejects > 100
- [ ] driving_experience_years custom clean(): cannot exceed (current_year - birth_year - 18)
- [ ] Form renders without errors in a test view
- [ ] Invalid data returns form.errors with human-readable error messages
- [ ] Valid data passes is_valid() check
- [ ] Widget overrides render select inputs for choices, number inputs for ages/ratings

**Out of scope**
- HTMX integration in form (see Task 10)
- Custom field widgets beyond HTML5 input types
- Client-side validation

**Constraints**
- Use Django forms.ModelForm
- Validation must accept valid boundary values (e.g., age 18, age 100, experience 0)
- Error messages must be clear and actionable for applicants

---

## Task 5: Risk Scoring Service

**Goal:** Wrap the pre-trained Scikit-learn model in a reusable Python class that takes an Application and returns a risk score.

**Acceptance criteria**
- [ ] `underwriting/services/risk_scorer.py` created with RiskScoringService class
- [ ] Constructor loads pre-trained model from `models/risk_model.pkl`
- [ ] If model file missing, raises informative error (not generic FileNotFoundError)
- [ ] predict(application: Application) method returns risk_score as int (0–100)
- [ ] Handles edge cases: missing optional fields, extreme values
- [ ] Unit test: predict() with known inputs returns expected score (or within margin)
- [ ] Method works with Application instance from Task 2 model

**Out of scope**
- Model training or retraining logic
- Batch prediction for multiple applications
- Model versioning or fallback models

**Constraints**
- Use Scikit-learn (as locked in `pyproject.toml`)
- Model file must be in `models/risk_model.pkl` (exact path)
- predict() must not modify the Application instance
- No HTTP requests or external service calls

---

## Task 6: Premium Calculator Service

**Goal:** Implement formulas to convert risk scores into initial and adjusted premiums.

**Acceptance criteria**
- [ ] `underwriting/services/premium_calculator.py` created
- [ ] calculate_premium(risk_score: int, coverage_limit: Decimal) returns Decimal (premium amount)
- [ ] Formula implemented per architecture.md (initial_premium = base + (risk_score * factor) + coverage_adjustment)
- [ ] calculate_premium_with_overrides(base_premium: Decimal, deductible: Decimal, risk_override_pct: float) returns Decimal
- [ ] Formula for override: adjusted_premium = base_premium * (1 + risk_override_pct / 100) * deductible_factor
- [ ] Edge cases: deductible £250–£2000, risk_override -25% to +25%
- [ ] Unit tests: known risk_score → expected premium
- [ ] Unit tests: known override values → expected adjusted premium

**Out of scope**
- Tax or fee calculations
- Currency conversion
- Logging premium calculations to audit trail

**Constraints**
- Functions must be pure (no side effects, no database writes)
- Use Decimal type for monetary values (not float)
- All formulas in architecture.md must be implemented exactly
- Must handle edge case boundaries (e.g., risk_override = -25%, +25%)

---

## Task 7: STP Engine Service

**Goal:** Implement Straight-Through Processing categorization logic that assigns applications to approval buckets.

**Acceptance criteria**
- [ ] `underwriting/services/stp_engine.py` created with categorize_status(risk_score: int) function
- [ ] Returns 'approved' when risk_score < 20
- [ ] Returns 'rejected' when risk_score > 85
- [ ] Returns 'flagged' when 20 ≤ risk_score ≤ 85
- [ ] Boundary tests: risk_score=19 → 'approved', 20 → 'flagged', 85 → 'flagged', 86 → 'rejected'
- [ ] Invalid input (negative, > 100) raises ValueError with clear message
- [ ] Unit tests for all three bands and boundary cases

**Out of scope**
- Manual override of STP categorization (see Task 16)
- Rules engine (no if-else chains beyond the 3 bands)
- A/B testing different thresholds

**Constraints**
- Function must be pure (no database queries)
- Thresholds must be constants at top of file (APPROVED_THRESHOLD, etc.)
- No floating-point risk scores (input must be int)

---

## Task 8: Home & Intake Form View

**Goal:** Create landing page and application intake form page with basic navigation.

**Acceptance criteria**
- [ ] `underwriting/views.py` contains home_view function/class
- [ ] `underwriting/urls.py` created with URL routing
- [ ] home_view renders `underwriting/templates/home.html` with title "Welcome to InsureHub"
- [ ] home.html contains link to intake form (`/applications/new/`)
- [ ] application_form_view renders `underwriting/templates/intake/form.html`
- [ ] intake/form.html displays ApplicationForm from Task 4
- [ ] intake/form.html is not full page HTMX response (uses base.html for initial GET)
- [ ] Both views accessible via browser without errors
- [ ] Form renders all fields: applicant_name, driver_age, vehicle_type, safety_rating, regional_risk_index, driving_experience_years

**Out of scope**
- Form submission handling (see Task 9)
- HTMX risk preview (see Task 10)
- Email notifications

**Constraints**
- Use function-based views or Django generic views (your choice)
- Templates must extend base.html (see Task 11)
- No HTMX attributes on form yet
- No inline CSS; use Tailwind classes only

---

## Task 9: Application Creation & Risk Scoring View

**Goal:** Handle form submission, calculate risk and premium, determine decision status, and save to database.

**Acceptance criteria**
- [ ] POST handler in views.py receives intake form submission
- [ ] ApplicationForm validates all fields; if invalid, re-render form with errors
- [ ] On valid submission:
  - Calls RiskScoringService.predict() to get risk_score
  - Calls premium_calculator.calculate_premium() to get initial_premium
  - Calls stp_engine.categorize_status() to get status ('approved', 'rejected', 'flagged')
  - Saves Application to database with all calculated fields
  - Does NOT set underwriter_id or override fields
- [ ] Redirects to confirmation page (`/applications/{id}/confirmation/`)
- [ ] confirmation.html displays: applicant_name, risk_score, initial_premium, status (decision)
- [ ] confirmation.html shows appropriate message per status (e.g., "Your application has been approved" or "Pending review")
- [ ] Test: valid submission → Application saved with correct calculated fields
- [ ] Test: invalid submission → form re-renders with errors, no Application created

**Out of scope**
- Email notifications on approval/rejection
- Payment processing
- Automatic underwriter assignment

**Constraints**
- Use the three services from Tasks 5, 6, 7 exactly as is
- Do not calculate risk/premium outside of services
- Database transaction must complete or roll back (no partial saves)
- No modification of initial_premium/risk_score after save

---

## Task 10: HTMX Risk Preview Endpoint

**Goal:** Create an endpoint that returns a live risk preview as the user fills out the form.

**Acceptance criteria**
- [ ] POST endpoint at `/applications/preview/` (or `/api/risk-preview/`)
- [ ] Accepts HTMX POST with partial form data (applicant_name, driver_age, etc.)
- [ ] Validates data with ApplicationForm; if invalid, returns partial with error messages
- [ ] On valid data:
  - Calls RiskScoringService.predict()
  - Calls premium_calculator.calculate_premium()
  - Calls stp_engine.categorize_status()
  - Returns `underwriting/partials/risk_preview.html` fragment (NOT full page)
- [ ] Fragment displays: calculated_risk_score, initial_premium, status label
- [ ] Fragment uses small/readable formatting for inline preview (not full page)
- [ ] Does NOT save Application to database
- [ ] Test: HTMX POST with valid data → correct risk_preview fragment returned
- [ ] Test: HTMX POST with invalid data → form errors returned in fragment

**Out of scope**
- Debouncing or rate limiting on preview requests
- History of previewed values
- Saving preview results

**Constraints**
- Endpoint must return HTML fragment only (content-type: text/html)
- Fragment file: `underwriting/partials/risk_preview.html`
- No database queries (stateless calculation)
- Must not save to Application model

---

## Task 11: Base Template & Static Setup

**Goal:** Create base HTML template with Tailwind CSS and HTMX library, establishing site-wide navigation and structure.

**Acceptance criteria**
- [ ] `underwriting/templates/base.html` created
- [ ] base.html includes Django blocks: head, title, body, content (minimum)
- [ ] base.html links to Tailwind CSS (via CDN: https://cdn.tailwindcss.com)
- [ ] base.html links to HTMX JS library (via CDN: https://unpkg.com/htmx.org)
- [ ] Navigation bar present with links: Home, Dashboard (if user.is_staff), Admin (if user.is_superuser)
- [ ] Navigation uses Tailwind styling (flexbox, padding, colors)
- [ ] All child templates can extend base.html without errors
- [ ] Footer placeholder present
- [ ] Static files directory created at `underwriting/static/` (empty, for future CSS)
- [ ] Browser loads page without console errors or missing resources

**Out of scope**
- Custom CSS files or SCSS
- Responsive breakpoints beyond Tailwind defaults
- Dark mode support

**Constraints**
- Use Tailwind CDN only (no npm/build step)
- Use HTMX CDN from unpkg.com
- No inline <style> tags
- Django static files must be configured in settings.py

---

## Task 12: Intake Templates

**Goal:** Build HTML templates for applicant intake form and confirmation page, including HTMX-powered risk preview.

**Acceptance criteria**
- [ ] `underwriting/templates/intake/form.html` created:
  - Extends base.html
  - Renders ApplicationForm with {{ form.as_p }} or custom fields
  - Submit button labeled "Get Risk Preview" or "Apply"
  - Hidden HTMX attribute on submit button: `hx-post="/applications/preview/"` or equivalent
  - Form validates client-side and server-side
- [ ] `underwriting/templates/intake/confirmation.html` created:
  - Extends base.html
  - Displays applicant_name, risk_score, initial_premium, status
  - Shows status-appropriate message (approved/rejected/flagged)
  - Link back to home or new application
- [ ] `underwriting/partials/risk_preview.html` created:
  - Fragment template (no base.html extension)
  - Displays risk_score, initial_premium, status
  - Formatted for inline display (small, readable)
  - Shows any validation errors if applicable
- [ ] intake/form.html renders without errors (in browser or via test)
- [ ] intake/confirmation.html renders without errors with sample Application data
- [ ] risk_preview.html renders without errors with sample values

**Out of scope**
- Custom form field styling beyond Tailwind
- File uploads or attachments
- Multi-step form wizard

**Constraints**
- All templates must extend or use base.html
- Use Tailwind classes only (no inline styles)
- Form fields must be accessible (labels, aria-labels)
- Partials must not include <html>, <head>, <body> tags

---

## Task 13: Underwriter Dashboard Queue View

**Goal:** Display a filterable list of flagged applications awaiting underwriter review.

**Acceptance criteria**
- [ ] View at `/dashboard/queue/` (or `/underwriter/queue/`)
- [ ] Requires authentication (staff or superuser only); redirects to login otherwise
- [ ] Queries Application.objects.filter(status='flagged'), ordered by created_at descending
- [ ] Renders `underwriting/templates/dashboard/queue.html`
- [ ] queue.html displays table with columns: applicant_name, driver_age, risk_score, created_at
- [ ] Each row is clickable (href to `/dashboard/policy/{id}/` or /policy/{id}/)
- [ ] Table shows empty message if no flagged applications
- [ ] Pagination shows at least first 20 results (or all if < 20)
- [ ] Test: only flagged applications shown (not approved/rejected)
- [ ] Test: applications ordered newest first

**Out of scope**
- Filtering by date range or risk score (see future Tasks)
- Bulk actions (see future Tasks)
- Export to CSV or PDF

**Constraints**
- View must check user permissions (is_staff or is_superuser)
- Database query must be efficient (use .select_related() if needed)
- Template must use base.html
- Table must be sortable by created_at ascending/descending (optional: other columns)

---

## Task 14: Policy Detail View & Sliders Template

**Goal:** Display a single flagged application with interactive sliders for underwriter deductible and risk adjustments.

**Acceptance criteria**
- [ ] View at `/dashboard/policy/{id}/` retrieves Application by ID
- [ ] Requires authentication (staff only)
- [ ] Renders `underwriting/templates/dashboard/policy_detail.html`
- [ ] policy_detail.html displays:
  - Applicant info: applicant_name, driver_age, vehicle_type, safety_rating, regional_risk_index, driving_experience_years
  - Calculated info: calculated_risk_score, initial_premium
  - Status and decision_timestamp (if present)
  - Current deductible_override and risk_override_percentage (if present)
- [ ] Two range sliders present:
  - Deductible slider: min £250, max £2000, step £50, current value from deductible_override or default
  - Risk override slider: min -25%, max +25%, step 1%, current value from risk_override_percentage or default
- [ ] Each slider has `hx-trigger="change"` to POST updated values (see Task 15)
- [ ] Textarea for underwriter_notes (optional, visible)
- [ ] Buttons: "Save Overrides", "Approve", "Reject" (see Tasks 16–17)
- [ ] Template extends base.html
- [ ] Test: view renders without errors for valid Application ID
- [ ] Test: view returns 404 for invalid/missing Application ID

**Out of scope**
- AuditTrail display on this page
- Historical override values or versioning
- Slider animations beyond HTML5 native

**Constraints**
- Sliders must use HTML5 <input type="range"> elements
- Slider values must be sent to backend via HTMX POST on change
- No CSS animations (use Tailwind transforms only)
- Must not auto-save; must wait for explicit "Save" button

---

## Task 15: Recalculate Premium HTMX Endpoint

**Goal:** Return updated premium display when underwriter adjusts deductible or risk override sliders.

**Acceptance criteria**
- [ ] POST endpoint at `/dashboard/policy/{id}/recalculate/` (or `/api/recalculate-premium/`)
- [ ] Receives: app_id, deductible (float), risk_override_percentage (float) from HTMX
- [ ] Validates input (deductible £250–£2000, risk_override -25% to +25%); returns error fragment if invalid
- [ ] On valid input:
  - Retrieves Application from database
  - Calls premium_calculator.calculate_premium_with_overrides(base_premium=Application.initial_premium, deductible, risk_override_pct)
  - Returns `underwriting/partials/premium_recalc.html` fragment with new final_premium value
- [ ] Fragment displays: final_premium amount, clear/readable formatting
- [ ] Does NOT save Application to database (preview only)
- [ ] Test: POST with valid values → correct premium returned
- [ ] Test: POST with invalid values → error message returned

**Out of scope**
- Saving overrides (see Task 16)
- History of recalculations
- Tax or fee calculations on top of premium

**Constraints**
- Endpoint must return HTML fragment (content-type: text/html)
- Fragment file: `underwriting/partials/premium_recalc.html`
- No database writes
- Formula must use premium_calculator service exactly as is

---

## Task 16: Save Underwriter Override Endpoint

**Goal:** Persist underwriter adjustments (deductible, risk override, notes) and save to database.

**Acceptance criteria**
- [ ] POST endpoint at `/dashboard/policy/{id}/save-overrides/` (or `/api/save-overrides/`)
- [ ] Receives: app_id, deductible, risk_override_percentage, underwriter_notes from form POST
- [ ] Validates input (same as Task 15); returns error if invalid
- [ ] On valid input:
  - Retrieves Application
  - Recalculates final_premium using premium_calculator.calculate_premium_with_overrides()
  - Updates Application fields: deductible_override, risk_override_percentage, underwriter_notes, underwriter_id (current user)
  - Sets updated_at timestamp
  - Saves to database
  - Returns success message or redirects to policy detail page
- [ ] Test: overrides saved correctly to database
- [ ] Test: final_premium recalculated and saved
- [ ] Test: underwriter_id set to current user

**Out of scope**
- Audit trail logging (see Task 22)
- Email notifications to applicant
- Rollback/undo functionality

**Constraints**
- User must be authenticated and is_staff
- Must use premium_calculator service for final_premium calculation
- Database transaction must complete atomically
- underwriter_id must be set to request.user

---

## Task 17: Approve/Reject Policy Endpoints

**Goal:** Allow underwriter to make final approval or rejection decisions and record the decision timestamp.

**Acceptance criteria**
- [ ] POST endpoint at `/dashboard/policy/{id}/approve/`
- [ ] POST endpoint at `/dashboard/policy/{id}/reject/`
- [ ] Both endpoints receive app_id via POST (from button on policy detail page)
- [ ] Both require authentication (is_staff)
- [ ] approve endpoint:
  - Retrieves Application by ID
  - Sets status = 'approved'
  - Sets decision_timestamp = now()
  - Saves to database
  - Returns success message or redirects to queue
- [ ] reject endpoint:
  - Retrieves Application by ID
  - Sets status = 'rejected'
  - Sets decision_timestamp = now()
  - Saves to database
  - Returns success message or redirects to queue
- [ ] Test: application status changes from 'flagged' to 'approved' or 'rejected'
- [ ] Test: decision_timestamp is set to a recent time
- [ ] Test: rejected applications no longer appear in queue view
- [ ] Test: 404 if application ID does not exist

**Out of scope**
- Reversing decisions or change history
- Notifying applicant of decision
- Conditional approval (e.g., only if overrides met certain criteria)

**Constraints**
- Endpoints must be protected by permission check (is_staff)
- decision_timestamp must use Django timezone.now()
- Must return success response (JSON or redirect)
- No soft deletes; status change is the only record

---

## Task 18: Dashboard Templates

**Goal:** Build HTML templates for underwriter queue and policy detail pages, including slider controls and action buttons.

**Acceptance criteria**
- [ ] `underwriting/templates/dashboard/queue.html` created:
  - Extends base.html
  - Displays table of flagged applications (applicant_name, driver_age, risk_score, created_at)
  - Each row is clickable link to policy detail page
  - Empty state message if no flagged applications
  - Pagination or "Load More" if > 20 results (optional for MVP)
- [ ] `underwriting/templates/dashboard/policy_detail.html` created:
  - Extends base.html
  - Displays full applicant and policy details (see Task 14)
  - Two range sliders with labels and current values displayed
  - Textarea for underwriter_notes
  - Buttons: "Save Overrides", "Approve", "Reject" with appropriate styling
  - "Save Overrides" button POSTs to Task 16 endpoint
  - "Approve"/"Reject" buttons POST to Task 17 endpoints
- [ ] `underwriting/partials/premium_recalc.html` created:
  - Fragment (no base.html)
  - Displays new final_premium value only
  - Used as HTMX swap target from Task 15
- [ ] All templates render without errors in browser/tests
- [ ] All templates use Tailwind styling (no inline CSS)

**Out of scope**
- Form validation UI beyond server responses
- Animations or transitions
- Mobile responsiveness (Tailwind defaults)

**Constraints**
- All templates must extend or use base.html
- Buttons must have clear labels (not just icons)
- Form data must be sent via HTMX or standard POST
- Partials must have no <html>, <head>, <body> tags

---

## Task 19: Docker Setup

**Goal:** Containerize the Django app for both local development and production environments.

**Acceptance criteria**
- [ ] Dockerfile created:
  - Based on python:3.11-slim
  - Installs dependencies from requirements/pyproject.toml
  - Copies code into container
  - Runs migrations on startup
  - Exposes port 8000
  - Starts Gunicorn (or development server for MVP)
- [ ] docker-compose.yml created with services:
  - web: Django app from Dockerfile
  - db: PostgreSQL image (or SQLite for MVP; SQLite OK for MVP sprint)
  - volumes for persistence and code mounting (for dev)
  - environment variables: DEBUG, DATABASE_URL, SECRET_KEY
- [ ] docker-compose up --build runs without errors
- [ ] App accessible at http://localhost:8000 after docker-compose up
- [ ] Database migrations run automatically on startup
- [ ] docker-compose down stops and removes containers cleanly
- [ ] Quick-start guide in README or _docs/ explains docker-compose commands

**Out of scope**
- Kubernetes deployment
- Multi-stage build optimization
- Nginx reverse proxy (for MVP)
- CI/CD pipeline integration

**Constraints**
- Python version 3.11+ only
- Use Gunicorn for production mode
- Development mode can use `python manage.py runserver` if simpler
- Environment variables must not be hard-coded in Dockerfile

---

## Task 20: Sample Data & Fixtures

**Goal:** Create test data covering all approval statuses so underwriters can manually test the dashboard and override workflows.

**Acceptance criteria**
- [ ] Sample data includes 10–15 Application instances
- [ ] Sample set covers all statuses: at least 3 'approved', 3 'rejected', 3–4 'flagged'
- [ ] Flagged applications have varied risk_scores (30, 50, 75) for testing
- [ ] Sample data includes at least one application with deductible_override and risk_override_percentage set
- [ ] Data is loadable via `python manage.py loaddata` or management command
- [ ] Data can be loaded into empty database without errors
- [ ] Data exists in `underwriting/fixtures/` or as a management command
- [ ] Documentation in comment or README explains how to load (e.g., `python manage.py loaddata initial_policies.json`)
- [ ] All sample applications have realistic field values

**Out of scope**
- Anonymized production data
- Automated data refresh/reset
- Large-scale performance testing data (1000+ records)

**Constraints**
- Fixture must be JSON format (Django standard) or management command
- All field values must pass model validation
- No real personal information (use made-up names, ages)
- Fixture/command must run without external dependencies

---

## Task 21: Integration Tests

**Goal:** Test full end-to-end workflows to ensure intake, underwriter review, and decision flows work together.

**Acceptance criteria**
- [ ] Test file: `underwriting/tests/test_workflows.py`
- [ ] Test 1: Intake submission workflow
  - POST valid application data to intake form view
  - Verify Application saved with correct risk_score, initial_premium, status
  - Verify redirect to confirmation page
  - Verify confirmation page displays correct values
- [ ] Test 2: Flagged application underwriter review
  - Create Application with status='flagged'
  - GET policy detail page (verify renders)
  - POST deductible and risk_override values
  - Verify final_premium recalculated correctly
  - POST save-overrides endpoint
  - Verify Application updated in database
- [ ] Test 3: Approval/rejection decision
  - Create flagged Application
  - POST to approve endpoint
  - Verify status='approved', decision_timestamp set
  - Verify application no longer in queue list
- [ ] Test 4: Rejection workflow
  - Create flagged Application
  - POST to reject endpoint
  - Verify status='rejected', decision_timestamp set
- [ ] All tests use Django TestClient (not mocks)
- [ ] All tests use real SQLite database
- [ ] Run `python manage.py test` or `pytest` and all tests pass
- [ ] Each test is independent (no shared state)

**Out of scope**
- Performance/load testing
- Selenium or browser automation tests
- API contract testing with external services

**Constraints**
- Use Django TestCase (not mock)
- Database must be real SQLite, not in-memory
- Each test must set up its own test data
- TestClient must simulate real HTTP requests (POST, GET)
- No fixtures or shared test state between tests

---

## Task 22: Audit Trail Model & Logging (Optional for MVP)

**Goal:** Record application state changes for compliance review and underwriter action tracking.

**Acceptance criteria**
- [ ] AuditTrail model in underwriting/models.py with fields:
  - application (ForeignKey to Application)
  - action (CharField: 'created', 'risk_calculated', 'overridden', 'approved', 'rejected')
  - changed_fields (JSONField: dict of field_name: [old_value, new_value])
  - underwriter_id (ForeignKey to User, nullable for system actions)
  - timestamp (DateTimeField, auto_now_add=True)
  - notes (TextField, optional)
- [ ] Migration created and applied
- [ ] Logging added to views:
  - Task 9: log 'created' when new Application saved
  - Task 16: log 'overridden' when deductible/risk_override changed
  - Task 17: log 'approved' or 'rejected' when decision made
- [ ] Each log entry includes changed_fields JSON (before → after values)
- [ ] Audit trail visible in Django admin with list_display and filters
- [ ] Test: audit trail entries created and saved correctly
- [ ] Documentation in CLAUDE.md explains audit trail format

**Out of scope**
- Real-time audit notifications
- Audit trail export/reporting UI
- Encryption of audit data at rest
- Compliance certifications (SOC 2, etc.)

**Constraints**
- Use Django JSONField (requires PostgreSQL or must be serialized)
- For MVP SQLite: serialize changed_fields as text or use TextField
- Each action must log consistently (same action name, same field format)
- Logging must not break existing views if AuditTrail insert fails

---

## Summary

- **Foundation tasks** (1–7): Set up models, services, basic business logic
- **Feature tasks** (8–18): Build views, forms, templates, HTMX integration
- **Polish tasks** (19–22): Docker, sample data, tests, audit trail

**Recommended order:** 1 → 2 → 3 → 4 → 5 → 6 → 7 → 11 → 8 → 12 → 10 → 9 → 13 → 14 → 15 → 16 → 17 → 18 → 21 → 20 → 19 → 22

Each task is self-contained with all context needed. Architecture.md and this document are the only external references needed.
