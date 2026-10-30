# Implementation Plan: Autonomous FinOps Orchestrator

## Project Overview
This repository serves as a practical proof-of-work for the AI & Workflow Automation Specialist role. It demonstrates end-to-end automation engineering by ingesting unstructured financial documents (receipts, PDF statements, SPEI transfers), extracting data using AI, and routing structured payloads to enterprise databases and spreadsheets.

## Tech Stack
*   **Orchestration:** n8n (Dockerized)
*   **Database:** PostgreSQL
*   **Middleware:** Python (FastAPI/Flask) or Node.js (Express)
*   **AI/LLM:** OpenAI GPT-4o / Anthropic Claude (Vision & Text)
*   **Integrations:** Google Sheets API, Slack Webhooks
*   **Infrastructure:** Docker & Docker Compose

---

## Sprint 1: Infrastructure, Ingestion & AI Extraction

**Goal:** Establish the local environment, build custom middleware, and successfully parse raw financial documents using AI vision/LLM APIs.

*   **Day 1: Containerized Setup**
    *   Initialize the GitHub monorepo (`autonomous-finops-orchestrator`).
    *   Create directory structure: `/webhooks`, `/n8n-workflows`, `/scripts`, `/tests`.
    *   Configure `docker-compose.yml` to spin up local n8n and PostgreSQL instances.
*   **Day 2: Middleware API**
    *   Build a lightweight REST API webhook receiver (Python or Node.js).
    *   Configure endpoints to accept incoming file payloads (mock SPEI transfers, PDFs).
*   **Day 3: Workflow Triggering**
    *   Link the custom webhook API to the n8n instance.
    *   Create the initial n8n scenario: trigger on incoming HTTP POST, parse JSON payload.
*   **Day 4: Data Destinations**
    *   Configure n8n output nodes for PostgreSQL and Google Sheets.
    *   Map dummy JSON data to verify OAuth2 and DB credential connections.
*   **Day 5: AI Parsing Engine**
    *   Write a Python script utilizing the OpenAI/Anthropic API.
    *   Prompt the LLM to extract vendor, date, amount, and transaction ID from text.
*   **Day 6: Vision Integration**
    *   Upgrade the AI script to handle image processing.
    *   Pass sample SPEI screenshots and receipt images through the LLM vision endpoint to output structured JSON.
*   **Day 7: Orchestration Merge**
    *   Embed the AI extraction script into the n8n pipeline.
    *   Test the full linear flow: Webhook → AI Extraction → PostgreSQL + Google Sheets.

---

## Sprint 2: Complex Routing, Resilience & Load Testing

**Goal:** Transform the linear pipeline into an enterprise-grade, fault-tolerant system capable of handling high traffic, human-in-the-loop approvals, and unexpected errors.

*   **Day 8: Intelligent Routing**
    *   Build multi-branch logic in n8n.
    *   Set conditions: if extracted amount > $10,000 or AI confidence is low, route to Slack/Email for human review instead of DB insertion.
*   **Day 9: Exception Handling**
    *   Implement global error handling using n8n "Error Trigger" nodes.
    *   Catch API timeouts or malformed payloads, logging failures to a dedicated Slack channel.
*   **Day 10: Script Hardening**
    *   Refactor Python/Node middleware with `try/except` blocks.
    *   Implement strict JSON schema validation for the LLM outputs.
    *   Secure `.env` variable management for all API keys and DB credentials.
*   **Day 11: Load & Stress Testing**
    *   Configure Postman to simulate incoming traffic.
    *   Run a stress test of 100 simultaneous webhook triggers to ensure n8n and PostgreSQL handle the volume.
*   **Day 12: State Export**
    *   Export all n8n workflows as raw JSON files.
    *   Commit these schemas to the `/n8n-workflows` directory for verifiable proof-of-work.
*   **Day 13: Documentation**
    *   Write the comprehensive `README.md`.
    *   Document mapped data flows, process friction points solved, and API architectures.
    *   Include Mermaid.js diagrams for visual workflow representation.
*   **Day 14: Final Polish**
    *   Clean the codebase and add inline comments.
    *   Ensure the repository explicitly highlights concrete deliverables (measurable time savings, error tolerance) to bypass resume filters.

---

## Next Steps for Execution
1.  Clone this repository locally.
2.  Populate the `.env` file with necessary API keys (OpenAI/Anthropic, Slack, Google).
3.  Run `docker-compose up -d` to begin Day 1 tasks.