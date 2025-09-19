# 🚀 Complete Server Startup Commands for MonoRepo

Here are the commands to run all the servers in the correct order:

## 📋 Prerequisites Check

First, make sure you're in the monorepo directory:

```bash
cd [location of monorepo]
```

## 🏗️ Architecture Diagram

```
+-------------------+      +--------------------------------+
|                   |      |                                |
|  User's Browser   |----->|  Frontend (Next.js) @ 3000     |
|                   |      |                                |
+-------------------+      +--------------------------------+
                             |                 |
                             |                 |
         +-------------------v-------------------+
         |                                       |
+--------v---------+                     +--------v---------+
|                  |                     |                  |
| Trading Agent    |                     | Original API     |
|   (@ 8001)       |                     |   (@ 8000)       |
|                  |                     |                  |
+------------------+                     +------------------+
         |                                       |
         |                                       |
         +-------------------v-------------------+
                             |
+----------------------------v-----------------------------+
|                                                          |
|                  Observability Stack                     |
| (Jaeger @16686, Prometheus @9090, Grafana @3000,          |
|  PostgreSQL @5432, Redis @6379)                          |
|                                                          |
+----------------------------------------------------------+
```

## 🔧 1. Start Observability Stack (Jaeger, Prometheus, Grafana)

```bash
# Start the observability infrastructure
npm run observability:start

# Or manually:
# For Windows
setup-observability.bat
# For macOS/Linux
./setup-observability.sh
```

This will start:

-   **Jaeger UI:** [http://localhost:16686](http://localhost:16686) (tracing)
-   **Prometheus:** [http://localhost:9090](http://localhost:9090) (metrics)
-   **Grafana:** [http://localhost:3000](http://localhost:3000) (dashboards)
-   **PostgreSQL:** `localhost:5432` (database)
-   **Redis:** `localhost:6379` (caching)

## 🎯 2. Start Trading Agent Server (MonoRepo)

```bash
# Start the trading agent (recommended)
npm run start:trading

# Or manually:
# For Windows
start-trading.bat
# For macOS/Linux
bash start-trading.sh

# Or directly:
# For Windows
cd apps/trading-agent && .\venv\Scripts\activate && python -m uvicorn app:app --host 0.0.0.0 --port 8001 --reload
# For macOS/Linux
cd apps/trading-agent && source venv/bin/activate && python -m uvicorn app:app --host 0.0.0.0 --port 8001 --reload
```

-   **Trading Agent:** [http://localhost:8001](http://localhost:8001) (MonoRepo main server)

## 🌐 3. Start Original API Server (Exercise 1-4)

```bash
# Start the original API server
npm run start:api

# Or manually:
cd apps/api && python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

-   **Original API:** [http://localhost:8000](http://localhost:8000) (Exercise 1-4 server)

## 💻 4. Start Frontend (App's UI)

```bash
# Start the Next.js frontend
npm run start:web

# Or manually:
cd apps/web && npm run dev
```

-   **Frontend:** [http://localhost:3000](http://localhost:3000) (Next.js UI)

## ⚡ Quick Start Commands

### Option 1: Start all servers at once

```bash
cd [location of monorepo]
npm run monorepo
```

### Option 2: Step by step

**Terminal 1: If Docker containers for observability are not running, start them with below command.**

```bash
cd [location of monorepo]
npm run observability:start
```

**Terminal 2: Start trading agent (wait 10 seconds after observability)**

```bash
cd [location of monorepo]
npm run start:trading
```

**Terminal 3: Start original API**

```bash
cd [location of monorepo]
npm run start:api
```

**Terminal 4: Start web UI**

```bash
cd [location of monorepo]
npm run start:web
```

## 🎮 Access Points

Once all servers are running, you can access:

| Service                 | URL                               | Purpose                         |
| ----------------------- | --------------------------------- | ------------------------------- |
| Trading Agent Chat UI   | [http://localhost:8001](http://localhost:8001) | MonoRepo main interface       |
| Trading Agent API       | [http://localhost:8001/docs](http://localhost:8001/docs) | FastAPI docs for MonoRepo     |
| Original API            | [http://localhost:8000/docs](http://localhost:8000/docs) | FastAPI docs for Exercise 1-4   |
| Jaeger Tracing          | [http://localhost:16686](http://localhost:16686) | View OpenTelemetry traces       |
| Prometheus Metrics      | [http://localhost:9090](http://localhost:9090) | View metrics                    |
| Grafana Dashboards      | [http://localhost:3000](http://localhost:3000) | View dashboards (admin/admin)   |

## 🔍 Health Checks

Verify servers are running:

```bash
# Check trading agent
curl http://localhost:8001/health

# Check original API
curl http://localhost:8000/health

# Check observability stack
docker-compose ps
```

## 🛑 Stop Servers

To stop all services:

```bash
# Stop observability stack
npm run observability:stop

# Stop individual servers with Ctrl+C in their terminals
```

## 📊 Demo Commands

Run demonstrations:

```bash
# Demo all MonoRepo features
npm run demo:trading

# Demo MonoRepo with observability
npm run monorepo:demo
```

## 🎯 Recommended startup order:

1.  Observability stack (wait ~10 seconds)
2.  Trading agent server
3.  Access [http://localhost:8001](http://localhost:8001) for the chat UI
4.  Access [http://localhost:16686](http://localhost:16686) for Jaeger traces

This gives you the complete MonoRepo trading agent with full observability! 🚀