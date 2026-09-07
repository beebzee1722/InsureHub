# InsureHub Development Guide

## Commands

### Dependency Management
- `uv sync` - install dependencies from `pyproject.toml`
- `uv pip list` - list installed packages

### Django Management
- `python manage.py runserver` - start dev server (http://localhost:8000)
- `python manage.py migrate` - apply database migrations
- `python manage.py makemigrations` - create new migrations after model changes
- `python manage.py createsuperuser` - create admin user
- `python manage.py test` - run all tests
- `python manage.py test underwriting.tests.test_models` - run one test module
- `python manage.py shell` - interactive Python shell with Django context

### Docker
- `docker-compose up --build` - start app + PostgreSQL locally
- `docker-compose down` - stop containers
- `docker-compose logs -f web` - stream app logs

### Code Quality
- `uv run pytest` - run full test suite
- `uv run pytest tests/test_home.py` - run one test file
- `uv run pytest -v` - verbose output with test names
- `uv run ruff check .` - lint code
- `uv run ruff format .` - auto-format code

### Git & Deployment
- `git push` - push commits (confirm destination)
- `git pull` - fetch and merge from remote

---

## Rules

### Dependencies
- **Dependencies are added in `pyproject.toml`.** Do not add one without asking first.
- Core stack locked: Django 5.0+, HTMX, Tailwind, Scikit-learn, SQLAlchemy
- Test dependencies: pytest, pytest-django

### Code Style
- **Format on save:** Run `uv run ruff format .` before committing
- **No print() debugging:** Use Django logging or pytest `capsys`
- **Type hints optional** but encouraged for service layer functions

### Models & Database
- **Always create migrations:** After any model change, run `makemigrations` and `migrate`
- **No raw SQL:** Use Django ORM / SQLAlchemy queries
- **Tests must hit real DB:** Never mock the database layer (use Django TestCase)

### Views & Forms
- **Validate at boundaries:** Use Django Forms for input validation; trust internal code
- **No CSRF shortcuts:** Always use `{% csrf_token %}` in POST forms or `@csrf_exempt` with justification
- **HTMX endpoints return fragments:** Return partial HTML, not full pages

### Testing
- **One test per task:** Each GitHub issue should have passing tests before merge
- **Happy path + edge cases:** Test normal flow and boundary conditions (e.g., risk_score = 19, 20, 85, 86)
- **Integration tests use Django TestClient:** Simulate real HTTP requests, not unit mocks

### Commits
- **Descriptive messages:** "Add risk scoring view" not "fix stuff"
- **Small, reviewable commits:** One feature per commit when possible
- **Co-author if pair programming:** Include `Co-Authored-By:` in message

### Architecture Reference
- **See `_docs/architecture.md`** for system design, data flow, HTMX patterns
- **See `_docs/tasks.md`** for task descriptions and order
- **See `_docs/plan.md`** for business requirements (SRD)

### Task Tracking
- **Work on one GitHub issue at a time** (mark as "in progress")
- **Each issue should be independent** (see task descriptions for context)
- **Link to issues in commit messages:** Reference `#51`, `#52`, etc.

### Common Mistakes to Avoid
- ❌ Modifying `requirements.txt` directly (use `pyproject.toml`)
- ❌ Saving Application model without risk score (always call RiskScoringService)
- ❌ Returning full HTML from HTMX endpoints (return fragments only)
- ❌ Hard-coding feature order in RiskScoringService (use consistent tuple)
- ❌ Skipping migrations before pushing (migrations must be committed)
- ❌ Testing mocked database (use Django TestCase with real SQLite)

---

## Development Workflow

1. **Pick a task** from GitHub issues (#51-#72)
2. **Mark issue as "in progress"** (GitHub UI)
3. **Create a branch** (optional but recommended): `git checkout -b issue-51-project-setup`
4. **Write code** following the rules above
5. **Run tests:** `uv run pytest` (or `python manage.py test`)
6. **Format:** `uv run ruff format .`
7. **Commit with reference:** `git commit -m "Add project setup (#51)"`
8. **Push & create PR** (or merge directly to main for MVP speed)
9. **Mark issue as "closed"**

---

## Debugging Tips

- **Django shell:** `python manage.py shell` to test queries, services interactively
- **Print model:**
  ```python
  from underwriting.models import Application
  app = Application.objects.first()
  print(app.__dict__)
  ```
- **Inspect test failures:** Run `pytest tests/test_x.py -vv` for detailed output
- **Check migrations:** `python manage.py showmigrations` to see migration state
- **HTMX debugging:** Browser DevTools → Network tab, inspect request/response payloads

---

## Quick Start (First Time)

```bash
# 1. Install dependencies
uv sync

# 2. Run migrations
python manage.py migrate

# 3. Create admin user
python manage.py createsuperuser

# 4. Start dev server
python manage.py runserver

# 5. Access
# - App: http://localhost:8000/
# - Admin: http://localhost:8000/admin/
```

---

## Questions?

- Refer to `_docs/architecture.md` for system design
- Refer to GitHub issue descriptions for task context
- Check Django docs: https://docs.djangoproject.com/
- Check HTMX docs: https://htmx.org/
