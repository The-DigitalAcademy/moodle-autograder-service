from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import json, os, threading, logging
from worker import listen_for_jobs
import re

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

@app.route("/grade", methods=["POST"])
def grade_code():
    data = request.json
    userid = data.get("userid")
    assignmentid = data.get("assignmentid")
    assignmentname = data.get("assignmentname")
    rubric = data.get("assignmentrubric")

    def strip_html(text):
        if text:
            return re.sub('<[^<]+?>', '', text)
        return ""

    github_link = strip_html(data.get("onlinetext"))
    assignmentintro = strip_html(data.get("assignmentintro"))
    question = strip_html(data.get("assignmentactivity"))



    if not github_link or not userid or not question:
            return jsonify({"error": "Missing fields"}), 400

    with engine.begin() as conn:
        result = conn.execute(
            text("""
                INSERT INTO grading_jobs (userid, github_link, question, rubric, assignmentid, assignmentname, assignmentintro)
                VALUES (:userid, :github_link, :question, :rubric, :assignmentid, :assignmentname, :assignmentintro)
                RETURNING id
            """),
            {
                "userid": userid,
                "github_link": github_link,
                "question": question,
                "rubric": json.dumps(rubric),
                "assignmentid": assignmentid,
                "assignmentname": assignmentname,
                "assignmentintro": assignmentintro
            }
        )
        job_id = result.fetchone()[0]

    logging.info(f"📩 Job {job_id} queued by user {userid}")
    return jsonify({"status": "queued", "job_id": job_id})



@app.route("/grade_status")
def grade_status():
    with engine.begin() as conn:
        job = conn.execute(
            text("SELECT * FROM grading_jobs"),
        ).fetchall()

        if not job:
            return jsonify({"error": "Job not found"}), 404

        return render_template('status.html', results=job)


@app.route('/index')
def home():
    return render_template('index.html')


def start_worker():
    """Start the background worker in a daemon thread."""
    logging.info("🧵 Starting background worker thread...")
    worker_thread = threading.Thread(target=listen_for_jobs, daemon=True)
    worker_thread.start()


if __name__ == "__main__":
    # Prevent double-threading when using Flask's debug reloader
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        start_worker()

    app.run(host='0.0.0.0', port=5550, debug=False)
