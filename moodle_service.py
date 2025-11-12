import os, requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load Moodle API credentials from environment variables.
MOODLE_API_URL = os.getenv('MOODLE_API_URL')
MOODLE_API_TOKEN = os.getenv('MOODLE_API_TOKEN')

class MoodleService:
    """
    Service class for interacting with the Moodle web service API.

    This class provides a static interface to send grade data (including rubric feedback)
    to a Moodle assignment using the `mod_assign_save_grade` function.

    The method assumes that the Moodle web services have been enabled and configured
    with an API token that has permissions to modify assignment grades.
    """

    @staticmethod
    def save_grade(assignmentid: int, userid: int, grade_results: dict) -> None:
        """
        Save a student's grade and rubric feedback for a specific Moodle assignment.

        Args:
            assignmentid (int): The Moodle assignment ID.
            userid (int): The Moodle user ID of the student being graded.
            grade_results (dict): A dictionary containing:
                - 'feedback_comment' (str): The overall feedback comment.
                - 'criteria_results' (list[dict]): Rubric grading details where each item includes:
                    * 'criterionid' (int): The criterion ID in the rubric.
                    * 'levelid' (int): The level selected for that criterion.
                    * 'remark' (str): Any comments specific to that criterion.

        Example:
            grade_results = {
                "feedback_comment": "Excellent work!",
                "criteria_results": [
                    {"criterionid": 12, "levelid": 34, "remark": "Good logic"},
                    {"criterionid": 13, "levelid": 36, "remark": "Great structure"}
                ]
            }

            MoodleService.save_grade(9, 21, grade_results)

        Raises:
            requests.HTTPError: If the POST request to Moodle fails.
            ValueError: If the Moodle API credentials are missing.

        """

        if not MOODLE_API_URL or not MOODLE_API_TOKEN:
            raise ValueError("Missing Moodle API credentials (MOODLE_API_URL or MOODLE_API_TOKEN).")
        
        # Base parameters required for Moodle's REST API call
        params = {
            'wstoken': MOODLE_API_TOKEN,
            'wsfunction': 'mod_assign_save_grade',
            'moodlewsrestformat': 'json',
            'assignmentid': assignmentid,
            'userid': userid,
            'grade': '100',
            'attemptnumber': '-1',
            'addattempt': '0',
            'workflowstate': 'graded',
            'applytoall': '0',
            'plugindata[assignfeedbackcomments_editor][text]': grade_results.get('feedback_comment', ''),
            'plugindata[assignfeedbackcomments_editor][format]': '1',
        }

         # Populate rubric (advanced grading) data
        for i, criterion in enumerate(grade_results['criteria_results'] or []):
            params[f'advancedgradingdata[rubric][criteria][{i}][criterionid]'] = criterion.get('criterionid')
            params[f'advancedgradingdata[rubric][criteria][{i}][fillings][{i}][criterionid]'] = criterion.get('criterionid')
            params[f'advancedgradingdata[rubric][criteria][{i}][fillings][{i}][levelid]'] = criterion.get('levelid')
            params[f'advancedgradingdata[rubric][criteria][{i}][fillings][{i}][remark]'] = criterion.get('remark')
        
        # Perform the API request
        response = requests.post(MOODLE_API_URL, params=params)
        if not response.ok:
            # Log error or raise exception if Moodle returns a failure
            raise requests.HTTPError(f"Moodle API request failed: {response.status_code} - {response.text}")
