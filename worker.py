import psycopg2
import select
import json
from tasks import grade_with_gemini, send_to_moodle
from dotenv import load_dotenv
import os

load_dotenv()
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

conn = psycopg2.connect(DATABASE_URL)
conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()
cur.execute("LISTEN new_grading_job;")
print("Worker listening for new grading jobs...")

def process_job(job_id):
    """
    Safely process a grading job from the database.
    """
    with engine.begin() as db_conn:
        job = db_conn.execute(
            text("SELECT * FROM grading_jobs WHERE id=:id"),
            {"id": job_id}
        ).fetchone()

        if not job or job.status != "queued":
            return

        db_conn.execute(
            text("UPDATE grading_jobs SET status='in_progress', updated_at=NOW() WHERE id=:id"),
            {"id": job_id}
        )

        try:
            import requests
            resp = requests.get(job.github_link)
            resp.raise_for_status()
            student_code = resp.text

            rubric = job.rubric
            if isinstance(rubric, str):
                rubric = json.loads(rubric)

            result = grade_with_gemini(student_code, job.question, rubric)

            evaluation_details = result.get("evaluation_details", [])
            moodle_result = send_to_moodle(job, evaluation_details)

            db_conn.execute(
                text("UPDATE grading_jobs SET status='done', result=:result, updated_at=NOW() WHERE id=:id"),
                {"id": job_id, "result": json.dumps({"gemini": result, "moodle": moodle_result})}
            )

        except Exception as e:
            db_conn.execute(
                text("UPDATE grading_jobs SET status='failed', result=:result, updated_at=NOW() WHERE id=:id"),
                {"id": job_id, "result": json.dumps({"error": str(e)})}
            )

while True:
    if select.select([conn], [], [], 5) == ([], [], []):
        continue
    conn.poll()
    while conn.notifies:
        notify = conn.notifies.pop(0)
        job_id = int(notify.payload)
        print(f"New job received: {job_id}")
        process_job(job_id)
# ... (existing imports and setup)

# # Define a simple retry logic
# RETRY_DELAY_SECONDS = 300 # Retry failed jobs older than 5 minutes

# while True:
#     # 1. Listen for new jobs (immediate priority)
#     if select.select([conn], [], [], 5) == ([], [], []):
#         pass # No new notification, proceed to sweep
#     else:
#         conn.poll()
#         while conn.notifies:
#             notify = conn.notifies.pop(0)
#             job_id = int(notify.payload)
#             print(f"New job received from NOTIFY: {job_id}")
#             process_job(job_id)
            
#     # 2. Add a periodic sweep for old/failed jobs (The Scheduler part)
#     # This prevents the worker from blocking indefinitely on select.select if no NOTIFYs come.
#     print("Sweeping for old or failed jobs...")
    
#     with engine.begin() as db_conn:
#         # Find jobs that failed a while ago, or are stuck in 'queued' without a NOTIFY
#         # You'll need an 'updated_at' column in your 'grading_jobs' table for this.
#         sweep_query = text("""
#             SELECT id FROM grading_jobs
#             WHERE (status = 'failed' AND updated_at < NOW() - INTERVAL '5 minutes')
#                OR (status = 'queued' AND updated_at < NOW() - INTERVAL '30 seconds')
#             ORDER BY updated_at ASC
#             LIMIT 10;
#         """)
        
#         jobs_to_retry = db_conn.execute(sweep_query).fetchall()

#     for job in jobs_to_retry:
#         job_id = job[0]
#         print(f"Retrying/Sweeping job: {job_id}")
#         process_job(job_id)
        
#     # 3. Add a short pause to prevent thrashing the DB during the sweep
#     import time
#     time.sleep(10)