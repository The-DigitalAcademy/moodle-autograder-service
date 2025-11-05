import requests
import json
from os import getenv
from dotenv import load_dotenv
import google.generativeai as genai
import ast

load_dotenv()

MODEL = "gemini-2.5-flash"
API_KEY = getenv("GEMINI_API_KEY")
BASE_URL = getenv("BASE_URL")
WEB_SERVICE_TOKEN = getenv("WEB_SERVICE_TOKEN")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(MODEL)


def grade_with_gemini(student_code, question, rubrictemplate):
    """
    Safely grade student code using Gemini.
    Handles cases where Gemini returns dict or malformed JSON.
    """
    prompt = f"""
You are an expert programming instructor and automatic grader.

### Task
Grade the following student's code using this rubric and the weightings set for each criterion :
{rubrictemplate}
Format your response like this:
 {{"criteria" : str,"criterionid": int, "definition": str, "levels": float}}

**Question:**  
{question}



**Instructions:**  
- Apply each criterion fairly.
- You may simulate test cases mentally; do not run code.
- Be concise and constructive.

Respond **only** in this JSON format:


{{
   
    "evaluation_details": [ 
       { {
            "criteria": "Correctness",
            "criterionid": 1,
            "definition": "Ease of reading and understanding.",
            "levels": 4.5
        }},
        {{
            "criteria": "Logic",
            "criterionid": 2,
            "definition": "Thoroughness of topic coverage.",
            "levels": 3.0
        }}
    ]
}}

**Student Code:**
{student_code}
"""
    try:
        response = model.generate_content(prompt)

        if isinstance(response.text, dict):
            return response.text

        raw = response.text.strip()
        if raw.startswith("```json"):
            raw = raw[7:-3].strip()

        try:
            return json.loads(raw)
        except:
            return ast.literal_eval(raw)

    except Exception as e:
        return {"error": str(e)}


def send_to_moodle(job, evaluation_details):
    """
    Sends graded result to Moodle using webservice API.
    """
    params = {
        "wstoken": WEB_SERVICE_TOKEN,
        "wsfunction": "mod_assign_save_grade",
        "moodlewsrestformat": "json",
        "assignmentid": job["assignmentid"],
        "userid": job["userid"],
        "grade": "50",
        "attemptnumber": "-1",
        "addattempt": "0",
        "workflowstate": "graded",
        "applytoall": "0",
        "plugindata[assignfeedbackcomments_editor][text]": job["github_link"],
        "plugindata[assignfeedbackcomments_editor][format]": "1",
    }

    for i, criterion in enumerate(evaluation_details):
        criterion_id = criterion.get("criterionid", 0)
        level = criterion.get("levels", 0)
        params[f"advancedgradingdata[rubric][criteria][{i}][criterionid]"] = criterion_id
        params[f"advancedgradingdata[rubric][criteria][{i}][fillings][{i}][criterionid]"] = criterion_id
        params[f"advancedgradingdata[rubric][criteria][{i}][fillings][{i}][levelid]"] = level
        params[f"advancedgradingdata[rubric][criteria][{i}][fillings][{i}][remark]"] = f"Automatically graded: {criterion.get('definition','')}"
    
    try:
        import urllib.parse

        # Encode params for URL
        encoded_params = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        final_url = f"{BASE_URL}?{encoded_params}"


        response = requests.post(BASE_URL, data=params)
        return response.json()
    except Exception as e:
        return {"error": str(e) +  "*****" + final_url}
