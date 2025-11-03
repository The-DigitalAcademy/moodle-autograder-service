

# from flask import Flask, request, jsonify, render_template
# from flask_cors import CORS
# from datetime import datetime
# from os import getenv
# from dotenv import load_dotenv


# import google.generativeai as genai
# import json
# import requests

# app = Flask(__name__)

# CORS(app, resources={r"/api/*": {"origins": "https://dms-api-d6fbfmhpd9erb3a2.southafricanorth-01.azurewebsites.net"}})


# load_dotenv()

# MODEL = "gemini-2.5-flash"
# API_KEY = getenv("GEMINI_API_KEY")




# genai.configure(api_key=API_KEY)
# model = genai.GenerativeModel(MODEL)



# def grade_with_gemini(student_code, question, rubrictemplate):
#     """Grade student's code using Gemini and fixed rubric."""
#     prompt = f"""
# You are an expert programming instructor and automatic grader.

# ### Task
# Grade the following student's code using this rubric and the weightings set for each criterion :
# {rubrictemplate}
# Format your response like this:
#  {{"criteria" : str,"criterionid": int, "definition": str, "levels": float}}

# **Question:**  
# {question}



# **Instructions:**  
# - Apply each criterion fairly.
# - You may simulate test cases mentally; do not run code.
# - Be concise and constructive.

# Respond **only** in this JSON format:


# {{    
#     "evaluation_details": [ 
  
#        { {
#             "criteria": "Correctness",
#             "criterionid": 1,
#             "definition": "Good Documentation",
#             "levels": 4.5
#         }},
#         {{
#             "criteria": "Logic",
#             "criterionid": 2,
#             "definition": "No logic at all",
#             "levels": 0.0
#         }}
#     ]
# }}

# **Student Code:**
# {student_code}
# """
#     try:
#         response = model.generate_content(prompt)
#         raw = response.text.strip()
#         if raw.startswith("```json"):
#             raw = raw[7:-3].strip()
#         return json.loads(raw)
#     except Exception as e:
#         return {f"Error: {e}"}

# @app.route("/grade", methods=["POST"])
# def grade_code():
#     """
#         Expects JSON:
#         {
#         "onlinetextid": "30",
#         "submissionid": "1",
#         "onlinetext": "https://raw.githubusercontent.com/Sbusiso-Phakathi/ytgi/refs/heads/main/rx.js",
#         "userid": "2",
#         "status": "submitted",
#         "courseid": "2",
#         "assignmentid": "1",
#         "assignmentname": "Coding Project",
#         "assignmentintro": "Project introduction",
#         "assignmentactivity": "Create a function that takes in two numbers, add them and return their sum",
#         "assignmentgrade": "100",
#         "assignmentrubric": {
#             "name": "Rubric Name",
#             "description": "Rubric Description",
#             "criteria": [
#                 {
#                     "criterionid": "1",
#                     "criterion": "Correctness",
#                     "levels": [
#                         {"id": "1", "definition": "little to no documentation", "score": 0},
#                         {"id": "2", "definition": "good documentation", "score": 25}
#                     ]
#                 },
#                 {
#                     "criterionid": "2",
#                     "criterion": "Logic",
#                     "levels": [
#                         {"id": "3", "definition": "partial functionality", "score": 15},
#                         {"id": "4", "definition": "fully functional", "score": 25}
#                     ]
#                 }
#             ]
#         }
#     }'

#     """
#     data = request.json
#     userid = data.get("userid")
#     question = data.get("assignmentactivity")
#     github_link = data.get("onlinetext")

#     if not userid or not question or not github_link:
#         return jsonify({"error": "Missing required fields: email, question, github_link"}), 400

#     try:
#         resp = requests.get(github_link.strip())
#         if resp.status_code != 200:
#             return jsonify({"error": f"Failed to fetch GitHub file ({resp.status_code})"}), 400
#         student_code = resp.text
#     except Exception as e:
#         return jsonify({"error": str(e)}), 400
    
#     rubrictemplate = data.get("assignmentrubric").get("criteria")

#     result = grade_with_gemini(student_code, question, rubrictemplate)

#     # Base URL and params
#     base_url = "{{baseUrl}}/webservice/rest/server.php"
#     params = {
#         "wstoken": "{{webServiceToken}}",
#         "wsfunction": "mod_assign_save_grade",
#         "moodlewsrestformat": "json",
#         "assignmentid": data["assignmentid"],
#         "userid": data["userid"],
#         "grade": "50",  
#         "attemptnumber": "-1",
#         "addattempt": "0",
#         "workflowstate": "graded",
#         "applytoall": "0",
#         "plugindata[assignfeedbackcomments_editor][text]": data["onlinetext"],
#         "plugindata[assignfeedbackcomments_editor][format]": "1",
#     }

#     evaluation_details = result.get("evaluation_details", "")
#     for i, criterion in enumerate(evaluation_details):
#         criterion_id = criterion["criterionid"]
#         level = criterion["levels"]
#         params[f"advancedgradingdata[rubric][criteria][{i}][criterionid]"] = criterion_id
#         params[f"advancedgradingdata[rubric][criteria][{i}][fillings][{i}][criterionid]"] = criterion_id
#         params[f"advancedgradingdata[rubric][criteria][{i}][fillings][{i}][levelid]"] = level
#         params[f"advancedgradingdata[rubric][criteria][{i}][fillings][{i}][remark]"] = f"Automatically graded: {criterion['definition']}"
    
#     import urllib.parse
    

#     encoded_params = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
#     final_url = f"{base_url}?{encoded_params}"


#     try:
#         response = requests.post(base_url, data=params)
#         moodle_response = response.json()
#     except Exception as e:
#         return jsonify({"error": f"Failed to send data to Moodle: {str(e)}"}), 500


#     return moodle_response



# @app.route('/index')
# def home():
#     return render_template('index.html')

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5510, debug=True)

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
    app.run(host='0.0.0.0', port=5535, debug=True)
