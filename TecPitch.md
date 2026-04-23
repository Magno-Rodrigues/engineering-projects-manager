I built a full engineering project management system in about 20 days using an AI-assisted approach.

The idea was not just to generate code, but to use AI as an accelerator while I focused on validating logic, correcting issues, and improving the architecture.

The system includes financial management, EVM analysis, project structuring, reporting, and a multi-user permission system.

From a technical perspective, I structured the application using a layered architecture with models, services, and routes. I also implemented a modular financial domain and an RBAC system for access control.

One of the biggest challenges was dealing with inconsistent database migrations. The AI-generated code created multiple conflicting revisions, so I had to manually fix the Alembic history, recreate missing migrations, and ensure the database state was consistent.

I also identified tight coupling between services and the database session, and started refactoring toward a cleaner architecture to improve testability and maintainability.

The project includes a full test suite with unit and integration tests, and it's running both locally and in a deployed environment.

Overall, this project demonstrates not just development speed, but the ability to critically evaluate, correct, and evolve AI-generated code into a production-ready system.
