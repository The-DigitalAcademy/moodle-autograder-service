import requests, os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Get Supabase API credentials from environment variables
SUPABASE_API_URL = os.getenv('SUPABASE_API_URL')
SUPABASE_API_KEY = os.getenv('SUPABASE_API_KEY')

class StatusReportService:
    """
    A service class responsible for sending status reports to a Supabase endpoint.

    This service is typically used to log or update the status of automated grading
    or processing tasks related to student submissions.
    """

    @staticmethod
    def send_report(submission: dict, status: str, details: str = ""):
        """
        Sends a status report to the Supabase API.

        Args:
            submission (dict): A dictionary containing submission metadata and assignment details.
            status (str): The current autograde status (e.g., "success", "failed", "pending").
            details (str, optional): Optional text providing additional information about the status.

        Raises:
            requests.HTTPError: If the API request fails or returns a non-200 response.

        Example:
            submission = {
                "submissionid": 123,
                "userid": 45,
                "status": "submitted",
                "courseid": 10,
                "assignmentid": 55,
                "assignmentname": "Basic Programming",
                "assignmentintro": "Intro assignment for Python basics",
                "assignmentactivity": "Write three simple Python programs",
                "onlinetext": "https://github.com/student/basic-programming-project",
                "timecreated": "1761309698"
            }

            StatusReportService.send_report(submission, status="success", details="Autograde completed successfully.")
        """

        # --- Basic Input Validation ---
        if not SUPABASE_API_URL or not SUPABASE_API_KEY:
            raise ValueError("Missing Supabase configuration. Check your .env file.")
        
        if not isinstance(submission, dict):
            raise TypeError("The 'submission' argument must be a dictionary.")
        
        required_keys = [
            "submissionid", "userid", "status", "courseid",
            "assignmentid", "assignmentname", "timecreated"
        ]

        missing_keys = [key for key in required_keys if key not in submission]

        if missing_keys:
            raise ValueError(f"Missing required submission fields: {', '.join(missing_keys)}")
        
        if not isinstance(status, str) or not status.strip():
            raise ValueError("Invalid 'status' value. It must be a non-empty string.")

        if not isinstance(details, str):
            raise TypeError("The 'details' argument must be a string.")


        # request headers
        headers = {
            "apiKey": SUPABASE_API_KEY,
            'Content-Type': 'application/json'
        }

        # Prepare the payload using data extracted from the submission dictionary

        unix_timestamp = int(submission.get("timecreated"))
        payload = {
            "submission_id": submission.get("submissionid"),
            "user_id": submission.get("userid"),
            "submission_status": submission.get("status"),
            "course_id": submission.get("courseid"),
            "assignment_id": submission.get("assignmentid"),
            "assignment_name": submission.get("assignmentname"),
            "assignment_intro": submission.get("assignmentintro"),
            "assignment_activity": submission.get("assignmentactivity"),
            "submission_content": submission.get("onlinetext"),
            "submitted_at": f"{datetime.utcfromtimestamp(unix_timestamp)}",
            "autograde_status": status,
            "autograde_status_details": details
        }

        # Send the HTTP POST request to the Supabase API
        response = requests.post(f"{SUPABASE_API_URL}/autograde_worker_log", json=payload, headers=headers)
        if not response.ok:
            raise requests.HTTPError(f"Supabase API request failed: {response.status_code} - {response.text}")
        