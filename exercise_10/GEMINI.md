# GEMINI.md - AI Call Center Assistant

## Project Overview

This project is a real-time AI call center assistant. It's designed to listen to live customer conversations and provide streaming, contextual suggestions to human agents.

The system is composed of three main parts:

*   **Frontend:** A Next.js application that serves as the user interface for the call center agent. It displays the live audio waveform, transcription, and AI suggestions.
*   **Backend:** A FastAPI application that handles the core logic. It manages the WebRTC audio streaming, performs speech-to-text transcription using OpenAI's Whisper API, generates AI suggestions using a large language model, and interacts with the database.
*   **Customer Simulator:** A simple HTML/JavaScript application to simulate customer calls for testing purposes.

The project uses a PostgreSQL database to store customer information, call history, and other relevant data. Redis is used for session state management.

## Building and Running

The project is containerized using Docker and can be run with a single command:

```bash
docker-compose up -d
```

This will start all the necessary services: the frontend, the backend, the PostgreSQL database, and Redis.

The services will be available at the following URLs:

*   **Frontend:** [http://localhost:3000](http://localhost:3000)
*   **Backend:** [http://localhost:8000](http://localhost:8000)
*   **Customer Simulator:** Open the `customer-sim/index.html` file in your browser.

### Development

To run the services in development mode with hot-reloading, you can use the following commands:

**Backend:**

```bash
# From the backend directory
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**

```bash
# From the frontend directory
npm run dev
```

## Development Conventions

*   **Backend:** The backend is written in Python using the FastAPI framework. It follows a standard project structure with a clear separation of concerns.
    *   **API:** The API endpoints are defined in the `app/api` directory.
    *   **Database:** The database models and session management are handled in `app/models.py` and `app/database.py`.
    *   **Configuration:** The application settings are managed in `app/config.py` and loaded from a `.env` file.
*   **Frontend:** The frontend is a Next.js application written in TypeScript.
    *   **Components:** Reusable React components are located in the `src/components` directory.
    *   **API Client:** The `src/lib/callApi.ts` file is used to make requests to the backend API.
    *   **Styling:** Tailwind CSS is used for styling.
*   **Testing:** The `README.md` mentions a `STUDENT_TASKS.md` file with a set of tasks for students to complete, which can be used as a guide for testing the application's functionality.
