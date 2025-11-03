# LMS-Auto_Grader
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

---

