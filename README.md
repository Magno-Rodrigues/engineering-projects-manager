# 🚀 Engineering Projects Manager

Engineering Project Management Platform

https://engineering-projects-manager-1.onrender.com/login

- User : User Testing
- Password: cmrda123

Developed a full-stack platform focused on engineering project management, financial control, and performance analysis, integrating centralized workflows for operational monitoring and decision-making.

Built features for project planning, budget tracking, KPI analysis, and process automation, improving visibility, organization, and management efficiency across engineering operations.

Leveraged AI-assisted development methodologies (vibe coding) to accelerate implementation, optimize productivity, and streamline the delivery of technical solutions throughout the development lifecycle.

---

## ⚡ TL;DR

* 🧠 Built with **AI-assisted workflow + manual engineering validation**
* 🏗️ Complex domain: **projects, finance, EVM, imports**
* 🔐 Multi-user system with **RBAC permissions**
* 📊 Advanced features: **financial scenarios, cost tracking, reporting**
* 🧪 Tested (unit + integration)
* 🌐 Running locally and deployed

---

## 🎯 Why this project matters

This is not a CRUD app.

It simulates a **real-world engineering management system**, including:

* Financial planning and tracking
* Earned Value Management (EVM)
* Scenario simulation for decision-making
* Integration with external tools (MS Project / Primavera)

---

## 🧠 Development Approach: Vibe Coding

This project was built using an AI-assisted workflow:

```text
AI generates → I validate → I fix → I refactor → I evolve
```

✔ AI accelerated development
✔ Human decisions ensured correctness and architecture

> Result: fast delivery without sacrificing engineering quality

---

## 🏗️ Architecture

Layered architecture:

```
Models (SQLAlchemy)
   ↓
Services (Business Logic)
   ↓
Routes (HTTP Layer)
```

### Key Design Decisions

* Separation of concerns (services vs routes)
* Modular financial domain
* RBAC (Role-Based Access Control)
* Migration control with Alembic

---

## 🔥 Core Features

### 📊 Project Management

* Full lifecycle tracking
* Task and timeline control
* Stakeholder management

### 💰 Financial System

* Budgets and transactions
* Cost centers
* Financial reports

### 📈 EVM (Earned Value Management)

* Performance indicators
* Cost & schedule analysis

### 🔄 Scenario Simulation

* Budget variance
* Schedule forecasting
* Decision support

### 📥 Data Import

* MS Project integration
* Primavera integration

### 🔐 Access Control

* User-based permissions
* Module-level authorization

---

## 🧪 Testing

* Unit tests for services
* Integration tests for routes
* Coverage for critical modules:

  * Financial
  * Import
  * Permissions

---

## ⚠️ Real Challenges Solved

### Migration Chaos (Alembic)

* Broken revision chains
* Duplicate migrations
* Missing revision files

✔ Fixed by:

* Recreating migrations
* Normalizing revision history
* Synchronizing DB state

---

### Code Quality Issues (AI-generated)

* Tight coupling in services
* Redundant logic

✔ Fixed by:

* Refactoring services
* Improving separation of concerns
* Preparing for scalable architecture

---

## 🚀 Future Improvements

* Repository Pattern
* Multi-tenant architecture (SaaS-ready)
* Redis caching
* Background jobs (Celery/RQ)
* Public API (REST/GraphQL)

---

## 🛠️ Tech Stack

* **Backend:** Flask
* **ORM:** SQLAlchemy
* **Database:** PostgreSQL
* **Migrations:** Alembic / Flask-Migrate
* **Frontend:** Jinja2 + JavaScript
* **Tests:** Pytest

---

## 📊 What this project demonstrates

* Ability to handle **complex domain logic**
* Strong understanding of **backend architecture**
* Experience with **AI-assisted development workflows**
* Capability to **debug, refactor, and stabilize systems**

---

## 👨‍💻 Author

**Magno Rodrigues**
Backend Developer | Python | Data | Systems Architecture

---

## ⭐ Final Note

This project demonstrates that AI can accelerate development —
but **engineering thinking is what makes it reliable.**
