from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import json, os

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)


@app.route("/grade", methods=["POST"])
def grade_code():
    data = request.json
    github_link = data.get("onlinetext")
    userid = data.get("userid")
    question = data.get("assignmentactivity")
    assignmentid = data.get("assignmentid")
    assignmentname = data.get("assignmentname")
    assignmentintro = data.get("assignmentintro")
    rubric_key = data.get("rubric_key", "simple_addition")
    rubric = data.get("assignmentrubric")

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

    return jsonify({"status": "queued", "job_id": job_id})


@app.route("/grade_status/<int:job_id>")
def grade_status(job_id):
    with engine.begin() as conn:
        job = conn.execute(
            text("SELECT status, result FROM grading_jobs WHERE id=:id"),
            {"id": job_id}
        ).fetchone()

        if not job:
            return jsonify({"error": "Job not found"}), 404

        return jsonify({"status": job.status, "result": job.result})


@app.route('/index')
def home():
    return render_template('index.html')


@app.route('/static/<path:path>')
def send_static(path):
    return app.send_static_file(path)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5546, debug=True)
