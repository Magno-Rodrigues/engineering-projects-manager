# Case Study: Engineering Projects Manager

## Context

This project was developed in 20 days with the goal of building a robust engineering project management system.

The development followed a **"vibe coding" approach**, where AI was used to accelerate implementation while all critical engineering decisions were manually validated and refined.

---

## What is Vibe Coding (in this project)

* AI-assisted code generation
* Manual validation of logic and domain rules
* Identification of inconsistencies
* Structural refactoring
* Incremental evolution with testing

---

## Key Technical Challenges

### 1. Migration Inconsistency

**Problem:**

* Multiple migrations for the same table (`financial_scenarios`)
* Broken Alembic revision chain
* Errors like:

  * "Can't locate revision"
  * "Could not determine revision id"

**Solution:**

* Recreated missing migration files
* Restored revision identifiers
* Normalized migration history
* Ensured database and code synchronization

---

### 2. Service Layer Coupling

**Problem:**

* Services directly manipulating `db.session`
* Tight coupling between business logic and persistence

**Solution:**

* Refactored service responsibilities
* Prepared structure for Repository Pattern
* Improved testability and separation of concerns

---

### 3. Redundant Financial Migrations

**Problem:**

* Multiple versions of financial schema changes
* Risk of inconsistent database state

**Solution:**

* Consolidated migration logic
* Standardized schema evolution

---

## Architecture

The system follows a layered architecture:

* **Models:** ORM-based persistence layer
* **Services:** Business rules and orchestration
* **Routes:** HTTP layer

Additionally:

* RBAC system for permissions
* Modular financial domain
* Import subsystem for external tools

---

## Domain Complexity

The application includes advanced modules:

* Earned Value Management (EVM)
* Financial scenarios and simulations
* Project structuring (WBS, PEP)
* Stakeholder and supplier management

---

## Testing Strategy

* Unit tests for services
* Integration tests for endpoints
* Coverage for critical modules:

  * Financial
  * Import
  * Permissions

---

## Results

* Fully functional system
* Stable database migrations
* Multi-user environment
* Deploy-ready architecture

---

## Lessons Learned

* AI accelerates development but requires strict validation
* Migration management is critical in real-world systems
* Separation of concerns improves long-term scalability
* Refactoring is essential when using generated code

---

## Future Roadmap

* Repository Pattern
* Domain isolation (Clean Architecture)
* Multi-tenant support
* Performance optimization
* Observability and monitoring
