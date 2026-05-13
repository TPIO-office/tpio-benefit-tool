# AGENTS.md — USAON Benefit Tool (Django)

## Quick Start

- **Local dev** (SQLite, no infra): `DJANGO_SETTINGS_MODULE=benefit_tool.settings_dev python manage.py runserver`
- **Production stack** (Postgres + Gunicorn + Nginx): `docker compose up --build`
- **Seed demo data** (users, nodes, assessments): `python manage.py seed_data`
- **Demo credentials**: admin/admin123, analyst/analyst123, respondent/respondent123

## Architecture

Single Django app (`vta`) ported from Flask. All CBVs live in `vta/views/{assessments,nodes,links,visualization,main}.py`.
Roles (Admin/Analyst/Respondent) are Django **Groups**, not custom models. User profiles extend auth via `UserProfile` one-to-one.

## Model Design Gotchas

- `Node` is a **single flat table** with nullable subtype fields — NOT multi-table inheritance. The original Flask code used SQLAlchemy polymorphic tables; Django port collapsed them to avoid shared-PK complications.
- `AssessmentNode` is the junction between `Assessment` and `Node`. All `Link` edges reference `AssessmentNode`, never `Node` directly.
- Links must have source and target in the **same assessment** (validated in `Link.clean()`).

## Templates

- Custom filter `has_any_group` (`vta/templatetags/vta_tags.py`) replaces Jinja2-style group checks. Usage: `{% if user|has_any_group:'Analyst,Admin' %}`
- Every child template must have `{% load vta_tags %}` on line 2 (after `{% extends %}`). The base template loads `static` too.
- All templates use Bootstrap 5 classes.

## Commands Order

1. `makemigrations vta` → `migrate` → `seed_data` → `runserver` or `docker compose up`
2. Never run `migrate` without first running `makemigrations` after model changes.

## Testing

### Unit Tests (Django)

132 tests covering models, forms, views, template tags, and URL resolution in `vta/tests.py`.

```bash
source venv/bin/activate && DJANGO_SETTINGS_MODULE=benefit_tool.settings_dev python manage.py test vta --verbosity=2
```

### E2E Tests (Playwright)

19 browser tests covering login, assessments, nodes, links, and visualization in `e2e/*.spec.js`. Requires the dev server running on port 8000.

```bash
# Terminal 1: Start dev server
DJANGO_SETTINGS_MODULE=benefit_tool.settings_dev python manage.py runserver

# Terminal 2: Run E2E tests
npx playwright test
```

### Test Coverage Areas

- **Models**: Assessment, Node, AssessmentNode, Link, UserProfile (properties, validators, constraints)
- **Forms**: All form validation including cross-assessment link validation
- **Views**: Auth requirements, role-based access (Admin/Analyst/Respondent), CRUD operations
- **Template Tags**: `has_group`, `has_any_group`, `is_analyst_or_admin`
- **URLs**: All named URL patterns resolve correctly

## Docker Notes

- `settings.py` configures Postgres at host `db` (compose service name). Local dev uses `settings_dev.py` (SQLite).
- The `web` service runs `migrate --noinput && collectstatic --noinput` on startup before gunicorn.