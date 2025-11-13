# 🧠 Moodle Auto-Grader Service

This project is an **automated code grading service** that integrates **Moodle**, **GitHub**, **RabbitMQ**, and **Google Gemini (Generative AI)**.  
It listens for student submissions from Moodle, retrieves the associated GitHub repository, performs an AI-powered code review based on a given rubric, and automatically sends the grading results back to Moodle.

---

## 🚀 How It Works

1. A student submits their assignment in Moodle, including a **GitHub repository link**.
2. Moodle sends a message to a **RabbitMQ queue** with submission details.
3. This service:
   - Listens for new messages in the queue.
   - Fetches the student's code from GitHub.
   - Uses a Gemini AI model to review and grade the code.
   - Sends structured grading results and feedback back to Moodle.
   - Send an autograding status report to the databse for the Autograder dahsboard

## ⚙️ Installation

Clone the Repository and install dependancies

```
git clone https://github.com/The-DigitalAcademy/LMS-Auto_Grader
cd LMS-Auto_Grader
pip install -r requirements.txt
```

Create a `.env` file in the root directory:

```
# RabbitMQ
MQ_HOST=localhost
QUEUE=grading_queue

# GitHub
GITHUB_TOKEN=your_github_personal_access_token

# Moodle API
MOODLE_API_URL=https://yourmoodle.com/webservice/rest/server.php
MOODLE_API_TOKEN=your_moodle_webservice_token

# Gemini API
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash

# Supabase API
SUPABASE_API_URL=https://<supabase-web-address>/rest/v1
SUPABASE_API_KEY=your_supabase_api_key
```

## 🧠 Usage

Start the Service

```
python main.py
```

The service will:

- Connect to RabbitMQ.
- Wait for new submissions.
- Process each submission automatically.

## 🧪 Testing

You can simulate a Moodle message by publishing to your RabbitMQ queue manually:

```
import pika, json

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
channel.queue_declare(queue='grading_queue', durable=True)

message = {
    "onlinetextid": "35",
	"submissionid": "1",
	"onlinetext": "https://github.com/{owner}/{repo}",
	"userid": "2",
	"status": "submitted",
	"courseid": "2",
	"assignmentid": "1",
	"assignmentname": "Assignment 1",
	"assignmentintro": "Create a python function",
	"assignmentactivity": "Create a python file. In it, write a function called divide_numbers. The function should take 2 arguments: The dividend and the divisor. The function should return the quotient of the division operation. The function should throw an error if the divisor is 0.",
	"assignmentgrade": "100",
	"timecreated": "1761309698",
        "assignmentrubric": {
            "name": "Rubric Name",
            "description": "Rubric Description",
            "criteria": [
                {
                    "criterionid": "1",
                    "criteriondescription": "Correctness & Functionality",
                    "levels": [{"id": "1", "definition": "major specifications are not met.", "score": "5.00000"}]
                }
            ]
        // ... more criteria
  }
}

channel.basic_publish(exchange='', routing_key='grading_queue', body=json.dumps(message))
connection.close()
```
