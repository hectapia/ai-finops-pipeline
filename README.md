# Autonomous FinOps Orchestrator

Local development scaffold for the FinOps document-ingestion and workflow-automation project.

## Prerequisites

- Docker Desktop with Docker Compose v2

## Start the local infrastructure

1. Copy `.env.example` to `.env`.
2. Replace `POSTGRES_PASSWORD`, `WEBHOOK_TOKEN`, and `N8N_ENCRYPTION_KEY` with unique random values. Set `OPENAI_API_KEY` to enable extraction. Keep `.env` private; it is ignored by Git.
3. Start the services:

   ```powershell
   docker compose up -d
   ```

4. Open n8n at <http://localhost:5678>. PostgreSQL is available on `localhost:5432` for local development tools.

PostgreSQL and n8n persist data in named Docker volumes. To stop the services without deleting data, run `docker compose down`. Do not use `docker compose down -v` unless you intend to permanently delete the database and n8n data.

The scaffold directories are `webhooks`, `n8n-workflows`, `scripts`, and `tests`.

## Middleware API

The FastAPI middleware is available on <http://localhost:8000> when Compose is running. Submit a PDF, JPEG, PNG, or WebP document to `POST /webhooks/financial-document` as multipart form field `file`, with `Authorization: Bearer <WEBHOOK_TOKEN>`. Uploads are limited to 10 MiB by default; `MAX_UPLOAD_BYTES` can adjust the limit.

The endpoint extracts vendor, date, amount, currency, transaction ID, and confidence. Missing dates and IDs are returned as `null`; amount is serialized as a decimal string to preserve monetary precision. The endpoint returns `503` if `OPENAI_API_KEY` is not configured and `502` if the provider fails or returns invalid data.

Run the API tests with:

```powershell
python -m pytest
```
