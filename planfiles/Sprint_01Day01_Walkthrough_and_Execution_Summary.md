# Sprint 01 — Day 01 Walkthrough and Execution Summary

## Day 01 goal

Establish the local development foundation for the Autonomous FinOps Orchestrator:

- Create the project directories for webhooks, n8n workflows, scripts, and tests.
- Configure Docker Compose to run n8n and PostgreSQL locally.
- Keep local credentials out of source control.

## What was implemented

### Project scaffold

The repository now has the planned working directories:

- `webhooks/` — API and webhook implementation.
- `n8n-workflows/` — exported workflow definitions.
- `scripts/` — utility and automation scripts.
- `tests/` — automated tests.

Each directory contains a `.gitkeep` so that the empty directory is retained by Git.

### Local configuration

- `.env.example` documents the variables used to configure the services.
- `.gitignore` excludes `.env` and common Python virtual-environment, bytecode, and test artifacts.
- A local `.env` was created with generated credentials. It is intentionally not tracked, and its values are not included in this document.

Before sharing the project or deploying it, replace example values with unique, securely generated credentials. Do not commit `.env` or paste its contents into logs, tickets, or documentation.

### Docker Compose

`docker-compose.yml` configures:

- **PostgreSQL** with a persistent named volume, a readiness health check, and a database/user configured through environment variables.
- **n8n** configured to use PostgreSQL, dependent on the database health check, and backed by a persistent named volume.
- **Middleware API** on port `8000`, added as the API work began after the initial Day 01 scaffold.

The n8n and PostgreSQL ports are bound to loopback (`127.0.0.1`) for local access rather than being exposed on all network interfaces. n8n is available at `http://localhost:5678` and PostgreSQL at `localhost:5432` when the Docker services are running.

## Walkthrough

1. Install and start Docker Desktop with its Linux container engine enabled.
2. Copy `.env.example` to `.env` if no local `.env` exists.
3. Set unique values for the database password and n8n encryption key. The current setup also requires a webhook bearer token. Set `OPENAI_API_KEY` to enable document extraction.
4. Validate the Compose configuration:

   ```powershell
   docker compose config --quiet
   ```

5. Start the stack:

   ```powershell
   docker compose up -d
   ```

6. Check service status:

   ```powershell
   docker compose ps
   ```

7. Open n8n at `http://localhost:5678`. Stop the services without deleting persistent data with:

   ```powershell
   docker compose down
   ```

Avoid `docker compose down -v` unless you intend to delete the n8n and PostgreSQL volumes and all data stored in them.

## Execution results

| Check | Result |
|---|---|
| Docker CLI detected | Passed — Docker version `29.1.3` |
| Docker Compose detected | Passed — Compose version `v2.40.3` |
| Compose configuration validation | Passed — `docker compose config --quiet` |
| Required scaffold and local `.env` present | Passed |
| Container startup | Blocked — Docker Desktop's Linux engine was unavailable |

`docker compose up -d` could not connect to `//./pipe/dockerDesktopLinuxEngine`. The configuration is valid, but the containers have **not** been started or runtime-verified. Start Docker Desktop's Linux engine and rerun the startup and status commands above.

## Outcome and next step

The Day 01 scaffold and Compose configuration are in place, and the static Compose validation passed. Runtime verification remains pending until Docker Desktop's Linux engine is available. Once the stack starts, proceed with Day 02 by exercising the FastAPI webhook receiver against the local environment.
