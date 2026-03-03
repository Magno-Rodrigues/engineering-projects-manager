# Engineering Projects Manager

A professional Flask application for managing engineering projects, tasks, and reports.

## ✅ Project Stability

> **Audit Status: STABLE** — The `main` branch has been audited and confirmed stable.
>
> All core modules (authentication, projects, tasks, reports, financial, API) are tested and functional.
> Database migrations are up to date. Dependencies are pinned and free of known vulnerabilities.
> The project is ready for local setup and development.

## 🚀 Features

- Project management (create, edit, delete, track status)
- Task management per project with priority levels
- Report generation per project
- User authentication (register, login, logout)
- RESTful JSON API endpoints
- Role-based access control

## 🏗️ Architecture

```
app/
├── __init__.py          # Application factory
├── models/              # SQLAlchemy database models
├── routes/              # Flask Blueprints
├── services/            # Business logic layer
├── static/              # CSS, JS, images
├── templates/           # Jinja2 HTML templates
└── utils/               # Decorators and helpers
```

## ⚙️ Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- pip

### Local Development

1. **Clone the repository and check out the main branch**
   ```bash
   git clone https://github.com/Magno-Rodrigues/engineering-projects-manager.git
   cd engineering-projects-manager

   # Fetch all remote branches and tags
   git fetch --all

   # Ensure you are on the stable main branch
   git checkout main
   git pull origin main
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

   The `.env.example` file is pre-configured for local development (`ENV=development`).
   Update `DATABASE_URL` to point to your local PostgreSQL instance, for example:
   ```
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/engineering_projects
   ```

5. **Create the PostgreSQL database**
   ```bash
   psql -U postgres -c "CREATE DATABASE engineering_projects;"
   ```

6. **Apply database migrations**
   ```bash
   flask db upgrade
   ```

   > **Note:** The `migrations/` folder already contains all migrations.
   > Run `flask db upgrade` (not `flask db init`) to apply them to your database.

7. **Run the application**
   ```bash
   flask run
   ```

   The application will be available at `http://localhost:5000`.

### Docker

Run the full stack with Docker Compose (no local PostgreSQL required):

```bash
docker-compose up --build
```

After the containers start, apply the migrations:

```bash
docker-compose exec web flask db upgrade
```

The application will be available at `http://localhost:5000`.

## 🧪 Running Tests

Tests use an in-memory SQLite database and require no external services:

```bash
pytest
```

With coverage report:

```bash
pytest --cov=app --cov-report=html
```

Run a specific test file:

```bash
pytest tests/test_auth.py -v
```

## 🖥️ VSCode Setup

Open the project folder in VSCode:

```bash
code .
```

Recommended extensions (install via the Extensions panel or `Ctrl+Shift+X`):

- **Python** (`ms-python.python`) — Python language support and IntelliSense
- **Pylance** (`ms-python.vscode-pylance`) — Fast type checking and auto-complete
- **Ruff** (`charliermarsh.ruff`) — Fast Python linter and formatter
- **GitLens** (`eamodio.gitlens`) — Enhanced Git integration

After installing the Python extension, select your virtual environment interpreter:

1. Press `Ctrl+Shift+P` → **Python: Select Interpreter**
2. Choose the interpreter inside your `venv/` directory (e.g. `./venv/bin/python`)

The `.vscode/settings.json` file already configures the recommended test runner and formatting options.

## 📦 Dependencies

| Package | Version | Purpose |
|---|---|---|
| Flask | 2.3.2 | Web framework |
| Flask-SQLAlchemy | 3.0.5 | ORM |
| Flask-Migrate | 4.0.5 | Database migrations |
| Flask-Login | 0.6.3 | Authentication |
| Flask-Mail | 0.10.0 | Email support |
| psycopg | 3.2.13 | PostgreSQL adapter |
| python-dotenv | 1.0.0 | Environment variables |
| pytest | 7.4.0 | Testing |
| Werkzeug | 2.3.7 | WSGI utilities |
| openpyxl | 3.1.0+ | Excel file import |
| defusedxml | 0.7.1+ | Safe XML parsing |

## 🌐 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/projects` | List user projects |
| GET | `/api/projects/<id>` | Get project details |

## 📝 Environment Variables

See `.env.example` for all available environment variables.

| Variable | Default | Description |
|---|---|---|
| `FLASK_APP` | `run.py` | Flask application entry point |
| `FLASK_ENV` | `development` | Flask environment |
| `ENV` | `development` | Application environment |
| `SECRET_KEY` | *(required)* | Flask secret key |
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/engineering_projects` | PostgreSQL connection URL |
| `MAIL_SERVER` | — | SMTP server (optional) |
| `MAIL_PORT` | `587` | SMTP port |
| `MAIL_USERNAME` | — | SMTP username |
| `MAIL_PASSWORD` | — | SMTP password |

## 🛠️ Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError` | Ensure the virtual environment is activated and run `pip install -r requirements.txt` |
| `could not connect to server` (PostgreSQL) | Check that PostgreSQL is running and `DATABASE_URL` in `.env` is correct |
| `flask: command not found` | Set `FLASK_APP=run.py` and ensure Flask is installed in the active venv |
| `flask db upgrade` fails with "Target database is not up to date" | Run `flask db stamp head` then `flask db upgrade` again |
| `SMTP / email errors` | Set `ENV=development` to disable email sending during local development |
| Tests fail with `ImportError` | Make sure you are running `pytest` from the project root directory |
| VSCode does not find the interpreter | Press `Ctrl+Shift+P` → **Python: Select Interpreter** and pick `./venv/bin/python` |

If you encounter an error not listed above, open an issue describing the error message and the steps you followed.
