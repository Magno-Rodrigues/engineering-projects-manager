# Architecture Analysis Document

**Date of Analysis**: 2026-03-05 19:08:33 UTC

## Data Model Relationships

The application uses a relational data model managed by SQLAlchemy (Flask-SQLAlchemy).
All tables follow `snake_case` naming and use integer primary keys.

### Core Entities

```
User (users)
 ├── owns → Project (projects.owner_id → users.id)
 ├── has → UserModulePermission (many-to-many via user_module_permissions)
 ├── creates → MeasurementCycle (measurement_cycles.created_by → users.id)
 └── manages → CostCenter (cost_centers.manager_id → users.id)

Project (projects)
 ├── has many → Task (tasks.project_id → projects.id)
 ├── has many → Report (reports.project_id → projects.id)
 ├── has one  → ProjectCharter (project_charters.project_id → projects.id)
 ├── has one  → ProjectClosure (project_closures.project_id → projects.id)
 ├── has many → Stakeholder (stakeholders.project_id → projects.id)
 ├── has many → CommunicationPlan (communication_plans.project_id → projects.id)
 ├── has many → FinancialBudget (financial_budgets.project_id → projects.id)
 ├── has many → FinancialTransaction (financial_transactions.project_id → projects.id)
 ├── has many → FinancialEarnedValue (financial_earned_values.project_id → projects.id)
 ├── has many → TimeEntry (time_entries.project_id → projects.id)
 └── has many ↔ CostCenter (many-to-many via project_cost_centers junction table)

FinancialBudget (financial_budgets)
 └── has many → FinancialBudgetItem (financial_budget_items.budget_id → financial_budgets.id)

MeasurementCycle (measurement_cycles)
 └── has many → TimeEntry (time_entries.cycle_id → measurement_cycles.id)

ModulePermission (module_permissions)
 └── has many → UserModulePermission (user_module_permissions.permission_id → module_permissions.id)
```

### Junction / Association Tables

| Table | Entities Linked | Purpose |
|-------|----------------|---------|
| `project_cost_centers` | Project ↔ CostCenter | Allows a project to share cost centers and a cost center to span multiple projects |
| `user_module_permissions` | User ↔ ModulePermission | Grants or restricts access to application modules and functions per user |

---

## Module Integrations

The application is organised as Flask **Blueprints**, each responsible for a distinct domain.

| Blueprint | URL Prefix | Key Interactions |
|-----------|-----------|-----------------|
| `auth` | `/auth` | Creates/authenticates `User`; stores session via `flask-login` |
| `main` | `/` | Renders dashboard; reads `MODULES_METADATA` from `constants.py` |
| `projects` | `/projects` | CRUD for `Project`; calls `ProjectService`; passes `PROJECT_STATUS`, `PROJECT_PRIORITY`, `PROJECT_CATEGORIES` to templates |
| `tasks` | `/tasks` | CRUD for `Task`; linked to `Project`; uses PMBOK knowledge areas |
| `reports` | `/reports` | Creates `Report` entities associated with a `Project` |
| `financial` | `/financial` | Manages `FinancialBudget`, `FinancialBudgetItem`, `FinancialTransaction`, `FinancialEarnedValue`, `CostCenter`; enforces `CostCenter.status` |
| `financial_api` | `/api/financial` | REST JSON endpoints used by financial front-end widgets |
| `timeentry` | `/apontamentos` | Manages `MeasurementCycle` and `TimeEntry`; validates project and cost-center status before recording hours |
| `scope` | `/scope` | Manages `WBSItem`, `Requirement`, `ScopeChange` linked to `Project` |
| `pmbok` | `/pmbok` | Reference guide sections; integrates PMBOK knowledge area labels from `task.py` constants |
| `admin` | `/admin` | Admin-only dashboard; delegates to `AdminService` |
| `admin_users` | `/admin/users` | User CRUD; calls `AdminService`; uses `USER_STATUS`, `USER_ROLES`, `COMPANIES`, `STATES` constants |
| `admin_permissions` | `/admin/permissions` | Grants/revokes `UserModulePermission` rows via `PermissionService` |
| `integration` | `/integration` | Handles file imports (`ImportLog`) and external data integration |
| `import_routes` | `/import` | Excel/XML import routes; uses `openpyxl` and `defusedxml` |
| `api` | `/api` | Internal REST API (e.g., `/api/projects`) consumed by AJAX calls in templates |

---

## Functionality Dependencies

| Functionality | Depends On |
|---------------|-----------|
| Login / Session | `User.is_active`, `werkzeug` password hashing, `flask-login` |
| Permission checks | `UserModulePermission`, `ModulePermission`, `PermissionService.can_perform_action()` |
| Template `user_can()` helper | `PermissionService` (injected via context processor in `app/__init__.py`) |
| Project creation | Authenticated `User`; valid `PROJECT_STATUS` / `PROJECT_PRIORITY` / `PROJECT_CATEGORIES` |
| Time-entry recording | Active `MeasurementCycle`; `Project.status != 'blocked'`; `CostCenter.status == 'active'` |
| Financial earned value | `FinancialBudget` and `FinancialTransaction` records for the same project |
| Admin operations | `User.role == 'admin'`; all admin blueprints guard routes with `@login_required` + role check |
| Email notifications | `Flask-Mail` configuration (SMTP or Outlook COM on Windows); `EmailService` |
| Database migrations | `Flask-Migrate` / Alembic; migration scripts in `migrations/versions/` |
| Module initialization | `init_default_modules()` in `app/utils/init_modules.py`; runs on first startup (skipped during tests) |

---

## Orphaned Features

| Feature | Location | Notes |
|---------|----------|-------|
| `FinancialReport` model | `app/models/financial_report.py` | Defined but not referenced by any active route or service |
| `FinancialScenario` model | `app/models/financial_scenario.py` | Defined but not wired to any route |
| Commented-out WBS import | `app/models/task.py` (line 4) | `from app.models.wbs import WBSItem` is commented out; `WBSItem` exists under `app/models/wbs_item.py` |

---

## Improvement Recommendations

1. **Resolve orphaned models** – Wire `FinancialReport` and `FinancialScenario` to routes or remove them to keep the schema lean.
2. **Consolidate route namespaces** – `financial_api` blueprint overlaps with the general `api` blueprint; consider merging under `/api/financial`.
3. **Add rate limiting** – The `/api/projects` endpoint and other public-facing API routes lack rate limiting; `Flask-Limiter` would protect against abuse.
4. **Centralise logging** – Individual services already use `logging.getLogger(__name__)`; a single `logging.basicConfig` call in the application factory (now added) ensures consistent formatting across all environments.
5. **Expand test coverage** – Financial module (`financial_budget`, `financial_transaction`, `financial_earned_value`) currently has no dedicated test files.
