# 🤖 Automated Gemini-Powered Code Grader

This project implements an automated code grading system using a **Flask API**, a **PostgreSQL database**, and a background **worker** powered by the **Gemini API** for code evaluation. It integrates with an external learning management system (like Moodle) for sending final grades.

---

## ⚡ Quick Start

1️⃣ **Clone the repository**
```bash
git clone https://github.com/yourusername/ai-autograder.git
cd ai-autograder
```

2️⃣ **Create and activate a virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3️⃣ **Install dependencies**
```bash
pip install -r requirements.txt
```

4️⃣ **Configure environment variables**
Create a `.env` file in the project root and add:
```bash
# PostgreSQL Database URL
DATABASE_URL="postgresql://user:password@localhost:5432/ai_autograder"

# Gemini API Configuration
GEMINI_API_KEY="your_gemini_api_key"
GEMINI_MODEL="gemini-2.5-flash"

# LMS Integration (e.g., Moodle)
BASE_URL="https://your-lms-site.com/webservice/rest/server.php"
WEB_SERVICE_TOKEN="your_moodle_web_service_token"
```

5️⃣ **Initialize the database**
```bash
psql -d ai_autograder -f init_db.sql
```

6️⃣ **Start the Flask API**
```bash
python app.py
```

7️⃣ The worker automatically listens for new grading jobs 🎧

---

## ✨ Features

* **RESTful API:** Submit grading jobs and check their status.
* **Asynchronous Processing:** Dedicated background worker to prevent API timeouts.
* **PostgreSQL Job Queue:** Uses NOTIFY/LISTEN for real-time job notifications.
* **Gemini Grading:** Evaluates student code using the Gemini model.
* **LMS Integration:** Sends grades and feedback back to systems like Moodle.

---

## 🛠️ Prerequisites

* Python 3.8+
* PostgreSQL
* Gemini API Key
* Moodle/LMS Web Service Token

**Python Dependencies:**
```
Flask==2.3.3
Flask-Cors==3.1.3
SQLAlchemy==2.0.21
psycopg2-binary==2.9.6
requests==2.31.0
python-dotenv==1.0.1
google-generativeai==0.6.0
```

---

## 💡 Usage

**Submit a Grading Job (POST /grade)**
Send a JSON payload:
```json
{
  "userid": "5",
  "assignmentactivity": "Write a Python function that adds two numbers.",
  "onlinetext": "https://raw.githubusercontent.com/user/repo/main/addition.py",
  "assignmentrubric": { "criteria": "Clarity, Correctness, Style" },
  "assignmentid": "1",
  "assignmentname": "Addition Function",
  "assignmentintro": "Implement a function to add two numbers."
}
```
**Example Response:**
```json
{
  "status": "queued",
  "job_id": 1
}
```

**Check Job Status (GET /grade_status/<job_id>)**
Possible status values:

| Status       | Description |
|-------------|-------------|
| queued      | Job is waiting for the worker. |
| in_progress | Worker is processing the job (fetching code, calling Gemini). |
| done        | Grading complete. Results include Gemini and LMS responses. |
| failed      | An error occurred during processing. |

---

## 🧩 Project Structure
```
ai-autograder/
├── app.py                  # Main Flask API
├── worker.py               # Background worker
├── db.py                   # Database helpers
├── utils.py                # Utility functions (Gemini, Moodle integration)
├── init_db.sql             # Database schema and triggers
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

---

## 🧠 How It Works

1. Submit a grading job via `/grade`.
2. PostgreSQL stores the job and triggers a `NOTIFY` event.
3. Worker receives notification and retrieves the student code.
4. Gemini evaluates the code and returns results.
5. Worker sends results back to the LMS.
6. Job status updates in PostgreSQL.

---

## 🧰 Troubleshooting

* Ensure PostgreSQL is running.
* Check `.env` variables for correctness.
* Inspect worker logs for errors.
* Query `grading_jobs` table to view job records:
```sql
SELECT * FROM grading_jobs;
```

---

## 📜 License

This project is licensed under the MIT License.

