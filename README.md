<!-- # LMS-Auto_Grader
# 🤖 AI Autograder

An AI-powered Flask backend that grades student code submissions using **Google Gemini 2.5 Flash** and syncs results to **PostgreSQL** and **Moodle**.

---

## 🚀 Setup Instructions

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/yourusername/ai-autograder.git
cd ai-autograder
```

### 2️⃣ Create and Activate Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Configure Environment Variables

You can set environment variables:
```bash
export DATABASE_URL="postgresql://<user>:<password>@<host>:<port>/<database>"
export GEMINI_API_KEY="your_google_gemini_api_key"
```

Or edit the values directly in `app.py`:
```python
DATABASE_URL = "postgresql://username:password@host:port/db_name"
API_KEY = "your_gemini_api_key"
```

---

## 🧠 How It Works

The API receives a POST request with JSON like this:
```json
{
  "onlinetextid": "30",
  "submissionid": "1",
  "onlinetext": "<p>https://github.com/The-DigitalAcademy/moodle-local-autograder-plugin</p>",
  "userid": "2",
  "status": "submitted",
  "courseid": "2",
  "assignmentid": "1",
  "assignmentname": "Coding Project",
  "assignmentintro": "<p>Project introduction</p>",
  "assignmentactivity": "<p>project instructions: submit a link to your github repo</p>",
  "assignmentgrade": "100",
  "assignmentrubric": {
    "name": "Rubric Name",
    "description": "Rubric Description",
    "criteria": [
      {
        "criterionid": "1",
        "criterion": "documentation",
        "levels": [
          {"id": "1", "definition": "little to no documentation", "score": "0.00000"},
          {"id": "2", "definition": "good documentation", "score": "25.00000"}
        ]
      },
      // ... more criteria
    ]
  }
}
```

### Backend Flow
1. Fetches the student’s code from GitHub.  
2. Sends the question, rubric, and code to **Gemini 2.5 Flash**.  
3. Parses the JSON response containing:
   - `score`
   - `feedback`
   - `suggestions`
   - `evaluation_details` (criteria-level scores)  
4. Stores results in **PostgreSQL**.  
5. Returns structured JSON feedback to the client (or Moodle).

---

## 📡 API Endpoint

### POST `/grade`

**Request Body:**
```json
{
  "email": "student@example.com",
  "assignmentid": 1,
  "userid": 2,
  "assignmentactivity": "Write a function to reverse a string.",
  "onlinetext": "https://raw.githubusercontent.com/user/repo/main/script.py",
  "assignmentrubric": {
    "criteria": "| Criterion | Description | Total Weight |\n| Correctness | Output matches expected result | 25 | ..."
  }
}
```

**Response Example:**
```json
{
  "score": 86,
  "feedback": "Good job — logic is solid but could improve error handling.",
  "suggestions": "Consider adding more exception coverage for edge cases."
}
```

---

## 🧮 Database Schema

### Table: `users`
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| name | String | Full name |
| email | String | Unique user email |
| hashed_password | String | Bcrypt-hashed password |
| role | String | `learner` or `admin` |

### Table: `grades`
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| user_email | String | Linked to user email |
| question | Text | The problem/question text |
| llm_score | Integer | AI-calculated score |
| final_score | Integer | Final grade stored |
| feedback | Text | AI-generated comments |
| suggestions | Text | Improvement advice |
| timestamp | DateTime | Auto-generated on creation |

---

## 🧑‍🏫 Rubric Template

| Criterion | Description | Weight |
|------------|--------------|--------|
| Correctness | Produces correct output | 25 |
| Logic | Proper problem-solving approach | 12 |
| Style | Code readability | 11 |
| Naming | Descriptive variable/function names | 11 |
| Test Cases | Passes at least 15/20 test cases | 11 |
| Error Handling | Handles errors gracefully | 12 |
| Efficiency | Optimized performance | 12 |
| Documentation | Clear and helpful docstrings | 6 |

---

## 🧰 Running the Server
```bash
python app.py
```
Server runs on:
```
http://0.0.0.0:5024
```

---

## 🔄 Moodle Integration

The API constructs and encodes a Moodle web service URL using:
```
/webservice/rest/server.php?wsfunction=mod_assign_save_grade&moodlewsrestformat=json&...
```
It supports **rubric-level grading** and **automatic feedback publishing**.

---

## 🧪 Example Workflow
1. Student submits code via Moodle or GitHub.  
2. Flask app fetches and grades the code.  
3. Gemini model returns scores + feedback.  
4. Grade is stored in PostgreSQL.  
5. Moodle is updated automatically via the REST endpoint.

---

## 🛡️ Security Notes
- Store API keys securely (use environment variables).
- Use hashed passwords (bcrypt) for user storage.
- Enable HTTPS and authentication for production environments.

--- -->




# 📘 Flask Postgres-Based AI Autograder (No Redis)

## 🚀 Overview
This project provides a lightweight **AI-powered autograder** built with **Flask** and **PostgreSQL**.  
It queues grading jobs directly in the database (no Redis required) and uses a **Gemini model** to evaluate student submissions from GitHub links.  
The system then posts results back to **Moodle** via REST API.

---

## 🧩 Project Structure

```
autograder/
│
├── app.py                # Flask app — handles submissions and creates jobs
├── worker.py             # Background worker listening for new jobs
├── tasks.py              # Gemini grading + Moodle posting logic
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (DB, API keys, etc.)
└── README.md             # You are here
```

---

## ⚙️ Setup Instructions

### 1️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 2️⃣ Set environment variables in `.env`
Example:
```
DATABASE_URL=postgresql://username:password@localhost:5432/student_grades
GEMINI_API_KEY=your_google_genai_key
BASE_URL=https://yourmoodleurl/webservice/rest/server.php
WEB_SERVICE_TOKEN=your_moodle_token
```

### 3️⃣ Initialize PostgreSQL schema
```sql
CREATE TABLE grading_jobs (
  id SERIAL PRIMARY KEY,
  userid VARCHAR(100),
  question TEXT,
  github_link TEXT,
  rubric JSONB,
  status VARCHAR(50) DEFAULT 'queued',
  result JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### 4️⃣ Start the Flask app
```bash
python app.py
```

### 5️⃣ Start the Worker
```bash
python worker.py
```

---

## 🧠 How It Works

The API receives a POST request with JSON like this:
```json
{
  "onlinetextid": "30",
  "submissionid": "1",
  "onlinetext": "<p>https://github.com/The-DigitalAcademy/moodle-local-autograder-plugin</p>",
  "userid": "2",
  "status": "submitted",
  "courseid": "2",
  "assignmentid": "1",
  "assignmentname": "Coding Project",
  "assignmentintro": "<p>Project introduction</p>",
  "assignmentactivity": "<p>project instructions: submit a link to your github repo</p>",
  "assignmentgrade": "100",
  "assignmentrubric": {
    "name": "Rubric Name",
    "description": "Rubric Description",
    "criteria": [
      {
        "criterionid": "1",
        "criterion": "documentation",
        "levels": [
          {"id": "1", "definition": "little to no documentation", "score": "0.00000"},
          {"id": "2", "definition": "good documentation", "score": "25.00000"}
        ]
      },
      // ... more criteria
    ]
  }
}
```

1. A POST request is made to the Flask API with:
   - `userid`
   - `assignmentactivity` (question)
   - `onlinetext` (GitHub URL)
   - `rubric` (JSON)

2. The Flask app inserts a new job into the `grading_jobs` table.

3. PostgreSQL triggers a `NOTIFY` event (`new_grading_job`), which the worker listens for.

4. The worker:
   - Fetches the student code from the GitHub link.
   - Sends the code and rubric to the Gemini model for grading.
   - Parses the response safely, even if malformed.
   - Posts the results back to Moodle via API.
   - Updates the job status and result in the DB.

---

## 🔍 Troubleshooting

- **Error:** `the JSON object must be str, not dict`  
  ✅ Fixed in this version with safe JSON parsing in `tasks.py`.

- **Worker not responding?**  
  Ensure PostgreSQL notifications are working (`LISTEN/NOTIFY` support).

- **Moodle not updating grades?**  
  Check your `BASE_URL` and `WEB_SERVICE_TOKEN`.

---

## 🧑‍💻 Author
Built by **Sbusiso Phakathi**  
For use in **AI autograding**, **learnership automation**, and **academic integrations**.

---

## 🧾 License
MIT License — free for educational and commercial use.
