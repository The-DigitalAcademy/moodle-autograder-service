import psycopg2
import select
import json
import os
import requests
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from tasks import grade_with_gemini, send_to_moodle
import logging

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

def process_job(job_id):
    """Process a grading job safely."""
    with engine.begin() as db_conn:
        job = db_conn.execute(
            text("SELECT * FROM grading_jobs WHERE id=:id"),
            {"id": job_id}
        ).fetchone()

        if not job or job.status != "queued":
            return

        logging.info(f"Processing job {job_id} for user {job.userid}")
        db_conn.execute(
            text("UPDATE grading_jobs SET status='in_progress', updated_at=NOW() WHERE id=:id"),
            {"id": job_id}
        )

        try:
            resp = requests.get(job.github_link.strip())
            resp.raise_for_status()
            student_code = resp.text

            rubric = job.rubric
            if isinstance(rubric, str):
                rubric = json.loads(rubric)

            result = grade_with_gemini(student_code, job.question, rubric)
            evaluation_details = result.get("evaluation_details", [])
            moodle_result = send_to_moodle(job, evaluation_details)

            db_conn.execute(
                text("""
                    UPDATE grading_jobs
                    SET status='done', result=:result, updated_at=NOW()
                    WHERE id=:id
                """),
                {"id": job_id, "result": json.dumps({"gemini": result, "moodle": moodle_result})}
            )
            logging.info(f"✅ Job {job_id} completed successfully")

        except Exception as e:
            logging.exception(f"❌ Job {job_id} failed: {e}")
            db_conn.execute(
                text("""
                    UPDATE grading_jobs
                    SET status='failed', result=:result, updated_at=NOW()
                    WHERE id=:id
                """),
                {"id": job_id, "result": json.dumps({"error": str(e)})}
            )


def listen_for_jobs():
    """Listen for PostgreSQL notifications and process jobs."""
    conn = psycopg2.connect(DATABASE_URL)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute("LISTEN new_grading_job;")

    logging.info("Worker listening for new grading jobs...")

    while True:
        if select.select([conn], [], [], 5) == ([], [], []):
            continue
        conn.poll()
        while conn.notifies:
            notify = conn.notifies.pop(0)
            job_id = int(notify.payload)
            logging.info(f"🆕 New job received: {job_id}")
            process_job(job_id)
