# InsureHub Agent Guidelines

## Commands

### Setup & Dependencies
- `uv sync` - install dependencies from `pyproject.toml`
- `uv pip list` - verify installed packages

### Testing
- `uv run pytest` - run full test suite
- `uv run pytest tests/test_home.py` - run one test file
- `uv run pytest -v` - verbose output
- `python manage.py test` - Django test runner (alternative)

### Development
- `python manage.py runserver` - start dev server (http://localhost:8000)
- `python manage.py migrate` - apply database migrations
- `python manage.py makemigrations` - create migrations after model changes
- `python manage.py createsuperuser` - create admin user
- `python manage.py shell` - interactive shell with Django context

### Code Quality
- `uv run ruff check .` - lint code
- `uv run ruff format .` - auto-format code

### Docker
- `docker-compose up --build` - start app + PostgreSQL
- `docker-compose down` - stop containers

### Git
- `git push` - push commits (specify branch/confirm destination)
- `git pull` - fetch and merge

---

## Rules

- **Dependencies are added in `pyproject.toml`. Do not add one without asking.**
- **Tests must hit real database.** Never mock the database layer (use Django `TestCase`).
- **HTMX endpoints return HTML fragments, not full pages.**
- **Format code before committing:** `uv run ruff format .`
- **Commit message format:** "Add feature description (#issue-number)" — reference the GitHub issue.
- **Always commit migrations** after model changes (`python manage.py makemigrations`).

### Architecture Reference
- **`_docs/architecture.md`** — system design, routes, data flow, HTMX patterns
- **`_docs/tasks.md`** — task descriptions (all context you need per task)
- **`_docs/plan.md`** — business requirements (SRD)
- **`CLAUDE.md`** — detailed development guide

### Task Workflow
1. Pick one GitHub issue (#51–#72)
2. Read issue description + `architecture.md` to understand context
3. Write code following rules above
4. Run tests: `uv run pytest`
5. Format: `uv run ruff format .`
6. Commit: `git commit -m "Description (#issue-number)"`
7. Push: `git push`

---

## Critical Points

- Migrations must be committed (run `makemigrations` after model changes)
- Tests use real SQLite, never mocks
- HTMX endpoints: return fragments only, not full pages
- Reference GitHub issue number in every commit message

---

## Quick Start

```bash
uv sync
python manage.py migrate
python manage.py runserver
# http://localhost:8000
```

Test a task:
```bash
uv run pytest tests/test_models.py -v
```

Format before pushing:
```bash
uv run ruff format .
git commit -m "Add model fields (#51)"
git push
```
