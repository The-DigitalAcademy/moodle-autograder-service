# Flask Postgres-Based AI Autograder (No Redis)

This project implements a simple AI-powered autograder using Flask and PostgreSQL.
Jobs are queued in Postgres (no Redis) and the worker processes them, calling Gemini
to grade code and posting results to Moodle.

## Quick start

1. Copy `.env.example` to `.env` and fill in values.
2. Install deps: `pip install -r requirements.txt`
3. Initialize DB using `init_db.sql`
4. Run Flask API: `python app.py`
5. Run worker: `python worker.py`

