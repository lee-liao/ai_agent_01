# Monorepo Codebase Overview

This is a comprehensive monorepo designed for the AI Agent Training Class, showcasing a range of concepts from basic tool creation to a full-fledged, observable, and reliable AI trading agent.

Here is an overview of the codebase:

### High-Level Architecture

The project is structured as a monorepo containing multiple applications (`apps`) and shared libraries (`packages`).

*   **`apps`**: Contains three main applications:
    1.  `api`: A foundational FastAPI backend providing several secure and reliable tools (HTTP, DB, File Ops).
    2.  `web`: A Next.js frontend that serves as a dashboard/console for the `api` backend.
    3.  `trading-agent`: A more advanced, standalone FastAPI application that simulates an AI-powered stock trading agent, demonstrating all the skills from the course exercises.
*   **`packages`**: Contains shared Python code.
    *   `agent`: A library with shared logic for schema validation, tool routing, and retry mechanisms.
*   **`observability`**: Contains the configuration for a Docker-based observability stack, including Jaeger (for tracing), Prometheus (for metrics), and Grafana (for dashboards).

Here is a diagram illustrating the main components:

```
+-----------------------------------------------------------------+
|                            monorepo                             |
+-----------------------------------------------------------------+
|                                                                 |
|  +------------------+      +------------------+     +------------------------+
|  |     apps/api     |      |     apps/web     |     |   apps/trading-agent   |
|  | (FastAPI Backend)|      | (Next.js Frontend)|     |  (Advanced AI Agent)   |
|  +------------------+      +------------------+     +------------------------+
|          ^                        | (connects to)             |
|          | (uses)                 |                           | (self-contained)
|          v                        v                           |
|  +------------------+      +------------------+               |
|  | packages/agent   |<---->|     apps/api     |               |
|  |  (Shared Logic)  |      +------------------+               |
|  +------------------+                                         |
|                                                                 |
|  +----------------------------------------------------------+ |
|  |                      Observability Stack (Docker)          | |
|  |  [ Jaeger | Prometheus | Grafana | PostgreSQL | Redis ]   | |
|  +----------------------------------------------------------+ |
|                                                                 |
+-----------------------------------------------------------------+
```

---

### Application Details

#### 1. `apps/api` (Core API)

This is the foundational backend service.
*   **Purpose**: Provides a set of robust, secure, and observable tools that an AI agent can use.
*   **Key Files**:
    *   `app.py`: The main FastAPI application that exposes the tool endpoints.
    *   `tools/`: Contains the implementation for the core tools:
        *   `http_fetch.py`: A safe HTTP client with retries, timeouts, and rate limiting.
        *   `db_query.py`: A secure database tool that uses a SQL whitelist to prevent modification queries.
        *   `file_ops.py`: A tool for file system operations that are sandboxed to a specific workspace directory to prevent path traversal attacks.
    *   `observability/otel.py`: Sets up OpenTelemetry for tracing and metrics.

#### 2. `apps/web` (Frontend Console)

This is a Next.js web application that acts as a UI for the `api`.
*   **Purpose**: Provides a dashboard to monitor the tool executions of the `api` backend.
*   **Key Files**:
    *   `src/app/page.tsx`: The main page of the dashboard, showing mock data for tool logs, system stats, and configuration. It's a placeholder for a more advanced agent console.
    *   `src/components/ui/`: Contains reusable UI components (Cards, Badges, Buttons).

#### 3. `apps/trading-agent` (Advanced Trading Agent)

This is the most complex application, designed to showcase all the skills learned in the course in a single, cohesive system.
*   **Purpose**: A complete AI-powered stock trading agent with a web-based chat UI. It can analyze market data, manage a portfolio, and execute trades based on AI recommendations.
*   **Key Files**:
    *   `app.py`: The FastAPI application for the trading agent, which includes a chat UI.
    *   `tools/`: Contains all the tools required for trading, such as `stock_tools.py` (getting quotes, executing trades) and `reporting.py`.
    *   `agents/llm_agent.py`: The core AI logic that uses an LLM (like GPT) to analyze data and make trading recommendations.
    *   `tools/registry.py`: A central registry for managing all the tools, their permissions, and metadata (demonstrates Exercise 2).
    *   `tools/reliability.py`: A layer that adds retry logic, timeouts, and circuit breakers to tool calls (demonstrates Exercise 3).
    *   `database/init.sql`: The PostgreSQL database schema for storing portfolios, transactions, and reports.

The architecture of the trading agent itself is a great summary of the course concepts:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │────│  Tool Registry  │────│   Trading Tools │
│  (Exercise 6)   │    │  (Exercise 2)   │    │  (Exercise 1)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐             │
         │              │  Reliability    │             │
         └──────────────│  (Exercise 3)   │─────────────┘
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │ Observability   │
                        │ (Exercise 4)    │
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │  Permissions    │
                        │ (Exercise 5)    │
                        └─────────────────┘
```

---

### Observability Stack

The `docker-compose.yml` file defines a complete, pre-configured observability stack that works with both the `api` and `trading-agent` applications.

*   **Purpose**: To provide deep insights into the applications' behavior, performance, and errors.
*   **Services**:
    *   **Jaeger**: For distributed tracing. It allows you to visualize the entire lifecycle of a request as it flows through different tools and functions.
    *   **Prometheus**: For collecting and storing metrics (e.g., tool execution counts, error rates, response times).
    *   **Grafana**: For creating dashboards to visualize the metrics collected by Prometheus.
    *   **PostgreSQL**: A database for the `trading-agent`.
    *   **OTEL Collector**: A component that receives telemetry data from the applications and exports it to Jaeger and Prometheus.

Here is a diagram of the data flow:

```
+---------------------+      +-------------------------+      +-----------------+
|     Application     |----->| OpenTelemetry Collector |----->|     Jaeger      |
| (api/trading-agent) |      |    (otel-collector)     |      | (Trace Backend) |
+---------------------+      +-------------------------+      +-----------------+
                                        |                      |
                                        | (Metrics)            | (Traces)
                                        v                      v
+-------------------+      +--------------------------+      +-----------------+
|    Prometheus     |<-----|                          |----->|     Grafana     |
| (Metrics Backend) |      +--------------------------+      |  (Dashboards)   |
+-------------------+                                      +-----------------+
```

In summary, this monorepo is a rich, well-structured project that provides both a foundational set of tools and an advanced, real-world example of an AI agent, complete with a professional-grade observability setup.
