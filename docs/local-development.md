# Développement local / Vận hành local

Docker Desktop Linux containers and Compose are required. Administration has no OpenAI dependency; no key is needed for Phase 1. Files and database persist locally; future generation sends selected context and embeddings send chunks/queries to the configured external provider.

Copy `.env.example` to `.env`, replace `POSTGRES_PASSWORD` with a strong URL-safe password, retain `APP_ORIGIN=http://localhost:3000`. Never commit `.env`. Run `docker compose up --build -d frontend`, then `docker compose exec backend python -m scripts.bootstrap_admin`. The bootstrap prompts for username/password without echo; repeat never overwrites an Admin. Visit http://localhost:3000/login. Only the frontend publishes `127.0.0.1:3000`; API and PostgreSQL are internal. This deployment is for localhost only.

Startup order: postgres healthy → migrate successfully applies Alembic → backend readiness checks actual head → frontend. Database uses named volume `postgres-data`, uploads `data/uploads`, storage `storage`; source directories are never public static routes. Do not delete volumes to troubleshoot ordinary startup failures.

## Automated isolated checks

From the repository root, unattended commands:

```
docker compose run --rm frontend-test npm run test:e2e -- phase1.spec.ts --grep tracer
docker compose run --rm backend-test python -m pytest -q
docker compose run --rm frontend npm run typecheck
docker compose run --rm frontend npm run build
docker compose run --rm frontend npm run lint
```

First build test images with `docker compose build backend-test next-test frontend-test`. No profiles are required. Health dependencies start postgres-test/rag_test → migrate-test → api-test → next-test → frontend-test. Backend tests and browser setup use the same migrated rag_test database and separate `postgres-test-data` volume, with no host ports and no operational network access. Next test target is selected during image build (`API_TARGET=http://api-test:8000`), not a runtime public variable. Test settings reject operational database hosts, fixtures reset only rag_test, and the production API has no test fixture routes. Test services cannot access operational PostgreSQL and have no outbound AI network path. Run suites sequentially because fixtures share rag_test.

Tests never clear operational/demo data. Browser proof asserts its session digest and dataset through api-test; backend-test can query the same database. Operational database checks must show no `Browser WMS` row. Python requirements are fully hash locked for Python 3.12, npm uses package-lock, and base images include exact digests. `pip check`, typecheck, lint and production build validate compatibility rather than assuming registry metadata proves it.

Authentication uses Argon2, opaque SHA-256-digested sessions, HttpOnly host-only Strict cookies. HTTP loopback alone permits Secure=false. Login requires exact Origin/Host, JSON and custom header; authenticated mutations additionally require synchronizer CSRF. No tokens in localStorage. Username is normalized immutable ASCII; passwords contain 15–128 Unicode characters without trimming.

Sessions reject at 30 minutes idle or 8 hours absolute, including equality. GET polling is passive. Visible navigation, key and pointer actions send a CSRF-protected activity request at most once per minute; no heartbeat timer renews idle. Logout and activity serialize through row locks; conditional activity also rejects a snapshot read before another transaction committed revocation. An already-authorized response cannot be recalled. Next rewrites change Host to the exact internal backend destination; the API accepts only that destination or the configured browser Host, alongside the exact browser Origin, and does not trust arbitrary forwarded headers.
