[Mariusz Godlewski] Added git lfs to repository
[Mariusz Godlewski] Added parsing xlsx lokaty to csv
[Mariusz Godlewski] Added pre-commit hooks to repository
[Mariusz Godlewski] Added .gitignore for Python and editor artifacts
[Mariusz Godlewski] Added docker-compose with PostgreSQL 17 database
[Mariusz Godlewski] Added DB schema: tables (bank, product, offer_variant), enum types (product_type, rate_type, term_unit, capitalization), and indexes for active offers, interest rate, term days, and FK joins
[Mariusz Godlewski] Added script that preprocess the data to the db format
[Mariusz Godlewski] Added alembic for DB migrations and converted initial schema to alembic migration
[Mariusz Godlewski] Added load data script to populate db with processed lokaty warianty (raises errors on conflict)
[Mariusz Godlewski] Added script to clear/reset the database
[Mariusz Godlewski] Added hadolint pre-commit hook to lint Dockerfiles
[Mariusz Godlewski] Added GitHub Actions CI pipeline and changelog format check
[Mariusz Godlewski] Added docker-compose-extended.yml as an extension to include Adminer (database UI)
[Mariusz Godlewski] Added parametrized pytest tests for preprocess_lokaty script
[Mariusz Godlewski] Added pytest test execution to GitHub Actions CI pipeline
[Mariusz Godlewski] Containerized FastAPI application and enabled BuildKit optimizations
[Mariusz Godlewski] Added database auto-initialization (reset, convert, preprocess, load) to docker-compose-extended.yml
