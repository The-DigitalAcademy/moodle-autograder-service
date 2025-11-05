import os, json, ast, logging, requests
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
API_KEY = os.getenv('GEMINI_API_KEY')
BASE_URL = os.getenv('BASE_URL')
WEB_SERVICE_TOKEN = os.getenv('WEB_SERVICE_TOKEN')

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(MODEL)

def _safe_parse_text_to_json(text):
    # try json, then ast.literal_eval, else return dict with error
    try:
        return json.loads(text)
    except Exception:
        try:
            return ast.literal_eval(text)
        except Exception:
            return {'error': 'failed_to_parse', 'raw': text[:1000]}

def grade_with_gemini(student_code, question, rubrictemplate):
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
        resp_text = response.text
        # if model returns dict-like object, handle
        if isinstance(resp_text, dict):
            return resp_text
        resp_text = resp_text.strip()
        if resp_text.startswith('```json'):
            resp_text = resp_text[7:].rsplit('```', 1)[0].strip()
        parsed = _safe_parse_text_to_json(resp_text)
        return parsed
    except Exception as e:
        logging.exception('Gemini call failed')
        return {'error': str(e)}

def send_to_moodle(job, evaluation_details):
    params = {
        'wstoken': WEB_SERVICE_TOKEN,
        'wsfunction': 'mod_assign_save_grade',
        'moodlewsrestformat': 'json',
        'assignmentid': job['assignmentid'],
        'userid': job['userid'],
        'grade': '50',
        'attemptnumber': '-1',
        'addattempt': '0',
        'workflowstate': 'graded',
        'applytoall': '0',
        'plugindata[assignfeedbackcomments_editor][text]': job['github_link'],
        'plugindata[assignfeedbackcomments_editor][format]': '1',
    }
    for i, criterion in enumerate(evaluation_details or []):
        criterion_id = criterion.get('criterionid') if isinstance(criterion, dict) else None
        level = criterion.get('levels') if isinstance(criterion, dict) else None
        params[f'advancedgradingdata[rubric][criteria][{i}][criterionid]'] = criterion_id
        params[f'advancedgradingdata[rubric][criteria][{i}][fillings][{i}][criterionid]'] = criterion_id
        params[f'advancedgradingdata[rubric][criteria][{i}][fillings][{i}][levelid]'] = level
        params[f'advancedgradingdata[rubric][criteria][{i}][fillings][{i}][remark]'] = criterion.get('definition') if isinstance(criterion, dict) else ''
    try:
        r = requests.post(BASE_URL, data=params)
        return r.json()
    except Exception as e:
        return {'error': str(e)}
