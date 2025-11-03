
import io
import psycopg2
from PIL import Image
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
from os import getenv
from dotenv import load_dotenv

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, func
from sqlalchemy.orm import sessionmaker, declarative_base
import bcrypt
import google.generativeai as genai
import json
import requests

app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": "https://dms-api-d6fbfmhpd9erb3a2.southafricanorth-01.azurewebsites.net"}})


load_dotenv()

MODEL = "gemini-2.5-flash"
DATABASE_URL = getenv("DATABASE_URL")
DATABASE_URL2 = getenv("DATABASE_URL2")
API_KEY = getenv("GEMINI_API_KEY")


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Grade(Base):
    __tablename__ = "grades"
    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, index=True)
    question = Column(Text)
    llm_score = Column(Integer)
    final_score = Column(Integer)
    feedback = Column(Text)
    suggestions = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="learner")

Base.metadata.create_all(bind=engine)

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(MODEL)



def save_grade_to_db(entry):
    db = SessionLocal()
    grade = Grade(
        user_email=entry["email"],
        question=entry["question"],
        llm_score=entry["llm_score"],
        final_score=entry["final_score"],
        feedback=entry["feedback"],
        suggestions=entry["suggestions"]
    )
    db.add(grade)
    db.commit()
    db.close()

def grade_with_gemini(student_code, question, rubrictemplate):
    """Grade student's code using Gemini and fixed rubric."""
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
    "score": 12,
    "feedback": "Great effort on the introduction.",
    "suggestions": "Review the citation style for the bibliography.",
    "evaluation_details": [ // Assuming a container key like this
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
        raw = response.text.strip()
        if raw.startswith("```json"):
            raw = raw[7:-3].strip()
        return json.loads(raw)
    except Exception as e:
        return {"score": 0, "feedback": f"Error: {e}", "suggestions": "N/A"}

@app.route("/grade", methods=["POST"])
def grade_code():
    """
        Expects JSON:
        {
        "onlinetextid": "30",
        "submissionid": "1",
        "onlinetext": "https://raw.githubusercontent.com/Sbusiso-Phakathi/ytgi/refs/heads/main/rx.js",
        "userid": "2",
        "status": "submitted",
        "courseid": "2",
        "assignmentid": "1",
        "assignmentname": "Coding Project",
        "assignmentintro": "Project introduction",
        "assignmentactivity": "Create a function that takes in two numbers, add them and return their sum",
        "assignmentgrade": "100",
        "assignmentrubric": {
            "name": "Rubric Name",
            "description": "Rubric Description",
            "criteria": [
                {
                    "criterionid": "1",
                    "criterion": "Correctness",
                    "levels": [
                        {"id": "1", "definition": "little to no documentation", "score": 0},
                        {"id": "2", "definition": "good documentation", "score": 25}
                    ]
                },
                {
                    "criterionid": "2",
                    "criterion": "Logic",
                    "levels": [
                        {"id": "3", "definition": "partial functionality", "score": 15},
                        {"id": "4", "definition": "fully functional", "score": 25}
                    ]
                }
            ]
        }
    }'

    """
    data = request.json
    userid = data.get("userid")
    question = data.get("assignmentactivity")
    github_link = data.get("onlinetext")

    if not userid or not question or not github_link:
        return jsonify({"error": "Missing required fields: email, question, github_link"}), 400

    try:
        resp = requests.get(github_link.strip())
        if resp.status_code != 200:
            return jsonify({"error": f"Failed to fetch GitHub file ({resp.status_code})"}), 400
        student_code = resp.text
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
    rubrictemplate = data.get("assignmentrubric").get("criteria")

    result = grade_with_gemini(student_code, question, rubrictemplate)
    final_score = result.get("score", 0)

    # Base URL and params
    base_url = "{{baseUrl}}/webservice/rest/server.php"
    params = {
        "wstoken": "{{webServiceToken}}",
        "wsfunction": "mod_assign_save_grade",
        "moodlewsrestformat": "json",
        "assignmentid": data["assignmentid"],
        "userid": data["userid"],
        "grade": "50",  
        "attemptnumber": "-1",
        "addattempt": "0",
        "workflowstate": "graded",
        "applytoall": "0",
        "plugindata[assignfeedbackcomments_editor][text]": data["onlinetext"],
        "plugindata[assignfeedbackcomments_editor][format]": "1",
    }

    evaluation_details = result.get("evaluation_details", "")
    for i, criterion in enumerate(evaluation_details):
        criterion_id = criterion["criterionid"]
        level = criterion["levels"]
        params[f"advancedgradingdata[rubric][criteria][{i}][criterionid]"] = criterion_id
        params[f"advancedgradingdata[rubric][criteria][{i}][fillings][{i}][criterionid]"] = criterion_id
        params[f"advancedgradingdata[rubric][criteria][{i}][fillings][{i}][levelid]"] = level
        params[f"advancedgradingdata[rubric][criteria][{i}][fillings][{i}][remark]"] = f"Automatically graded: {criterion['definition']}"
    
    import urllib.parse
    

    encoded_params = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    final_url = f"{base_url}?{encoded_params}"

    print(final_url)

    save_grade_to_db({
        "email": userid,
        "question": question,
        "llm_score": final_score,
        "final_score": final_score,
        "feedback": result.get("feedback", ""),
        "suggestions": result.get("suggestions", "")
    })


    # return jsonify({
    #     "score": final_score,
    #     "feedback": result.get("feedback", ""),
    #     "suggestions": result.get("suggestions", "")
    # })
    return final_url



########## Face Recognition Service. ################
#####################
###############################
###############
#################
################################



def decode_base64_to_image(base64_string):
    if "base64," in base64_string:
        base64_string = base64_string.split("base64,")[1]
    
    img_data = base64.b64decode(base64_string)
    image = Image.open(io.BytesIO(img_data))
    image_np = np.array(image.convert("RGB"))
    return image_np

def get_known_face_base64(user_id):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print((user_id))

        cur.execute('SELECT image FROM "learners" WHERE id = %s LIMIT 1;', (user_id,))
        result = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if result:
            return result[0]
        else:
            return None
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return None

def add_attendance(user_id, latitude, longitude):
    print("dcdscdsdcfsdcfsdcdddddd")
    try:
        print("erferf")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        cur.execute('INSERT INTO "learner_attendances" (learner_id, latitude, longitude, updated_at, created_at) VALUES (%s, %s, %s, %s, %s);', (user_id, latitude, longitude, datetime.utcnow(), datetime.utcnow()))
        conn.commit()
        cur.close()
        conn.close()
    except psycopg2.Error as e:
        print(f"Database error (attendance insert): {e}")
        return False
    return True

@app.route('/verify', methods=['POST'])
def verify_face():
    if not request.json or 'image' not in request.json or 'user_id' not in request.json:
        return jsonify({"error": "Missing 'image' or 'user_id' key in JSON payload."}), 400

    base64_image = request.json['image']
    user_id = request.json['user_id']
    latitude = request.json.get('latitude')
    longitude = request.json.get('longitude')

    try:
        known_base64 = get_known_face_base64(user_id)
        if not known_base64:
            return jsonify({"error": "No known face found for the given user_id."}), 404

        known_image_np = decode_base64_to_image(known_base64)
        known_face_encoding = face_recognition.face_encodings(known_image_np)[0]

    except IndexError:
        return jsonify({"error": "No face found in the known image for this user."}), 500
    except Exception as e:
        return jsonify({"error": f"Failed to process known image: {e}"}), 500

    try:
        unknown_image_np = decode_base64_to_image(base64_image)
    except Exception as e:
        return jsonify({"error": f"Failed to decode Base64 image: {e}"}), 400

    unknown_face_encodings = face_recognition.face_encodings(unknown_image_np)

    if not unknown_face_encodings:
        return jsonify({"match": False, "message": "No face found in the provided image."}), 404

    unknown_face_encoding = unknown_face_encodings[0]

    results = face_recognition.compare_faces([known_face_encoding], unknown_face_encoding, tolerance=0.39)
    face_distance = face_recognition.face_distance([known_face_encoding], unknown_face_encoding)[0]
    match = bool(results[0])

    if match:
        if latitude is not None and longitude is not None:
            success = add_attendance(user_id, latitude, longitude)
            if not success:
                return jsonify({"error": "Face matched, but failed to record attendance"}), 500

        return jsonify({
            'status': 200,
            'data': "match successful and attendance recorded"
        }), 200
    
    else:
        return jsonify({
            'status': 400,
            'data': "match failed"
        }), 400

@app.route('/add')
def add_learner_page():
    return render_template('add_learner.html')

@app.route('/auto-verify')
def auto_verify_page():
    return render_template('auto_verify.html')

def insert_new_learner(name, surname, base64_image):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        insert_query = """
        INSERT INTO "learners" (firstname, lastname, image, cohort_id,updated_at)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
        """
        import datetime
        cur.execute(insert_query, (name, surname, base64_image, 20, datetime.datetime.now()))
        learner_id = cur.fetchone()[0]
        
        conn.commit()
        cur.close()
        conn.close()
        
        return learner_id
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return None

@app.route('/add_learner', methods=['POST'])
def add_learner():
    if not request.json or 'name' not in request.json or 'surname' not in request.json or 'image' not in request.json:
        return jsonify({"error": "Missing 'name', 'surname', or 'image' key in JSON payload."}), 400
    
    name = request.json['name']
    surname = request.json['surname']
    base64_image = request.json['image']

    try:
        image_np = decode_base64_to_image(base64_image)
        face_encodings = face_recognition.face_encodings(image_np)
        if not face_encodings:
            return jsonify({"error": "No face found in the provided image. Learner not added."}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to process image: {e}"}), 400

    learner_id = insert_new_learner(name, surname, base64_image)
    print(learner_id)
    if learner_id:
        return jsonify({
            "status": 201,
            "message": "Learner added successfully.",
            "learner_id": learner_id
        }), 201
    else:
        return jsonify({
            "status": 500,
            "message": "Failed to add learner due to a database error."
        }), 500

@app.route('/index')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
