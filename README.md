# Engineering Projects Manager

A professional Flask application for managing engineering projects, tasks, and reports.

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

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd engineering-projects-manager
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
