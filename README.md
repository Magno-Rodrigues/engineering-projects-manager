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

5. **Initialize the database**
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. **Run the application**
   ```bash
   flask run
   ```

   The application will be available at `http://localhost:5000`.

### Docker

Run the full stack with Docker Compose:

```bash
docker-compose up --build
```

## 🧪 Running Tests

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
| Flask | 2.3.0 | Web framework |
| Flask-SQLAlchemy | 3.0.5 | ORM |
| Flask-Migrate | 4.0.5 | Database migrations |
| Flask-Login | 0.6.3 | Authentication |
| psycopg2-binary | 2.9.9 | PostgreSQL adapter |
| python-dotenv | 1.0.0 | Environment variables |
| pytest | 7.4.0 | Testing |
| Werkzeug | 2.3.7 | WSGI utilities |

## 🌐 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/projects` | List user projects |
| GET | `/api/projects/<id>` | Get project details |

## 📝 Environment Variables

See `.env.example` for all available environment variables.
